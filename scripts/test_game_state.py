"""Test GameState layer against a live game.

Usage: uv run python scripts/test_game_state.py

Requires Civ 6 to be running with EnableTuner=1 and a game in progress.
Map coordinates depend on your current game — adjust as needed.
"""

import asyncio

from civ_mcp.connection import GameConnection
from civ_mcp.game_state import GameState
from civ_mcp.narrate import (
    narrate_overview,
    narrate_units,
    narrate_cities,
    narrate_map,
    narrate_diplomacy,
    narrate_tech_civics,
)


async def main():
    conn = GameConnection()
    await conn.connect()
    gs = GameState(conn)

    # Overview
    ov = await gs.get_game_overview()
    print("=== OVERVIEW ===")
    print(narrate_overview(ov))

    # Units
    units = await gs.get_units()
    print("\n=== UNITS ===")
    print(narrate_units(units))

    # Cities
    cities, distances = await gs.get_cities()
    print("\n=== CITIES ===")
    print(narrate_cities(cities, distances))

    # Map — use first city's coordinates if available, otherwise a default
    if cities:
        cx, cy = cities[0].x, cities[0].y
    else:
        cx, cy = 0, 0
    tiles = await gs.get_map_area(cx, cy, 1)
    print(f"\n=== MAP (around {cx},{cy}) ===")
    print(narrate_map(tiles))

    # Diplomacy
    civs = await gs.get_diplomacy()
    print("\n=== DIPLOMACY ===")
    print(narrate_diplomacy(civs))

    # Tech/Civics
    tc = await gs.get_tech_civics()
    print("\n=== TECH/CIVICS ===")
    print(narrate_tech_civics(tc))

    await conn.disconnect()


asyncio.run(main())
