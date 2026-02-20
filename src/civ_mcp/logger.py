"""Optional JSONL game logger for observing MCP tool calls and turn events."""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

DEFAULT_LOG_DIR = Path.home() / ".civ6-mcp"
DEFAULT_LOG_PATH = DEFAULT_LOG_DIR / "game_log.jsonl"


class GameLogger:
    """Appends structured JSON lines to a log file.

    Each line is a self-contained JSON object with timestamp, turn, type,
    tool name, params, result, and duration. The web viewer reads this file
    to display a real-time timeline of game events.
    """

    def __init__(self, path: Path | None = None) -> None:
        env_path = os.environ.get("CIV6_LOG_PATH")
        if env_path:
            self.path = Path(env_path)
        elif path:
            self.path = path
        else:
            self.path = DEFAULT_LOG_PATH

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.session_id = uuid.uuid4().hex[:8]
        self.session_path = self.path.parent / f"game_log_{self.session_id}.jsonl"
        self._lock = asyncio.Lock()
        self._turn: int | None = None

    def set_turn(self, turn: int) -> None:
        self._turn = turn

    async def log(
        self,
        entry_type: str,
        *,
        tool: str | None = None,
        params: dict[str, Any] | None = None,
        result: str | None = None,
        duration_ms: int | None = None,
        events: list[dict[str, Any]] | None = None,
    ) -> None:
        entry: dict[str, Any] = {
            "ts": time.time(),
            "session": self.session_id,
            "turn": self._turn,
            "type": entry_type,
        }
        if tool is not None:
            entry["tool"] = tool
        if params is not None:
            entry["params"] = params
        if result is not None:
            entry["result"] = result
        if duration_ms is not None:
            entry["duration_ms"] = duration_ms
        if events is not None:
            entry["events"] = events

        line = json.dumps(entry, separators=(",", ":")) + "\n"
        async with self._lock:
            with open(self.session_path, "a") as f:
                f.write(line)
            with open(self.path, "a") as f:
                f.write(line)

    async def log_tool_call(
        self,
        tool: str,
        params: dict[str, Any],
        result: str,
        duration_ms: int,
    ) -> None:
        await self.log(
            "tool_call",
            tool=tool,
            params=params,
            result=result,
            duration_ms=duration_ms,
        )

    async def log_turn_report(
        self,
        result: str,
        events: list[dict[str, Any]],
    ) -> None:
        await self.log(
            "turn_report",
            tool="end_turn",
            result=result,
            events=events,
        )

    async def log_error(self, tool: str, error: str) -> None:
        await self.log("error", tool=tool, result=error)
