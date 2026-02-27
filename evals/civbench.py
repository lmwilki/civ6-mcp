"""CivBench: Strategic reasoning evaluation through Civilization VI.

Two evaluation tracks:

- civbench_standard: Fixed react() agent with AGENTS.md playbook as system
  prompt. Isolates model capability — all models get the same scaffolding
  and the same strategic guidance. The scenarios test whether models follow
  that guidance under Sensorium constraints.

- civbench_open: Open-architecture track. Default solver can be overridden
  via --solver flag for custom agent systems.

Usage:
    # Standard baseline (fixed agent, varies model)
    inspect eval evals/civbench.py@civbench_standard \
        --model anthropic/claude-sonnet-4-5-20250929

    # Specific scenario
    inspect eval evals/civbench.py@civbench_standard \
        --model openai/gpt-4o \
        -T scenarios=ground_control

    # Short test run
    inspect eval evals/civbench.py@civbench_standard \
        --model anthropic/claude-sonnet-4-5-20250929 \
        -T scenarios=empty_canvas \
        --message-limit 50

    # Open track (custom solver)
    inspect eval evals/civbench.py@civbench_open \
        --model anthropic/claude-sonnet-4-5-20250929 \
        --solver my_agent.py

    # Bulk runner
    uv run python evals/runner.py --model anthropic/claude-sonnet-4-5-20250929
"""

import sys
from pathlib import Path

# Inspect loads this file directly — ensure the project root is on sys.path
# so sibling modules (prompts, scenarios, scorer) resolve as `evals.*`.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from inspect_ai import Task, task
from inspect_ai.agent import AgentPrompt, AgentState, react
from inspect_ai.dataset import Sample
from inspect_ai.model import CompactionAuto
from inspect_ai.tool import mcp_server_stdio

from evals.prompts import (
    BASELINE_SYSTEM_PROMPT,
    STANDARD_SYSTEM_PROMPT,
    build_scenario_prompt,
)
from evals.scenarios import SCENARIOS
from evals.scorer import civbench_scorer

# Project root — used to locate the MCP server entry point
PROJECT_ROOT = str(_PROJECT_ROOT)

# Default limits
DEFAULT_MESSAGE_LIMIT = 1_000_000
DEFAULT_TOKEN_LIMIT = 1_000_000_000  # effectively unlimited
DEFAULT_TIME_LIMIT = 172800  # 48 hours

CONTINUE_PLAYING = (
    "The game is still in progress. Continue playing — follow the turn loop "
    "from the system prompt. Call `get_game_overview` to orient yourself, "
    "then proceed with unit orders, city management, and `end_turn`."
)


async def _keep_playing(state: AgentState) -> str:
    """Nudge the model to keep playing when it stops calling tools."""
    return CONTINUE_PLAYING


def _civ_mcp_server():
    """Create the civ-mcp MCP server instance (stdio transport)."""
    return mcp_server_stdio(
        name="civ6",
        command="uv",
        args=["run", "--directory", PROJECT_ROOT, "civ-mcp"],
    )


def _make_dataset(scenario_ids: list[str] | None = None) -> list[Sample]:
    """Convert scenarios into Inspect Sample objects.

    Each scenario may have multiple save files (seeds). Each seed becomes
    a separate Sample, enabling statistical coverage across map variations.
    """
    if scenario_ids:
        scenarios = [SCENARIOS[sid] for sid in scenario_ids if sid in SCENARIOS]
    else:
        scenarios = list(SCENARIOS.values())

    samples = []
    for s in scenarios:
        for seed_idx, save_file in enumerate(s.save_files):
            samples.append(
                Sample(
                    id=f"{s.scenario_id}_s{seed_idx}",
                    input=build_scenario_prompt(s, seed_idx),
                    target=str(s.turn_limit),
                    metadata={
                        "scenario_id": s.scenario_id,
                        "scenario_name": s.name,
                        "seed_index": seed_idx,
                        "save_file": save_file,
                        "turn_limit": s.turn_limit,
                        "difficulty": s.difficulty,
                        "map_type": s.map_type,
                        "civilization": s.civilization,
                        "opponents": list(s.opponents),
                        "blind_spot": s.blind_spot,
                        "description": s.description,
                    },
                )
            )
    return samples


def _normalise_scenarios(scenarios: str | list[str] | None) -> list[str] | None:
    """Normalise the scenarios parameter from CLI or Python."""
    if isinstance(scenarios, str):
        return [s.strip() for s in scenarios.split(",")]
    return scenarios


@task
def civbench_standard(
    scenarios: str | list[str] | None = None,
    message_limit: int = DEFAULT_MESSAGE_LIMIT,
    token_limit: int = DEFAULT_TOKEN_LIMIT,
    time_limit: int = DEFAULT_TIME_LIMIT,
):
    """Standardised baseline track.

    Fixed react() agent with AGENTS.md as system prompt. Isolates model
    capability — all models get identical scaffolding and strategic guidance.
    Differences in results are purely model ability.

    Args:
        scenarios: Scenario ID(s) to run. None = all scenarios.
        message_limit: Max agent messages before stopping.
        token_limit: Max tokens before stopping.
        time_limit: Max wall-clock seconds before stopping.
    """
    scenario_list = _normalise_scenarios(scenarios)
    server = _civ_mcp_server()

    return Task(
        dataset=_make_dataset(scenario_list),
        solver=react(
            prompt=AgentPrompt(instructions=STANDARD_SYSTEM_PROMPT),
            tools=[server],
            submit=False,
            on_continue=_keep_playing,
            compaction=CompactionAuto(),
        ),
        scorer=civbench_scorer(),
        message_limit=message_limit,
        token_limit=token_limit,
        time_limit=time_limit,
    )


@task
def civbench_open(
    scenarios: str | list[str] | None = None,
    message_limit: int = DEFAULT_MESSAGE_LIMIT,
    token_limit: int = DEFAULT_TOKEN_LIMIT,
    time_limit: int = DEFAULT_TIME_LIMIT,
):
    """Open-architecture track.

    Uses a default react() agent with minimal prompt. Can be overridden
    with --solver for custom agent systems. Teams submit their own
    scaffolding and system prompts.

    The MCP server is still provided — custom solvers get the same
    tool interface to the game.

    Args:
        scenarios: Scenario ID(s) to run. None = all scenarios.
        message_limit: Max agent messages before stopping.
        token_limit: Max tokens before stopping.
        time_limit: Max wall-clock seconds before stopping.
    """
    scenario_list = _normalise_scenarios(scenarios)
    server = _civ_mcp_server()

    return Task(
        dataset=_make_dataset(scenario_list),
        solver=react(
            prompt=BASELINE_SYSTEM_PROMPT,
            tools=[server],
            submit=False,
            on_continue=_keep_playing,
            compaction=CompactionAuto(),
        ),
        scorer=civbench_scorer(),
        message_limit=message_limit,
        token_limit=token_limit,
        time_limit=time_limit,
    )
