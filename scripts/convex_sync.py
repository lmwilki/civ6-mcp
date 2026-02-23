#!/usr/bin/env python3
"""Watchdog that tails civ-mcp JSONL files and syncs to Convex.

Standalone process — the MCP server has zero knowledge of this.
Watches ~/.civ6-mcp/ for diary, city, and log JSONL files and pushes
new/changed rows to Convex via the HTTP mutation API.

Usage:
    CONVEX_URL=https://your-deployment.convex.cloud \
    CONVEX_DEPLOY_KEY=prod:... \
    python scripts/convex_sync.py

Optional:
    CIV6_DIARY_DIR=~/.civ6-mcp   (default)
"""

from __future__ import annotations

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

DIARY_DIR = Path(os.environ.get("CIV6_DIARY_DIR", Path.home() / ".civ6-mcp"))
CONVEX_URL = os.environ.get("CONVEX_URL", "")
CONVEX_DEPLOY_KEY = os.environ.get("CONVEX_DEPLOY_KEY", "")
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
    tmp.write_text(json.dumps(state, indent=2))
    tmp.rename(STATE_FILE)


# ---------------------------------------------------------------------------
# File classification
# ---------------------------------------------------------------------------


def classify_file(name: str) -> str | None:
    """Return file type: 'diary', 'cities', 'log', or None."""
    if name.startswith("diary_") and name.endswith("_cities.jsonl"):
        return "cities"
    if name.startswith("diary_") and name.endswith(".jsonl"):
        return "diary"
    if name.startswith("log_") and name.endswith(".jsonl"):
        return "log"
    return None


def extract_game_id(name: str) -> str:
    """Extract game ID from filename: diary_india_123.jsonl → india_123"""
    name = name.removesuffix("_cities.jsonl").removesuffix(".jsonl")
    for prefix in ("diary_", "log_"):
        if name.startswith(prefix):
            name = name[len(prefix) :]
    return name


def hash_lines(lines: list[str]) -> str:
    """Content hash for a set of lines."""
    return hashlib.md5("".join(lines).encode()).hexdigest()


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
        """Call a Convex mutation with retries."""
        url = f"{self.base_url}/api/mutation"
        payload = {"path": path, "args": args, "format": "json"}
        for attempt in range(MAX_RETRIES):
            try:
                resp = await self.client.post(url, json=payload)
                data = resp.json()
                if data.get("status") == "success":
                    return data.get("value")
                log.error("Mutation %s failed: %s", path, data.get("errorMessage"))
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_BACKOFF[attempt])
            except (httpx.HTTPError, json.JSONDecodeError) as e:
                log.error("HTTP error calling %s: %s", path, e)
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_BACKOFF[attempt])
        return None

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
    agent_row = next((r for r in rows_to_upsert if r.get("is_agent")), rows_to_upsert[0])
    civ = agent_row.get("civ", "")
    leader = agent_row.get("leader", "")
    seed = game_id.rsplit("_", 1)[-1] if "_" in game_id else ""

    # Batch and send
    for i in range(0, len(rows_to_upsert), BATCH_SIZE):
        batch = rows_to_upsert[i : i + BATCH_SIZE]
        await client.mutation(
            "ingest:ingestPlayerRows",
            {"gameId": game_id, "civ": civ, "leader": leader, "seed": seed, "rows": batch},
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


async def sync_log(
    path: Path, game_id: str, state: dict, client: ConvexClient
) -> None:
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
    except Exception:
        log.exception("Error syncing %s", name)


async def check_idle_games(state: dict, client: ConvexClient) -> None:
    """Mark games as completed if no writes for IDLE_TIMEOUT."""
    now = time.time()
    for game_id, last_seen in list(state.get("game_last_seen", {}).items()):
        if now - last_seen > IDLE_TIMEOUT:
            await client.mutation("ingest:markGameCompleted", {"gameId": game_id})
            log.info("Marked game %s as completed (idle %dm)", game_id, (now - last_seen) // 60)
            del state["game_last_seen"][game_id]


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


async def main() -> None:
    if not CONVEX_URL:
        log.error("CONVEX_URL not set")
        sys.exit(1)
    if not CONVEX_DEPLOY_KEY:
        log.error("CONVEX_DEPLOY_KEY not set")
        sys.exit(1)

    log.info("Watching %s → %s", DIARY_DIR, CONVEX_URL)

    state = load_state()
    client = ConvexClient(CONVEX_URL, CONVEX_DEPLOY_KEY)

    # Graceful shutdown
    shutdown = asyncio.Event()

    def on_signal(*_: Any) -> None:
        log.info("Shutting down...")
        shutdown.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, on_signal)

    try:
        # Initial sync: process all existing files
        for pattern in ("diary_*.jsonl", "log_*.jsonl"):
            for filepath in sorted(glob(str(DIARY_DIR / pattern))):
                await sync_file(Path(filepath), state, client)
        save_state(state)
        log.info("Initial sync complete")

        # Watch for changes
        idle_check_time = time.time()
        async for changes in watchfiles.awatch(
            DIARY_DIR,
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
        await client.close()
        log.info("State saved, exiting")


if __name__ == "__main__":
    asyncio.run(main())
