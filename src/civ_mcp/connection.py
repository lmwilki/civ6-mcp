"""Persistent, reconnectable FireTuner connection to Civilization VI.

Wraps tuner_client.py into a stateful connection manager with:
- Lua state index discovery (GameCore_Tuner, InGame)
- asyncio lock for serializing commands
- Sentinel-based multi-line response collection
- Output prefix parsing (O\x00<context>: <value>)
- Reconnection on connection loss
"""

from __future__ import annotations

import asyncio
import logging

from civ_mcp import tuner_client

log = logging.getLogger(__name__)

SENTINEL = "---END---"


class LuaError(Exception):
    """Raised when Lua code execution returns an error."""


class GameConnection:
    """Persistent FireTuner TCP connection to Civ 6."""

    def __init__(self, host: str = "127.0.0.1", port: int = 4318):
        self.host = host
        self.port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self.lua_states: dict[int, str] = {}  # index -> name
        self.gamecore_index: int | None = None
        self.ingame_index: int | None = None

    @property
    def is_connected(self) -> bool:
        return self._writer is not None and not self._writer.is_closing()

    async def connect(self) -> None:
        """Connect to Civ 6 and discover Lua state indexes."""
        log.info("Connecting to Civ 6 at %s:%d", self.host, self.port)
        try:
            self._reader, self._writer = await tuner_client.connect(self.host, self.port)
        except (asyncio.TimeoutError, OSError) as e:
            raise ConnectionError(
                f"Cannot connect to Civ 6 at {self.host}:{self.port}. "
                "Is the game running with EnableTuner=1?"
            ) from e
        app_identity, raw_states = await tuner_client.handshake(self._reader, self._writer)
        log.info("Connected: %s", app_identity)

        # Parse state list: alternating [index_number, state_name] pairs
        self.lua_states = {}
        self.gamecore_index = None
        self.ingame_index = None
        i = 0
        while i + 1 < len(raw_states):
            try:
                idx = int(raw_states[i])
                name = raw_states[i + 1]
                self.lua_states[idx] = name
                if name == "GameCore_Tuner" and self.gamecore_index is None:
                    self.gamecore_index = idx
                if name == "InGame" and self.ingame_index is None:
                    self.ingame_index = idx
                i += 2
            except ValueError:
                i += 1

        log.info(
            "Discovered %d Lua states (GameCore=%s, InGame=%s)",
            len(self.lua_states),
            self.gamecore_index,
            self.ingame_index,
        )

    async def disconnect(self) -> None:
        if self._writer and not self._writer.is_closing():
            self._writer.close()
            await self._writer.wait_closed()
        self._writer = None
        self._reader = None

    async def ensure_connected(self) -> None:
        """Connect (or reconnect) if not connected. Raises ConnectionError on failure."""
        if self.is_connected:
            return
        log.info("Connecting to Civ 6...")
        await self.connect()

    async def reconnect(self) -> None:
        """Force a fresh connection and re-discover Lua states."""
        await self.disconnect()
        await self.connect()

    async def _ensure_game_states(self) -> None:
        """Ensure we have GameCore and InGame state indexes.

        If connected but missing game states (e.g. connected at main menu),
        reconnect to re-discover states now that a game may be loaded.
        """
        await self.ensure_connected()
        if self.gamecore_index is None or self.ingame_index is None:
            log.info("Game states not found, reconnecting to re-discover...")
            await self.reconnect()
        if self.gamecore_index is None or self.ingame_index is None:
            raise ConnectionError(
                "GameCore_Tuner/InGame states not found. "
                "Make sure a game is in progress (not at the main menu)."
            )

    async def execute_read(self, lua_code: str, timeout: float = 5.0) -> list[str]:
        """Execute Lua in GameCore context (read state). Returns parsed output lines."""
        await self._ensure_game_states()
        return await self._execute_and_collect(self.gamecore_index, lua_code, timeout)

    async def execute_write(self, lua_code: str, timeout: float = 5.0) -> list[str]:
        """Execute Lua in InGame context (issue commands). Returns parsed output lines."""
        await self._ensure_game_states()
        return await self._execute_and_collect(self.ingame_index, lua_code, timeout)

    async def execute_in_state(
        self, state_index: int, lua_code: str, timeout: float = 5.0
    ) -> list[str]:
        """Execute Lua in an arbitrary state index. Returns parsed output lines."""
        return await self._execute_and_collect(state_index, lua_code, timeout)

    async def _execute_and_collect(
        self, state_index: int, lua_code: str, timeout: float
    ) -> list[str]:
        """Send Lua code and collect output lines until sentinel or timeout.

        Auto-reconnects once on dead socket (e.g. after game crash/reload).
        """
        await self.ensure_connected()
        async with self._lock:
            try:
                return await self._locked_execute(state_index, lua_code, timeout)
            except (ConnectionError, OSError, asyncio.IncompleteReadError):
                # Dead socket — reconnect once and retry (still holding lock)
                log.info("Connection lost, reconnecting...")
                await self.reconnect()
                return await self._locked_execute(state_index, lua_code, timeout)

    async def _locked_execute(
        self, state_index: int, lua_code: str, timeout: float
    ) -> list[str]:
        """Inner execute — must be called while holding self._lock."""
        assert self._reader is not None
        assert self._writer is not None

        # Drain any stale messages
        await tuner_client.drain_messages(self._reader, timeout=0.1)

        await tuner_client.send_message(
            self._writer, tuner_client.TAG_COMMAND, f"CMD:{state_index}:{lua_code}"
        )

        lines: list[str] = []
        deadline = asyncio.get_event_loop().time() + timeout

        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                break

            msg = await tuner_client.recv_message_timeout(
                self._reader, timeout=min(remaining, 2.0)
            )
            if msg is None:
                break

            if msg.payload.startswith("ERR:"):
                raise LuaError(msg.payload)

            text = _parse_output(msg.payload)
            if text is not None:
                if text.strip() == SENTINEL:
                    break
                lines.append(text)
            # Ignore non-output messages (e.g. tag=3 empty ack)

        # Drain any trailing unsolicited output
        await tuner_client.drain_messages(self._reader, timeout=0.2)
        return lines


def _parse_output(payload: str) -> str | None:
    """Extract value from a print() output message.

    Format: O\\x00<context_name>: <value>
    Returns the value part, or None if not an output message.
    """
    if not payload.startswith("O"):
        return None

    # Find the ': ' separator after the context name
    sep = payload.find(": ", 2)
    if sep >= 0:
        return payload[sep + 2:]

    # Fallback: strip the O and null byte prefix
    return payload.lstrip("O").lstrip("\x00").strip()
