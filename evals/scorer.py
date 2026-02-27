"""Multi-dimensional scorer for CivBench.

Extracts metrics from the full tool-call transcript in TaskState.messages.
Universal metrics (score, economy, tool fluency) apply to all scenarios.
Scenario-specific metrics are dispatched via state.metadata["scenario_id"].

Each dimension gets mean() and stderr() aggregation across samples.
"""

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

from inspect_ai.scorer import (
    Score,
    Target,
    mean,
    scorer,
    stderr,
)
from inspect_ai.solver import TaskState

from evals import metrics

# ---------------------------------------------------------------------------
# Internal: tool call extraction
# ---------------------------------------------------------------------------


@dataclass
class ToolCall:
    """A single tool invocation extracted from the message history."""

    name: str
    arguments: dict[str, Any]
    result: str  # the tool's text response
    inspect_error: bool = False  # Inspect-level tool execution error

    @property
    def is_error(self) -> bool:
        """Check for Inspect-level OR application-level errors."""
        if self.inspect_error:
            return True
        text = self.result.strip()
        return text.startswith("Error:") or text.startswith("ERR:")


def _extract_tool_calls(state: TaskState) -> list[ToolCall]:
    """Walk state.messages and pair assistant tool_calls with tool responses."""
    # Build a map of tool_call_id -> (name, arguments) from assistant messages
    call_map: dict[str, tuple[str, dict[str, Any]]] = {}
    for msg in state.messages:
        if msg.role == "assistant" and hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                call_map[tc.id] = (tc.function, tc.arguments)

    # Now walk tool messages and match them
    calls: list[ToolCall] = []
    for msg in state.messages:
        if msg.role == "tool":
            call_id = getattr(msg, "tool_call_id", None)
            func_name = getattr(msg, "function", None) or ""
            is_error = getattr(msg, "error", None) is not None

            # Get the text content
            content = msg.content if isinstance(msg.content, str) else ""
            if isinstance(msg.content, list):
                content = " ".join(c.text for c in msg.content if hasattr(c, "text"))

            # Match with the assistant's call info
            if call_id and call_id in call_map:
                name, args = call_map[call_id]
            else:
                name, args = func_name, {}

            calls.append(
                ToolCall(
                    name=name,
                    arguments=args,
                    result=content,
                    inspect_error=is_error,
                )
            )

    return calls


# ---------------------------------------------------------------------------
# Internal: metric extraction helpers
# ---------------------------------------------------------------------------


def _find_last_overview(calls: list[ToolCall]) -> dict[str, Any] | None:
    """Find the last successful get_game_overview result and parse it."""
    for call in reversed(calls):
        if call.name == "get_game_overview" and not call.is_error:
            return _parse_overview_text(call.result)
    return None


def _parse_overview_text(text: str) -> dict[str, Any]:
    """Extract key-value pairs from narrated game overview text.

    Actual format from narrate_overview():
        Turn 42 | Rome (Trajan) | Score: 89
        Gold: 150 (+12/turn) | Science: 25.4 | Culture: 18.2 | Faith: 10 | Favor: 0
        Research: TECH_MINING | Civic: CIVIC_CODE_OF_LAWS
        Cities: 2 | Units: 5
    """
    data: dict[str, Any] = {}

    # Turn
    m = re.search(r"Turn\s+(\d+)", text)
    if m:
        data["turn"] = int(m.group(1))

    # Score
    m = re.search(r"Score:\s*(\d+)", text)
    if m:
        data["score"] = int(m.group(1))

    # Gold — format: "Gold: 150 (+12/turn)"
    m = re.search(r"Gold:\s*([\d.]+)\s*\(([+-]?[\d.]+)/turn\)", text)
    if m:
        data["gold"] = float(m.group(1))
        data["gold_per_turn"] = float(m.group(2))

    # Science — format: "Science: 25.4" (no /turn suffix)
    m = re.search(r"Science:\s*([\d.]+)", text)
    if m:
        data["science"] = float(m.group(1))

    # Culture — format: "Culture: 18.2" (no /turn suffix)
    m = re.search(r"Culture:\s*([\d.]+)", text)
    if m:
        data["culture"] = float(m.group(1))

    # Faith — format: "Faith: 10"
    m = re.search(r"Faith:\s*([\d.]+)", text)
    if m:
        data["faith"] = float(m.group(1))

    return data


def _find_first_overview(calls: list[ToolCall]) -> dict[str, Any] | None:
    """Find the first successful get_game_overview result."""
    for call in calls:
        if call.name == "get_game_overview" and not call.is_error:
            return _parse_overview_text(call.result)
    return None


def _count_errors(calls: list[ToolCall]) -> int:
    return sum(1 for c in calls if c.is_error)


def _count_unique_tools(calls: list[ToolCall]) -> int:
    return len({c.name for c in calls})


def _count_end_turns(calls: list[ToolCall]) -> int:
    return sum(1 for c in calls if c.name == "end_turn")


def _count_attacks(calls: list[ToolCall]) -> int:
    return sum(
        1
        for c in calls
        if c.name == "unit_action" and c.arguments.get("action") == "attack"
    )


def _count_cities_founded(calls: list[ToolCall]) -> int:
    return sum(
        1
        for c in calls
        if c.name == "unit_action"
        and c.arguments.get("action") == "found_city"
        and not c.is_error
    )


def _count_map_scans(calls: list[ToolCall]) -> int:
    return sum(1 for c in calls if c.name == "get_map_area")


def _count_research_sets(calls: list[ToolCall]) -> int:
    return sum(
        1
        for c in calls
        if c.name == "set_research"
        and c.arguments.get("category", "tech") == "tech"
        and not c.is_error
    )


def _count_civic_sets(calls: list[ToolCall]) -> int:
    return sum(
        1
        for c in calls
        if c.name == "set_research"
        and c.arguments.get("category") == "civic"
        and not c.is_error
    )


def _count_diplomatic_actions(calls: list[ToolCall]) -> int:
    diplo_tools = {
        "respond_to_diplomacy",
        "send_diplomatic_action",
        "send_envoy",
    }
    return sum(1 for c in calls if c.name in diplo_tools and not c.is_error)


# ---------------------------------------------------------------------------
# Public scorer
# ---------------------------------------------------------------------------


@scorer(metrics={"*": [mean(), stderr()]})
def civbench_scorer():
    """Score a CivBench run across multiple dimensions.

    Dimensions:
    - overall_score: Raw Civ 6 game score from final overview
    - economic: Yield growth (gold + science + culture per-turn growth)
    - military: Attack actions taken (proxy for threat response)
    - scientific: Research changes made
    - cultural: Civic changes made
    - spatial: Map scans + cities founded (exploration & expansion)
    - diplomatic: Diplomatic actions taken
    - tool_fluency: 1 - error_rate (higher = better)
    - turns_played: Number of end_turn calls (progress measure)
    """

    async def score(state: TaskState, target: Target) -> Score:
        calls = _extract_tool_calls(state)
        total_calls = len(calls)

        if total_calls == 0:
            return Score(
                value={
                    "overall_score": 0.0,
                    "economic": 0.0,
                    "military": 0.0,
                    "scientific": 0.0,
                    "cultural": 0.0,
                    "spatial": 0.0,
                    "diplomatic": 0.0,
                    "tool_fluency": 0.0,
                    "turns_played": 0.0,
                },
                answer="No tool calls made",
                explanation="Agent produced no tool calls.",
                metadata={"total_calls": 0, "errors": 0},
            )

        first_overview = _find_first_overview(calls)
        last_overview = _find_last_overview(calls)

        # --- Overall score ---
        overall = float(last_overview.get("score", 0)) if last_overview else 0.0

        # --- Economic: yield growth ---
        economic = 0.0
        if first_overview and last_overview:
            for key in ("gold_per_turn", "science", "culture"):
                start = first_overview.get(key, 0.0)
                end = last_overview.get(key, 0.0)
                economic += max(0.0, end - start)

        # --- Military ---
        military = float(_count_attacks(calls))

        # --- Scientific ---
        scientific = float(_count_research_sets(calls))

        # --- Cultural ---
        cultural = float(_count_civic_sets(calls))

        # --- Spatial ---
        spatial = float(_count_map_scans(calls) + _count_cities_founded(calls) * 10)

        # --- Diplomatic ---
        diplomatic = float(_count_diplomatic_actions(calls))

        # --- Tool fluency ---
        errors = _count_errors(calls)
        tool_fluency = 1.0 - (errors / total_calls) if total_calls > 0 else 0.0

        # --- Turns played (actual game turns advanced, not end_turn calls) ---
        if first_overview and last_overview:
            t0 = first_overview.get("turn", 0)
            t1 = last_overview.get("turn", 0)
            turns_played = float(max(0, t1 - t0))
        else:
            turns_played = float(_count_end_turns(calls))

        # --- Scenario-specific metrics ---
        scenario_id = state.metadata.get("scenario_id", "")
        scenario_metrics: dict[str, float] = {}
        if scenario_id == "ground_control":
            scenario_metrics = metrics.score_ground_control(calls)
        elif scenario_id == "empty_canvas":
            scenario_metrics = metrics.score_empty_canvas(calls)
        elif scenario_id == "deus_vult":
            scenario_metrics = metrics.score_deus_vult(calls)
        elif scenario_id == "snowflake":
            scenario_metrics = metrics.score_snowflake(calls)
        elif scenario_id == "cry_havoc":
            scenario_metrics = metrics.score_cry_havoc(calls)

        # Build summary
        turn_info = (
            f"Turn {last_overview.get('turn', '?')}"
            if last_overview
            else "unknown turn"
        )
        summary = (
            f"Score {overall:.0f} at {turn_info} | "
            f"{turns_played:.0f} turns | "
            f"{total_calls} tool calls ({errors} errors)"
        )

        value = {
            "overall_score": overall,
            "economic": economic,
            "military": military,
            "scientific": scientific,
            "cultural": cultural,
            "spatial": spatial,
            "diplomatic": diplomatic,
            "tool_fluency": tool_fluency,
            "turns_played": turns_played,
            **scenario_metrics,
        }

        return Score(
            value=value,
            answer=summary,
            explanation=(
                f"Extracted from {total_calls} tool calls over {turns_played:.0f} turns.\n"
                f"Final overview: {last_overview or 'not found'}\n"
                f"Unique tools used: {_count_unique_tools(calls)}\n"
                f"Error rate: {errors}/{total_calls} = {(1 - tool_fluency) * 100:.1f}%"
            ),
            metadata={
                "total_calls": total_calls,
                "errors": errors,
                "unique_tools": _count_unique_tools(calls),
                "end_turn_calls": _count_end_turns(calls),
                "turns_played": int(turns_played),
                "first_overview": first_overview,
                "last_overview": last_overview,
                "tool_distribution": dict(Counter(c.name for c in calls)),
            },
        )

    return score
