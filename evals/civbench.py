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

import os
import re
import sys
import uuid
from pathlib import Path

# Inspect loads this file directly — ensure the project root is on sys.path
# so sibling modules (prompts, scenarios, scorer) resolve as `evals.*`.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from inspect_ai import Task, task
from inspect_ai.agent import AgentPrompt, AgentState, react
from inspect_ai.dataset import Sample
from inspect_ai.model import ChatMessageTool
from inspect_ai.model import CompactionAuto
from inspect_ai.tool import mcp_server_stdio
from inspect_ai.util import store

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


# ---------------------------------------------------------------------------
# Store extraction — capture structured data before compaction destroys it
# ---------------------------------------------------------------------------


def _parse_overview(text: str) -> dict:
    """Extract structured fields from a get_game_overview result."""
    data: dict = {}
    for pat, key, conv in [
        (r"Turn\s+(\d+)", "turn", int),
        (r"Score:\s*(\d+)", "score", int),
        (r"Science:\s*([\d.]+)", "science", float),
        (r"Culture:\s*([\d.]+)", "culture", float),
        (r"Faith:\s*([\d.]+)", "faith", float),
        (r"Cities:\s*(\d+)", "cities", int),
    ]:
        m = re.search(pat, text)
        if m:
            data[key] = conv(m.group(1))
    m = re.search(r"Gold:\s*([\d.]+)\s*\(([+-]?[\d.]+)/turn\)", text)
    if m:
        data["gold"] = float(m.group(1))
        data["gold_per_turn"] = float(m.group(2))
    return data


def _extract_to_store(state: AgentState) -> None:
    """Scan recent tool results and write structured data to the store.

    Runs inside on_continue — after tool results are appended to messages,
    before the next compaction cycle. The store survives compaction; the
    tool result text may not.
    """
    s = store()
    scanned = s.get("_scanned", 0)

    for i in range(scanned, len(state.messages)):
        msg = state.messages[i]
        if not isinstance(msg, ChatMessageTool):
            continue
        func = getattr(msg, "function", None)
        if getattr(msg, "error", None) is not None:
            continue
        text = msg.content if isinstance(msg.content, str) else ""
        if isinstance(msg.content, list):
            text = " ".join(
                c.text for c in msg.content if hasattr(c, "text")
            )

        if func == "get_game_overview":
            parsed = _parse_overview(text)
            if parsed:
                if s.get("first_overview") is None:
                    s.set("first_overview", parsed)
                s.set("last_overview", parsed)

        elif func == "end_turn":
            m = re.search(r"Turn\s+(\d+)\s*->\s*(\d+)", text)
            if m:
                turn_to = int(m.group(2))
                s.set("last_turn", turn_to)
            m = re.search(r"Score:\s*(\d+)", text)
            if m:
                s.set("last_score", int(m.group(1)))

        # Detect game-over — emitted by get_game_overview and end_turn
        if "GAME OVER" in text:
            s.set("game_over", True)

    s.set("_scanned", len(state.messages))


# ---------------------------------------------------------------------------
# on_continue callback
# ---------------------------------------------------------------------------


async def _keep_playing(state: AgentState) -> str | bool:
    """Extract structured data to store, then nudge model to keep playing.

    Returns False to stop the agent when a game-over condition is detected.
    """
    _extract_to_store(state)
    s = store()
    if s.get("game_over"):
        return False
    return CONTINUE_PLAYING


# ---------------------------------------------------------------------------
# MCP server and dataset
# ---------------------------------------------------------------------------


def _civ_mcp_server(run_id: str | None = None):
    """Create the civ-mcp MCP server instance (stdio transport).

    When run_id is provided, it's passed as CIV_MCP_RUN_ID so the MCP
    server uses the same identifier in all output filenames.
    """
    env = {"CIV_MCP_RUN_ID": run_id} if run_id else None
    return mcp_server_stdio(
        name="civ6",
        command="uv",
        args=["run", "--directory", PROJECT_ROOT, "civ-mcp"],
        env=env,
    )


def _make_dataset(
    scenario_ids: list[str] | None = None,
    resume_save: str | None = None,
    resume_context: str | None = None,
) -> list[Sample]:
    """Convert scenarios into Inspect Sample objects.

    One Sample per scenario — single save file for comparison clarity.
    All models play the exact same map.
    """
    if scenario_ids:
        scenarios = [SCENARIOS[sid] for sid in scenario_ids if sid in SCENARIOS]
    else:
        scenarios = list(SCENARIOS.values())

    samples = []
    for s in scenarios:
        samples.append(
            Sample(
                id=s.scenario_id,
                input=build_scenario_prompt(
                    s,
                    resume_save=resume_save,
                    resume_context=resume_context,
                ),
                target=str(s.turn_limit),
                metadata={
                    "scenario_id": s.scenario_id,
                    "scenario_name": s.name,
                    "save_file": s.save_file,
                    "turn_limit": s.turn_limit,
                    "difficulty": s.difficulty,
                    "map_type": s.map_type,
                    "civilization": s.civilization,
                    "opponents": list(s.opponents),
                    "blind_spot": s.blind_spot,
                    "description": s.description,
                    "resume_save": resume_save,
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
    resume_save: str | None = None,
    resume_context: str | None = None,
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
        resume_save: Resume from this save instead of the scenario start save.
        resume_context: Diary summary / game history for context when resuming.
    """
    scenario_list = _normalise_scenarios(scenarios)
    run_id = uuid.uuid4().hex[:8]
    server = _civ_mcp_server(run_id=run_id)

    # Resolve file:// references (Inspect -T passes raw strings)
    if resume_context and resume_context.startswith("file://"):
        ctx_path = Path(resume_context.removeprefix("file://"))
        resume_context = ctx_path.read_text(encoding="utf-8") if ctx_path.exists() else None

    return Task(
        dataset=_make_dataset(scenario_list, resume_save, resume_context),
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
    run_id = uuid.uuid4().hex[:8]
    server = _civ_mcp_server(run_id=run_id)

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
