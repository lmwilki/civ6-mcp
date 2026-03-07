#!/usr/bin/env python3
"""Sync civ-mcp JSONL files to Convex — watch mode or batch upload.

Modes:
  --watch            Stream local file changes in real-time (default).
  --upload DIR       One-shot batch upload of all local files in DIR.
  --cloud BUCKET     Batch sync from a cloud bucket (Azure Blob / GCS / S3).
  --watch --cloud BUCKET  Poll cloud bucket for changes every 30s.

Usage:
    python scripts/convex_sync.py                              # watch local (dev)
    python scripts/convex_sync.py --prod                       # watch local (prod)
    python scripts/convex_sync.py --upload ./results/          # batch local
    python scripts/convex_sync.py --cloud az://civbench --prod # batch cloud
    python scripts/convex_sync.py --watch --cloud az://civbench --prod

Env files are loaded from web/ relative to this script. Environment variables
CONVEX_URL and CONVEX_DEPLOY_KEY override file values if set.

Optional:
    CIV6_DIARY_DIR=~/.civ6-mcp   (default, for local watch mode)
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import signal
import sys
import time
from glob import glob
from pathlib import Path
from typing import Any

import httpx
import watchfiles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("convex_sync")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
WEB_DIR = SCRIPT_DIR.parent / "web"


def _load_env_file(path: Path) -> dict[str, str]:
    """Parse a .env file into a dict. Ignores comments and blank lines."""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().split("#")[0].strip()  # strip inline comments
        env[key] = value
    return env


def _resolve_config(prod: bool) -> tuple[str, str]:
    """Resolve CONVEX_URL and CONVEX_DEPLOY_KEY from env file + environment.

    Environment variables take precedence over file values.
    """
    env_file = WEB_DIR / (".env.prod" if prod else ".env.dev")
    file_env = _load_env_file(env_file)

    convex_url = os.environ.get("CONVEX_URL") or file_env.get("CONVEX_URL", "")
    deploy_key = os.environ.get("CONVEX_DEPLOY_KEY") or file_env.get(
        "CONVEX_DEPLOY_KEY", ""
    )

    # .env.local uses NEXT_PUBLIC_CONVEX_URL, .env.prod uses CONVEX_URL
    if not convex_url:
        convex_url = file_env.get("NEXT_PUBLIC_CONVEX_URL", "")

    return convex_url, deploy_key


DIARY_DIR = Path(os.environ.get("CIV6_DIARY_DIR", Path.home() / ".civ6-mcp"))
STATE_FILE = DIARY_DIR / ".sync_state.json"

# How many recent diary lines to re-check for reflection merges
DIARY_LOOKBACK = 12
# Batch size for Convex mutations
BATCH_SIZE = 50
# Idle timeout before marking a game as completed (seconds)
IDLE_TIMEOUT = 30 * 60
# Retry config
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 3, 10]

# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------


def load_state() -> dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            log.warning("Corrupt state file, starting fresh")
    return {"files": {}, "game_last_seen": {}}


def save_state(state: dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(state, indent=2))
        tmp.rename(STATE_FILE)
    except OSError:
        # Atomic rename can fail on some FS configs; fall back to direct write
        STATE_FILE.write_text(json.dumps(state, indent=2))
        tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# File classification
# ---------------------------------------------------------------------------


def classify_file(name: str) -> str | None:
    """Return file type: 'diary', 'cities', 'log', 'spatial', 'mapturns', or None."""
    if name.startswith("diary_") and name.endswith("_cities.jsonl"):
        return "cities"
    if name.startswith("diary_") and name.endswith(".jsonl"):
        return "diary"
    if name.startswith("log_") and name.endswith(".jsonl"):
        return "log"
    if name.startswith("spatial_") and name.endswith(".jsonl"):
        return "spatial"
    if name.startswith("mapturns_") and name.endswith(".jsonl"):
        return "mapturns"
    return None


def extract_game_id(name: str) -> str:
    """Extract game ID from filename: diary_india_123.jsonl → india_123"""
    name = (
        name.removesuffix("_cities.jsonl").removesuffix(".jsonl").removesuffix(".json")
    )
    for prefix in ("diary_", "log_", "spatial_", "mapstatic_", "mapturns_"):
        if name.startswith(prefix):
            name = name[len(prefix) :]
    return name


def hash_lines(lines: list[str]) -> str:
    """Content hash for a set of lines."""
    return hashlib.md5("".join(lines).encode()).hexdigest()


def discover_games(directory: Path) -> dict[str, dict[str, Path]]:
    """Scan directory for JSONL/JSON game files, grouped by game_id.

    Returns {game_id: {file_type: path, ...}, ...}
    """
    games: dict[str, dict[str, Path]] = {}
    for f in sorted(directory.iterdir()):
        if f.is_dir():
            continue
        name = f.name
        ftype = classify_file(name)
        if ftype is None:
            # Also pick up mapstatic JSON files (consumed by sync_map_data)
            if name.startswith("mapstatic_") and name.endswith(".json"):
                ftype = "mapstatic"
            else:
                continue
        game_id = extract_game_id(name)
        games.setdefault(game_id, {})[ftype] = f
    return games


# ---------------------------------------------------------------------------
# Cloud source (via fsspec)
# ---------------------------------------------------------------------------


def _get_cloud_fs(bucket_url: str) -> tuple[Any, str]:
    """Create fsspec filesystem from bucket URL.

    Returns (fs, prefix) where prefix is the path portion without scheme.
    E.g. "az://civbench" → (AzureBlobFileSystem, "civbench").
    """
    import fsspec

    scheme = bucket_url.split("://")[0]
    prefix = bucket_url[len(scheme) + 3 :]
    fs = fsspec.filesystem(scheme)
    return fs, prefix


def discover_cloud_runs(bucket_url: str) -> list[dict[str, Any]]:
    """List all runs in a cloud bucket by reading their manifest.json files."""
    fs, prefix = _get_cloud_fs(bucket_url)
    try:
        manifest_paths = fs.glob(f"{prefix}/runs/*/manifest.json")
    except Exception:
        log.exception("Failed to list cloud manifests at %s", bucket_url)
        return []

    manifests = []
    for mp in manifest_paths:
        try:
            data = json.loads(fs.cat_file(mp))
            manifests.append(data)
        except Exception:
            log.warning("Failed to read manifest: %s", mp)
    return manifests


def _cloud_run_is_complete(fs: Any, prefix: str, run_id: str) -> bool:
    """Check if a cloud run has a game_over entry in its log file."""
    log_path = f"{prefix}/runs/{run_id}/log.jsonl"
    try:
        content = fs.cat_file(log_path).decode("utf-8")
        for line in content.strip().splitlines():
            try:
                entry = json.loads(line)
                if entry.get("type") == "game_over":
                    return True
            except json.JSONDecodeError:
                continue
    except FileNotFoundError:
        pass
    except Exception:
        log.warning("Failed to read log for run %s", run_id)
    return False


def _download_cloud_run(
    fs: Any, prefix: str, run_id: str, manifest: dict[str, Any], dest_dir: Path
) -> str | None:
    """Download a cloud run's files to dest_dir with local naming conventions.

    Returns the game_id (e.g. "babylon_-1498189056_abc12345") or None.
    """
    civ = manifest.get("civ", "")
    seed = manifest.get("seed", "")

    if not civ or seed == "":
        log.warning("Run %s: incomplete manifest (no civ/seed) — skipping", run_id)
        return None

    game_id = f"{civ}_{seed}_{run_id}"

    # Cloud filename → local filename (matches LocalSink naming)
    file_map = {
        "diary.jsonl": f"diary_{game_id}.jsonl",
        "cities.jsonl": f"diary_{game_id}_cities.jsonl",
        "log.jsonl": f"log_{game_id}.jsonl",
        "spatial.jsonl": f"spatial_{game_id}.jsonl",
        "map_static.json": f"mapstatic_{game_id}.json",
        "map_turns.jsonl": f"mapturns_{game_id}.jsonl",
    }

    downloaded = 0
    for cloud_name, local_name in file_map.items():
        cloud_path = f"{prefix}/runs/{run_id}/{cloud_name}"
        local_path = dest_dir / local_name
        try:
            data = fs.cat_file(cloud_path)
            local_path.write_bytes(data)
            downloaded += 1
        except FileNotFoundError:
            pass  # Not all file types exist for every run
        except Exception:
            log.warning("Failed to download %s", cloud_path)

    if downloaded == 0:
        log.warning("Run %s: no data files found in cloud", run_id)
        return None

    log.debug("Downloaded run %s → %s (%d files)", run_id, game_id, downloaded)
    return game_id


# ---------------------------------------------------------------------------
# Convex HTTP client
# ---------------------------------------------------------------------------


class ConvexClient:
    def __init__(self, url: str, deploy_key: str) -> None:
        self.base_url = url.rstrip("/")
        self.client = httpx.AsyncClient(
            timeout=30,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Convex {deploy_key}",
            },
        )

    async def mutation(self, path: str, args: dict[str, Any]) -> Any:
        """Call a Convex mutation with retries. Raises on persistent failure."""
        url = f"{self.base_url}/api/mutation"
        payload = {"path": path, "args": args, "format": "json"}
        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = await self.client.post(url, json=payload)
                data = resp.json()
                if data.get("status") == "success":
                    return data.get("value")
                last_error = RuntimeError(
                    f"Mutation {path} failed: {data.get('errorMessage')}"
                )
                log.error("Mutation %s failed: %s", path, data.get("errorMessage"))
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_BACKOFF[attempt])
            except (httpx.HTTPError, json.JSONDecodeError) as e:
                last_error = e
                log.exception("HTTP error calling %s", path)
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_BACKOFF[attempt])
        raise last_error or RuntimeError(
            f"Mutation {path} failed after {MAX_RETRIES} retries"
        )

    async def close(self) -> None:
        await self.client.aclose()


# ---------------------------------------------------------------------------
# Sync logic per file type
# ---------------------------------------------------------------------------


async def sync_diary(
    path: Path, game_id: str, state: dict, client: ConvexClient
) -> None:
    """Sync a diary JSONL file (player rows). Handles reflection merges."""
    name = path.name
    file_state = state["files"].get(name, {"line_count": 0, "tail_hash": ""})

    lines = path.read_text().strip().splitlines()
    total = len(lines)

    if total == 0:
        return

    # Determine what to check: new lines + lookback window for merges
    old_count = file_state.get("line_count", 0)
    lookback_start = max(0, old_count - DIARY_LOOKBACK)
    tail_lines = lines[lookback_start:]
    new_hash = hash_lines(tail_lines)

    if old_count == total and new_hash == file_state.get("tail_hash"):
        return  # No changes

    # Parse rows that may be new or changed
    rows_to_upsert = []
    for line in tail_lines:
        try:
            rows_to_upsert.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not rows_to_upsert:
        return

    # Extract civ/leader from first agent row
    agent_row = next(
        (r for r in rows_to_upsert if r.get("is_agent")), rows_to_upsert[0]
    )
    civ = agent_row.get("civ", "")
    leader = agent_row.get("leader", "")
    # Read seed from row data's "game" field (= "civ_seed"), not from
    # the filename-based game_id which now includes the run_id suffix.
    game_field = agent_row.get("game", "")
    seed = game_field.rsplit("_", 1)[-1] if "_" in game_field else ""

    # Batch and send
    for i in range(0, len(rows_to_upsert), BATCH_SIZE):
        batch = rows_to_upsert[i : i + BATCH_SIZE]
        await client.mutation(
            "ingest:ingestPlayerRows",
            {
                "gameId": game_id,
                "civ": civ,
                "leader": leader,
                "seed": seed,
                "rows": batch,
            },
        )

    log.info(
        "diary %s: synced %d rows (total %d lines)", game_id, len(rows_to_upsert), total
    )
    file_state["line_count"] = total
    file_state["tail_hash"] = new_hash
    state["files"][name] = file_state
    state["game_last_seen"][game_id] = time.time()


async def sync_cities(
    path: Path, game_id: str, state: dict, client: ConvexClient
) -> None:
    """Sync a cities diary JSONL file. Append-only — use line count."""
    name = path.name
    file_state = state["files"].get(name, {"line_count": 0})

    lines = path.read_text().strip().splitlines()
    total = len(lines)
    old_count = file_state.get("line_count", 0)

    if total <= old_count:
        return

    new_lines = lines[old_count:]
    rows = []
    for line in new_lines:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not rows:
        return

    for i in range(0, len(rows), BATCH_SIZE * 2):
        batch = rows[i : i + BATCH_SIZE * 2]
        await client.mutation(
            "ingest:ingestCityRows", {"gameId": game_id, "rows": batch}
        )

    log.info("cities %s: synced %d new rows", game_id, len(rows))
    file_state["line_count"] = total
    state["files"][name] = file_state
    state["game_last_seen"][game_id] = time.time()


async def sync_log(path: Path, game_id: str, state: dict, client: ConvexClient) -> None:
    """Sync a log JSONL file. Append-only — use byte offset."""
    name = path.name
    file_state = state["files"].get(name, {"byte_offset": 0, "line_count": 0})

    file_size = path.stat().st_size
    old_offset = file_state.get("byte_offset", 0)

    if file_size <= old_offset:
        return

    with open(path, "rb") as f:
        f.seek(old_offset)
        new_bytes = f.read()

    new_text = new_bytes.decode("utf-8", errors="replace")
    new_lines = new_text.strip().splitlines()
    line_num = file_state.get("line_count", 0)

    entries = []
    for line in new_lines:
        try:
            entry = json.loads(line)
            line_num += 1
            entry["line"] = line_num
            entries.append(entry)
        except json.JSONDecodeError:
            continue

    if not entries:
        return

    civ = entries[0].get("civ", "")
    seed = str(entries[0].get("seed", ""))

    for i in range(0, len(entries), BATCH_SIZE * 2):
        batch = entries[i : i + BATCH_SIZE * 2]
        await client.mutation(
            "ingest:ingestLogEntries",
            {"gameId": game_id, "civ": civ, "seed": seed, "entries": batch},
        )

    log.info("log %s: synced %d new entries", game_id, len(entries))
    file_state["byte_offset"] = file_size
    file_state["line_count"] = line_num
    state["files"][name] = file_state
    state["game_last_seen"][game_id] = time.time()


async def sync_spatial(
    path: Path, game_id: str, state: dict, client: ConvexClient
) -> None:
    """Sync a spatial JSONL file. Aggregates per-turn and pushes to Convex."""
    name = path.name
    file_state = state["files"].get(name, {"line_count": 0})

    lines = path.read_text().strip().splitlines()
    total = len(lines)
    old_count = file_state.get("line_count", 0)

    if total <= old_count:
        return

    # Parse all entries (re-process from start for cumulative tracking)
    entries: list[dict[str, Any]] = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not entries:
        return

    # Group by turn and compute aggregates
    by_turn: dict[int, list[dict[str, Any]]] = {}
    for entry in entries:
        turn = entry.get("turn")
        if turn is None:
            continue
        by_turn.setdefault(turn, []).append(entry)

    cumulative_tiles: set[tuple[int, int]] = set()
    rows: list[dict[str, Any]] = []

    for turn in sorted(by_turn.keys()):
        turn_entries = by_turn[turn]
        turn_tiles: set[tuple[int, int]] = set()
        by_type: dict[str, int] = {
            "deliberate_scan": 0,
            "deliberate_action": 0,
            "survey": 0,
            "peripheral": 0,
            "reactive": 0,
        }
        total_ms = 0

        for entry in turn_entries:
            for tile in entry.get("tiles", []):
                if isinstance(tile, list) and len(tile) == 2:
                    turn_tiles.add((tile[0], tile[1]))
            atype = entry.get("type", "")
            if atype in by_type:
                by_type[atype] += 1
            total_ms += entry.get("ms", 0)

        cumulative_tiles |= turn_tiles
        rows.append(
            {
                "turn": turn,
                "tiles_observed": len(turn_tiles),
                "tool_calls": len(turn_entries),
                "cumulative_tiles": len(cumulative_tiles),
                "total_ms": total_ms,
                "by_type": by_type,
            }
        )

    if not rows:
        return

    # Only push rows for turns we haven't synced yet
    last_synced_turn = file_state.get("last_turn", -1)
    new_rows = [r for r in rows if r["turn"] > last_synced_turn]
    if not new_rows:
        file_state["line_count"] = total
        state["files"][name] = file_state
        return

    for i in range(0, len(new_rows), BATCH_SIZE):
        batch = new_rows[i : i + BATCH_SIZE]
        await client.mutation(
            "ingest:ingestSpatialTurns",
            {"gameId": game_id, "rows": batch},
        )

    log.info(
        "spatial %s: synced %d new turn aggregates (%d total)",
        game_id,
        len(new_rows),
        len(rows),
    )
    file_state["line_count"] = total
    file_state["last_turn"] = max(r["turn"] for r in new_rows)
    state["files"][name] = file_state
    state["game_last_seen"][game_id] = time.time()

    # Also push tile-level heatmap blob
    await sync_spatial_map(entries, game_id, client)


async def sync_spatial_map(
    entries: list[dict[str, Any]], game_id: str, client: ConvexClient
) -> None:
    """Compute per-tile aggregates from spatial entries and push as one blob."""
    TYPE_MAP = {
        "deliberate_scan": "ds",
        "deliberate_action": "da",
        "survey": "sv",
        "peripheral": "pe",
        "reactive": "re",
    }

    tile_data: dict[tuple[int, int], dict[str, int]] = {}

    for entry in entries:
        turn = entry.get("turn")
        short = TYPE_MAP.get(entry.get("type", ""), "")
        if turn is None:
            continue
        for tile in entry.get("tiles", []):
            if not isinstance(tile, list) or len(tile) != 2:
                continue
            key = (tile[0], tile[1])
            if key not in tile_data:
                tile_data[key] = {
                    "ds": 0,
                    "da": 0,
                    "sv": 0,
                    "pe": 0,
                    "re": 0,
                    "ft": turn,
                    "lt": turn,
                }
            td = tile_data[key]
            if short:
                td[short] += 1
            td["ft"] = min(td["ft"], turn)
            td["lt"] = max(td["lt"], turn)

    if not tile_data:
        return

    xs = [k[0] for k in tile_data]
    ys = [k[1] for k in tile_data]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # Pack: [x, y, total, ds, da, sv, pe, re, firstTurn, lastTurn] per tile
    flat: list[int] = []
    for (x, y), td in tile_data.items():
        total = td["ds"] + td["da"] + td["sv"] + td["pe"] + td["re"]
        flat.extend(
            [
                x,
                y,
                total,
                td["ds"],
                td["da"],
                td["sv"],
                td["pe"],
                td["re"],
                td["ft"],
                td["lt"],
            ]
        )

    await client.mutation(
        "ingest:ingestSpatialMap",
        {
            "gameId": game_id,
            "minX": min_x,
            "maxX": max_x,
            "minY": min_y,
            "maxY": max_y,
            "tileCount": len(tile_data),
            "tiles": flat,
        },
    )
    log.info(
        "spatial map %s: %d tiles, bounds (%d,%d)-(%d,%d)",
        game_id,
        len(tile_data),
        min_x,
        min_y,
        max_x,
        max_y,
    )


async def sync_map_data(
    path: Path, game_id: str, state: dict, client: ConvexClient
) -> None:
    """Sync strategic map data (static terrain + per-turn deltas) to Convex.

    Reads mapstatic_{id}.json for terrain grid + initial state, and
    mapturns_{id}.jsonl for per-turn ownership/road/city deltas.
    Packs everything into flat arrays and sends as a single mutation.
    """
    name = path.name
    file_state = state["files"].get(name, {"line_count": 0})

    lines = path.read_text().strip().splitlines()
    total = len(lines)
    old_count = file_state.get("line_count", 0)

    if total <= old_count:
        return

    # Find the corresponding mapstatic JSON file
    static_name = name.replace("mapturns_", "mapstatic_").replace(".jsonl", ".json")
    static_path = path.parent / static_name
    if not static_path.exists():
        log.debug("Map static file not found for %s", game_id)
        return

    # Read static data
    try:
        static_data = json.loads(static_path.read_text())
    except (json.JSONDecodeError, OSError):
        log.warning("Failed to read map static file for %s", game_id)
        return

    # Parse turn deltas
    turn_entries: list[dict[str, Any]] = []
    for line in lines:
        try:
            turn_entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    # Pack frames into flat arrays matching Convex schema
    # ownerFrames: [turn, count, tileIdx, owner, ...]
    # cityFrames: [turn, count, x, y, pid, pop, ...]
    # roadFrames: [turn, count, tileIdx, routeType, ...]
    owner_frames: list[int] = []
    city_frames: list[int] = []
    road_frames: list[int] = []
    # city names: "x,y" → name (last seen name wins)
    city_names: dict[str, str] = {}
    max_turn = static_data.get("initialTurn", 0)

    # Seed city names from initial cities
    for c in static_data.get("initialCities", []):
        name = c.get("name", "")
        if name:
            city_names[f"{c['x']},{c['y']}"] = name

    for entry in turn_entries:
        turn = entry.get("turn", 0)
        max_turn = max(max_turn, turn)

        owners = entry.get("owners", [])
        if owners:
            owner_frames.append(turn)
            owner_frames.append(len(owners) // 2)
            owner_frames.extend(owners)

        cities = entry.get("cities", [])
        if cities:
            city_frames.append(turn)
            city_frames.append(len(cities))
            for c in cities:
                city_frames.extend([c["x"], c["y"], c["pid"], c["pop"]])
                name = c.get("name", "")
                if name:
                    city_names[f"{c['x']},{c['y']}"] = name

        roads = entry.get("roads", [])
        if roads:
            road_frames.append(turn)
            road_frames.append(len(roads) // 2)
            road_frames.extend(roads)

    # Convex caps arrays at 8192 elements — encode large arrays as JSON strings
    payload = {
        "gameId": game_id,
        "gridW": static_data["gridW"],
        "gridH": static_data["gridH"],
        "terrain": json.dumps(static_data["terrain"]),
        "initialOwners": json.dumps(static_data["initialOwners"]),
        "initialRoutes": json.dumps(static_data.get("initialRoutes", [])),
        "initialTurn": static_data.get("initialTurn", 0),
        "ownerFrames": json.dumps(owner_frames),
        "cityFrames": json.dumps(city_frames),
        "roadFrames": json.dumps(road_frames),
        "cityNames": json.dumps(city_names) if city_names else None,
        "players": static_data.get("players", []),
        "maxTurn": max_turn,
    }

    payload_bytes = len(json.dumps(payload).encode())
    if payload_bytes > 800_000:
        log.warning(
            "Map payload for %s is %dKB — approaching 1MB Convex limit",
            game_id,
            payload_bytes // 1024,
        )

    await client.mutation("ingest:ingestMapData", payload)

    log.info(
        "map %s: %dx%d grid, %d turn deltas, maxTurn=%d",
        game_id,
        static_data["gridW"],
        static_data["gridH"],
        len(turn_entries),
        max_turn,
    )
    file_state["line_count"] = total
    state["files"][name] = file_state
    state["game_last_seen"][game_id] = time.time()


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


async def sync_file(path: Path, state: dict, client: ConvexClient) -> None:
    """Route a file change to the appropriate sync handler."""
    name = path.name
    ftype = classify_file(name)
    if ftype is None:
        return

    game_id = extract_game_id(name)

    try:
        if ftype == "diary":
            await sync_diary(path, game_id, state, client)
        elif ftype == "cities":
            await sync_cities(path, game_id, state, client)
        elif ftype == "log":
            await sync_log(path, game_id, state, client)
        elif ftype == "spatial":
            await sync_spatial(path, game_id, state, client)
        elif ftype == "mapturns":
            await sync_map_data(path, game_id, state, client)
    except Exception:
        log.exception("Error syncing %s", name)


async def check_idle_games(state: dict, client: ConvexClient) -> None:
    """Mark games as completed if no writes for IDLE_TIMEOUT."""
    now = time.time()
    for game_id, last_seen in list(state.get("game_last_seen", {}).items()):
        if now - last_seen > IDLE_TIMEOUT:
            await client.mutation("ingest:markGameCompleted", {"gameId": game_id})
            log.info(
                "Marked game %s as completed (idle %dm)",
                game_id,
                (now - last_seen) // 60,
            )
            del state["game_last_seen"][game_id]


# ---------------------------------------------------------------------------
# Batch upload
# ---------------------------------------------------------------------------


async def batch_upload(directory: Path, client: ConvexClient) -> None:
    """One-shot upload of all JSONL files in directory, then exit."""
    games = discover_games(directory)
    if not games:
        log.error("No game files found in %s", directory)
        return

    log.info("Found %d game(s) in %s:", len(games), directory)
    for gid, files in sorted(games.items()):
        types = ", ".join(sorted(files.keys()))
        log.info("  %s: %s", gid, types)

    # Stateless — never reads/writes .sync_state.json
    state: dict[str, Any] = {"files": {}, "game_last_seen": {}}
    total_start = time.time()
    games_uploaded = 0

    for gid, files in sorted(games.items()):
        game_start = time.time()
        log.info("--- %s ---", gid)

        # Process diary first (creates the games row in Convex)
        for ftype in ("diary", "cities", "log", "spatial", "mapturns"):
            if ftype in files:
                await sync_file(files[ftype], state, client)

        await client.mutation("ingest:markGameCompleted", {"gameId": gid})

        elapsed = time.time() - game_start
        log.info("  %s done (%.1fs)", gid, elapsed)
        games_uploaded += 1

    total_elapsed = time.time() - total_start
    log.info(
        "=== Batch upload complete: %d game(s) in %.1fs ===",
        games_uploaded,
        total_elapsed,
    )


async def batch_upload_cloud(bucket_url: str, client: ConvexClient) -> None:
    """Batch sync all runs from cloud bucket to Convex.

    Downloads cloud files to a temp directory with local naming conventions,
    then delegates to the existing batch_upload() function.
    """
    import tempfile

    manifests = discover_cloud_runs(bucket_url)
    if not manifests:
        log.error("No runs found in %s", bucket_url)
        return

    fs, prefix = _get_cloud_fs(bucket_url)

    # Only sync runs that have a game identity (civ + seed from bind_game)
    valid = [m for m in manifests if m.get("civ") and m.get("seed") is not None]
    log.info(
        "Found %d run(s) in cloud (%d with game identity)",
        len(manifests),
        len(valid),
    )

    with tempfile.TemporaryDirectory(prefix="civbench_") as tmp:
        tmp_dir = Path(tmp)
        for manifest in valid:
            run_id = manifest.get("run_id", "")
            if not run_id:
                continue
            _download_cloud_run(fs, prefix, run_id, manifest, tmp_dir)

        # Reuse existing batch upload on the downloaded files
        await batch_upload(tmp_dir, client)


# ---------------------------------------------------------------------------
# Watch loop
# ---------------------------------------------------------------------------


async def watch_loop(diary_dir: Path, client: ConvexClient) -> None:
    """Watch directory and stream changes to Convex in real-time."""
    state = load_state()

    # Graceful shutdown
    shutdown = asyncio.Event()

    def on_signal(*_: Any) -> None:
        log.info("Shutting down...")
        shutdown.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, on_signal)

    try:
        # Initial sync: process all existing files
        for pattern in (
            "diary_*.jsonl",
            "log_*.jsonl",
            "spatial_*.jsonl",
            "mapturns_*.jsonl",
        ):
            for filepath in sorted(glob(str(diary_dir / pattern))):
                await sync_file(Path(filepath), state, client)
        save_state(state)
        log.info("Initial sync complete")

        # Watch for changes
        idle_check_time = time.time()
        async for changes in watchfiles.awatch(
            diary_dir,
            watch_filter=lambda _, p: p.endswith(".jsonl"),
            stop_event=shutdown,
        ):
            for _, filepath in changes:
                await sync_file(Path(filepath), state, client)
            save_state(state)

            # Periodically check for idle games
            if time.time() - idle_check_time > 300:
                await check_idle_games(state, client)
                save_state(state)
                idle_check_time = time.time()

    finally:
        save_state(state)
        log.info("State saved, exiting")


async def watch_loop_cloud(bucket_url: str, client: ConvexClient) -> None:
    """Poll cloud bucket for new/changed runs and sync to Convex.

    Uses a persistent temp directory so that incremental sync state (line
    counts, byte offsets) works correctly across poll iterations.
    """
    import tempfile

    shutdown = asyncio.Event()

    def on_signal(*_: Any) -> None:
        log.info("Shutting down...")
        shutdown.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, on_signal)

    fs, prefix = _get_cloud_fs(bucket_url)
    state: dict[str, Any] = {"files": {}, "game_last_seen": {}}
    completed_runs: set[str] = set()

    with tempfile.TemporaryDirectory(prefix="civbench_watch_") as tmp:
        tmp_dir = Path(tmp)

        while not shutdown.is_set():
            try:
                manifests = discover_cloud_runs(bucket_url)

                for manifest in manifests:
                    run_id = manifest.get("run_id", "")
                    if not run_id or run_id in completed_runs:
                        continue

                    game_id = _download_cloud_run(fs, prefix, run_id, manifest, tmp_dir)
                    if not game_id:
                        continue

                    # Sync using stateful functions (track line counts etc.)
                    games = discover_games(tmp_dir)
                    if game_id in games:
                        for ftype in (
                            "diary",
                            "cities",
                            "log",
                            "spatial",
                            "mapturns",
                        ):
                            if ftype in games[game_id]:
                                await sync_file(games[game_id][ftype], state, client)

                    # Check completion via game_over entry in log
                    if _cloud_run_is_complete(fs, prefix, run_id):
                        await client.mutation(
                            "ingest:markGameCompleted", {"gameId": game_id}
                        )
                        log.info(
                            "Marked %s as completed (game_over in log)",
                            game_id,
                        )
                        completed_runs.add(run_id)
            except Exception:
                log.exception("Error during cloud watch poll")

            # Wait 30s or until shutdown
            try:
                await asyncio.wait_for(shutdown.wait(), timeout=30)
                break
            except asyncio.TimeoutError:
                pass

    log.info("Cloud watch loop exiting")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    parser = argparse.ArgumentParser(description="Sync civ-mcp JSONL files to Convex")
    parser.add_argument(
        "--prod",
        action="store_true",
        help="Target production deployment (reads web/.env.prod instead of web/.env.dev)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--watch",
        action="store_true",
        help="Watch for changes and stream to Convex (default for local)",
    )
    mode.add_argument(
        "--upload",
        type=str,
        metavar="DIR",
        help="One-shot batch upload of all files in DIR, then exit",
    )
    parser.add_argument(
        "--cloud",
        type=str,
        metavar="BUCKET",
        help="Cloud bucket URL (e.g. az://civbench). "
        "Batch sync by default; add --watch to poll for changes.",
    )
    args = parser.parse_args()

    convex_url, deploy_key = _resolve_config(prod=args.prod)
    env_label = "PROD" if args.prod else "DEV"

    if not convex_url:
        log.error(
            "CONVEX_URL not set — check web/.env.%s", "prod" if args.prod else "dev"
        )
        sys.exit(1)
    if not deploy_key:
        log.error(
            "CONVEX_DEPLOY_KEY not set — check web/.env.%s",
            "prod" if args.prod else "dev",
        )
        sys.exit(1)

    client = ConvexClient(convex_url, deploy_key)
    try:
        if args.upload:
            upload_dir = Path(args.upload).expanduser().resolve()
            if not upload_dir.is_dir():
                log.error("Directory not found: %s", upload_dir)
                sys.exit(1)
            log.info("[%s] Batch upload %s → %s", env_label, upload_dir, convex_url)
            await batch_upload(upload_dir, client)
        elif args.cloud:
            if args.watch:
                log.info(
                    "[%s] Watching cloud %s → %s", env_label, args.cloud, convex_url
                )
                await watch_loop_cloud(args.cloud, client)
            else:
                log.info("[%s] Batch cloud %s → %s", env_label, args.cloud, convex_url)
                await batch_upload_cloud(args.cloud, client)
        else:
            log.info("[%s] Watching %s → %s", env_label, DIARY_DIR, convex_url)
            await watch_loop(DIARY_DIR, client)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
