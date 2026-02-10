"""CivBench: Strategic reasoning evaluation through Civilization VI.

Two evaluation tracks:

- civbench_standard: Fixed react() agent with standardised system prompt.
  Isolates model capability — all models get the same scaffolding.

- civbench_open: Open-architecture track. Default solver can be overridden
  via --solver flag for custom agent systems.

Usage:
    # Standard baseline (fixed agent, varies model)
    inspect eval evals/civbench.py@civbench_standard \
        --model anthropic/claude-sonnet-4-5-20250929

    # Specific scenario with short budget for testing
    inspect eval evals/civbench.py@civbench_standard \
        --model openai/gpt-4o \
        -T scenarios=early_game_50 \
        --message-limit 50

    # Open track (custom solver)
    inspect eval evals/civbench.py@civbench_open \
        --model anthropic/claude-sonnet-4-5-20250929 \
        --solver my_agent.py
"""

from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.agent import react
from inspect_ai.dataset import Sample
from inspect_ai.tool import mcp_server_stdio

from evals.prompts import BASELINE_SYSTEM_PROMPT, build_scenario_prompt
from evals.scenarios import SCENARIOS, Scenario
from evals.scorer import civbench_scorer

# Project root — used to locate the MCP server entry point
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)

# Default limits
DEFAULT_MESSAGE_LIMIT = 5000
DEFAULT_TOKEN_LIMIT = 15_000_000
DEFAULT_TIME_LIMIT = 14400  # 4 hours


def _civ_mcp_server():
    """Create the civ-mcp MCP server instance (stdio transport)."""
    return mcp_server_stdio(
        name="civ6",
        command="uv",
        args=["run", "--directory", PROJECT_ROOT, "civ-mcp"],
    )


def _make_dataset(scenario_ids: list[str] | None = None) -> list[Sample]:
    """Convert scenarios into Inspect Sample objects.

    Each sample's input is the scenario objective (shown to the agent).
    Metadata carries scenario details for the scorer.
    """
    if scenario_ids:
        scenarios = [SCENARIOS[sid] for sid in scenario_ids if sid in SCENARIOS]
    else:
        scenarios = list(SCENARIOS.values())

    samples = []
    for s in scenarios:
        samples.append(
            Sample(
                input=build_scenario_prompt(s.objective, s.turn_limit),
                target=str(s.turn_limit),  # scorer uses metadata, not target
                metadata={
                    "scenario_id": s.scenario_id,
                    "save_file": s.save_file,
                    "turn_limit": s.turn_limit,
                    "difficulty": s.difficulty,
                    "map_type": s.map_type,
                    "civilization": s.civilization,
                    "description": s.description,
                },
            )
        )
    return samples


@task
def civbench_standard(
    scenarios: str | list[str] | None = None,
    message_limit: int = DEFAULT_MESSAGE_LIMIT,
    token_limit: int = DEFAULT_TOKEN_LIMIT,
    time_limit: int = DEFAULT_TIME_LIMIT,
):
    """Standardised baseline track.

    Fixed react() agent with fixed system prompt. Isolates model capability.
    All models get identical scaffolding — differences are purely model ability.

    Args:
        scenarios: Scenario ID(s) to run. None = all scenarios.
        message_limit: Max agent messages before stopping.
        token_limit: Max tokens before stopping.
        time_limit: Max wall-clock seconds before stopping.
    """
    # Normalise scenarios param (Inspect passes -T values as strings)
    if isinstance(scenarios, str):
        scenario_list = [s.strip() for s in scenarios.split(",")]
    else:
        scenario_list = scenarios

    server = _civ_mcp_server()

    return Task(
        dataset=_make_dataset(scenario_list),
        solver=react(
            prompt=BASELINE_SYSTEM_PROMPT,
            tools=[server],
            submit=False,  # Agent plays until limits, not until it "submits"
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

    Uses a default react() agent but can be overridden with --solver
    for custom agent systems. Teams submit their own scaffolding.

    The MCP server is still provided — custom solvers get the same
    tool interface to the game.

    Args:
        scenarios: Scenario ID(s) to run. None = all scenarios.
        message_limit: Max agent messages before stopping.
        token_limit: Max tokens before stopping.
        time_limit: Max wall-clock seconds before stopping.
    """
    if isinstance(scenarios, str):
        scenario_list = [s.strip() for s in scenarios.split(",")]
    else:
        scenario_list = scenarios

    server = _civ_mcp_server()

    return Task(
        dataset=_make_dataset(scenario_list),
        solver=react(tools=[server], submit=False),
        scorer=civbench_scorer(),
        message_limit=message_limit,
        token_limit=token_limit,
        time_limit=time_limit,
    )
