"""MCP server for Civilization VI — lets LLM agents read game state and play.

Uses FastMCP with the lifespan pattern to maintain a persistent TCP connection
to the running game via FireTuner protocol.
"""

import asyncio
import logging
import subprocess
import tempfile
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Awaitable, Callable, Optional

import uvicorn
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.utilities.types import Image

from civ_mcp.connection import GameConnection, LuaError
from civ_mcp.game_state import GameState
from civ_mcp.logger import GameLogger
from civ_mcp.web_api import create_app

log = logging.getLogger(__name__)


@dataclass
class AppContext:
    game: GameState
    logger: GameLogger


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    conn = GameConnection()
    logger = GameLogger()
    gs = GameState(conn)
    log.info("Game log: %s", logger.path)

    # Start the web dashboard API as a background task (port 8000)
    web_app = create_app(gs)
    uvi_config = uvicorn.Config(web_app, host="0.0.0.0", port=8000, log_level="info")
    uvi_server = uvicorn.Server(uvi_config)
    api_task = asyncio.create_task(uvi_server.serve())
    log.info("Web API starting on http://0.0.0.0:8000")

    try:
        yield AppContext(game=gs, logger=logger)
    finally:
        uvi_server.should_exit = True
        await api_task
        await conn.disconnect()


mcp = FastMCP(
    "Civilization VI",
    instructions="Read game state and issue commands to a running Civ 6 game. Call get_game_overview first to orient yourself.",
    lifespan=lifespan,
)


def _get_game(ctx: Context) -> GameState:
    return ctx.request_context.lifespan_context.game


def _get_logger(ctx: Context) -> GameLogger:
    return ctx.request_context.lifespan_context.logger


async def _logged(
    ctx: Context,
    tool_name: str,
    params: dict[str, Any],
    fn: Callable[[], Awaitable[str]],
) -> str:
    """Run a tool function with timing, error handling, and logging."""
    logger = _get_logger(ctx)
    start = time.monotonic()
    try:
        result = await fn()
    except (LuaError, ValueError) as e:
        result = f"Error: {e}"
        await logger.log_error(tool_name, result)
        return result
    except ConnectionError as e:
        result = str(e)
        await logger.log_error(tool_name, result)
        return result
    ms = int((time.monotonic() - start) * 1000)
    await logger.log_tool_call(tool_name, params, result, ms)
    return result


# ---------------------------------------------------------------------------
# Query tools (read-only)
# ---------------------------------------------------------------------------


@mcp.tool(annotations={"readOnlyHint": True})
async def get_game_overview(ctx: Context) -> str:
    """Get a high-level summary of the current game state.

    Returns turn number, civilization, yields (gold/science/culture/faith),
    current research and civic, and counts of cities and units.
    Call this first to orient yourself.
    """
    gs = _get_game(ctx)

    async def _run():
        ov = await gs.get_game_overview()
        _get_logger(ctx).set_turn(ov.turn)
        return gs.narrate_overview(ov)

    return await _logged(ctx, "get_game_overview", {}, _run)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_units(ctx: Context) -> str:
    """List all your units with position, type, movement, and health.

    Each unit shows its id and idx (needed for action commands).
    Consumed units (e.g. settlers that founded cities) are excluded.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "get_units", {}, lambda: _narrate(gs.get_units, gs.narrate_units))


@mcp.tool(annotations={"readOnlyHint": True})
async def get_cities(ctx: Context) -> str:
    """List all your cities with yields, population, production, and growth.

    Each city shows its id (needed for production commands).
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "get_cities", {}, lambda: _narrate(gs.get_cities, gs.narrate_cities))


@mcp.tool(annotations={"readOnlyHint": True})
async def get_city_production(ctx: Context, city_id: int) -> str:
    """List what a city can produce right now.

    Args:
        city_id: City ID (from get_cities output)

    Returns available units, buildings, and districts with production costs.
    Call this when a city finishes building or to decide what to produce next.
    """
    gs = _get_game(ctx)

    async def _run():
        options = await gs.list_city_production(city_id)
        return gs.narrate_city_production(options)

    return await _logged(ctx, "get_city_production", {"city_id": city_id}, _run)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_map_area(ctx: Context, center_x: int, center_y: int, radius: int = 2) -> str:
    """Get terrain info for tiles around a point.

    Args:
        center_x: X coordinate of center tile
        center_y: Y coordinate of center tile
        radius: How many tiles out from center (default 2, max 4)
    """
    radius = min(radius, 4)
    gs = _get_game(ctx)

    async def _run():
        tiles = await gs.get_map_area(center_x, center_y, radius)
        return gs.narrate_map(tiles)

    return await _logged(ctx, "get_map_area", {"center_x": center_x, "center_y": center_y, "radius": radius}, _run)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_settle_advisor(ctx: Context, unit_id: int) -> str:
    """List best settle locations near a settler unit.

    Args:
        unit_id: The settler's composite ID (from get_units output)

    Scores locations by yields, water, defense, and resource value.
    Returns top 5 candidates sorted by score.
    """
    gs = _get_game(ctx)
    unit_index = unit_id % 65536
    return await _logged(ctx, "get_settle_advisor", {"unit_id": unit_id},
                         lambda: gs.get_settle_advisor(unit_index))


@mcp.tool(annotations={"readOnlyHint": True})
async def get_empire_resources(ctx: Context) -> str:
    """Get a summary of all resources in and near your empire.

    Shows owned resources (improved/unimproved) grouped by type,
    and unclaimed resources near your cities.
    """
    gs = _get_game(ctx)

    async def _run():
        stockpiles, owned, nearby, luxuries = await gs.get_empire_resources()
        return gs.narrate_empire_resources(stockpiles, owned, nearby, luxuries)

    return await _logged(ctx, "get_empire_resources", {}, _run)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_diplomacy(ctx: Context) -> str:
    """Get diplomatic status with all known civilizations.

    Shows diplomatic state (Friendly/Neutral/Unfriendly), relationship modifiers
    with scores and reasons, grievances, delegations/embassies, and available
    diplomatic actions you can take.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "get_diplomacy", {}, lambda: _narrate(gs.get_diplomacy, gs.narrate_diplomacy))


@mcp.tool(annotations={"readOnlyHint": True})
async def get_tech_civics(ctx: Context) -> str:
    """Get technology and civic research status.

    Shows current research, current civic, turns remaining,
    and lists of available technologies and civics to choose from.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "get_tech_civics", {}, lambda: _narrate(gs.get_tech_civics, gs.narrate_tech_civics))


@mcp.tool(annotations={"readOnlyHint": True})
async def get_pending_deals(ctx: Context) -> str:
    """Check for pending trade deal offers from other civilizations.

    Shows what each civ is offering and what they want in return.
    Use respond_to_deal to accept or reject.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "get_pending_deals", {},
                         lambda: _narrate(gs.get_pending_deals, gs.narrate_pending_deals))


@mcp.tool(annotations={"readOnlyHint": True})
async def get_policies(ctx: Context) -> str:
    """Get current government, policy slots, and available policies.

    Shows current government type, each policy slot with its type and current
    policy (if any), and all unlocked policies grouped by compatible slot type.
    Wildcard slots accept any policy type.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "get_policies", {}, lambda: _narrate(gs.get_policies, gs.narrate_policies))


@mcp.tool(annotations={"readOnlyHint": True})
async def get_notifications(ctx: Context) -> str:
    """Get all active game notifications.

    Shows action-required items (need your decision) and informational
    notifications. Action-required items include which MCP tool to use
    to resolve them. Call this to check what needs attention without
    ending the turn.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "get_notifications", {},
                         lambda: _narrate(gs.get_notifications, gs.narrate_notifications))


@mcp.tool(annotations={"readOnlyHint": True})
async def get_pending_diplomacy(ctx: Context) -> str:
    """Check for pending diplomacy encounters (e.g. first meeting with a civ).

    Diplomacy encounters block turn progression. Call this if end_turn
    reports the turn didn't advance. Returns any open sessions and how
    to respond.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "get_pending_diplomacy", {},
                         lambda: _narrate(gs.get_diplomacy_sessions, gs.narrate_diplomacy_sessions))


# ---------------------------------------------------------------------------
# Action tools (mutating)
# ---------------------------------------------------------------------------


@mcp.tool(annotations={"readOnlyHint": True})
async def get_governors(ctx: Context) -> str:
    """Get governor status, appointed governors, and available types.

    Shows governor points, currently appointed governors with assignments,
    and governors available to appoint. Use appoint_governor to appoint one.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "get_governors", {}, lambda: _narrate(gs.get_governors, gs.narrate_governors))


@mcp.tool()
async def appoint_governor(ctx: Context, governor_type: str) -> str:
    """Appoint a new governor.

    Args:
        governor_type: e.g. GOVERNOR_THE_EDUCATOR (Pingala), GOVERNOR_THE_DEFENDER (Victor)

    Requires available governor points. Use get_governors to see options.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "appoint_governor", {"governor_type": governor_type},
                         lambda: gs.appoint_governor(governor_type))


@mcp.tool()
async def assign_governor(ctx: Context, governor_type: str, city_id: int) -> str:
    """Assign an appointed governor to a city.

    Args:
        governor_type: The governor type (from get_governors output)
        city_id: The city ID (from get_cities output)

    Governor must already be appointed. Takes several turns to establish.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "assign_governor", {"governor_type": governor_type, "city_id": city_id},
                         lambda: gs.assign_governor(governor_type, city_id))


@mcp.tool(annotations={"readOnlyHint": True})
async def get_unit_promotions(ctx: Context, unit_id: int) -> str:
    """List available promotions for a unit.

    Args:
        unit_id: The unit's composite ID (from get_units output)

    Shows promotions filtered by the unit's promotion class.
    Only units with enough XP will have promotions available.
    """
    gs = _get_game(ctx)

    async def _run():
        status = await gs.get_unit_promotions(unit_id)
        return gs.narrate_unit_promotions(status)

    return await _logged(ctx, "get_unit_promotions", {"unit_id": unit_id}, _run)


@mcp.tool()
async def promote_unit(ctx: Context, unit_id: int, promotion_type: str) -> str:
    """Apply a promotion to a unit.

    Args:
        unit_id: The unit's composite ID (from get_units output)
        promotion_type: e.g. PROMOTION_BATTLECRY, PROMOTION_TORTOISE

    Use get_unit_promotions first to see available options.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "promote_unit", {"unit_id": unit_id, "promotion_type": promotion_type},
                         lambda: gs.promote_unit(unit_id, promotion_type))


@mcp.tool(annotations={"readOnlyHint": True})
async def get_city_states(ctx: Context) -> str:
    """List known city-states with envoy counts and types.

    Shows envoy tokens available, each city-state's type (Scientific,
    Industrial, etc.), how many envoys you've sent, and who is suzerain.
    Use send_envoy to send an envoy.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "get_city_states", {}, lambda: _narrate(gs.get_city_states, gs.narrate_city_states))


@mcp.tool()
async def send_envoy(ctx: Context, city_state_player_id: int) -> str:
    """Send an envoy to a city-state.

    Args:
        city_state_player_id: The player ID of the city-state (from get_city_states)

    Requires available envoy tokens. Use get_city_states to see options.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "send_envoy", {"city_state_player_id": city_state_player_id},
                         lambda: gs.send_envoy(city_state_player_id))


@mcp.tool(annotations={"readOnlyHint": True})
async def get_available_beliefs(ctx: Context) -> str:
    """Get pantheon status and available beliefs for selection.

    Shows current pantheon (if any), faith balance, and all available
    pantheon beliefs with their bonuses. Use choose_pantheon to found one.
    """
    gs = _get_game(ctx)

    async def _run():
        status = await gs.get_pantheon_status()
        return gs.narrate_pantheon_status(status)

    return await _logged(ctx, "get_available_beliefs", {}, _run)


@mcp.tool()
async def choose_pantheon(ctx: Context, belief_type: str) -> str:
    """Found a pantheon with the specified belief.

    Args:
        belief_type: e.g. BELIEF_GOD_OF_THE_FORGE, BELIEF_DIVINE_SPARK

    Use get_available_beliefs first to see options. Requires enough faith
    and no existing pantheon.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "choose_pantheon", {"belief_type": belief_type},
                         lambda: gs.choose_pantheon(belief_type))


@mcp.tool()
async def upgrade_unit(ctx: Context, unit_id: int) -> str:
    """Upgrade a unit to its next type (e.g. Slinger -> Archer).

    Args:
        unit_id: The unit's composite ID (from get_units output)

    Requires the right technology, enough gold, and the unit must have
    moves remaining. The unit's movement is consumed by upgrading.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "upgrade_unit", {"unit_id": unit_id},
                         lambda: gs.upgrade_unit(unit_id))


@mcp.tool()
async def get_dedications(ctx: Context) -> str:
    """Get current era age, available dedications, and active ones.

    Shows era score thresholds, whether you're in a Golden/Dark/Normal age,
    and lists available dedication choices with their bonuses.
    Use choose_dedication to select one when required.
    """
    gs = _get_game(ctx)

    async def _run():
        status = await gs.get_dedications()
        return gs.narrate_dedications(status)

    return await _logged(ctx, "get_dedications", {}, _run)


@mcp.tool()
async def choose_dedication(ctx: Context, dedication_index: int) -> str:
    """Choose a dedication/commemoration for the current era.

    Args:
        dedication_index: The index of the dedication (from get_dedications output)

    Use get_dedications first to see available options and their bonuses.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "choose_dedication", {"dedication_index": dedication_index},
                         lambda: gs.choose_dedication(dedication_index))


@mcp.tool()
async def respond_to_deal(ctx: Context, other_player_id: int, accept: bool) -> str:
    """Accept or reject a pending trade deal.

    Args:
        other_player_id: The player ID of the civilization (from get_pending_deals)
        accept: True to accept the deal, False to reject it

    Use get_pending_deals first to see what's being offered.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "respond_to_deal", {"other_player_id": other_player_id, "accept": accept},
                         lambda: gs.respond_to_deal(other_player_id, accept))


@mcp.tool()
async def set_policies(ctx: Context, assignments: str) -> str:
    """Set policy cards in government slots.

    Args:
        assignments: Comma-separated slot assignments, e.g.
            "0=POLICY_AGOGE,1=POLICY_URBAN_PLANNING"
            Slots not listed will be cleared. Use get_policies to see
            available policies and slot indices.

    Wildcard slots can accept any policy type. Military slots accept
    military policies, economic slots accept economic policies, etc.
    """
    gs = _get_game(ctx)

    async def _run():
        parsed: dict[int, str] = {}
        for pair in assignments.split(","):
            pair = pair.strip()
            if "=" not in pair:
                continue
            idx_str, policy = pair.split("=", 1)
            parsed[int(idx_str.strip())] = policy.strip()
        if not parsed:
            return "Error: no valid assignments. Format: '0=POLICY_AGOGE,1=POLICY_URBAN_PLANNING'"
        return await gs.set_policies(parsed)

    return await _logged(ctx, "set_policies", {"assignments": assignments}, _run)


@mcp.tool()
async def diplomacy_respond(ctx: Context, other_player_id: int, response: str) -> str:
    """Respond to a pending diplomacy encounter.

    Args:
        other_player_id: The player ID of the other civilization (from get_pending_diplomacy)
        response: "POSITIVE" (friendly) or "NEGATIVE" (dismissive)

    First meetings typically have 2-3 rounds. After your POSITIVE/NEGATIVE
    response, the tool auto-closes the session if it reaches the goodbye phase.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "diplomacy_respond", {"other_player_id": other_player_id, "response": response},
                         lambda: gs.diplomacy_respond(other_player_id, response))


@mcp.tool()
async def send_diplomatic_action(ctx: Context, other_player_id: int, action: str) -> str:
    """Send a proactive diplomatic action to another civilization.

    Args:
        other_player_id: The player ID (from get_diplomacy output)
        action: One of: DIPLOMATIC_DELEGATION, DECLARE_FRIENDSHIP, DENOUNCE,
                RESIDENT_EMBASSY, OPEN_BORDERS

    Delegations cost 25 gold and can be rejected if the civ dislikes you.
    Embassies require Writing tech. Use get_diplomacy to see available actions.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "send_diplomatic_action",
                         {"other_player_id": other_player_id, "action": action},
                         lambda: gs.send_diplomatic_action(other_player_id, action))


@mcp.tool()
async def execute_unit_action(
    ctx: Context,
    unit_id: int,
    action: str,
    target_x: Optional[int] = None,
    target_y: Optional[int] = None,
    improvement: Optional[str] = None,
) -> str:
    """Issue a command to a unit.

    Args:
        unit_id: The unit's composite ID (from get_units output)
        action: One of: move, attack, fortify, skip, found_city, improve, automate, heal, alert, sleep, delete, trade_route, activate, teleport
        target_x: Target X coordinate (required for move/attack/trade_route/teleport)
        target_y: Target Y coordinate (required for move/attack/trade_route/teleport)
        improvement: Improvement type for builders (required for improve), e.g.
            IMPROVEMENT_FARM, IMPROVEMENT_MINE, IMPROVEMENT_QUARRY,
            IMPROVEMENT_PLANTATION, IMPROVEMENT_CAMP, IMPROVEMENT_PASTURE,
            IMPROVEMENT_FISHING_BOATS, IMPROVEMENT_LUMBER_MILL

    For move/attack: provide target_x and target_y.
    For trade_route: provide target_x and target_y of destination city.
    For teleport: provide target_x and target_y of destination city. Traders only, must be idle (not on active route).
    For improve: provide improvement name. Builder must be on the tile.
    For activate: activates a Great Person on their matching district.
    For fortify/skip/found_city/automate/heal/alert/sleep/delete: no target needed.
    heal = fortify until healed (auto-wake at full HP).
    alert = sleep but auto-wake when enemy enters sight range.
    delete = permanently disband the unit.
    """
    gs = _get_game(ctx)
    unit_index = unit_id % 65536
    params: dict[str, Any] = {"unit_id": unit_id, "action": action}
    if target_x is not None:
        params["target_x"] = target_x
    if target_y is not None:
        params["target_y"] = target_y
    if improvement:
        params["improvement"] = improvement

    async def _run():
        match action.lower():
            case "move":
                if target_x is None or target_y is None:
                    return "Error: move requires target_x and target_y"
                return await gs.move_unit(unit_index, target_x, target_y)
            case "attack":
                if target_x is None or target_y is None:
                    return "Error: attack requires target_x and target_y"
                return await gs.attack_unit(unit_index, target_x, target_y)
            case "fortify":
                return await gs.fortify_unit(unit_index)
            case "skip":
                return await gs.skip_unit(unit_index)
            case "found_city":
                return await gs.found_city(unit_index)
            case "improve":
                if not improvement:
                    return "Error: improve requires improvement name (e.g. IMPROVEMENT_FARM)"
                return await gs.improve_tile(unit_index, improvement)
            case "automate":
                return await gs.automate_explore(unit_index)
            case "heal":
                return await gs.heal_unit(unit_index)
            case "alert":
                return await gs.alert_unit(unit_index)
            case "sleep":
                return await gs.sleep_unit(unit_index)
            case "delete":
                return await gs.delete_unit(unit_index)
            case "trade_route":
                if target_x is None or target_y is None:
                    return "Error: trade_route requires target_x and target_y of destination city"
                return await gs.make_trade_route(unit_index, target_x, target_y)
            case "activate":
                return await gs.activate_great_person(unit_index)
            case "teleport":
                if target_x is None or target_y is None:
                    return "Error: teleport requires target_x and target_y of the destination city"
                return await gs.teleport_to_city(unit_index, target_x, target_y)
            case _:
                return f"Error: Unknown action '{action}'. Valid: move, attack, fortify, skip, found_city, improve, automate, heal, alert, sleep, delete, trade_route, activate, teleport"

    return await _logged(ctx, "execute_unit_action", params, _run)


@mcp.tool()
async def set_city_production(
    ctx: Context, city_id: int, item_type: str, item_name: str,
    target_x: int | None = None, target_y: int | None = None,
) -> str:
    """Set what a city should produce.

    Args:
        city_id: City ID (from get_cities output)
        item_type: UNIT, BUILDING, or DISTRICT
        item_name: e.g. UNIT_WARRIOR, BUILDING_MONUMENT, DISTRICT_CAMPUS
        target_x: X coordinate for district placement (use get_district_advisor to find best tile)
        target_y: Y coordinate for district placement

    Tip: call get_cities first to see your cities and their IDs.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "set_city_production",
                         {"city_id": city_id, "item_type": item_type, "item_name": item_name},
                         lambda: gs.set_city_production(city_id, item_type, item_name, target_x, target_y))


@mcp.tool()
async def purchase_item(ctx: Context, city_id: int, item_type: str, item_name: str, yield_type: str = "YIELD_GOLD") -> str:
    """Purchase a unit or building instantly with gold or faith.

    Args:
        city_id: City ID (from get_cities output)
        item_type: UNIT or BUILDING
        item_name: e.g. UNIT_WARRIOR, BUILDING_MONUMENT
        yield_type: YIELD_GOLD (default) or YIELD_FAITH

    Costs gold/faith immediately. Use get_city_production to see what's available.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "purchase_item",
                         {"city_id": city_id, "item_type": item_type, "item_name": item_name, "yield_type": yield_type},
                         lambda: gs.purchase_item(city_id, item_type, item_name, yield_type))


@mcp.tool()
async def set_research(ctx: Context, tech_or_civic: str, category: str = "tech") -> str:
    """Choose a technology or civic to research.

    Args:
        tech_or_civic: The type name, e.g. TECH_POTTERY or CIVIC_CRAFTSMANSHIP
        category: "tech" or "civic" (default: tech)

    Tip: call get_tech_civics first to see available options.
    """
    gs = _get_game(ctx)

    async def _run():
        if category.lower() == "civic":
            return await gs.set_civic(tech_or_civic)
        return await gs.set_research(tech_or_civic)

    return await _logged(ctx, "set_research", {"tech_or_civic": tech_or_civic, "category": category}, _run)


@mcp.tool(annotations={"destructiveHint": True})
async def end_turn(ctx: Context) -> str:
    """End the current turn.

    Make sure you've moved all units, set production, and chosen research
    before ending the turn.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "end_turn", {}, gs.end_turn)


# ---------------------------------------------------------------------------
# Trade routes
# ---------------------------------------------------------------------------


@mcp.tool(annotations={"readOnlyHint": True})
async def get_trade_destinations(ctx: Context, unit_id: int) -> str:
    """List valid trade route destinations for a trader unit.

    Args:
        unit_id: The trader's composite ID (from get_units output)

    Shows domestic and international destinations. Use execute_unit_action
    with action='trade_route' and target_x/target_y to start a route.
    """
    gs = _get_game(ctx)
    unit_index = unit_id % 65536

    async def _run():
        dests = await gs.get_trade_destinations(unit_index)
        return gs.narrate_trade_destinations(dests)

    return await _logged(ctx, "get_trade_destinations", {"unit_id": unit_id}, _run)


# ---------------------------------------------------------------------------
# District advisor
# ---------------------------------------------------------------------------


@mcp.tool(annotations={"readOnlyHint": True})
async def get_district_advisor(ctx: Context, city_id: int, district_type: str) -> str:
    """Show best tiles to place a district with adjacency bonuses.

    Args:
        city_id: City ID (from get_cities)
        district_type: e.g. DISTRICT_CAMPUS, DISTRICT_HOLY_SITE, DISTRICT_INDUSTRIAL_ZONE

    Returns valid placement tiles ranked by adjacency bonus.
    Use set_city_production with target_x/target_y to build the district.
    """
    gs = _get_game(ctx)

    async def _run():
        placements = await gs.get_district_advisor(city_id, district_type)
        return gs.narrate_district_advisor(placements, district_type)

    return await _logged(ctx, "get_district_advisor", {"city_id": city_id, "district_type": district_type}, _run)


# ---------------------------------------------------------------------------
# Tile purchase tools
# ---------------------------------------------------------------------------


@mcp.tool(annotations={"readOnlyHint": True})
async def get_purchasable_tiles(ctx: Context, city_id: int) -> str:
    """List tiles a city can purchase with gold.

    Args:
        city_id: City ID (from get_cities)

    Shows cost, terrain, and resources for each purchasable tile.
    Tiles with luxury/strategic resources are listed first.
    """
    gs = _get_game(ctx)

    async def _run():
        tiles = await gs.get_purchasable_tiles(city_id)
        return gs.narrate_purchasable_tiles(tiles)

    return await _logged(ctx, "get_purchasable_tiles", {"city_id": city_id}, _run)


@mcp.tool()
async def purchase_tile(ctx: Context, city_id: int, x: int, y: int) -> str:
    """Buy a tile for a city with gold.

    Args:
        city_id: City ID
        x: Tile X coordinate
        y: Tile Y coordinate

    Use get_purchasable_tiles first to see costs and options.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "purchase_tile", {"city_id": city_id, "x": x, "y": y},
                         lambda: gs.purchase_tile(city_id, x, y))


# ---------------------------------------------------------------------------
# Government change
# ---------------------------------------------------------------------------


@mcp.tool()
async def change_government(ctx: Context, government_type: str) -> str:
    """Switch to a different government type.

    Args:
        government_type: e.g. GOVERNMENT_CLASSICAL_REPUBLIC, GOVERNMENT_OLIGARCHY

    Use get_policies to see current government. First switch after
    unlocking a new tier is free (no anarchy).
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "change_government", {"government_type": government_type},
                         lambda: gs.change_government(government_type))


# ---------------------------------------------------------------------------
# Great People
# ---------------------------------------------------------------------------


@mcp.tool(annotations={"readOnlyHint": True})
async def get_great_people(ctx: Context) -> str:
    """See available Great People and recruitment progress.

    Shows which Great People are available, their recruitment cost,
    and which civilization (if any) is recruiting them.
    """
    gs = _get_game(ctx)

    async def _run():
        gp = await gs.get_great_people()
        return gs.narrate_great_people(gp)

    return await _logged(ctx, "get_great_people", {}, _run)


# ---------------------------------------------------------------------------
# World Congress
# ---------------------------------------------------------------------------


@mcp.tool(annotations={"readOnlyHint": True})
async def get_world_congress(ctx: Context) -> str:
    """Get World Congress status, active resolutions, and voting options.

    Shows whether congress is in session, resolutions to vote on (with options A/B
    and possible targets), turns until next session, and your diplomatic favor.
    When in session, use vote_world_congress to cast votes.
    """
    gs = _get_game(ctx)

    async def _run():
        status = await gs.get_world_congress()
        return gs.narrate_world_congress(status)

    return await _logged(ctx, "get_world_congress", {}, _run)


@mcp.tool()
async def vote_world_congress(
    ctx: Context, resolution_hash: int, option: int,
    target_index: int, num_votes: int = 1,
) -> str:
    """Vote on a World Congress resolution.

    Args:
        resolution_hash: Resolution type hash (from get_world_congress)
        option: 1 for option A, 2 for option B
        target_index: 0-based index into the resolution's possible targets list
        num_votes: Number of votes (1 is free, extras cost diplomatic favor)

    After voting on all resolutions, call submit_congress or end_turn.
    Use get_world_congress first to see available resolutions and targets.
    """
    gs = _get_game(ctx)
    params = {
        "resolution_hash": resolution_hash, "option": option,
        "target_index": target_index, "num_votes": num_votes,
    }

    async def _run():
        result = await gs.vote_world_congress(resolution_hash, option, target_index, num_votes)
        # Auto-submit after voting — the game requires all resolutions voted before submitting
        # Try to submit; if it's not ready yet (more resolutions to vote), that's fine
        try:
            submit_result = await gs.submit_congress()
            if "CONGRESS_SUBMITTED" in submit_result:
                return result + "\nCongress votes submitted!"
        except Exception:
            pass
        return result

    return await _logged(ctx, "vote_world_congress", params, _run)


# ---------------------------------------------------------------------------
# City yield focus
# ---------------------------------------------------------------------------


@mcp.tool()
async def set_city_focus(ctx: Context, city_id: int, focus: str) -> str:
    """Set a city's citizen yield priority.

    Args:
        city_id: City ID
        focus: One of: food, production, gold, science, culture, faith, default
               'default' clears all focus settings.

    Cities automatically assign citizens to tiles. This biases the AI
    toward the chosen yield type when assigning new citizens.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "set_city_focus", {"city_id": city_id, "focus": focus},
                         lambda: gs.set_city_focus(city_id, focus))


# ---------------------------------------------------------------------------
# Utility tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def dismiss_popup(ctx: Context) -> str:
    """Dismiss any blocking popup in the game UI.

    Call this if you suspect a popup (e.g. historic moment, boost notification)
    is blocking interaction.
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "dismiss_popup", {}, gs.dismiss_popup)


@mcp.tool(annotations={"destructiveHint": True})
async def execute_lua(ctx: Context, code: str, context: str = "gamecore") -> str:
    """Run arbitrary Lua code in the game. Advanced escape hatch.

    Args:
        code: Lua code to execute. Use print() for output, end with print("---END---").
        context: "gamecore" for simulation state, "ingame" for UI commands (default: gamecore)

    The code runs in the game's Lua environment with full access to the
    Civ 6 API. Always use print() for output (not return).
    """
    gs = _get_game(ctx)
    return await _logged(ctx, "execute_lua", {"context": context},
                         lambda: gs.execute_lua(code, context))


@mcp.tool(annotations={"readOnlyHint": True})
async def screenshot(ctx: Context) -> Image:
    """Capture a screenshot of the Civilization VI game window.

    Returns the current game screen as an image for visual reasoning.
    Useful for verifying game state, reading UI elements, or checking
    map positions that are hard to describe with data alone.
    """
    # Find the Civ 6 window ID via Swift/CoreGraphics
    swift_code = """
import CoreGraphics
let options = CGWindowListOption(arrayLiteral: .optionAll)
if let list = CGWindowListCopyWindowInfo(options, kCGNullWindowID) as? [[String: Any]] {
    for w in list {
        let owner = w["kCGWindowOwnerName"] as? String ?? ""
        let name = w["kCGWindowName"] as? String ?? ""
        if owner.contains("Civilization") && name.contains("Civilization") {
            print(w["kCGWindowNumber"] as? Int ?? 0)
            break
        }
    }
}
"""
    result = subprocess.run(
        ["swift", "-e", swift_code],
        capture_output=True, text=True, timeout=10,
    )
    wid = result.stdout.strip()
    if not wid or not wid.isdigit():
        raise ValueError("Could not find Civilization VI window")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name

    try:
        subprocess.run(
            ["screencapture", "-x", "-l", wid, tmp_path],
            check=True, timeout=10,
        )
        return Image(data=Path(tmp_path).read_bytes(), format="png")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


async def _narrate(query_fn: Callable[[], Awaitable[Any]], narrate_fn: Callable[..., str]) -> str:
    """Helper: call a query function then narrate the result."""
    data = await query_fn()
    return narrate_fn(data)


def main():
    """Entry point for the MCP server."""
    logging.basicConfig(level=logging.INFO)
    mcp.run(transport="stdio")
