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
        -T scenarios=snowflake \
        --message-limit 50

    # Open track (custom solver)
    inspect eval evals/civbench.py@civbench_open \
        --model anthropic/claude-sonnet-4-5-20250929 \
        --solver my_agent.py

    # Bulk runner
    uv run python evals/runner.py --model anthropic/claude-sonnet-4-5-20250929
"""

import json
import os
import re
import sys
import time
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
from inspect_ai.model import ChatMessageAssistant, ChatMessageTool
from inspect_ai.model import CompactionSummary
from inspect_ai.tool import mcp_server_stdio
from inspect_ai.util import store

from evals.prompts import (
    BASELINE_SYSTEM_PROMPT,
    STANDARD_SYSTEM_PROMPT,
    build_scenario_prompt,
)
from evals.scenarios import SCENARIOS, Scenario
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

# Reasoning capture — JSONL sidecar for assistant message text
REASONING_DIR = Path.home() / ".civ6-mcp"


def _reasoning_path(run_id: str) -> Path:
    return REASONING_DIR / f"reasoning_{run_id}.jsonl"


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
# Reasoning capture — extract assistant message text to JSONL sidecar
# ---------------------------------------------------------------------------


def _extract_visible_text(msg: ChatMessageAssistant) -> str:
    """Extract visible text from an assistant message, excluding reasoning blocks."""
    if isinstance(msg.content, str):
        return msg.content
    parts = []
    for item in msg.content:
        if getattr(item, "type", None) == "text" and hasattr(item, "text"):
            parts.append(item.text)
    return "\n".join(parts)


def _extract_reasoning(state: AgentState) -> None:
    """Scan recent assistant messages and write reasoning text to JSONL sidecar.

    Writes to reasoning_{run_id}.jsonl alongside diary/log files.
    Also updates store["reasoning_summary"] with aggregate counts.
    """
    s = store()
    scanned = s.get("_scanned_reasoning", 0)
    run_id = os.environ.get("CIV_MCP_RUN_ID")
    if not run_id:
        s.set("_scanned_reasoning", len(state.messages))
        return

    path = _reasoning_path(run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    turn = s.get("last_turn", 0)
    entries: list[dict] = []

    for i in range(scanned, len(state.messages)):
        msg = state.messages[i]
        if not isinstance(msg, ChatMessageAssistant):
            continue
        text = _extract_visible_text(msg)
        if not text.strip():
            continue

        has_tools = bool(msg.tool_calls)
        entries.append({
            "run_id": run_id,
            "turn": turn,
            "msg_index": i,
            "msg_type": "reasoning" if has_tools else "summary",
            "tool_call_count": len(msg.tool_calls) if msg.tool_calls else 0,
            "text": text.strip(),
            "text_len": len(text.strip()),
            "ts": time.time(),
        })

    if entries:
        with open(path, "a") as f:
            for entry in entries:
                f.write(json.dumps(entry, separators=(",", ":")) + "\n")

    s.set("_scanned_reasoning", len(state.messages))

    if entries:
        summary = s.get("reasoning_summary", {
            "total_entries": 0,
            "summary_count": 0,
            "reasoning_count": 0,
            "total_chars": 0,
        })
        for e in entries:
            summary["total_entries"] += 1
            summary["total_chars"] += e["text_len"]
            if e["msg_type"] == "summary":
                summary["summary_count"] += 1
            else:
                summary["reasoning_count"] += 1
        s.set("reasoning_summary", summary)


# ---------------------------------------------------------------------------
# on_continue callback
# ---------------------------------------------------------------------------


LOOP_THRESHOLD = 5  # identical consecutive tool calls before intervention
LOOP_HARD_LIMIT = 15  # hard stop after this many identical consecutive calls


def _detect_tool_loop(state: AgentState) -> int:
    """Count consecutive identical tool calls at the tail of the conversation.

    Fingerprints each tool call as (function_name, sorted_args_json) and counts
    how many consecutive identical calls appear at the end of the message history.
    Returns the streak length (0 if no repetition).
    """
    # Walk backwards through messages collecting tool call fingerprints
    fingerprints: list[str] = []
    for msg in reversed(state.messages):
        if not isinstance(msg, ChatMessageAssistant):
            continue
        if not msg.tool_calls:
            break  # hit an assistant message without tool calls — stop scanning
        for tc in reversed(msg.tool_calls):
            args = json.dumps(tc.arguments, sort_keys=True) if tc.arguments else "{}"
            fingerprints.append(f"{tc.function}|{args}")

    if len(fingerprints) < 2:
        return 0

    # fingerprints[0] is the most recent call — count how many match it
    latest = fingerprints[0]
    streak = 0
    for fp in fingerprints:
        if fp == latest:
            streak += 1
        else:
            break
    return streak


async def _keep_playing(state: AgentState) -> str | bool:
    """Extract structured data to store, then nudge model to keep playing.

    Returns False to stop the agent when a game-over condition is detected
    or when a hard tool-call loop limit is exceeded.
    Returns True (silent continue) when the model is actively calling tools.
    Only injects the nudge message when the model goes quiet (no tool calls).
    """
    _extract_to_store(state)
    _extract_reasoning(state)
    s = store()
    if s.get("game_over"):
        return False

    # Detect degenerate tool-call loops (same tool+args repeated)
    streak = _detect_tool_loop(state)
    if streak >= LOOP_HARD_LIMIT:
        s.set("loop_terminated", True)
        return False
    if streak >= LOOP_THRESHOLD:
        tool_calls = state.output.message.tool_calls
        tool_name = tool_calls[0].function if tool_calls else "unknown"
        return (
            f"LOOP DETECTED: You have called `{tool_name}` with the same "
            f"arguments {streak} times consecutively. This is not productive. "
            f"Stop repeating this call. Either act on the information you "
            f"already have, try a different approach, or call `end_turn`."
        )

    if state.output.message.tool_calls:
        return True
    return CONTINUE_PLAYING


# ---------------------------------------------------------------------------
# MCP server and dataset
# ---------------------------------------------------------------------------


def _civ_mcp_server(
    run_id: str | None = None,
    scenario: Scenario | None = None,
    eval_track: str = "",
    model_id: str = "",
    resume_save: str | None = None,
):
    """Create the civ-mcp MCP server instance (stdio transport).

    Passes run_id, eval metadata, and model ID as env vars so the MCP server
    writes them to the telemetry manifest and diary entries.
    """
    env: dict[str, str] = {}
    if run_id:
        env["CIV_MCP_RUN_ID"] = run_id
    if model_id:
        env["CIV_MCP_AGENT_MODEL"] = model_id
    if scenario:
        # Auto-boot: resume_save overrides scenario start save
        env["CIV_MCP_SAVE_FILE"] = resume_save or scenario.save_file.replace(".Civ6Save", "")
    # Package eval metadata as a single JSON blob → written to manifest
    metadata: dict[str, str] = {}
    if scenario:
        metadata["scenario_id"] = scenario.scenario_id
        metadata["difficulty"] = scenario.difficulty
        metadata["map_type"] = scenario.map_type
        metadata["map_size"] = scenario.map_size
        metadata["game_speed"] = scenario.game_speed
    if eval_track:
        metadata["eval_track"] = eval_track
    if model_id:
        metadata["model_id"] = model_id
    if metadata:
        env["CIV_MCP_METADATA"] = json.dumps(metadata)
    # Pass through cloud telemetry bucket if configured
    cloud_bucket = os.environ.get("CIV_MCP_TELEMETRY_BUCKET", "")
    if cloud_bucket:
        env["CIV_MCP_TELEMETRY_BUCKET"] = cloud_bucket
    # Pass through Azure storage credentials for CloudSink
    for az_var in ("AZURE_STORAGE_ACCOUNT_NAME", "AZURE_STORAGE_ACCOUNT_KEY",
                   "AZURE_STORAGE_SAS_TOKEN", "AZURE_STORAGE_ANON",
                   "AZURE_STORAGE_CONNECTION_STRING"):
        val = os.environ.get(az_var)
        if val:
            env[az_var] = val
    # Pass through display/GUI env vars needed for Linux GUI automation
    # (xdotool, mss screen capture). mcp_server_stdio only inherits a
    # minimal Posix set (HOME, PATH, SHELL, etc.) — DISPLAY is not included.
    for gui_var in ("DISPLAY", "XAUTHORITY", "WAYLAND_DISPLAY", "XDG_RUNTIME_DIR"):
        val = os.environ.get(gui_var)
        if val:
            env[gui_var] = val
    # Include platform-specific launcher deps so the MCP server can do
    # GUI automation (OCR, window focus, clicks) for save loading / recovery.
    extras = []
    if cloud_bucket:
        extras.append("cloud")
    if sys.platform == "darwin":
        extras.append("launcher-macos")
    elif sys.platform == "linux":
        extras.append("launcher-linux")
    elif sys.platform == "win32":
        extras.append("launcher-windows")

    args = ["run", "--directory", PROJECT_ROOT]
    for ex in extras:
        args.extend(["--extra", ex])
    args.append("civ-mcp")

    return mcp_server_stdio(
        name="civ6",
        command="uv",
        args=args,
        env=env or None,
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
                    "map_size": s.map_size,
                    "game_speed": s.game_speed,
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
    run_id: str | None = None,
    model_id: str = "",
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
        run_id: Reuse an existing run_id (for resume). Generated if not provided.
    """
    scenario_list = _normalise_scenarios(scenarios)
    run_id = run_id or uuid.uuid4().hex[:8]
    os.environ["CIV_MCP_RUN_ID"] = run_id  # reasoning capture reads this
    # Pass scenario metadata when running a single scenario. Multi-scenario
    # runs share one MCP process, so env vars can't vary per sample — the
    # diary/log entries still carry per-turn civ/game info for identification.
    scenario_obj = SCENARIOS.get(scenario_list[0]) if scenario_list and len(scenario_list) == 1 else None
    server = _civ_mcp_server(run_id=run_id, scenario=scenario_obj, eval_track="civbench_standard", model_id=model_id, resume_save=resume_save)

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
            compaction=CompactionSummary(),
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
    model_id: str = "",
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
    os.environ["CIV_MCP_RUN_ID"] = run_id  # reasoning capture reads this
    # See civbench_standard for why scenario_obj is None for multi-scenario runs
    scenario_obj = SCENARIOS.get(scenario_list[0]) if scenario_list and len(scenario_list) == 1 else None
    server = _civ_mcp_server(run_id=run_id, scenario=scenario_obj, eval_track="civbench_open", model_id=model_id)

    return Task(
        dataset=_make_dataset(scenario_list),
        solver=react(
            prompt=BASELINE_SYSTEM_PROMPT,
            tools=[server],
            submit=False,
            on_continue=_keep_playing,
            compaction=CompactionSummary(),
        ),
        scorer=civbench_scorer(),
        message_limit=message_limit,
        token_limit=token_limit,
        time_limit=time_limit,
    )
