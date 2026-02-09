"""MCP server for Civilization VI — lets LLM agents read game state and play.

Uses FastMCP with the lifespan pattern to maintain a persistent TCP connection
to the running game via FireTuner protocol.
"""

import logging
import subprocess
import tempfile
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Optional

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.utilities.types import Image

from civ_mcp.connection import GameConnection, LuaError
from civ_mcp.game_state import GameState

log = logging.getLogger(__name__)


@dataclass
class AppContext:
    game: GameState


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    conn = GameConnection()
    # Don't connect here — connect lazily on first tool call via ensure_connected().
    # This lets the MCP server start even when the game isn't running yet.
    try:
        yield AppContext(game=GameState(conn))
    finally:
        await conn.disconnect()


mcp = FastMCP(
    "Civilization VI",
    instructions="Read game state and issue commands to a running Civ 6 game. Call get_game_overview first to orient yourself.",
    lifespan=lifespan,
)


def _get_game(ctx: Context) -> GameState:
    return ctx.request_context.lifespan_context.game


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
    try:
        gs = _get_game(ctx)
        ov = await gs.get_game_overview()
        return gs.narrate_overview(ov)
    except LuaError as e:
        return f"Error reading game state: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_units(ctx: Context) -> str:
    """List all your units with position, type, movement, and health.

    Each unit shows its id and idx (needed for action commands).
    Consumed units (e.g. settlers that founded cities) are excluded.
    """
    try:
        gs = _get_game(ctx)
        units = await gs.get_units()
        return gs.narrate_units(units)
    except LuaError as e:
        return f"Error reading units: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_cities(ctx: Context) -> str:
    """List all your cities with yields, population, production, and growth.

    Each city shows its id (needed for production commands).
    """
    try:
        gs = _get_game(ctx)
        cities = await gs.get_cities()
        return gs.narrate_cities(cities)
    except LuaError as e:
        return f"Error reading cities: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_city_production(ctx: Context, city_id: int) -> str:
    """List what a city can produce right now.

    Args:
        city_id: City ID (from get_cities output)

    Returns available units, buildings, and districts with production costs.
    Call this when a city finishes building or to decide what to produce next.
    """
    try:
        gs = _get_game(ctx)
        options = await gs.list_city_production(city_id)
        return gs.narrate_city_production(options)
    except LuaError as e:
        return f"Error listing production: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_map_area(ctx: Context, center_x: int, center_y: int, radius: int = 2) -> str:
    """Get terrain info for tiles around a point.

    Args:
        center_x: X coordinate of center tile
        center_y: Y coordinate of center tile
        radius: How many tiles out from center (default 2, max 4)
    """
    radius = min(radius, 4)
    try:
        gs = _get_game(ctx)
        tiles = await gs.get_map_area(center_x, center_y, radius)
        return gs.narrate_map(tiles)
    except LuaError as e:
        return f"Error reading map: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_settle_advisor(ctx: Context, unit_id: int) -> str:
    """List best settle locations near a settler unit.

    Args:
        unit_id: The settler's composite ID (from get_units output)

    Scores locations by yields, water, defense, and resource value.
    Returns top 5 candidates sorted by score.
    """
    try:
        gs = _get_game(ctx)
        unit_index = unit_id % 65536
        return await gs.get_settle_advisor(unit_index)
    except LuaError as e:
        return f"Error running settle advisor: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_empire_resources(ctx: Context) -> str:
    """Get a summary of all resources in and near your empire.

    Shows owned resources (improved/unimproved) grouped by type,
    and unclaimed resources near your cities.
    """
    try:
        gs = _get_game(ctx)
        stockpiles, owned, nearby, luxuries = await gs.get_empire_resources()
        return gs.narrate_empire_resources(stockpiles, owned, nearby, luxuries)
    except LuaError as e:
        return f"Error reading resources: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_diplomacy(ctx: Context) -> str:
    """Get diplomatic status with all known civilizations.

    Shows diplomatic state (Friendly/Neutral/Unfriendly), relationship modifiers
    with scores and reasons, grievances, delegations/embassies, and available
    diplomatic actions you can take.
    """
    try:
        gs = _get_game(ctx)
        civs = await gs.get_diplomacy()
        return gs.narrate_diplomacy(civs)
    except LuaError as e:
        return f"Error reading diplomacy: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_tech_civics(ctx: Context) -> str:
    """Get technology and civic research status.

    Shows current research, current civic, turns remaining,
    and lists of available technologies and civics to choose from.
    """
    try:
        gs = _get_game(ctx)
        tc = await gs.get_tech_civics()
        return gs.narrate_tech_civics(tc)
    except LuaError as e:
        return f"Error reading tech/civics: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_pending_deals(ctx: Context) -> str:
    """Check for pending trade deal offers from other civilizations.

    Shows what each civ is offering and what they want in return.
    Use respond_to_deal to accept or reject.
    """
    try:
        gs = _get_game(ctx)
        deals = await gs.get_pending_deals()
        return gs.narrate_pending_deals(deals)
    except LuaError as e:
        return f"Error reading deals: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_policies(ctx: Context) -> str:
    """Get current government, policy slots, and available policies.

    Shows current government type, each policy slot with its type and current
    policy (if any), and all unlocked policies grouped by compatible slot type.
    Wildcard slots accept any policy type.
    """
    try:
        gs = _get_game(ctx)
        gov = await gs.get_policies()
        return gs.narrate_policies(gov)
    except LuaError as e:
        return f"Error reading policies: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_notifications(ctx: Context) -> str:
    """Get all active game notifications.

    Shows action-required items (need your decision) and informational
    notifications. Action-required items include which MCP tool to use
    to resolve them. Call this to check what needs attention without
    ending the turn.
    """
    try:
        gs = _get_game(ctx)
        notifs = await gs.get_notifications()
        return gs.narrate_notifications(notifs)
    except LuaError as e:
        return f"Error reading notifications: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_pending_diplomacy(ctx: Context) -> str:
    """Check for pending diplomacy encounters (e.g. first meeting with a civ).

    Diplomacy encounters block turn progression. Call this if end_turn
    reports the turn didn't advance. Returns any open sessions and how
    to respond.
    """
    try:
        gs = _get_game(ctx)
        sessions = await gs.get_diplomacy_sessions()
        return gs.narrate_diplomacy_sessions(sessions)
    except LuaError as e:
        return f"Error checking diplomacy: {e}"
    except ConnectionError as e:
        return str(e)


# ---------------------------------------------------------------------------
# Action tools (mutating)
# ---------------------------------------------------------------------------


@mcp.tool(annotations={"readOnlyHint": True})
async def get_governors(ctx: Context) -> str:
    """Get governor status, appointed governors, and available types.

    Shows governor points, currently appointed governors with assignments,
    and governors available to appoint. Use appoint_governor to appoint one.
    """
    try:
        gs = _get_game(ctx)
        gov = await gs.get_governors()
        return gs.narrate_governors(gov)
    except LuaError as e:
        return f"Error reading governors: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool()
async def appoint_governor(ctx: Context, governor_type: str) -> str:
    """Appoint a new governor.

    Args:
        governor_type: e.g. GOVERNOR_THE_EDUCATOR (Pingala), GOVERNOR_THE_DEFENDER (Victor)

    Requires available governor points. Use get_governors to see options.
    """
    try:
        gs = _get_game(ctx)
        return await gs.appoint_governor(governor_type)
    except LuaError as e:
        return f"Error appointing governor: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool()
async def assign_governor(ctx: Context, governor_type: str, city_id: int) -> str:
    """Assign an appointed governor to a city.

    Args:
        governor_type: The governor type (from get_governors output)
        city_id: The city ID (from get_cities output)

    Governor must already be appointed. Takes several turns to establish.
    """
    try:
        gs = _get_game(ctx)
        return await gs.assign_governor(governor_type, city_id)
    except LuaError as e:
        return f"Error assigning governor: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_unit_promotions(ctx: Context, unit_id: int) -> str:
    """List available promotions for a unit.

    Args:
        unit_id: The unit's composite ID (from get_units output)

    Shows promotions filtered by the unit's promotion class.
    Only units with enough XP will have promotions available.
    """
    try:
        gs = _get_game(ctx)
        status = await gs.get_unit_promotions(unit_id)
        return gs.narrate_unit_promotions(status)
    except (LuaError, ValueError) as e:
        return f"Error reading promotions: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool()
async def promote_unit(ctx: Context, unit_id: int, promotion_type: str) -> str:
    """Apply a promotion to a unit.

    Args:
        unit_id: The unit's composite ID (from get_units output)
        promotion_type: e.g. PROMOTION_BATTLECRY, PROMOTION_TORTOISE

    Use get_unit_promotions first to see available options.
    """
    try:
        gs = _get_game(ctx)
        return await gs.promote_unit(unit_id, promotion_type)
    except LuaError as e:
        return f"Error promoting unit: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_city_states(ctx: Context) -> str:
    """List known city-states with envoy counts and types.

    Shows envoy tokens available, each city-state's type (Scientific,
    Industrial, etc.), how many envoys you've sent, and who is suzerain.
    Use send_envoy to send an envoy.
    """
    try:
        gs = _get_game(ctx)
        status = await gs.get_city_states()
        return gs.narrate_city_states(status)
    except LuaError as e:
        return f"Error reading city-states: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool()
async def send_envoy(ctx: Context, city_state_player_id: int) -> str:
    """Send an envoy to a city-state.

    Args:
        city_state_player_id: The player ID of the city-state (from get_city_states)

    Requires available envoy tokens. Use get_city_states to see options.
    """
    try:
        gs = _get_game(ctx)
        return await gs.send_envoy(city_state_player_id)
    except LuaError as e:
        return f"Error sending envoy: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool(annotations={"readOnlyHint": True})
async def get_available_beliefs(ctx: Context) -> str:
    """Get pantheon status and available beliefs for selection.

    Shows current pantheon (if any), faith balance, and all available
    pantheon beliefs with their bonuses. Use choose_pantheon to found one.
    """
    try:
        gs = _get_game(ctx)
        status = await gs.get_pantheon_status()
        return gs.narrate_pantheon_status(status)
    except LuaError as e:
        return f"Error reading beliefs: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool()
async def choose_pantheon(ctx: Context, belief_type: str) -> str:
    """Found a pantheon with the specified belief.

    Args:
        belief_type: e.g. BELIEF_GOD_OF_THE_FORGE, BELIEF_DIVINE_SPARK

    Use get_available_beliefs first to see options. Requires enough faith
    and no existing pantheon.
    """
    try:
        gs = _get_game(ctx)
        return await gs.choose_pantheon(belief_type)
    except LuaError as e:
        return f"Error choosing pantheon: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool()
async def upgrade_unit(ctx: Context, unit_id: int) -> str:
    """Upgrade a unit to its next type (e.g. Slinger -> Archer).

    Args:
        unit_id: The unit's composite ID (from get_units output)

    Requires the right technology, enough gold, and the unit must have
    moves remaining. The unit's movement is consumed by upgrading.
    """
    try:
        gs = _get_game(ctx)
        return await gs.upgrade_unit(unit_id)
    except LuaError as e:
        return f"Error upgrading unit: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool()
async def get_dedications(ctx: Context) -> str:
    """Get current era age, available dedications, and active ones.

    Shows era score thresholds, whether you're in a Golden/Dark/Normal age,
    and lists available dedication choices with their bonuses.
    Use choose_dedication to select one when required.
    """
    try:
        gs = _get_game(ctx)
        status = await gs.get_dedications()
        return gs.narrate_dedications(status)
    except LuaError as e:
        return f"Error getting dedications: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool()
async def choose_dedication(ctx: Context, dedication_index: int) -> str:
    """Choose a dedication/commemoration for the current era.

    Args:
        dedication_index: The index of the dedication (from get_dedications output)

    Use get_dedications first to see available options and their bonuses.
    """
    try:
        gs = _get_game(ctx)
        return await gs.choose_dedication(dedication_index)
    except LuaError as e:
        return f"Error choosing dedication: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool()
async def respond_to_deal(ctx: Context, other_player_id: int, accept: bool) -> str:
    """Accept or reject a pending trade deal.

    Args:
        other_player_id: The player ID of the civilization (from get_pending_deals)
        accept: True to accept the deal, False to reject it

    Use get_pending_deals first to see what's being offered.
    """
    try:
        gs = _get_game(ctx)
        return await gs.respond_to_deal(other_player_id, accept)
    except LuaError as e:
        return f"Error responding to deal: {e}"
    except ConnectionError as e:
        return str(e)


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
    try:
        gs = _get_game(ctx)
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
    except ValueError as e:
        return f"Error parsing assignments: {e}"
    except LuaError as e:
        return f"Error setting policies: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool()
async def diplomacy_respond(ctx: Context, other_player_id: int, response: str) -> str:
    """Respond to a pending diplomacy encounter.

    Args:
        other_player_id: The player ID of the other civilization (from get_pending_diplomacy)
        response: "POSITIVE" (friendly) or "NEGATIVE" (dismissive)

    First meetings typically have 2-3 rounds. After your POSITIVE/NEGATIVE
    response, the tool auto-closes the session if it reaches the goodbye phase.
    """
    try:
        gs = _get_game(ctx)
        return await gs.diplomacy_respond(other_player_id, response)
    except LuaError as e:
        return f"Error responding: {e}"
    except ConnectionError as e:
        return str(e)


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
    try:
        gs = _get_game(ctx)
        return await gs.send_diplomatic_action(other_player_id, action)
    except LuaError as e:
        return f"Error sending diplomatic action: {e}"
    except ConnectionError as e:
        return str(e)


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
        action: One of: move, attack, fortify, skip, found_city, improve, automate, heal, alert, sleep, delete
        target_x: Target X coordinate (required for move/attack)
        target_y: Target Y coordinate (required for move/attack)
        improvement: Improvement type for builders (required for improve), e.g.
            IMPROVEMENT_FARM, IMPROVEMENT_MINE, IMPROVEMENT_QUARRY,
            IMPROVEMENT_PLANTATION, IMPROVEMENT_CAMP, IMPROVEMENT_PASTURE,
            IMPROVEMENT_FISHING_BOATS, IMPROVEMENT_LUMBER_MILL

    For move/attack: provide target_x and target_y.
    For improve: provide improvement name. Builder must be on the tile.
    For fortify/skip/found_city/automate/heal/alert/sleep/delete: no target needed.
    heal = fortify until healed (auto-wake at full HP).
    alert = sleep but auto-wake when enemy enters sight range.
    delete = permanently disband the unit.
    """
    gs = _get_game(ctx)
    unit_index = unit_id % 65536

    try:
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
            case _:
                return f"Error: Unknown action '{action}'. Valid: move, attack, fortify, skip, found_city, improve, automate, heal, alert, sleep, delete"
    except LuaError as e:
        return f"Error executing action: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool()
async def set_city_production(ctx: Context, city_id: int, item_type: str, item_name: str) -> str:
    """Set what a city should produce.

    Args:
        city_id: City ID (from get_cities output)
        item_type: UNIT, BUILDING, or DISTRICT
        item_name: e.g. UNIT_WARRIOR, BUILDING_MONUMENT, DISTRICT_CAMPUS

    Tip: call get_cities first to see your cities and their IDs.
    """
    try:
        gs = _get_game(ctx)
        return await gs.set_city_production(city_id, item_type, item_name)
    except LuaError as e:
        return f"Error setting production: {e}"
    except ConnectionError as e:
        return str(e)


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
    try:
        gs = _get_game(ctx)
        return await gs.purchase_item(city_id, item_type, item_name, yield_type)
    except LuaError as e:
        return f"Error purchasing: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool()
async def set_research(ctx: Context, tech_or_civic: str, category: str = "tech") -> str:
    """Choose a technology or civic to research.

    Args:
        tech_or_civic: The type name, e.g. TECH_POTTERY or CIVIC_CRAFTSMANSHIP
        category: "tech" or "civic" (default: tech)

    Tip: call get_tech_civics first to see available options.
    """
    try:
        gs = _get_game(ctx)
        if category.lower() == "civic":
            return await gs.set_civic(tech_or_civic)
        return await gs.set_research(tech_or_civic)
    except LuaError as e:
        return f"Error setting research: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool(annotations={"destructiveHint": True})
async def end_turn(ctx: Context) -> str:
    """End the current turn.

    Make sure you've moved all units, set production, and chosen research
    before ending the turn.
    """
    try:
        gs = _get_game(ctx)
        return await gs.end_turn()
    except LuaError as e:
        return f"Error ending turn: {e}"
    except ConnectionError as e:
        return str(e)


# ---------------------------------------------------------------------------
# Utility tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def dismiss_popup(ctx: Context) -> str:
    """Dismiss any blocking popup in the game UI.

    Call this if you suspect a popup (e.g. historic moment, boost notification)
    is blocking interaction.
    """
    try:
        gs = _get_game(ctx)
        return await gs.dismiss_popup()
    except LuaError as e:
        return f"Error dismissing popup: {e}"
    except ConnectionError as e:
        return str(e)


@mcp.tool(annotations={"destructiveHint": True})
async def execute_lua(ctx: Context, code: str, context: str = "gamecore") -> str:
    """Run arbitrary Lua code in the game. Advanced escape hatch.

    Args:
        code: Lua code to execute. Use print() for output, end with print("---END---").
        context: "gamecore" for simulation state, "ingame" for UI commands (default: gamecore)

    The code runs in the game's Lua environment with full access to the
    Civ 6 API. Always use print() for output (not return).
    """
    try:
        gs = _get_game(ctx)
        return await gs.execute_lua(code, context)
    except LuaError as e:
        return f"Lua error: {e}"
    except ConnectionError as e:
        return str(e)


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


def main():
    """Entry point for the MCP server."""
    logging.basicConfig(level=logging.INFO)
    mcp.run(transport="stdio")
