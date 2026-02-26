"""Spatiotemporal attention tracker — records which tiles the agent observes.

Writes per-game JSONL to ~/.civ6-mcp/spatial_{civ}_{seed}.jsonl.
This is research instrumentation only — data does NOT feed back to the agent.

Each tool call that surfaces coordinate data is classified by attention type
and the observed tile set is extracted via regex from the narrated result text.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from pathlib import Path
from typing import Any

LOG_DIR = Path.home() / ".civ6-mcp"

# Every narration function formats coordinates as (x,y).
_COORD_RE = re.compile(r"\((\d+),(\d+)\)")

# ── Attention type classification ────────────────────────────────────────

_DELIBERATE_SCAN = frozenset(
    {
        "get_map_area",
        "get_settle_advisor",
        "get_district_advisor",
        "get_wonder_advisor",
        "get_purchasable_tiles",
        "get_pathing_estimate",
    }
)

_DELIBERATE_ACTION = frozenset(
    {
        "unit_action",
        "city_action",
        "spy_action",
        "set_city_production",
        "purchase_tile",
    }
)

_SURVEY = frozenset(
    {
        "get_strategic_map",
        "get_global_settle_advisor",
        "get_empire_resources",
    }
)

_PERIPHERAL = frozenset(
    {
        "get_units",
        "get_cities",
        "get_spies",
        "get_diplomacy",
        "get_trade_routes",
        "get_trade_destinations",
    }
)

_REACTIVE = frozenset(
    {
        "get_notifications",
    }
)


def _classify_attention(tool_name: str) -> str | None:
    """Return attention type for a tool, or None if non-spatial."""
    if tool_name in _DELIBERATE_SCAN:
        return "deliberate_scan"
    if tool_name in _DELIBERATE_ACTION:
        return "deliberate_action"
    if tool_name in _SURVEY:
        return "survey"
    if tool_name in _PERIPHERAL:
        return "peripheral"
    if tool_name in _REACTIVE:
        return "reactive"
    return None


def _extract_tiles_from_text(text: str) -> set[tuple[int, int]]:
    """Extract all (x,y) coordinate pairs from narrated result text."""
    return {(int(m.group(1)), int(m.group(2))) for m in _COORD_RE.finditer(text)}


def _extract_tiles_from_params(
    tool_name: str, params: dict[str, Any]
) -> set[tuple[int, int]]:
    """Extract coordinate tiles from tool input parameters."""
    tiles: set[tuple[int, int]] = set()

    # Action tools with target_x/target_y
    tx = params.get("target_x")
    ty = params.get("target_y")
    if tx is not None and ty is not None:
        tiles.add((int(tx), int(ty)))

    # purchase_tile uses x/y
    px = params.get("x")
    py = params.get("y")
    if px is not None and py is not None:
        tiles.add((int(px), int(py)))

    # get_map_area: compute full tile set from center + radius
    # (matches the Lua square iteration: for dy = -r, r do for dx = -r, r do)
    if tool_name == "get_map_area":
        cx = params.get("center_x")
        cy = params.get("center_y")
        r = params.get("radius", 2)
        if cx is not None and cy is not None:
            cx, cy, r = int(cx), int(cy), int(r)
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    tiles.add((cx + dx, cy + dy))

    return tiles


# ── Tracker ──────────────────────────────────────────────────────────────


class SpatialTracker:
    """Records spatial observations from tool calls to a per-game JSONL file.

    Follows the same bind pattern as GameLogger: starts unbound, buffers
    observations until bind_game() is called, then appends to disk.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._turn: int | None = None
        self._game: str | None = None
        self._path: Path | None = None
        self._buffer: list[dict[str, Any]] = []

    @property
    def bound(self) -> bool:
        return self._path is not None

    def set_turn(self, turn: int) -> None:
        self._turn = turn

    def bind_game(self, civ: str, seed: int) -> None:
        """Bind to a game identity. Flushes any buffered observations."""
        game_id = f"{civ}_{seed}"
        if self._game == game_id:
            return
        self._game = game_id
        self._path = LOG_DIR / f"spatial_{civ}_{seed}.jsonl"
        self._path.parent.mkdir(parents=True, exist_ok=True)

        if self._buffer:
            with open(self._path, "a") as f:
                for entry in self._buffer:
                    entry["game"] = self._game
                    f.write(json.dumps(entry, separators=(",", ":")) + "\n")
            self._buffer.clear()

    async def record(
        self,
        tool_name: str,
        params: dict[str, Any],
        result_text: str,
        duration_ms: int,
    ) -> None:
        """Record a spatial observation from a tool call.

        Silently skips non-spatial tools or results with no coordinates.
        """
        attention_type = _classify_attention(tool_name)
        if attention_type is None:
            return

        tiles = _extract_tiles_from_text(result_text)
        tiles |= _extract_tiles_from_params(tool_name, params)

        if not tiles:
            return

        entry: dict[str, Any] = {
            "game": self._game,
            "turn": self._turn,
            "tool": tool_name,
            "type": attention_type,
            "tiles": sorted(tiles),
            "n_tiles": len(tiles),
            "ts": time.time(),
            "ms": duration_ms,
        }

        async with self._lock:
            if self._path is not None:
                with open(self._path, "a") as f:
                    f.write(json.dumps(entry, separators=(",", ":")) + "\n")
            else:
                self._buffer.append(entry)
