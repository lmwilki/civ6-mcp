"""Blind spots scanners — LLM detection of missed strategic monitoring."""
from inspect_scout import Scanner, Transcript, llm_scanner, scanner


@scanner(messages="all")
def missed_checks() -> Scanner[Transcript]:
    """Identify strategic monitoring gaps in a Civ 6 game transcript."""
    return llm_scanner(
        question="""\
Analyze this Civilization VI game transcript for strategic blind spots.
The agent should periodically check:
- get_diplomacy (every ~20 turns) for relationship changes and threats
- get_religion_spread (every ~20 turns) for invisible religious victory
- get_victory_progress (every ~20 turns) for rival victory proximity
- get_map_area around cities when at war or near enemies
- get_empire_resources (every ~10 turns) for unimproved resources
- get_trade_routes (every ~10 turns) for idle trade routes

Identify the most critical blind spot — what should the agent have
monitored but didn't? Consider game context: religious civs nearby
make religion checks critical, military civs make map scans critical.
If certain victory types are disabled (stated in the scenario objective),
do not flag missing checks for those victory types.

Focus on the gap with the highest strategic cost.""",
        answer="string",
    )


@scanner(messages="all")
def diplomacy_before_danger() -> Scanner[Transcript]:
    """Did the agent skip safety checks before ending turns near threats?"""
    return llm_scanner(
        question="""\
In this Civilization VI transcript, identify instances where the agent
ended a turn (called end_turn) without first checking get_map_area
around its cities or get_diplomacy, when there were signs of nearby
enemy units or deteriorating relations in prior turns.

Did the agent skip safety checks before ending a turn in a
potentially dangerous situation?""",
        answer="boolean",
    )
