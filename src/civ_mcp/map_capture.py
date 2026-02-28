"""Map capture — records per-game terrain and ownership for strategic map replay.

Writes per-game files to ~/.civ6-mcp/:
  mapstatic_{civ}_{seed}.json  — one-time full terrain dump
  mapturns_{civ}_{seed}.jsonl  — per-turn ownership/road deltas + city snapshots

Data is consumed by convex_sync.py for the web app strategic map view.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

from civ_mcp import lua as lq

if TYPE_CHECKING:
    from civ_mcp.connection import GameConnection

LOG_DIR = Path.home() / ".civ6-mcp"

log = logging.getLogger(__name__)


class MapCapture:
    """Captures per-game map state to disk for strategic view replay."""

    def __init__(self) -> None:
        self._game: str | None = None
        self._static_path: Path | None = None
        self._turns_path: Path | None = None
        self._has_static: bool = False

    def bind_game(self, civ: str, seed: int) -> None:
        """Bind to a game identity. Sets file paths."""
        game_id = f"{civ}_{seed}"
        if self._game == game_id:
            return
        self._game = game_id
        self._static_path = LOG_DIR / f"mapstatic_{civ}_{seed}.json"
        self._turns_path = LOG_DIR / f"mapturns_{civ}_{seed}.jsonl"
        self._has_static = self._static_path.exists()
        LOG_DIR.mkdir(parents=True, exist_ok=True)

    async def capture(self, conn: GameConnection, turn: int) -> None:
        """Run static dump (if needed) and per-turn delta."""
        if self._static_path is None:
            return

        if not self._has_static:
            await self._capture_static(conn, turn)

        await self._capture_delta(conn, turn)

    async def _capture_static(self, conn: GameConnection, turn: int) -> None:
        """One-time full terrain dump."""
        assert self._static_path is not None
        try:
            lines = await conn.execute_write(lq.build_static_map_dump())
            dump = lq.parse_static_map_dump(lines)
            if dump.grid_w == 0 or dump.grid_h == 0:
                log.warning("Map dump returned empty grid")
                return

            # Pack into JSON-serializable format
            terrain_flat: list[int] = []
            for t in dump.tiles:
                terrain_flat.extend([
                    t.terrain, t.feature,
                    1 if t.hills else 0,
                    1 if t.river else 0,
                    1 if t.coastal else 0,
                    t.resource,
                ])

            data = {
                "gridW": dump.grid_w,
                "gridH": dump.grid_h,
                "terrain": terrain_flat,
                "initialOwners": dump.initial_owners,
                "initialRoutes": dump.initial_routes,
                "initialCities": [
                    {"x": c[0], "y": c[1], "pid": c[2], "pop": c[3]}
                    for c in dump.initial_cities
                ],
                "players": [
                    {"pid": p[0], "civ": p[1]} for p in dump.players
                ],
                "initialTurn": turn,
            }

            self._static_path.write_text(
                json.dumps(data, separators=(",", ":"))
            )
            self._has_static = True
            log.info(
                "Map static dump: %s — %dx%d grid, %d tiles, %d cities, %d players",
                self._game,
                dump.grid_w,
                dump.grid_h,
                len(dump.tiles),
                len(dump.initial_cities),
                len(dump.players),
            )
        except Exception:
            log.debug("Static map dump failed", exc_info=True)

    async def _capture_delta(self, conn: GameConnection, turn: int) -> None:
        """Per-turn ownership/road delta + city snapshot."""
        assert self._turns_path is not None
        try:
            lines = await conn.execute_write(lq.build_ownership_delta())
            delta = lq.parse_ownership_delta(lines)

            entry: dict = {"turn": turn}
            if delta.owner_changes:
                # Pack as flat array: [idx, owner, idx, owner, ...]
                flat: list[int] = []
                for idx, owner in delta.owner_changes:
                    flat.extend([idx, owner])
                entry["owners"] = flat
            if delta.road_changes:
                flat_r: list[int] = []
                for idx, route in delta.road_changes:
                    flat_r.extend([idx, route])
                entry["roads"] = flat_r
            if delta.cities:
                entry["cities"] = [
                    {"x": c[0], "y": c[1], "pid": c[2], "pop": c[3]}
                    for c in delta.cities
                ]

            with open(self._turns_path, "a") as f:
                f.write(json.dumps(entry, separators=(",", ":")) + "\n")
        except Exception:
            log.debug("Ownership delta capture failed", exc_info=True)
