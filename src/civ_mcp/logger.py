"""Per-game JSONL tool logger for observing MCP tool calls and turn events.

Builds structured log entries and emits them through a TelemetryEmitter.
The emitter routes entries to LocalSink (always) and optionally CloudSink.
"""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from civ_mcp.telemetry import TelemetryEmitter

# Tool classification — matches web client getToolCategory()
_QUERY_TOOLS = frozenset({"screenshot"})
_TURN_TOOLS = frozenset({"end_turn"})


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
    """Builds structured log entries and emits them via TelemetryEmitter.

    Starts unbound (no game identity). Entries are built with whatever
    identity is known and emitted immediately — the sink handles
    buffering and file management.
    """

    def __init__(self, emitter: TelemetryEmitter) -> None:
        from civ_mcp.telemetry import EVENT_GAME_OVER, EVENT_TOOL_CALL

        self._emitter = emitter
        self._event_tool_call = EVENT_TOOL_CALL
        self._event_game_over = EVENT_GAME_OVER
        self.session_id = emitter.run_id
        self._turn: int | None = None
        self._game: str | None = None
        self._civ: str | None = None
        self._seed: int | None = None
        self._agent_model: str | None = os.environ.get("CIV_MCP_AGENT_MODEL") or None
        self._game_over_logged: bool = False

    @property
    def bound(self) -> bool:
        return self._game is not None

    @property
    def game_id(self) -> str | None:
        return self._game

    def set_turn(self, turn: int) -> None:
        self._turn = turn

    def set_agent_model(self, model: str) -> None:
        self._agent_model = model

    def bind_game(self, civ: str, seed: int) -> None:
        """Bind to a game identity. Propagates to emitter for sink binding."""
        game_id = f"{civ}_{seed}"
        if self._game == game_id:
            return  # already bound to this game
        self._game_over_logged = False
        self._game = game_id
        self._civ = civ
        self._seed = seed
        self._emitter.bind_game(civ, seed)

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
            success=not result.startswith(("Error", "ERR")),
        )
        await self._emitter.emit(self._event_tool_call, entry)

    async def log_error(self, tool: str, error: str) -> None:
        entry = self._build_entry(
            "error",
            tool=tool,
            result=error,
            success=False,
        )
        await self._emitter.emit(self._event_tool_call, entry)

    async def log_game_over(
        self,
        *,
        is_defeat: bool,
        winner_civ: str,
        winner_leader: str,
        victory_type: str,
        player_alive: bool,
    ) -> None:
        if self._game_over_logged:
            return
        self._game_over_logged = True
        result_str = (
            f"{'Defeat' if is_defeat else 'Victory'}"
            f" — {winner_leader} of {winner_civ} ({victory_type})"
        )
        entry = self._build_entry(
            "game_over",
            tool="end_turn",
            result=result_str,
            success=True,
        )
        entry["outcome"] = {
            "is_defeat": is_defeat,
            "winner_civ": winner_civ,
            "winner_leader": winner_leader,
            "victory_type": victory_type,
            "player_alive": player_alive,
        }
        await self._emitter.emit(self._event_game_over, entry)
