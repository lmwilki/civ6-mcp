"""Smoke test: connect to Civ 6's FireTuner port and verify the protocol works.

Usage: uv run python scripts/test_connection.py [host] [port]

Requires Civ 6 to be running with EnableTuner=1 in AppOptions.txt.
"""

from __future__ import annotations

import asyncio
import sys

sys.path.insert(0, "src")
from civ_mcp.tuner_client import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    TAG_COMMAND,
    connect,
    drain_messages,
    execute_lua,
    handshake,
    recv_message_timeout,
    send_message,
)


async def main() -> None:
    host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT

    print(f"=== Civ 6 FireTuner Connection Test ===\n")

    # Step 1: TCP connect
    print(f"1. Connecting to {host}:{port}...")
    try:
        reader, writer = await connect(host, port)
        print(f"   OK — TCP connection established\n")
    except ConnectionRefusedError:
        print(f"   FAIL — Connection refused.")
        print(f"   Is Civ 6 running with EnableTuner=1 in AppOptions.txt?")
        sys.exit(1)
    except OSError as e:
        print(f"   FAIL — {e}")
        sys.exit(1)

    # Step 2: Handshake
    print("2. Performing handshake (APP: + LSQ:)...")
    app_identity, lua_states = await handshake(reader, writer)
    print(f"   Game identity: {app_identity}")
    print(f"   Lua states found: {len(lua_states)}")
    if lua_states:
        for i, state in enumerate(lua_states):
            print(f"     [{i}] {state}")
    print()

    # Step 3: Execute a simple Lua command
    if lua_states:
        print("3. Executing: print('hello from civ-mcp') in state 0...")
        result = await execute_lua(reader, writer, 0, "print('hello from civ-mcp')")
        if result:
            print(f"   Response: {result}")
        else:
            print("   (no direct response — print() output goes to Lua.log)")

        # Check for any extra messages
        extras = await drain_messages(reader, timeout=1.0)
        for msg in extras:
            print(f"   Extra: tag={msg.tag} payload={msg.payload!r}")
        print()

    # Step 4: Try reading game state
    if lua_states:
        print("4. Querying game turn number...")
        result = await execute_lua(
            reader, writer, 0, "return tostring(Game.GetCurrentGameTurn())"
        )
        if result:
            print(f"   Current turn: {result}")
        else:
            print("   (no response — may need a different Lua state, or no game in progress)")

        extras = await drain_messages(reader, timeout=1.0)
        for msg in extras:
            print(f"   Extra: tag={msg.tag} payload={msg.payload!r}")
        print()

    # Done
    writer.close()
    await writer.wait_closed()

    print("=== Test complete ===")
    print("If steps 1-2 succeeded, the FireTuner protocol works on macOS!")
    print("Run the interactive REPL with: uv run python -m civ_mcp.tuner_client")


if __name__ == "__main__":
    asyncio.run(main())
