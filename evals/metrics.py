"""Per-scenario metric extraction for CivBench.

Each function takes a list of ToolCall objects (from scorer.py) and returns
a dict of scenario-specific metrics. All values are floats for Inspect
Score compatibility.

Extraction is regex-based against narrated tool output — the narrate.py
module produces structured text with consistent patterns.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from evals.scorer import ToolCall


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tag_calls_with_turns(calls: list[ToolCall]) -> list[tuple[int, ToolCall]]:
    """Tag each tool call with the game turn it occurred on.

    Turn numbers are inferred from get_game_overview results in the transcript.
    """
    current_turn = 0
    tagged: list[tuple[int, ToolCall]] = []
    for call in calls:
        if call.name == "get_game_overview" and not call.is_error:
            m = re.search(r"Turn\s+(\d+)", call.result)
            if m:
                current_turn = int(m.group(1))
        tagged.append((current_turn, call))
    return tagged


def _get_turns_played(calls: list[ToolCall]) -> int:
    """Get the number of turns actually played from overview bookends."""
    first_turn = 0
    last_turn = 0
    for call in calls:
        if call.name == "get_game_overview" and not call.is_error:
            m = re.search(r"Turn\s+(\d+)", call.result)
            if m:
                turn = int(m.group(1))
                if first_turn == 0:
                    first_turn = turn
                last_turn = turn
    return max(0, last_turn - first_turn)


def _count_tool(calls: list[ToolCall], tool_name: str) -> int:
    """Count successful calls to a specific tool."""
    return sum(1 for c in calls if c.name == tool_name and not c.is_error)


def _count_tool_with_arg(
    calls: list[ToolCall],
    tool_name: str,
    arg_key: str,
    arg_value: str,
) -> int:
    """Count calls to a tool where a specific argument matches."""
    return sum(
        1
        for c in calls
        if c.name == tool_name
        and not c.is_error
        and c.arguments.get(arg_key) == arg_value
    )


def _count_production(calls: list[ToolCall], item_pattern: str) -> int:
    """Count set_city_production calls where item_name matches a regex."""
    pat = re.compile(item_pattern, re.IGNORECASE)
    return sum(
        1
        for c in calls
        if c.name == "set_city_production"
        and not c.is_error
        and pat.search(c.arguments.get("item_name", ""))
    )


def _first_turn_of_tool(tagged: list[tuple[int, ToolCall]], tool_name: str) -> float:
    """Return the turn of the first successful call to a tool, or -1."""
    for turn, call in tagged:
        if call.name == tool_name and not call.is_error:
            return float(turn)
    return -1.0


def _first_turn_of_production(
    tagged: list[tuple[int, ToolCall]], item_pattern: str
) -> float:
    """Return the turn of the first production matching a pattern, or -1."""
    pat = re.compile(item_pattern, re.IGNORECASE)
    for turn, call in tagged:
        if (
            call.name == "set_city_production"
            and not call.is_error
            and pat.search(call.arguments.get("item_name", ""))
        ):
            return float(turn)
    return -1.0


def _first_turn_of_attack(tagged: list[tuple[int, ToolCall]]) -> float:
    """Return the turn of the first attack action, or -1."""
    for turn, call in tagged:
        if (
            call.name == "unit_action"
            and not call.is_error
            and call.arguments.get("action") == "attack"
        ):
            return float(turn)
    return -1.0


def _city_count_at_turn(tagged: list[tuple[int, ToolCall]], target_turn: int) -> float:
    """Extract city count from the last get_game_overview at or before target_turn."""
    city_count = 0.0
    for turn, call in tagged:
        if turn > target_turn:
            break
        if call.name == "get_game_overview" and not call.is_error:
            m = re.search(r"Cities:\s*(\d+)", call.result)
            if m:
                city_count = float(m.group(1))
    return city_count


def _exploration_pct(calls: list[ToolCall]) -> float:
    """Extract exploration % from the last get_game_overview."""
    for call in reversed(calls):
        if call.name == "get_game_overview" and not call.is_error:
            m = re.search(r"Explored:\s*([\d.]+)%", call.result)
            if m:
                return float(m.group(1))
    return 0.0


# ---------------------------------------------------------------------------
# Per-scenario scorers
# ---------------------------------------------------------------------------


def score_ground_control(calls: list[ToolCall]) -> dict[str, float]:
    """Ground Control: tempo awareness in a science race."""
    tagged = _tag_calls_with_turns(calls)
    turns = max(_get_turns_played(calls), 1)

    vp_calls = _count_tool(calls, "get_victory_progress")
    gp_calls = _count_tool(calls, "get_great_people")
    spaceport_turn = _first_turn_of_production(tagged, "DISTRICT_SPACEPORT")
    space_projects = _count_production(calls, "PROJECT_LAUNCH")

    return {
        "victory_check_freq": vp_calls / turns,
        "victory_check_count": float(vp_calls),
        "great_people_check_count": float(gp_calls),
        "spaceport_turn": spaceport_turn,
        "space_project_count": float(space_projects),
    }


def score_empty_canvas(calls: list[ToolCall]) -> dict[str, float]:
    """Empty Canvas: civ kit awareness for culture victory."""
    tagged = _tag_calls_with_turns(calls)

    theater_squares = _count_production(calls, "DISTRICT_THEATER")
    mbanza = _count_production(calls, "DISTRICT_MBANZA")
    first_theater = _first_turn_of_production(tagged, "DISTRICT_THEATER")

    # Count Great Work mentions in any tool result
    great_works = sum(
        1
        for c in calls
        if not c.is_error and re.search(r"Great Work", c.result, re.IGNORECASE)
    )

    # Tourism from get_victory_progress
    tourism = 0.0
    for call in reversed(calls):
        if call.name == "get_victory_progress" and not call.is_error:
            m = re.search(r"Tourism:\s*([\d.]+)", call.result)
            if m:
                tourism = float(m.group(1))
            break

    return {
        "theater_square_count": float(theater_squares),
        "mbanza_count": float(mbanza),
        "first_theater_turn": first_theater,
        "great_work_mentions": float(great_works),
        "tourism_final": tourism,
    }


def score_deus_vult(calls: list[ToolCall]) -> dict[str, float]:
    """Deus Vult: monitoring for invisible religious victory."""
    tagged = _tag_calls_with_turns(calls)
    turns = max(_get_turns_played(calls), 1)

    religion_checks = _count_tool(calls, "get_religion_spread")
    first_check = _first_turn_of_tool(tagged, "get_religion_spread")

    # Faith purchases of religious units (Missionaries, Apostles, Inquisitors)
    religious_purchases = sum(
        1
        for c in calls
        if c.name == "purchase_item"
        and not c.is_error
        and re.search(
            r"UNIT_(MISSIONARY|APOSTLE|INQUISITOR)",
            c.arguments.get("item_name", ""),
        )
    )

    # Detect first turn where religion_spread result mentions a rival majority
    threat_detection_turn = -1.0
    for turn, call in tagged:
        if call.name == "get_religion_spread" and not call.is_error:
            if re.search(r"majority|dominant|spread", call.result, re.IGNORECASE):
                threat_detection_turn = float(turn)
                break

    # Response latency: turns between threat detection and first defensive action
    response_latency = -1.0
    if threat_detection_turn > 0:
        for turn, call in tagged:
            if turn < threat_detection_turn:
                continue
            if call.name == "purchase_item" and re.search(
                r"UNIT_(MISSIONARY|APOSTLE|INQUISITOR)",
                call.arguments.get("item_name", ""),
            ):
                response_latency = float(turn) - threat_detection_turn
                break

    return {
        "religion_check_freq": religion_checks / turns,
        "religion_check_count": float(religion_checks),
        "religion_first_check_turn": first_check,
        "religion_threat_detection_turn": threat_detection_turn,
        "religion_response_latency": response_latency,
        "religious_unit_purchases": float(religious_purchases),
    }


def score_snowflake(calls: list[ToolCall]) -> dict[str, float]:
    """Snowflake: military awareness under sustained pressure."""
    tagged = _tag_calls_with_turns(calls)
    turns = max(_get_turns_played(calls), 1)

    map_scans = _count_tool(calls, "get_map_area")

    return {
        "cities_t40": _city_count_at_turn(tagged, 40),
        "cities_t60": _city_count_at_turn(tagged, 60),
        "cities_t80": _city_count_at_turn(tagged, 80),
        "cities_t100": _city_count_at_turn(tagged, 100),
        "map_scan_freq": map_scans / turns,
        "map_scan_count": float(map_scans),
        "exploration_pct": _exploration_pct(calls),
    }


def score_cry_havoc(calls: list[ToolCall]) -> dict[str, float]:
    """Cry Havoc: difficulty context adaptation."""
    tagged = _tag_calls_with_turns(calls)

    first_attack = _first_turn_of_attack(tagged)
    war_carts_early = sum(
        1
        for turn, call in tagged
        if turn <= 25
        and call.name == "set_city_production"
        and not call.is_error
        and "WAR_CART" in call.arguments.get("item_name", "")
    )
    ziggurats = _count_production(calls, "IMPROVEMENT_ZIGGURAT")

    # Build order: first 5 set_city_production calls
    build_order: list[str] = []
    for call in calls:
        if call.name == "set_city_production" and not call.is_error:
            item = call.arguments.get("item_name", "unknown")
            build_order.append(item)
            if len(build_order) >= 5:
                break

    # Encode build order as a single string for metadata
    # (Score values must be floats, so we track counts instead)
    military_in_first_5 = sum(1 for item in build_order if re.search(r"UNIT_", item))

    # Cities captured by T40 — look for city_action keep/raze
    cities_captured_t40 = sum(
        1
        for turn, call in tagged
        if turn <= 40
        and call.name == "city_action"
        and not call.is_error
        and call.arguments.get("action") in ("keep", "raze")
    )

    return {
        "first_attack_turn": first_attack,
        "war_carts_by_t25": float(war_carts_early),
        "ziggurat_count": float(ziggurats),
        "military_in_first_5_builds": float(military_in_first_5),
        "cities_captured_by_t40": float(cities_captured_t40),
    }
