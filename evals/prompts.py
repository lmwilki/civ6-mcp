"""System prompts and scenario prompt builder for CivBench.

Two system prompt tiers:
- STANDARD_SYSTEM_PROMPT: Full AGENTS.md playbook (~15KB). Used by the
  standard track to test whether models follow known-good guidance under
  Sensorium constraints.
- BASELINE_SYSTEM_PROMPT: Minimal ~75-line generic prompt. Used by the
  open track as a default (teams can override with --solver).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from evals.scenarios import Scenario

# ---------------------------------------------------------------------------
# Standard track: full AGENTS.md playbook
# ---------------------------------------------------------------------------

_AGENTS_MD = Path(__file__).resolve().parent.parent / "AGENTS.md"
STANDARD_SYSTEM_PROMPT = _AGENTS_MD.read_text()

# ---------------------------------------------------------------------------
# Baseline: minimal generic prompt (open track default)
# ---------------------------------------------------------------------------

BASELINE_SYSTEM_PROMPT = """\
You are playing Civilization VI through MCP tools. You can read the full game \
state and issue commands as if you were a human player. All commands respect \
game rules — there are no cheats.

## Coordinate System

The hex grid uses (X, Y) where higher Y = visually south (down on screen).
- Y increases going down (south), decreases going up (north)
- X increases going right (east), decreases going left (west)

## Turn Loop

Follow this pattern every turn:

1. `get_game_overview` — orient: turn, yields, research, score
2. `get_units` — see all units, positions, HP, moves, charges
3. `get_map_area` around your cities and units — see terrain, resources, \
enemy units. This is your ONLY source of threat information.
4. For each unit: decide action based on context (threats, resources, terrain)
5. `get_cities` — check production queues
6. `set_city_production` / `set_research` if needed
7. `end_turn` — auto-checks for blockers and reports events

## Blocker Resolution

`end_turn` will report blockers that must be resolved before advancing:
- **Units** — unmoved units need orders (move, skip, or fortify)
- **Production** — a city needs new build orders
- **Research/Civic** — choose next tech or civic
- **Governor** — appoint a governor
- **Promotion** — promote a unit
- **Pantheon** — choose a pantheon belief
- **Envoys** — assign envoy tokens to city-states
- **Diplomacy** — respond to AI diplomatic encounters
- **Dedication** — choose a golden/dark age dedication

Always resolve all blockers before calling `end_turn` again.

## Combat

- Check `get_map_area` before moving units — hostile units show as \
**[Barbarian WARRIOR]** etc.
- Barbarians are player 63
- Ranged units attack without taking damage
- Melee attacks move your unit onto the target tile if the enemy dies
- Fortified units get +4 defense — fortify damaged units to heal

## Key Rules

- One military unit per tile, one civilian per tile (can stack 1 of each)
- Builders have limited charges and 0 combat strength — protect them
- Builders can only improve tiles inside your territory
- Set production immediately when a city finishes building
- Set research/civic immediately when one completes

## Strategy Priorities

1. **Explore** — send scouts outward, discover the map and neighbours
2. **Expand** — settle new cities in strong locations (fresh water, resources)
3. **Exploit** — improve tiles (farms, mines), build districts (Campus, \
Commercial Hub), establish trade routes
4. **Defend** — keep military near cities, respond to barbarian threats fast
5. **Research** — prioritise science and culture for compound growth
6. **Diplomacy** — meet civs, send delegations, avoid unnecessary wars
7. **Balance** — don't over-invest in military during peace, or economy during war

Think step by step each turn. Observe the full game state before acting.
"""


# ---------------------------------------------------------------------------
# Scenario prompt builder
# ---------------------------------------------------------------------------


def build_scenario_prompt(scenario: Scenario) -> str:
    """Build the user message for a scenario, including save loading instructions."""
    save_name = scenario.save_file.replace(".Civ6Save", "")
    return (
        f"## Scenario: {scenario.name}\n\n"
        f"**Civilisation:** {scenario.civilization}\n"
        f"**Difficulty:** {scenario.difficulty}\n"
        f"**Map:** {scenario.map_type}\n"
        f"**Game Speed:** {scenario.game_speed}\n"
        f"**Turn Budget:** {scenario.turn_limit} turns\n\n"
        f"### Objective\n\n"
        f"{scenario.objective}\n\n"
        f"### Getting Started\n\n"
        f"The game is running. Call `get_game_overview` first — if you're "
        f"already in the correct game (playing as {scenario.civilization}), "
        f"continue from where you are. If the overview fails or shows a "
        f"different civilisation, call `load_game_save(\"{save_name}\")` to "
        f"load the scenario save, then `get_game_overview` to orient yourself.\n\n"
        f"### Save Management\n\n"
        f"The game auto-saves every turn as `MCP_AutoSave_NNNN`. If you need "
        f"to recover from a crash or bad state, call `list_saves` to find the "
        f"most recent MCP autosave, then `load_game_save(\"MCP_AutoSave_NNNN\")` "
        f"to reload it. Do NOT load `{save_name}` to recover — that is the "
        f"Turn 1 starting save and will erase all progress."
    )
