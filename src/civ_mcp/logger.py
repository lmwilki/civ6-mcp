"""Per-game JSONL tool logger for observing MCP tool calls and turn events.

Writes enriched log entries to ~/.civ6-mcp/log_{civ}_{seed}.jsonl, matching
the diary naming convention. Each entry includes game identity, pre-computed
category, success flag, and result summary for analytical queries.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Any

LOG_DIR = Path.home() / ".civ6-mcp"

# Tool classification — matches web client getToolCategory()
_QUERY_TOOLS = frozenset({"screenshot"})
_TURN_TOOLS = frozenset({"end_turn"})


def log_path(civ: str, seed: int) -> Path:
    """Per-game log file: log_{civ}_{seed}.jsonl"""
    return LOG_DIR / f"log_{civ}_{seed}.jsonl"


def _classify_tool(tool: str | None) -> str:
    """Pre-compute category for a tool name."""
    if not tool:
        return "query"
    if tool in _TURN_TOOLS:
        return "turn"
    if tool.startswith("get_") or tool in _QUERY_TOOLS:
        return "query"
    return "action"


class GameLogger:
    """Appends structured JSON lines to a per-game log file.

    Starts unbound (no game identity). Tool calls are buffered in memory
    until bind_game() is called, which flushes the buffer and opens the
    per-game file for all subsequent writes.
    """

    def __init__(self) -> None:
        self.session_id = uuid.uuid4().hex[:8]
        self._lock = asyncio.Lock()
        self._turn: int | None = None
        self._seq: int = 0
        self._game: str | None = None
        self._civ: str | None = None
        self._seed: int | None = None
        self._path: Path | None = None
        self._buffer: list[dict[str, Any]] = []
        self._agent_model: str | None = None

    @property
    def bound(self) -> bool:
        return self._path is not None

    @property
    def game_id(self) -> str | None:
        return self._game

    def set_turn(self, turn: int) -> None:
        self._turn = turn

    def set_agent_model(self, model: str) -> None:
        self._agent_model = model

    def bind_game(self, civ: str, seed: int) -> None:
        """Bind to a game identity. Flushes any buffered entries to disk."""
        game_id = f"{civ}_{seed}"
        if self._game == game_id:
            return  # already bound to this game

        self._game = game_id
        self._civ = civ
        self._seed = seed
        self._path = log_path(civ, seed)
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # Set seq counter from existing file length
        if self._path.exists():
            with open(self._path, "rb") as f:
                self._seq = sum(1 for _ in f)
        else:
            self._seq = 0

        # Flush buffered entries with now-known identity
        if self._buffer:
            with open(self._path, "a") as f:
                for entry in self._buffer:
                    entry["game"] = self._game
                    entry["civ"] = self._civ
                    entry["seed"] = self._seed
                    entry["seq"] = self._seq
                    self._seq += 1
                    f.write(json.dumps(entry, separators=(",", ":")) + "\n")
            self._buffer.clear()

    def _build_entry(
        self,
        entry_type: str,
        *,
        tool: str | None = None,
        params: dict[str, Any] | None = None,
        result: str | None = None,
        duration_ms: int | None = None,
        events: list[dict[str, Any]] | None = None,
        success: bool = True,
    ) -> dict[str, Any]:
        tool_name = tool or "unknown"
        result_summary = result[:200] if result else None

        entry: dict[str, Any] = {
            "game": self._game,
            "civ": self._civ,
            "seed": self._seed,
            "session": self.session_id,
            "ts": time.time(),
            "turn": self._turn,
            "seq": self._seq,
            "type": entry_type,
            "tool": tool_name,
            "category": _classify_tool(tool_name),
            "params": params,
            "result_summary": result_summary,
            "result": result,
            "duration_ms": duration_ms,
            "success": success,
            "agent_model": self._agent_model,
        }
        if events is not None:
            entry["events"] = events
        return entry

    async def _write(self, entry: dict[str, Any]) -> None:
        """Write an entry to file or buffer if unbound."""
        async with self._lock:
            if self._path is not None:
                entry["seq"] = self._seq
                self._seq += 1
                line = json.dumps(entry, separators=(",", ":")) + "\n"
                with open(self._path, "a") as f:
                    f.write(line)
            else:
                self._buffer.append(entry)

    async def log_tool_call(
        self,
        tool: str,
        params: dict[str, Any],
        result: str,
        duration_ms: int,
    ) -> None:
        entry = self._build_entry(
            "tool_call",
            tool=tool,
            params=params,
            result=result,
            duration_ms=duration_ms,
            success=True,
        )
        await self._write(entry)

    async def log_error(self, tool: str, error: str) -> None:
        entry = self._build_entry(
            "error",
            tool=tool,
            result=error,
            success=False,
        )
        await self._write(entry)
