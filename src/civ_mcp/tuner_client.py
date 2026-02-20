"""Minimal FireTuner TCP client for Civilization VI.

Implements the Firaxis Nexus wire protocol to connect to Civ 6's tuner port,
discover Lua states, and execute arbitrary Lua code in the game.

Wire format: [4-byte LE uint32 length][4-byte LE int32 tag][null-terminated payload]
Default port: 4318
"""

from __future__ import annotations

import asyncio
import struct
import sys
from dataclasses import dataclass

# Wire format constants
HEADER_FMT = "<Ii"  # little-endian: unsigned 32-bit length, signed 32-bit tag
HEADER_SIZE = struct.calcsize(HEADER_FMT)

# Tag values
TAG_HANDSHAKE = 4
TAG_COMMAND = 3
TAG_HELP = 1

# Default connection
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 4318


@dataclass
class Message:
    tag: int
    payload: str


async def send_message(writer: asyncio.StreamWriter, tag: int, payload: str) -> None:
    """Send a framed message to the game."""
    data = payload.encode("utf-8") + b"\x00"
    header = struct.pack(HEADER_FMT, len(data), tag)
    writer.write(header + data)
    await writer.drain()


async def recv_message(reader: asyncio.StreamReader) -> Message:
    """Read a single framed message from the game."""
    header = await reader.readexactly(HEADER_SIZE)
    length, tag = struct.unpack(HEADER_FMT, header)
    data = await reader.readexactly(length)
    # Strip trailing null bytes and decode
    payload = data.rstrip(b"\x00").decode("utf-8", errors="replace")
    return Message(tag=tag, payload=payload)


async def recv_message_timeout(
    reader: asyncio.StreamReader, timeout: float = 2.0
) -> Message | None:
    """Read a message with a timeout. Returns None on timeout."""
    try:
        return await asyncio.wait_for(recv_message(reader), timeout=timeout)
    except asyncio.TimeoutError:
        return None


async def drain_messages(
    reader: asyncio.StreamReader, timeout: float = 0.5
) -> list[Message]:
    """Read all available messages until timeout (for consuming unsolicited output)."""
    messages = []
    while True:
        msg = await recv_message_timeout(reader, timeout=timeout)
        if msg is None:
            break
        messages.append(msg)
    return messages


async def connect(
    host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: float = 5.0
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Open a TCP connection to the game's tuner port."""
    return await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)


async def handshake(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> tuple[str, list[str]]:
    """Perform the FireTuner handshake. Returns (app_identity, lua_states)."""
    # Drain any unsolicited messages first
    await drain_messages(reader, timeout=0.3)

    # APP: — get game identity
    await send_message(writer, TAG_HANDSHAKE, "APP:")
    app_msg = await recv_message_timeout(reader, timeout=5.0)
    app_identity = app_msg.payload if app_msg else "<no response>"

    # LSQ: — list Lua states
    await send_message(writer, TAG_HANDSHAKE, "LSQ:")
    lsq_msg = await recv_message_timeout(reader, timeout=5.0)
    lua_states = []
    if lsq_msg:
        # States come as null-separated or newline-separated entries
        raw = lsq_msg.payload
        lua_states = [s.strip() for s in raw.split("\x00") if s.strip()]
        if len(lua_states) <= 1 and "\n" in raw:
            lua_states = [s.strip() for s in raw.split("\n") if s.strip()]

    return app_identity, lua_states


async def execute_lua(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    state_index: int,
    code: str,
    timeout: float = 5.0,
) -> str | None:
    """Execute Lua code in the given state. Returns response payload or None."""
    await send_message(writer, TAG_COMMAND, f"CMD:{state_index}:{code}")
    msg = await recv_message_timeout(reader, timeout=timeout)
    return msg.payload if msg else None


async def interactive_repl(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    lua_states: list[str],
) -> None:
    """Interactive Lua REPL over the tuner connection."""
    state_index = 0
    print(
        f"\nUsing Lua state {state_index}. Type 'states' to list, 'use N' to switch, 'quit' to exit.\n"
    )

    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(
                None, lambda: input(f"[{state_index}]> ")
            )
        except (EOFError, KeyboardInterrupt):
            break

        line = line.strip()
        if not line:
            continue
        if line == "quit":
            break
        if line == "states":
            for i, s in enumerate(lua_states):
                print(f"  {i}: {s}")
            continue
        if line.startswith("use "):
            try:
                state_index = int(line.split()[1])
                print(f"Switched to state {state_index}")
            except (ValueError, IndexError):
                print("Usage: use <number>")
            continue

        result = await execute_lua(reader, writer, state_index, line)
        if result:
            print(result)
        else:
            print("(no response)")

        # Drain any extra messages (e.g. print() output)
        extras = await drain_messages(reader, timeout=0.3)
        for msg in extras:
            print(msg.payload)


async def main() -> None:
    host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT

    print(f"Connecting to Civ 6 tuner at {host}:{port}...")
    try:
        reader, writer = await connect(host, port)
    except ConnectionRefusedError:
        print(f"Connection refused. Is Civ 6 running with EnableTuner=1?")
        sys.exit(1)
    except OSError as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    print("Connected! Performing handshake...\n")
    app_identity, lua_states = await handshake(reader, writer)

    print(f"Game: {app_identity}")
    print(f"Lua states ({len(lua_states)}):")
    for i, state in enumerate(lua_states):
        print(f"  {i}: {state}")

    await interactive_repl(reader, writer, lua_states)

    writer.close()
    await writer.wait_closed()
    print("\nDisconnected.")


if __name__ == "__main__":
    asyncio.run(main())
