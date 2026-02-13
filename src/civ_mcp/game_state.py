"""High-level game state API with server-side narration.

Wraps GameConnection + lua_queries into typed async methods that return
both structured data and human-readable narrated text. Has ZERO MCP
dependency — enabling multi-agent architectures where specialist servers
import the same GameState class but expose different tool subsets.
"""

from __future__ import annotations

import logging

from civ_mcp.connection import GameConnection, LuaError
from civ_mcp import lua_queries as lq

log = logging.getLogger(__name__)


class GameState:
    """High-level async API for Civ 6 game state + actions."""

    def __init__(self, connection: GameConnection):
        self.conn = connection
        self._last_snapshot: lq.TurnSnapshot | None = None

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    async def get_game_overview(self) -> lq.GameOverview:
        # InGame context needed for GetFavor() (nil in GameCore)
        lines = await self.conn.execute_write(lq.build_overview_query())
        ov = lq.parse_overview_response(lines)
        # Bootstrap: capture baseline snapshot for first end_turn diff
        if self._last_snapshot is None:
            try:
                self._last_snapshot = await self._take_snapshot(ov)
            except Exception:
                log.debug("Failed to bootstrap snapshot", exc_info=True)
        return ov

    async def get_units(self) -> list[lq.UnitInfo]:
        lines = await self.conn.execute_write(lq.build_units_query())
        return lq.parse_units_response(lines)

    async def get_threat_scan(self) -> list[lq.ThreatInfo]:
        lines = await self.conn.execute_read(lq.build_threat_scan_query())
        return lq.parse_threat_scan_response(lines)

    async def get_victory_progress(self) -> lq.VictoryProgress:
        lines = await self.conn.execute_write(lq.build_victory_progress_query())
        return lq.parse_victory_progress_response(lines)

    async def get_cities(self) -> tuple[list[lq.CityInfo], list[str]]:
        lines = await self.conn.execute_write(lq.build_cities_query())
        return lq.parse_cities_response(lines)

    async def get_map_area(
        self, center_x: int, center_y: int, radius: int = 2
    ) -> list[lq.TileInfo]:
        lines = await self.conn.execute_read(
            lq.build_map_area_query(center_x, center_y, radius)
        )
        return lq.parse_map_response(lines)

    async def get_strategic_map(self) -> lq.StrategicMapData:
        lines = await self.conn.execute_read(lq.build_strategic_map_query())
        return lq.parse_strategic_map_response(lines)

    async def get_diplomacy(self) -> list[lq.CivInfo]:
        # Uses InGame context for GetDiplomaticAI access
        lines = await self.conn.execute_write(lq.build_diplomacy_query())
        return lq.parse_diplomacy_response(lines)

    async def get_tech_civics(self) -> lq.TechCivicStatus:
        lines = await self.conn.execute_read(lq.build_tech_civics_query())
        return lq.parse_tech_civics_response(lines)

    async def get_empire_resources(
        self,
    ) -> tuple[list[lq.ResourceStockpile], list[lq.OwnedResource], list[lq.NearbyResource], dict[str, int]]:
        # InGame context needed for GetResourceStockpileCap etc.
        lines = await self.conn.execute_write(lq.build_empire_resources_query())
        return lq.parse_empire_resources_response(lines)

    # ------------------------------------------------------------------
    # Action methods (run in InGame context for UnitManager access)
    # ------------------------------------------------------------------

    async def move_unit(self, unit_index: int, target_x: int, target_y: int) -> str:
        lua = lq.build_move_unit(unit_index, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def attack_unit(self, unit_index: int, target_x: int, target_y: int) -> str:
        # Pre-attack: run combat estimator
        estimate_str = ""
        try:
            est_lua = lq.build_combat_estimate_query(unit_index, target_x, target_y)
            est_lines = await self.conn.execute_write(est_lua)
            est = lq.parse_combat_estimate(est_lines, 0, 0)
            if est:
                estimate_str = self.narrate_combat_estimate(est) + "\n"
        except Exception as e:
            log.debug("Combat estimate failed: %s", e)
        lua = lq.build_attack_unit(unit_index, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        # Follow up with GameCore read for actual post-combat HP
        if result.startswith("RANGE_ATTACK") or result.startswith("MELEE_ATTACK"):
            try:
                followup = await self.conn.execute_read(
                    lq.build_attack_followup_query(target_x, target_y))
                result += "\n  Post-combat: " + _format_attack_followup(followup)
            except Exception as e:
                log.debug("Attack followup read failed: %s", e)
        return estimate_str + result

    async def city_attack(self, city_id: int, target_x: int, target_y: int) -> str:
        lua = lq.build_city_attack(city_id, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        if result.startswith("CITY_RANGE_ATTACK"):
            try:
                followup = await self.conn.execute_read(
                    lq.build_attack_followup_query(target_x, target_y))
                result += "\n  Post-combat: " + _format_attack_followup(followup)
            except Exception as e:
                log.debug("City attack followup failed: %s", e)
        return result

    async def resolve_city_capture(self, action: str) -> str:
        lua = lq.build_resolve_city_capture(action)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def found_city(self, unit_index: int) -> str:
        lua = lq.build_found_city(unit_index)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        # On settle failure, run the settle advisor to suggest alternatives
        if result.startswith("Error: CANNOT_FOUND") or result.startswith("Error: FOUND_FAILED"):
            try:
                advisor_result = await self.get_settle_advisor(unit_index)
                result += "\n\n" + advisor_result
            except Exception as e:
                log.debug("Settle advisor failed: %s", e)
        return result

    async def get_settle_advisor(self, unit_index: int) -> str:
        lua = lq.build_settle_advisor_query(unit_index)
        lines = await self.conn.execute_read(lua)
        candidates = lq.parse_settle_advisor_response(lines)
        return self.narrate_settle_candidates(candidates)

    async def get_global_settle_scan(self) -> list[lq.SettleCandidate]:
        lua = lq.build_global_settle_scan()
        lines = await self.conn.execute_read(lua)
        return lq.parse_settle_advisor_response(lines)

    async def get_minimap(self) -> lq.MinimapData:
        lua = lq.build_minimap_query()
        lines = await self.conn.execute_read(lua)
        return lq.parse_minimap_response(lines)

    async def fortify_unit(self, unit_index: int) -> str:
        lua = lq.build_fortify_unit(unit_index)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        if result.startswith("SLEEPING"):
            return "Unit is sleeping (this unit type cannot fortify)"
        return result

    async def skip_unit(self, unit_index: int) -> str:
        lua = lq.build_skip_unit(unit_index)
        lines = await self.conn.execute_read(lua)
        return _action_result(lines)

    async def skip_remaining_units(self) -> str:
        # First try to fortify/heal combat units (InGame context)
        fortify_result = ""
        try:
            lua_fort = lq.build_fortify_remaining_units()
            fort_lines = await self.conn.execute_write(lua_fort)
            fortify_result = _action_result(fort_lines)
        except Exception as e:
            log.debug("Fortify remaining failed: %s", e)
        # Then skip anything still with moves (GameCore context)
        lua = lq.build_skip_remaining_units()
        lines = await self.conn.execute_read(lua)
        skip_result = _action_result(lines)
        if fortify_result and not fortify_result.startswith("Error"):
            return f"{fortify_result}\n{skip_result}"
        return skip_result

    async def automate_explore(self, unit_index: int) -> str:
        lua = lq.build_automate_explore(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def heal_unit(self, unit_index: int) -> str:
        lua = lq.build_heal_unit(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def alert_unit(self, unit_index: int) -> str:
        lua = lq.build_alert_unit(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def sleep_unit(self, unit_index: int) -> str:
        lua = lq.build_sleep_unit(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def delete_unit(self, unit_index: int) -> str:
        lua = lq.build_delete_unit(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def improve_tile(self, unit_index: int, improvement_name: str) -> str:
        lua = lq.build_improve_tile(unit_index, improvement_name)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def set_city_production(
        self, city_id: int, item_type: str, item_name: str,
        target_x: int | None = None, target_y: int | None = None,
    ) -> str:
        lua = lq.build_produce_item(city_id, item_type, item_name, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def purchase_item(self, city_id: int, item_type: str, item_name: str, yield_type: str = "YIELD_GOLD") -> str:
        lua = lq.build_purchase_item(city_id, item_type, item_name, yield_type)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def list_city_production(self, city_id: int) -> list[lq.ProductionOption]:
        lua = lq.build_city_production_query(city_id)
        # Must use InGame context — bq:CanProduce() throws "Not Implemented" in GameCore
        lines = await self.conn.execute_write(lua)
        return lq.parse_city_production_response(lines)

    async def set_research(self, tech_name: str) -> str:
        lua = lq.build_set_research(tech_name)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def set_civic(self, civic_name: str) -> str:
        lua = lq.build_set_civic(civic_name)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        if "OK:PROGRESSING" in result:
            # Verify InGame actually accepted it (desync check)
            verify = await self.conn.execute_read(
                f'local me = Game.GetLocalPlayer(); '
                f'print(Players[me]:GetCulture():GetProgressingCivic()); '
                f'print("{lq.SENTINEL}")'
            )
            gc_civic = int(verify[0]) if verify and verify[0].lstrip("-").isdigit() else -1
            if gc_civic == -1:
                # InGame silently failed — fall back to GameCore
                lua_gc = lq.build_set_civic_gamecore(civic_name)
                gc_lines = await self.conn.execute_read(lua_gc)
                return _action_result(gc_lines)
        return result

    # ------------------------------------------------------------------
    # Diplomacy methods
    # ------------------------------------------------------------------

    async def get_diplomacy_sessions(self) -> list[lq.DiplomacySession]:
        lua = lq.build_diplomacy_session_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_diplomacy_sessions(lines)

    async def diplomacy_respond(self, other_player_id: int, response: str) -> str:
        lua = lq.build_diplomacy_respond(other_player_id, response.upper())
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def send_diplomatic_action(self, other_player_id: int, action: str) -> str:
        lua = lq.build_send_diplo_action(other_player_id, action.upper())
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Trade deal methods (InGame context)
    # ------------------------------------------------------------------

    async def get_deal_options(self, other_player_id: int) -> lq.DealOptions:
        lua = lq.build_deal_options_query(other_player_id)
        lines = await self.conn.execute_write(lua)
        return lq.parse_deal_options_response(lines)

    async def get_pending_deals(self) -> list[lq.PendingDeal]:
        lua = lq.build_pending_deals_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_pending_deals_response(lines)

    async def respond_to_deal(self, other_player_id: int, accept: bool) -> str:
        lua = lq.build_respond_to_deal(other_player_id, accept)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def propose_trade(
        self,
        other_player_id: int,
        offer_items: list[dict],
        request_items: list[dict],
    ) -> str:
        lua = lq.build_propose_trade(other_player_id, offer_items, request_items)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def propose_peace(self, other_player_id: int) -> str:
        lua = lq.build_propose_peace(other_player_id)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def form_alliance(self, other_player_id: int, alliance_type: str) -> str:
        lua = lq.build_form_alliance(other_player_id, alliance_type.upper())
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Policy methods (InGame context)
    # ------------------------------------------------------------------

    async def get_policies(self) -> lq.GovernmentStatus:
        lua = lq.build_policies_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_policies_response(lines)

    async def set_policies(self, assignments: dict[int, str]) -> str:
        lua = lq.build_set_policies(assignments)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Governor methods (InGame context)
    # ------------------------------------------------------------------

    async def get_governors(self) -> lq.GovernorStatus:
        lua = lq.build_governors_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_governors_response(lines)

    async def appoint_governor(self, governor_type: str) -> str:
        lua = lq.build_appoint_governor(governor_type)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def assign_governor(self, governor_type: str, city_id: int) -> str:
        lua = lq.build_assign_governor(governor_type, city_id)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def promote_governor(self, governor_type: str, promotion_type: str) -> str:
        lua = lq.build_promote_governor(governor_type, promotion_type)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Promotion methods
    # ------------------------------------------------------------------

    async def get_unit_promotions(self, unit_id: int) -> lq.UnitPromotionStatus:
        unit_index = unit_id % 65536
        lua = lq.build_unit_promotions_query(unit_index)
        lines = await self.conn.execute_read(lua)
        return lq.parse_unit_promotions_response(lines)

    async def promote_unit(self, unit_id: int, promotion_type: str) -> str:
        unit_index = unit_id % 65536
        lua = lq.build_promote_unit(unit_index, promotion_type)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # City-state / Envoy methods (InGame context)
    # ------------------------------------------------------------------

    async def get_city_states(self) -> lq.EnvoyStatus:
        lua = lq.build_city_states_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_city_states_response(lines)

    async def send_envoy(self, city_state_player_id: int) -> str:
        lua = lq.build_send_envoy(city_state_player_id)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Pantheon methods (InGame context)
    # ------------------------------------------------------------------

    async def get_pantheon_status(self) -> lq.PantheonStatus:
        lua = lq.build_pantheon_status_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_pantheon_status_response(lines)

    async def choose_pantheon(self, belief_type: str) -> str:
        lua = lq.build_choose_pantheon(belief_type)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Unit upgrade methods (InGame context)
    # ------------------------------------------------------------------

    async def check_unit_upgrade(self, unit_id: int) -> str:
        unit_index = unit_id % 65536
        lua = lq.build_unit_upgrade_query(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def upgrade_unit(self, unit_id: int) -> str:
        unit_index = unit_id % 65536
        lua = lq.build_upgrade_unit(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Dedications / Commemorations
    # ------------------------------------------------------------------

    async def get_dedications(self) -> lq.DedicationStatus:
        lua = lq.build_dedications_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_dedications_response(lines)

    async def choose_dedication(self, dedication_index: int) -> str:
        lua = lq.build_choose_dedication(dedication_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # District advisor
    # ------------------------------------------------------------------

    async def get_district_advisor(self, city_id: int, district_type: str) -> list[lq.DistrictPlacement]:
        lua = lq.build_district_advisor_query(city_id, district_type)
        lines = await self.conn.execute_write(lua)
        return lq.parse_district_advisor_response(lines)

    # ------------------------------------------------------------------
    # Tile purchase methods (InGame context)
    # ------------------------------------------------------------------

    async def get_purchasable_tiles(self, city_id: int) -> list[lq.PurchasableTile]:
        lua = lq.build_purchasable_tiles_query(city_id)
        lines = await self.conn.execute_write(lua)
        return lq.parse_purchasable_tiles_response(lines)

    async def purchase_tile(self, city_id: int, x: int, y: int) -> str:
        lua = lq.build_purchase_tile(city_id, x, y)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Government change (InGame context)
    # ------------------------------------------------------------------

    async def change_government(self, government_type: str) -> str:
        lua = lq.build_change_government(government_type)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Great People (InGame context)
    # ------------------------------------------------------------------

    async def get_great_people(self) -> list[lq.GreatPersonInfo]:
        lua = lq.build_great_people_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_great_people_response(lines)

    async def recruit_great_person(self, individual_id: int) -> str:
        lua = lq.build_recruit_great_person(individual_id)
        lines = await self.conn.execute_write(lua)
        return lines[0] if lines else "No response"

    async def patronize_great_person(self, individual_id: int, yield_type: str = "YIELD_GOLD") -> str:
        lua = lq.build_patronize_great_person(individual_id, yield_type)
        lines = await self.conn.execute_write(lua)
        return lines[0] if lines else "No response"

    async def reject_great_person(self, individual_id: int) -> str:
        lua = lq.build_reject_great_person(individual_id)
        lines = await self.conn.execute_write(lua)
        return lines[0] if lines else "No response"

    # ------------------------------------------------------------------
    # Trade route methods (InGame context)
    # ------------------------------------------------------------------

    async def get_trade_routes(self) -> lq.TradeRouteStatus:
        lua = lq.build_trade_routes_query()
        lines = await self.conn.execute_write(lua)  # InGame context (GetOutgoingRoutes is InGame-only)
        return lq.parse_trade_routes_response(lines)

    async def get_trade_destinations(self, unit_index: int) -> list[lq.TradeDestination]:
        lua = lq.build_trade_destinations_query(unit_index)
        lines = await self.conn.execute_write(lua)
        return lq.parse_trade_destinations_response(lines)

    async def make_trade_route(self, unit_index: int, target_x: int, target_y: int) -> str:
        lua = lq.build_make_trade_route(unit_index, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Great Person activation (InGame context)
    # ------------------------------------------------------------------

    async def activate_great_person(self, unit_index: int) -> str:
        lua = lq.build_activate_great_person(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Trader teleport (InGame context)
    # ------------------------------------------------------------------

    async def teleport_to_city(self, unit_index: int, target_x: int, target_y: int) -> str:
        lua = lq.build_teleport_to_city(unit_index, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # World Congress (InGame context)
    # ------------------------------------------------------------------

    async def get_world_congress(self) -> lq.WorldCongressStatus:
        lua = lq.build_world_congress_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_world_congress_response(lines)

    async def vote_world_congress(self, resolution_hash: int, option: int, target_index: int, num_votes: int) -> str:
        lua = lq.build_congress_vote(resolution_hash, option, target_index, num_votes)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def submit_congress(self) -> str:
        lua = lq.build_congress_submit()
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # City yield focus (InGame context)
    # ------------------------------------------------------------------

    async def set_city_focus(self, city_id: int, focus: str) -> str:
        lua = lq.build_set_yield_focus(city_id, focus)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    async def get_notifications(self) -> list[lq.GameNotification]:
        lua = lq.build_notifications_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_notifications_response(lines)

    # ------------------------------------------------------------------
    # Snapshot-diff for turn event detection
    # ------------------------------------------------------------------

    async def _take_snapshot(self, overview: lq.GameOverview | None = None) -> lq.TurnSnapshot:
        """Capture current game state for diffing."""
        if overview is None:
            ov_lines = await self.conn.execute_write(lq.build_overview_query())
            overview = lq.parse_overview_response(ov_lines)

        unit_lines = await self.conn.execute_read(lq.build_units_query())
        units = lq.parse_units_response(unit_lines)

        city_lines = await self.conn.execute_write(lq.build_cities_query())
        cities, _ = lq.parse_cities_response(city_lines)

        return lq.TurnSnapshot(
            turn=overview.turn,
            units={u.unit_id: u for u in units},
            cities={
                c.city_id: lq.CitySnapshot(
                    city_id=c.city_id,
                    name=c.name,
                    population=c.population,
                    currently_building=c.currently_building,
                )
                for c in cities
            },
            current_research=overview.current_research,
            current_civic=overview.current_civic,
        )

    @staticmethod
    def _diff_snapshots(before: lq.TurnSnapshot, after: lq.TurnSnapshot) -> list[lq.TurnEvent]:
        """Compare two snapshots and generate events."""
        events: list[lq.TurnEvent] = []

        # --- Unit events ---
        for uid, ub in before.units.items():
            if uid not in after.units:
                events.append(lq.TurnEvent(
                    priority=1, category="unit",
                    message=f"Your {ub.name} ({ub.unit_type}) was killed! Last seen at ({ub.x},{ub.y}).",
                ))
            else:
                ua = after.units[uid]
                dmg = ub.health - ua.health
                if dmg > 0:
                    events.append(lq.TurnEvent(
                        priority=2, category="unit",
                        message=f"Your {ua.name} ({ua.unit_type}) took {dmg} damage! HP: {ua.health}/{ua.max_health} at ({ua.x},{ua.y}).",
                    ))
                elif dmg < 0:
                    events.append(lq.TurnEvent(
                        priority=3, category="unit",
                        message=f"Your {ua.name} ({ua.unit_type}) healed {-dmg} HP. HP: {ua.health}/{ua.max_health}.",
                    ))

        for uid, ua in after.units.items():
            if uid not in before.units:
                events.append(lq.TurnEvent(
                    priority=3, category="unit",
                    message=f"New unit: {ua.name} ({ua.unit_type}) at ({ua.x},{ua.y}).",
                ))

        # --- City events ---
        for cid, cb in before.cities.items():
            if cid not in after.cities:
                events.append(lq.TurnEvent(
                    priority=1, category="city",
                    message=f"City {cb.name} was lost!",
                ))
            else:
                ca = after.cities[cid]
                if ca.population > cb.population:
                    events.append(lq.TurnEvent(
                        priority=3, category="city",
                        message=f"{ca.name} grew to population {ca.population}.",
                    ))
                if cb.currently_building != "NONE" and ca.currently_building != cb.currently_building:
                    events.append(lq.TurnEvent(
                        priority=2, category="city",
                        message=f"{ca.name} finished building {cb.currently_building}. Now: {ca.currently_building if ca.currently_building != 'NONE' else 'nothing (queue empty)'}.",
                    ))

        for cid, ca in after.cities.items():
            if cid not in before.cities:
                events.append(lq.TurnEvent(
                    priority=2, category="city",
                    message=f"New city founded: {ca.name}!",
                ))

        # --- Research/civic events ---
        if before.current_research != "None" and after.current_research != before.current_research:
            events.append(lq.TurnEvent(
                priority=2, category="research",
                message=f"Research complete: {before.current_research}! Now: {after.current_research}.",
            ))

        if before.current_civic != "None" and after.current_civic != before.current_civic:
            events.append(lq.TurnEvent(
                priority=2, category="civic",
                message=f"Civic complete: {before.current_civic}! Now: {after.current_civic}.",
            ))

        events.sort(key=lambda e: e.priority)
        return events

    @staticmethod
    def _build_turn_report(
        turn_before: int,
        turn_after: int,
        events: list[lq.TurnEvent],
        notifications: list[lq.GameNotification],
    ) -> str:
        """Format turn events and notifications into a scannable report."""
        lines = [f"Turn {turn_before} -> {turn_after}"]

        if events:
            lines.append("")
            lines.append("== Events ==")
            icons = {1: "!!!", 2: ">>", 3: "--"}
            for e in events:
                icon = icons.get(e.priority, "--")
                lines.append(f"  {icon} {e.message}")

        # Use the enriched is_action_required field from the parser
        action_required = [n for n in notifications if n.is_action_required]
        info_notifs = [n for n in notifications if not n.is_action_required]

        if action_required:
            lines.append("")
            lines.append("== Action Required ==")
            for n in action_required:
                hint = f"  -> Use: {n.resolution_hint}" if n.resolution_hint else ""
                lines.append(f"  * {n.message}{hint}")

        if info_notifs:
            lines.append("")
            lines.append("== Notifications ==")
            for n in info_notifs:
                lines.append(f"  - {n.message}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Turn management
    # ------------------------------------------------------------------

    async def end_turn(self) -> str:
        """End the turn with snapshot-diff event detection."""
        import asyncio

        # 1. Diplomacy sessions block turn advancement
        sessions = await self.get_diplomacy_sessions()
        if sessions:
            names = [f"{s.other_civ_name} ({s.other_leader_name})" for s in sessions]
            return f"Cannot end turn: diplomacy encounter pending with {', '.join(names)}. Use diplomacy_respond to handle it."

        # 2. Pre-dismiss any ExclusivePopupManager popups (wonder, disaster, era)
        # that may hold engine locks blocking turn advancement.
        try:
            pre_dismiss = await self.dismiss_popup()
            if "Dismissed" in pre_dismiss:
                log.info("Pre-turn popup dismissed: %s", pre_dismiss)
        except Exception:
            log.debug("Pre-turn dismiss failed", exc_info=True)

        # 3. Check for EndTurnBlocking notifications — turn will silently fail without resolving these
        #    Some blockers (like government change) can be auto-resolved with a retry loop.
        for _ in range(3):
            try:
                blocking_lines = await self.conn.execute_write(lq.build_end_turn_blocking_query())
                blocking_type, blocking_msg = lq.parse_end_turn_blocking(blocking_lines)
                if not blocking_type:
                    break  # no blocker

                # Auto-resolve: governor idle (unassigned governors with no open city slots)
                # UI.CanEndTurn() returns true for these — they're dismissible soft blockers
                if blocking_type == "ENDTURN_BLOCKING_GOVERNOR_IDLE":
                    await self.conn.execute_write(
                        f'local me = Game.GetLocalPlayer(); '
                        f'local list = NotificationManager.GetList(me); '
                        f'for _, nid in ipairs(list) do '
                        f'  local e = NotificationManager.Find(me, nid); '
                        f'  if e and not e:IsDismissed() and e:CanUserDismiss() then '
                        f'    local bt = e:GetEndTurnBlocking(); '
                        f'    if bt and bt == EndTurnBlockingTypes.ENDTURN_BLOCKING_GOVERNOR_IDLE then '
                        f'      NotificationManager.Dismiss(me, nid) '
                        f'    end '
                        f'  end '
                        f'end; '
                        f'print("OK"); print("{lq.SENTINEL}")'
                    )
                    continue  # re-check for more blockers

                # Auto-resolve: government change consideration
                if blocking_type == "ENDTURN_BLOCKING_CONSIDER_GOVERNMENT_CHANGE":
                    await self.conn.execute_write(
                        f'local me = Game.GetLocalPlayer(); '
                        f'Players[me]:GetCulture():SetGovernmentChangeConsidered(true); '
                        f'print("OK"); print("{lq.SENTINEL}")'
                    )
                    continue  # re-check for more blockers

                # Auto-resolve: World Congress review (informational only)
                if blocking_type == "ENDTURN_BLOCKING_WORLD_CONGRESS_LOOK":
                    await self.conn.execute_write(
                        f'local me = Game.GetLocalPlayer(); '
                        f'UI.RequestPlayerOperation(me, PlayerOperations.WORLD_CONGRESS_LOOKED_AT_AVAILABLE, {{}}); '
                        f'local i = ContextPtr:LookUpControl("/InGame/WorldCongressIntro"); '
                        f'if i then i:SetHide(true) end; '
                        f'local p = ContextPtr:LookUpControl("/InGame/WorldCongressPopup"); '
                        f'if p then p:SetHide(true) end; '
                        f'print("OK"); print("{lq.SENTINEL}")'
                    )
                    continue  # re-check for more blockers

                # Auto-resolve: World Congress session with no resolutions
                # (e.g. Special Sessions / Aid Requests we're not party to)
                if blocking_type == "ENDTURN_BLOCKING_WORLD_CONGRESS_SESSION":
                    try:
                        wc_lines = await self.conn.execute_write(
                            f'local wc = Game.GetWorldCongress(); '
                            f'if wc then '
                            f'  local ok, res = pcall(function() return wc:GetResolutions() end); '
                            f'  if ok and res and #res == 0 then '
                            f'    local me = Game.GetLocalPlayer(); '
                            f'    UI.RequestPlayerOperation(me, PlayerOperations.WORLD_CONGRESS_SUBMIT_TURN, {{}}); '
                            f'    local i = ContextPtr:LookUpControl("/InGame/WorldCongressIntro"); '
                            f'    if i then i:SetHide(true) end; '
                            f'    local p = ContextPtr:LookUpControl("/InGame/WorldCongressPopup"); '
                            f'    if p then p:SetHide(true) end; '
                            f'    print("AUTO_RESOLVED"); '
                            f'  else print("HAS_RESOLUTIONS"); end; '
                            f'else print("NO_WC"); end; '
                            f'print("{lq.SENTINEL}")'
                        )
                        if any("AUTO_RESOLVED" in l for l in wc_lines):
                            continue  # re-check for more blockers
                    except Exception:
                        log.debug("WC session auto-resolve failed", exc_info=True)

                # Auto-resolve: disloyal city (loyalty flip) — default to KEEP
                if blocking_type == "ENDTURN_BLOCKING_CONSIDER_DISLOYAL_CITY":
                    try:
                        result = await self.resolve_city_capture("keep")
                        if "Error" not in result:
                            log.info("Auto-kept disloyal city: %s", result)
                            continue  # re-check for more blockers
                    except Exception:
                        log.debug("Disloyal city auto-resolve failed", exc_info=True)

                # Auto-resolve: captured city (conquest) — default to KEEP
                if blocking_type == "ENDTURN_BLOCKING_CONSIDER_RAZE_CITY":
                    try:
                        result = await self.resolve_city_capture("keep")
                        if "Error" not in result:
                            log.info("Auto-kept captured city: %s", result)
                            continue  # re-check for more blockers
                    except Exception:
                        log.debug("Captured city auto-resolve failed", exc_info=True)

                # Auto-resolve: stale envoy token notification (0 tokens available)
                if blocking_type == "ENDTURN_BLOCKING_GIVE_INFLUENCE_TOKEN":
                    try:
                        envoy_lines = await self.conn.execute_write(
                            f'local me = Game.GetLocalPlayer(); '
                            f'local inf = Players[me]:GetInfluence(); '
                            f'local tokens = inf:GetTokensToGive(); '
                            f'if tokens == 0 then '
                            f'  inf:SetGivingTokensConsidered(true); '
                            f'  print("AUTO_RESOLVED"); '
                            f'else print("HAS_TOKENS|" .. tokens); end; '
                            f'print("{lq.SENTINEL}")'
                        )
                        if any("AUTO_RESOLVED" in l for l in envoy_lines):
                            continue  # re-check for more blockers
                    except Exception:
                        log.debug("Envoy auto-resolve failed", exc_info=True)

                # Special check: production blocker may be caused by corrupted queue
                if blocking_type == "ENDTURN_BLOCKING_PRODUCTION":
                    try:
                        corruption_lines = await self.conn.execute_write(
                            f'local me = Game.GetLocalPlayer(); '
                            f'local corrupted = {{}}; '
                            f'for i, c in Players[me]:GetCities():Members() do '
                            f'  local bq = c:GetBuildQueue(); '
                            f'  if bq:GetSize() > 0 and bq:GetCurrentProductionTypeHash() == 0 then '
                            f'    table.insert(corrupted, Locale.Lookup(c:GetName()) .. " (id:" .. c:GetID() .. ")") '
                            f'  end '
                            f'end; '
                            f'if #corrupted > 0 then '
                            f'  print("CORRUPTED|" .. table.concat(corrupted, ",")) '
                            f'else print("CLEAN") end; '
                            f'print("{lq.SENTINEL}")'
                        )
                        is_corrupted = any(cl.startswith("CORRUPTED|") for cl in corruption_lines)
                        if is_corrupted:
                            city_names = next(cl.split("|", 1)[1] for cl in corruption_lines if cl.startswith("CORRUPTED|"))
                            # Attempt to dismiss the blocking production notification
                            dismiss_lines = await self.conn.execute_write(
                                f'local me = Game.GetLocalPlayer(); '
                                f'local dismissed = 0; '
                                f'local list = NotificationManager.GetList(me); '
                                f'if list then '
                                f'  for _, nid in ipairs(list) do '
                                f'    local e = NotificationManager.Find(me, nid); '
                                f'    if e and not e:IsDismissed() then '
                                f'      local bt = e:GetEndTurnBlocking(); '
                                f'      if bt and bt == EndTurnBlockingTypes.ENDTURN_BLOCKING_PRODUCTION then '
                                f'        NotificationManager.Dismiss(me, nid); dismissed = dismissed + 1 '
                                f'      end '
                                f'    end '
                                f'  end '
                                f'end; '
                                f'print("DISMISSED|" .. dismissed); '
                                f'print("{lq.SENTINEL}")'
                            )
                            if any("DISMISSED|" in l and not l.endswith("|0") for l in dismiss_lines):
                                log.info("Auto-dismissed corrupted production for: %s", city_names)
                                continue  # re-check for more blockers
                            return (
                                f"WARNING: Production queue corruption in: {city_names}\n"
                                f"Ghost entry (hash=0) from pillaged district. "
                                f"Try set_city_production for each affected city, or use execute_lua to dismiss notifications."
                            )
                    except Exception:
                        log.debug("Corruption check failed", exc_info=True)

                hint = lq.BLOCKING_TOOL_MAP.get(blocking_type, "Resolve the blocking notification")
                display_type = blocking_type.replace("ENDTURN_BLOCKING_", "").replace("_", " ").title()
                msg = f"Cannot end turn: {display_type} required."
                if blocking_msg:
                    msg += f" ({blocking_msg})"
                msg += f"\n-> {hint}"
                return msg
            except Exception:
                log.debug("Blocking check failed, proceeding anyway", exc_info=True)
                break

        # Take pre-turn snapshot
        try:
            snap_before = await self._take_snapshot()
        except Exception:
            log.debug("Pre-turn snapshot failed", exc_info=True)
            snap_before = self._last_snapshot

        turn_before = snap_before.turn if snap_before else await self._get_turn_number()

        # Request end turn
        lua = lq.build_end_turn()
        await self.conn.execute_write(lua)

        # Poll for turn advancement — longer initial delay, then faster checks
        turn_after = None
        advanced = False
        delays = [1.0, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]  # 4.5s total
        for delay in delays:
            await asyncio.sleep(delay)
            turn_after = await self._get_turn_number()
            if turn_after is not None and turn_before is not None and turn_after > turn_before:
                advanced = True
                break

        if not advanced:
            # Turn didn't advance — popups (disasters, wonders, era changes) may
            # hold engine locks blocking progression.  Let each popup display
            # briefly for spectators before dismissing.
            for attempt in range(5):
                await asyncio.sleep(1.5)  # let popup render for spectator
                dismissed = await self.dismiss_popup()
                if "Dismissed" in dismissed:
                    log.info("Mid-turn popup dismissed (attempt %d): %s", attempt + 1, dismissed)
                    await self.conn.execute_write(lua)
                    await asyncio.sleep(1.5)
                    turn_after = await self._get_turn_number()
                    if turn_after is not None and turn_before is not None and turn_after > turn_before:
                        advanced = True
                        break
                else:
                    break  # no more popups to dismiss

        if not advanced:
            # Final verification — the turn may have slipped through during AI processing
            await asyncio.sleep(2.0)
            turn_after = await self._get_turn_number()
            if turn_after is not None and turn_before is not None and turn_after > turn_before:
                advanced = True

        if not advanced:
            return f"End turn requested (turn is still {turn_after or turn_before}). Check get_pending_diplomacy or dismiss_popup."

        # Take post-turn snapshot and diff
        try:
            snap_after = await self._take_snapshot()
            self._last_snapshot = snap_after
        except Exception:
            log.debug("Post-turn snapshot failed", exc_info=True)
            return f"Turn {turn_before} -> {turn_after}"

        events: list[lq.TurnEvent] = []
        if snap_before:
            events = self._diff_snapshots(snap_before, snap_after)

        # Query active notifications
        notifications: list[lq.GameNotification] = []
        try:
            notif_lines = await self.conn.execute_write(lq.build_notifications_query())
            notifications = lq.parse_notifications_response(notif_lines)
        except Exception:
            log.debug("Notification query failed", exc_info=True)

        # Check for pending trade deals (AI may propose during their turn)
        try:
            deals = await self.get_pending_deals()
            for d in deals:
                events.append(lq.TurnEvent(
                    priority=2, category="diplomacy",
                    message=f"Trade deal offered by {d.other_player_name} ({d.other_leader_name}). Use get_pending_deals to review.",
                ))
        except Exception:
            log.debug("Trade deal check failed", exc_info=True)

        # Threat scan — check for hostile units near cities
        threats: list[lq.ThreatInfo] = []
        try:
            threat_lines = await self.conn.execute_read(lq.build_threat_scan_query())
            threats = lq.parse_threat_scan_response(threat_lines)
            for t in threats:
                rs_str = f" RS:{t.ranged_strength}" if t.ranged_strength > 0 else ""
                events.append(lq.TurnEvent(
                    priority=2, category="unit",
                    message=f"THREAT: {t.unit_type} CS:{t.combat_strength}{rs_str} HP:{t.hp}/{t.max_hp} spotted {t.distance} tiles away at ({t.x},{t.y})",
                ))
            events.sort(key=lambda e: e.priority)
        except Exception:
            log.debug("Threat scan failed", exc_info=True)

        return self._build_turn_report(turn_before, turn_after, events, notifications)

    async def _get_turn_number(self) -> int | None:
        """Read the current game turn number."""
        try:
            lines = await self.conn.execute_read(
                'print(Game.GetCurrentGameTurn()); print("---END---")'
            )
            if lines:
                return int(lines[0])
        except (LuaError, ValueError, IndexError):
            pass
        return None

    async def dismiss_popup(self) -> str:
        """Dismiss any blocking popup or UI overlay in the game.

        Three-phase approach:
        1. Single batched InGame call that checks all known popup/overlay names
           and closes diplomacy screens (fast — one TCP roundtrip).
        2. Only if Phase 1 found nothing: scan individual Lua states for
           ExclusivePopupManager popups (disaster, wonder, era screens) that
           need Close() in their own state to release the engine event lock.
        3. Safety net: always fire ExclusivePopupManager Close LuaEvents to
           ensure BulkHide counters are decremented even if Phase 1 caught
           the popup by name (SetHide) without proper cleanup.
        """
        dismissed = []

        # Phase 1: Single batched InGame call — handles most cases in one roundtrip.
        # Covers: diplomacy screens, generic popups, world congress, boosts, etc.
        popup_names = [
            "InGamePopup", "GenericPopup", "PopupDialog",
            "BoostUnlockedPopup", "GreatWorkShowcase",
            "WorldCongressPopup", "WorldCongressIntro",
            "NaturalDisasterPopup", "NaturalWonderPopup",
            "RockBandMoviePopup",
            "DiplomacyActionView", "DiplomacyDealView",
            "LeaderScene",
        ]
        checks = []
        for name in popup_names:
            checks.append(
                f'do local c = ContextPtr:LookUpControl("/InGame/{name}") '
                f'if c and not c:IsHidden() then '
                f'  pcall(function() UIManager:DequeuePopup(c) end) '
                f'  pcall(function() Input.PopContext() end) '
                f'  c:SetHide(true) '
                f'  print("DISMISSED|{name}") '
                f'end end'
            )
        # Also close diplomacy via LuaEvents (proper cleanup path)
        checks.append(
            'pcall(function() LuaEvents.DiplomacyActionView_ShowIngameUI() end)'
        )
        # Camera reset for cinematic mode
        checks.append(
            'local mode = UI.GetInterfaceMode() '
            'if mode == InterfaceModeTypes.CINEMATIC then '
            '  pcall(function() UI.ClearTemporaryPlotVisibility("NaturalDisaster") end) '
            '  pcall(function() UI.ClearTemporaryPlotVisibility("NaturalWonder") end) '
            '  pcall(function() Events.StopAllCameraAnimations() end) '
            '  pcall(function() UILens.RestoreActiveLens() end) '
            '  UI.SetInterfaceMode(InterfaceModeTypes.SELECTION) '
            '  print("DISMISSED|cinematic_camera") '
            'end'
        )
        try:
            lua = " ".join(checks) + f' print("{lq.SENTINEL}")'
            lines = await self.conn.execute_write(lua)
            for line in lines:
                if line.startswith("DISMISSED|"):
                    dismissed.append(line.split("|", 1)[1])
        except Exception as e:
            log.debug("Phase 1 dismiss failed: %s", e)

        # Phase 2: ALWAYS check ExclusivePopupManager popups — they need Close()
        # in their OWN Lua state to release engine lock.  Phase 1's SetHide()
        # does NOT release this lock, so we must run Phase 2 even if Phase 1
        # found/hid a popup.  These have their own state index (not accessible
        # from InGame).
        if True:
            popup_keywords = ("Popup", "Wonder", "Moment")
            for state_idx, name in self.conn.lua_states.items():
                if not any(kw in name for kw in popup_keywords):
                    continue
                # Loop to drain the ExclusivePopupManager's engine queue —
                # each Close() pops the next event, so we keep closing until
                # the popup stays hidden (max 20 to avoid infinite loops).
                for _drain in range(20):
                    try:
                        lines = await self.conn.execute_in_state(
                            state_idx,
                            'pcall(function() if m_kQueuedPopups then m_kQueuedPopups = {} end end); '
                            'if not ContextPtr:IsHidden() then '
                            '  local ok = pcall(Close); '
                            '  if not ok then pcall(OnClose) end; '
                            '  print("DISMISSED") '
                            'end; '
                            'print("---END---")',
                        )
                        if any("DISMISSED" in l for l in lines):
                            dismissed.append(name)
                        else:
                            break  # popup stayed hidden, queue drained
                    except Exception as e:
                        log.debug("Popup check failed for %s (state %d): %s", name, state_idx, e)
                        break

        # Phase 3: Safety net — ALWAYS fire all ExclusivePopupManager Close
        # LuaEvents.  These decrement InGame.lua's BulkHide counter.  Each
        # popup type calls BulkHide(true, <tag>) when shown, and the matching
        # *_Closed() event calls BulkHide(false, <tag>).  Firing extra Close
        # events is harmless — BulkHide logs "Show past limit" but handles it.
        if True:
            safety_lua = (
                'pcall(function() LuaEvents.NaturalWonderPopup_Closed() end) '
                'pcall(function() LuaEvents.WonderBuiltPopup_Closed() end) '
                'pcall(function() LuaEvents.ProjectBuiltPopup_Closed() end) '
                'pcall(function() LuaEvents.EraCompletePopup_Closed() end) '
                'pcall(function() LuaEvents.NaturalDisasterPopup_Closed() end) '
                'pcall(function() UI.ReleaseCurrentEvent() end) '
                f'print("{lq.SENTINEL}")'
            )
            try:
                await self.conn.execute_write(safety_lua)
            except Exception:
                log.debug("Phase 3 safety net failed", exc_info=True)

        if dismissed:
            return f"Dismissed: {', '.join(dismissed)}"
        return "No popups to dismiss."

    # ------------------------------------------------------------------
    # Save / Load
    # ------------------------------------------------------------------

    async def quicksave(self) -> str:
        """Trigger a quicksave."""
        lines = await self.conn.execute_write(
            f'local gf = {{}}; '
            f'gf.Name = "quicksave"; '
            f'gf.Location = SaveLocations.LOCAL_STORAGE; '
            f'gf.Type = SaveTypes.SINGLE_PLAYER; '
            f'gf.IsAutosave = false; '
            f'gf.IsQuicksave = true; '
            f'Network.SaveGame(gf); '
            f'print("OK|quicksave"); '
            f'print("{lq.SENTINEL}")'
        )
        if any("OK|" in l for l in lines):
            return "Quicksave triggered."
        return "Quicksave may have failed: " + " ".join(lines)

    async def list_saves(self) -> str:
        """Query available saves (normal + autosave + quicksave) and stash in ExposedMembers.

        Returns a list of save names. Use load_save(index) to load one.
        """
        # Step 1: register listener and trigger async query
        await self.conn.execute_write(
            f'if not ExposedMembers then ExposedMembers = {{}} end; '
            f'ExposedMembers.MCPSaveList = nil; '
            f'ExposedMembers.MCPSaveQueryDone = false; '
            f'local function OnResults(fileList, qid) '
            f'  ExposedMembers.MCPSaveList = fileList; '
            f'  ExposedMembers.MCPSaveQueryDone = true; '
            f'  UI.CloseFileListQuery(qid); '
            f'  LuaEvents.FileListQueryResults.Remove(OnResults); '
            f'end; '
            f'LuaEvents.FileListQueryResults.Add(OnResults); '
            f'local opts = SaveLocationOptions.NORMAL + SaveLocationOptions.AUTOSAVE + SaveLocationOptions.QUICKSAVE + SaveLocationOptions.LOAD_METADATA; '
            f'UI.QuerySaveGameList(SaveLocations.LOCAL_STORAGE, SaveTypes.SINGLE_PLAYER, opts); '
            f'print("QUERY_SENT"); '
            f'print("{lq.SENTINEL}")'
        )

        # Step 2: poll for results (async callback fires between frames)
        import asyncio
        for _ in range(20):
            await asyncio.sleep(0.25)
            check_lines = await self.conn.execute_write(
                f'if ExposedMembers.MCPSaveQueryDone then '
                f'  local fl = ExposedMembers.MCPSaveList; '
                f'  if fl and #fl > 0 then '
                f'    print("COUNT|" .. #fl); '
                f'    for i, s in ipairs(fl) do '
                f'      if i <= 20 then print("SAVE|" .. i .. "|" .. tostring(s.Name)) end '
                f'    end '
                f'  else print("EMPTY") end '
                f'else print("PENDING") end; '
                f'print("{lq.SENTINEL}")'
            )
            if any(l.startswith("COUNT|") or l == "EMPTY" for l in check_lines):
                results = [l for l in check_lines if l.startswith("SAVE|")]
                if not results:
                    return "No saves found."
                lines_out = ["Available saves (use load_save with the index number):"]
                for r in results:
                    parts = r.split("|", 2)
                    idx = parts[1]
                    name = parts[2] if len(parts) > 2 else "?"
                    lines_out.append(f"  {idx}. {name}")
                return "\n".join(lines_out)

        return "Save list query timed out after 5 seconds."

    async def load_save(self, save_index: int) -> str:
        """Load a save by index from the most recent list_saves() query.

        The game will reload — the FireTuner connection stays alive but
        all Lua state is wiped. Wait a few seconds after calling this.
        """
        lines = await self.conn.execute_write(
            f'if not ExposedMembers or not ExposedMembers.MCPSaveList then '
            f'  print("ERR:NO_SAVE_LIST"); print("{lq.SENTINEL}"); return '
            f'end; '
            f'local fl = ExposedMembers.MCPSaveList; '
            f'local idx = {save_index}; '
            f'if idx < 1 or idx > #fl then '
            f'  print("ERR:INDEX_OUT_OF_RANGE|" .. #fl); print("{lq.SENTINEL}"); return '
            f'end; '
            f'local save = fl[idx]; '
            f'print("LOADING|" .. tostring(save.Name)); '
            f'print("{lq.SENTINEL}"); '
            f'Network.LeaveGame(); '
            f'Network.LoadGame(save, ServerType.SERVER_TYPE_NONE)'
        )
        for line in lines:
            if line.startswith("ERR:NO_SAVE_LIST"):
                return "Error: No save list cached. Call list_saves() first."
            if line.startswith("ERR:INDEX_OUT_OF_RANGE"):
                count = line.split("|")[1] if "|" in line else "?"
                return f"Error: Index {save_index} out of range (1-{count}). Call list_saves() to see available saves."
            if line.startswith("LOADING|"):
                name = line.split("|", 1)[1]
                return f"Loading save: {name}. Game will reload — wait ~10 seconds then call get_game_overview to verify."
        return "Load command sent. Wait for game to reload."

    async def execute_lua(self, code: str, context: str = "gamecore") -> str:
        """Escape hatch: run arbitrary Lua code."""
        if context == "ingame":
            lines = await self.conn.execute_write(code)
        elif context.isdigit():
            lines = await self.conn.execute_in_state(int(context), code)
        else:
            lines = await self.conn.execute_read(code)
        return "\n".join(lines) if lines else "(no output)"

    # ------------------------------------------------------------------
    # Narration — server-side text formatting for LLM consumption
    # ------------------------------------------------------------------

    @staticmethod
    def narrate_overview(ov: lq.GameOverview) -> str:
        lines = [
            f"Turn {ov.turn} | {ov.civ_name} ({ov.leader_name}) | Score: {ov.score}",
            f"Gold: {ov.gold:.0f} ({ov.gold_per_turn:+.0f}/turn) | Science: {ov.science_yield:.1f} | Culture: {ov.culture_yield:.1f} | Faith: {ov.faith:.0f} | Favor: {ov.diplomatic_favor} ({ov.favor_per_turn:+d}/turn)",
            f"Research: {ov.current_research} | Civic: {ov.current_civic}",
            f"Cities: {ov.num_cities} | Units: {ov.num_units}",
        ]
        if ov.total_land > 0:
            pct = ov.explored_land * 100 // ov.total_land
            lines.append(f"Explored: {pct}% of land ({ov.explored_land}/{ov.total_land} tiles)")
        if ov.rankings:
            all_scores = [(ov.civ_name, ov.score)] + [(r.civ_name, r.score) for r in ov.rankings]
            all_scores.sort(key=lambda x: x[1], reverse=True)
            rank_strs = [f"{name} {score}" for name, score in all_scores]
            lines.append(f"Rankings: {' > '.join(rank_strs)}")
        return "\n".join(lines)

    @staticmethod
    def narrate_units(units: list[lq.UnitInfo], threats: list[lq.ThreatInfo] | None = None) -> str:
        if not units:
            return "No units."
        lines = [f"{len(units)} units:"]
        for u in units:
            strength = ""
            if u.combat_strength > 0:
                strength = f" CS:{u.combat_strength}"
                if u.ranged_strength > 0:
                    strength += f" RS:{u.ranged_strength}"
            status = ""
            if u.health < u.max_health:
                status = f" [HP: {u.health}/{u.max_health}]"
            if u.moves_remaining == 0:
                status += " (no moves)"
            charges = f" charges:{u.build_charges}" if u.build_charges > 0 else ""
            promo_flag = " **NEEDS PROMOTION**" if u.needs_promotion else ""
            upgrade_flag = ""
            if u.can_upgrade:
                upgrade_flag = f" **CAN UPGRADE to {u.upgrade_target} ({u.upgrade_cost}g)**"
            lines.append(
                f"  {u.name} ({u.unit_type}) at ({u.x},{u.y}) —{strength} "
                f"moves {u.moves_remaining}/{u.max_moves}{charges}{status}{promo_flag}{upgrade_flag} "
                f"[id:{u.unit_id}, idx:{u.unit_index}]"
            )
            if u.targets:
                for t in u.targets:
                    lines.append(f"    >> CAN ATTACK: {t}")
            if u.valid_improvements:
                lines.append(f"    >> Can build: {', '.join(u.valid_improvements)}")
        if threats:
            lines.append("")
            lines.append(f"Nearby barbarian threats ({len(threats)}):")
            for t in threats:
                rs_str = f" RS:{t.ranged_strength}" if t.ranged_strength > 0 else ""
                lines.append(
                    f"  {t.unit_type} at ({t.x},{t.y}) — CS:{t.combat_strength}{rs_str} "
                    f"HP:{t.hp}/{t.max_hp} ({t.distance} tiles away)"
                )
        return "\n".join(lines)

    @staticmethod
    def narrate_cities(cities: list[lq.CityInfo], distances: list[str] | None = None) -> str:
        if not cities:
            return "No cities."
        lines = [f"{len(cities)} cities:"]
        for c in cities:
            building = c.currently_building if c.currently_building not in ("NONE", "nothing") else "nothing"
            prod_str = f"Building: {building}"
            if building != "nothing" and c.production_turns_left > 0:
                prod_str += f" ({c.production_turns_left} turns)"
            defense = ""
            if c.wall_max_hp > 0:
                defense = (
                    f" | Walls {c.wall_hp}/{c.wall_max_hp}"
                    f" Garrison {c.garrison_hp}/{c.garrison_max_hp}"
                    f" Def:{c.defense_strength}"
                )
            elif c.defense_strength > 0:
                defense = f" | Def:{c.defense_strength}"
            lines.append(
                f"  {c.name} (pop {c.population}) at ({c.x},{c.y}) — "
                f"Food {c.food:.0f} Prod {c.production:.0f} Gold {c.gold:.0f} "
                f"Sci {c.science:.0f} Cul {c.culture:.0f} | "
                f"Housing {c.housing:.0f} Amenities {c.amenities} | "
                f"Growth in {c.turns_to_grow} turns | {prod_str}{defense} "
                f"[id:{c.city_id}]"
            )
            if c.currently_building == "CORRUPTED_QUEUE":
                lines.append(f"    !! CORRUPTED QUEUE: ghost entry (hash=0). Load earlier autosave to fix.")
            for t in c.attack_targets:
                lines.append(f"    >> CAN ATTACK: {t}")
            if c.districts:
                dist_strs = []
                for d in c.districts:
                    dtype, coords = d.split("@")
                    short = dtype.replace("DISTRICT_", "")
                    dist_strs.append(f"{short}({coords})")
                lines.append(f"    Districts: {' '.join(dist_strs)}")
            if c.pillaged_districts:
                pill_names = [d.replace("DISTRICT_", "") for d in c.pillaged_districts]
                lines.append(f"    !! PILLAGED: {', '.join(pill_names)}")
        if distances:
            lines.append("")
            lines.append("City Distances:")
            for d in distances:
                lines.append(f"  {d}")
        return "\n".join(lines)

    @staticmethod
    def narrate_combat_estimate(est: lq.CombatEstimate) -> str:
        atk_type = "Ranged" if est.is_ranged else "Melee"
        mods_str = ", ".join(est.modifiers) if est.modifiers else "none"
        lines = [
            f"Combat Estimate ({atk_type}):",
            f"  {est.attacker_type} (CS:{est.attacker_cs}, HP:{est.attacker_hp}) vs "
            f"{est.defender_type} (CS:{est.defender_cs}, HP:{est.defender_hp})",
            f"  Modifiers: {mods_str}",
            f"  Est damage to defender: ~{est.est_damage_to_defender}",
        ]
        if not est.is_ranged:
            lines.append(f"  Est damage to attacker: ~{est.est_damage_to_attacker}")
        if est.est_damage_to_defender >= est.defender_hp:
            lines.append("  -> LIKELY KILL")
        elif not est.is_ranged and est.est_damage_to_attacker >= est.attacker_hp:
            lines.append("  -> WARNING: attacker likely dies!")
        return "\n".join(lines)

    @staticmethod
    def narrate_city_production(options: list[lq.ProductionOption]) -> str:
        if not options:
            return "No production options available."
        units = [o for o in options if o.category == "UNIT"]
        buildings = [o for o in options if o.category == "BUILDING"]
        districts = [o for o in options if o.category == "DISTRICT"]
        def _fmt(o: lq.ProductionOption) -> str:
            t = f", {o.turns} turns" if o.turns > 0 else ""
            buy = f", buy: {o.gold_cost}g" if o.gold_cost > 0 else ""
            return f"  {o.item_name} (cost {o.cost}{t}{buy})"

        lines = []
        if units:
            lines.append("Units:")
            for o in units:
                lines.append(_fmt(o))
        if buildings:
            lines.append("Buildings:")
            for o in buildings:
                lines.append(_fmt(o))
        if districts:
            lines.append("Districts:")
            for o in districts:
                lines.append(_fmt(o))
        return "\n".join(lines)

    @staticmethod
    def narrate_map(tiles: list[lq.TileInfo]) -> str:
        if not tiles:
            return "No tiles."
        lines = [f"{len(tiles)} tiles:"]
        for t in tiles:
            parts = [t.terrain.replace("TERRAIN_", "")]
            if t.is_hills:
                parts.append("Hills")
            if t.feature:
                parts.append(t.feature.replace("FEATURE_", ""))
            if t.resource:
                res_label = t.resource.replace('RESOURCE_', '')
                if t.resource_class == "strategic":
                    res_label += "*"
                elif t.resource_class == "luxury":
                    res_label += "+"
                parts.append(f"[{res_label}]")
            if t.is_river:
                parts.append("River")
            if t.is_coastal:
                parts.append("Coast")
            if t.is_fresh_water and not t.is_river:
                # Fresh water from lake/oasis (river already implies fresh water)
                parts.append("FreshWater")
            if t.improvement:
                imp_label = t.improvement.replace('IMPROVEMENT_', '')
                if t.is_pillaged:
                    imp_label += " PILLAGED"
                parts.append(f"({imp_label})")
            if t.yields:
                f, p, g = t.yields[0], t.yields[1], t.yields[2]
                yield_str = f"F:{f} P:{p}"
                if g > 0:
                    yield_str += f" G:{g}"
                # Include science/culture/faith only if non-zero
                for label, val in [("S", t.yields[3]), ("C", t.yields[4]), ("Fa", t.yields[5])]:
                    if val > 0:
                        yield_str += f" {label}:{val}"
                parts.append(f"{{{yield_str}}}")
            owner = f" (owned by player {t.owner_id})" if t.owner_id >= 0 else ""
            vis_tag = ""
            if t.visibility == "revealed":
                vis_tag = " [fog]"
            unit_str = ""
            if t.units:
                unit_str = f" **[{', '.join(t.units)}]**"
            lines.append(f"  ({t.x},{t.y}): {' '.join(parts)}{owner}{vis_tag}{unit_str}")
        return "\n".join(lines)

    @staticmethod
    def narrate_strategic_map(data: lq.StrategicMapData) -> str:
        dir_names = ["N", "NE", "SE", "S", "SW", "NW"]
        lines = ["=== STRATEGIC MAP ===", ""]

        # Fog boundaries
        lines.append("FOG BOUNDARIES (distance to unexplored, -1 = fully explored):")
        for fb in data.fog_boundaries:
            dir_strs = []
            explore_dirs = []
            for i, d in enumerate(fb.fog_distances):
                label = dir_names[i] if i < len(dir_names) else f"D{i}"
                if d == -1:
                    dir_strs.append(f"{label}:clear")
                else:
                    dir_strs.append(f"{label}:{d}")
                    if d <= 5:
                        explore_dirs.append(label)
            suffix = ""
            if explore_dirs:
                suffix = f" <- EXPLORE {'/'.join(explore_dirs)}!"
            lines.append(f"  {fb.city_name} ({fb.city_x},{fb.city_y}): {' '.join(dir_strs)}{suffix}")

        # Unclaimed resources
        luxuries = [r for r in data.unclaimed_resources if "LUXURY" in r.resource_class]
        strategics = [r for r in data.unclaimed_resources if "STRATEGIC" in r.resource_class]
        if luxuries or strategics:
            lines.append("")
            lines.append("UNCLAIMED RESOURCES (revealed, unowned):")
            for r in luxuries:
                name = r.resource_type.replace("RESOURCE_", "")
                lines.append(f"  {name}+ at ({r.x},{r.y}) — luxury")
            for r in strategics:
                name = r.resource_type.replace("RESOURCE_", "")
                lines.append(f"  {name}* at ({r.x},{r.y}) — strategic")
        elif not data.fog_boundaries:
            lines.append("\nNo data available.")

        return "\n".join(lines)

    @staticmethod
    def narrate_minimap(data: lq.MinimapData) -> str:
        if not data.rows:
            return "No minimap data available."
        lines = [
            "=== MINIMAP ===",
            "Legend: O=our city, X=enemy city, !=barbarian",
            "  UPPER=our territory, lower=enemy territory",
            "  ~=water, ^=mountain, #=hills, T=forest/jungle, .=flat",
            "  +=luxury resource, *=strategic resource, ' '=unexplored",
            "",
        ]
        # Render rows with hex offset (even rows shift right)
        for y in sorted(data.rows.keys()):
            row_str = data.rows[y]
            # Hex grid: offset even rows by half-cell
            prefix = " " if y % 2 == 1 else ""
            # Add spacing between characters for readability
            spaced = " ".join(row_str)
            lines.append(f"{y:3d}|{prefix}{spaced}")
        return "\n".join(lines)

    @staticmethod
    def narrate_settle_candidates(candidates: list[lq.SettleCandidate]) -> str:
        if not candidates:
            return "No valid settle locations found within 5 tiles."
        lines = [f"Top {len(candidates)} settle locations:"]
        _WATER = {"fresh": "fresh water", "coast": "coast", "none": "no water"}
        for i, c in enumerate(candidates, 1):
            water = _WATER.get(c.water_type, c.water_type)
            header = f"  #{i} ({c.x},{c.y}): Score {c.score:.0f} — F:{c.total_food} P:{c.total_prod} — {water}, defense:{c.defense_score}"
            lines.append(header)
            if c.resources:
                # Format: [S] IRON, [L] DIAMONDS, [B] WHEAT
                res_parts = []
                for r in c.resources:
                    if ":" in r:
                        prefix, name = r.split(":", 1)
                        res_parts.append(f"[{prefix}] {name}")
                    else:
                        res_parts.append(r)
                lines.append(f"     {', '.join(res_parts)}")
        return "\n".join(lines)

    @staticmethod
    def narrate_empire_resources(
        stockpiles: list[lq.ResourceStockpile],
        owned: list[lq.OwnedResource],
        nearby: list[lq.NearbyResource],
        luxuries: dict[str, int],
    ) -> str:
        if not stockpiles and not owned and not nearby and not luxuries:
            return "No resources found in or near your empire."
        _CLASS_PREFIX = {"strategic": "S", "luxury": "L", "bonus": "B"}
        lines = ["Empire Resources:"]
        # Strategic stockpiles
        visible_strats = [s for s in stockpiles]
        if visible_strats:
            lines.append("\nStrategic Stockpiles:")
            for s in visible_strats:
                net = s.per_turn - s.demand
                net_str = f"+{net}" if net >= 0 else str(net)
                parts = [f"  {s.name}: {s.amount}/{s.cap} ({net_str}/turn)"]
                details = []
                if s.per_turn > 0:
                    details.append(f"income {s.per_turn}")
                if s.imported > 0:
                    details.append(f"import {s.imported}")
                if s.demand > 0:
                    details.append(f"demand {s.demand}")
                if details:
                    parts.append(f" [{', '.join(details)}]")
                lines.append("".join(parts))
        # Luxury summary
        if luxuries:
            lines.append("\nLuxury Resources:")
            for name, count in sorted(luxuries.items()):
                extra = f" ({count - 1} tradeable)" if count > 1 else ""
                lines.append(f"  {name}: {count}{extra}")
        # Owned tile resources grouped by class
        for cls, label in [("strategic", "Strategic Tiles"), ("luxury", "Luxury Tiles"), ("bonus", "Bonus Tiles")]:
            items = [r for r in owned if r.resource_class == cls]
            if not items:
                continue
            lines.append(f"\n{label}:")
            for r in items:
                if r.improved:
                    lines.append(f"  {r.name} — improved at ({r.x},{r.y})")
                elif cls in ("luxury", "strategic"):
                    lines.append(f"  !! {r.name} — UNIMPROVED at ({r.x},{r.y}) — needs builder!")
                else:
                    lines.append(f"  {r.name} — UNIMPROVED at ({r.x},{r.y})")
        # Nearby unclaimed
        if nearby:
            lines.append("\nNearby Unclaimed:")
            for r in nearby:
                prefix = _CLASS_PREFIX.get(r.resource_class, "?")
                lines.append(f"  [{prefix}] {r.name} at ({r.x},{r.y}) — {r.distance} tiles from {r.nearest_city}")
        return "\n".join(lines)

    @staticmethod
    def narrate_diplomacy(civs: list[lq.CivInfo]) -> str:
        if not civs:
            return "No known civilizations."
        lines = [f"{len(civs)} civilizations:"]
        for c in civs:
            if not c.has_met:
                lines.append(f"  {c.civ_name} ({c.leader_name}) — not met")
                continue
            # Header with state and score
            war_str = " **AT WAR**" if c.is_at_war else ""
            if c.alliance_type:
                level_str = f" Lv{c.alliance_level}" if c.alliance_level > 0 else ""
                alliance_str = f" ({c.alliance_type} alliance{level_str})"
            else:
                alliance_str = ""
            lines.append(f"  {c.civ_name} ({c.leader_name}) — {c.diplomatic_state} ({c.relationship_score:+d}){war_str}{alliance_str} [player {c.player_id}]")
            # Access: delegations/embassies
            access = []
            if c.has_delegation:
                access.append("we have delegation")
            if c.they_have_delegation:
                access.append("they have delegation")
            if c.has_embassy:
                access.append("we have embassy")
            if c.they_have_embassy:
                access.append("they have embassy")
            if c.grievances > 0:
                access.append(f"grievances: {c.grievances}")
            if access:
                lines.append(f"    Access: {', '.join(access)}")
            # Relationship modifiers
            if c.modifiers:
                for m in c.modifiers:
                    lines.append(f"    {m.score:+d} {m.text}")
            # Defensive pacts
            if c.defensive_pacts:
                pact_names = []
                for pid in c.defensive_pacts:
                    # Find the civ name for this player ID
                    pact_civ = next((ci for ci in civs if ci.player_id == pid), None)
                    if pact_civ:
                        pact_names.append(f"{pact_civ.civ_name} (player {pid})")
                    else:
                        pact_names.append(f"player {pid}")
                lines.append(f"    !! DEFENSIVE PACTS with: {', '.join(pact_names)}")
            # Available actions
            if c.available_actions:
                actions_str = ", ".join(a.replace("_", " ").title() for a in c.available_actions)
                lines.append(f"    Can: {actions_str}")
        return "\n".join(lines)

    @staticmethod
    def narrate_diplomacy_sessions(sessions: list[lq.DiplomacySession]) -> str:
        if not sessions:
            return "No pending diplomacy sessions."
        lines = [f"{len(sessions)} pending diplomacy session(s):"]
        for s in sessions:
            lines.append(
                f"  {s.other_civ_name} ({s.other_leader_name}) — "
                f"session {s.session_id}, player {s.other_player_id}"
            )
            if s.dialogue_text:
                lines.append(f'  Says: "{s.dialogue_text}"')
            if s.reason_text:
                lines.append(f"  Reason: {s.reason_text}")
            lines.append("  Respond with: POSITIVE (friendly) or NEGATIVE (dismissive)")
        return "\n".join(lines)

    @staticmethod
    def narrate_tech_civics(tc: lq.TechCivicStatus) -> str:
        lines = []
        completed = ""
        if tc.completed_tech_count > 0 or tc.completed_civic_count > 0:
            completed = f" | Completed: {tc.completed_tech_count} techs, {tc.completed_civic_count} civics"
        if tc.current_research != "None":
            lines.append(f"Researching: {tc.current_research} ({tc.current_research_turns} turns){completed}")
        else:
            lines.append(f"No technology being researched!{completed}")
        if tc.current_civic != "None":
            lines.append(f"Civic: {tc.current_civic} ({tc.current_civic_turns} turns)")
        else:
            lines.append("No civic being progressed!")
        if tc.available_techs:
            lines.append("\nAvailable techs:")
            for t in tc.available_techs:
                lines.append(f"  {t}")
        if tc.available_civics:
            lines.append("\nAvailable civics:")
            for c in tc.available_civics:
                lines.append(f"  {c}")
        return "\n".join(lines)

    @staticmethod
    def narrate_pending_deals(deals: list[lq.PendingDeal]) -> str:
        if not deals:
            return "No pending trade deals."
        lines = [f"{len(deals)} pending trade deal(s):"]
        for d in deals:
            lines.append(f"\n  From: {d.other_player_name} ({d.other_leader_name}) [player {d.other_player_id}]")
            if d.items_from_them:
                lines.append("  They offer:")
                for item in d.items_from_them:
                    dur = f" for {item.duration} turns" if item.duration > 0 else ""
                    amt = f" x{item.amount}" if item.amount > 1 or item.item_type == "GOLD" else ""
                    lines.append(f"    + {item.name}{amt}{dur}")
            if d.items_from_us:
                lines.append("  They want:")
                for item in d.items_from_us:
                    dur = f" for {item.duration} turns" if item.duration > 0 else ""
                    amt = f" x{item.amount}" if item.amount > 1 or item.item_type == "GOLD" else ""
                    lines.append(f"    - {item.name}{amt}{dur}")
            lines.append(f"  -> respond_to_deal(other_player_id={d.other_player_id}, accept=True/False)")
        return "\n".join(lines)

    @staticmethod
    def narrate_deal_options(opts: lq.DealOptions) -> str:
        lines = [f"Trade options with {opts.other_civ_name} (player {opts.other_player_id}):"]
        lines.append(f"\nEconomy:")
        lines.append(f"  Our gold: {opts.our_gold} ({opts.our_gpt:+d}/turn) | Favor: {opts.our_favor}")
        lines.append(f"  Their gold: {opts.their_gold} ({opts.their_gpt:+d}/turn) | Favor: {opts.their_favor}")
        if opts.our_luxuries or opts.our_strategics:
            lines.append(f"\nOur tradeable resources:")
            if opts.our_luxuries:
                lines.append(f"  Luxuries: {', '.join(opts.our_luxuries)}")
            if opts.our_strategics:
                lines.append(f"  Strategics: {', '.join(opts.our_strategics)}")
        if opts.their_luxuries or opts.their_strategics:
            lines.append(f"\nTheir tradeable resources:")
            if opts.their_luxuries:
                lines.append(f"  Luxuries: {', '.join(opts.their_luxuries)}")
            if opts.their_strategics:
                lines.append(f"  Strategics: {', '.join(opts.their_strategics)}")
        lines.append(f"\nAgreements:")
        ob_status = "active" if opts.has_open_borders else "not active (available)"
        lines.append(f"  Open borders: {ob_status}")
        if opts.current_alliance:
            lines.append(f"  Alliance: {opts.current_alliance} (active)")
        elif opts.alliance_eligible:
            lines.append(f"  Alliance: eligible (MILITARY, RESEARCH, CULTURAL, ECONOMIC, RELIGIOUS)")
        else:
            lines.append(f"  Alliance: not eligible (requires declared friendship + Diplomatic Service civic)")
        return "\n".join(lines)

    @staticmethod
    def narrate_policies(gov: lq.GovernmentStatus) -> str:
        lines = [f"Government: {gov.government_name} ({gov.government_type})"]

        if gov.slots:
            lines.append(f"\n{len(gov.slots)} policy slots:")
            for s in gov.slots:
                slot_label = s.slot_type.replace("SLOT_", "").title()
                if s.current_policy:
                    lines.append(f"  Slot {s.slot_index} ({slot_label}): {s.current_policy_name} ({s.current_policy})")
                else:
                    lines.append(f"  Slot {s.slot_index} ({slot_label}): EMPTY")

        if gov.available_policies:
            by_type: dict[str, list[lq.PolicyInfo]] = {}
            for p in gov.available_policies:
                by_type.setdefault(p.slot_type, []).append(p)
            lines.append("\nAvailable policies:")
            for slot_type in ["SLOT_MILITARY", "SLOT_ECONOMIC", "SLOT_DIPLOMATIC", "SLOT_WILDCARD"]:
                policies = by_type.get(slot_type, [])
                if policies:
                    label = slot_type.replace("SLOT_", "").title()
                    lines.append(f"  {label}:")
                    for p in policies:
                        lines.append(f"    {p.name} ({p.policy_type}): {p.description}")

        lines.append("\nUse set_policies with slot assignments, e.g. '0=POLICY_AGOGE,1=POLICY_URBAN_PLANNING'")
        lines.append("Wildcard slots can accept any policy type.")
        return "\n".join(lines)

    @staticmethod
    def narrate_governors(gov: lq.GovernorStatus) -> str:
        lines = [f"Governor Points: {gov.points_available} available, {gov.points_spent} spent"]
        if gov.can_appoint:
            lines.append("** Can appoint a new governor! **")

        if gov.appointed:
            lines.append(f"\nAppointed ({len(gov.appointed)}):")
            for g in gov.appointed:
                if g.assigned_city_id >= 0:
                    est = " (established)" if g.is_established else f" ({g.turns_to_establish} turns to establish)"
                    lines.append(f"  {g.name} ({g.governor_type}) — {g.assigned_city_name}{est}")
                else:
                    lines.append(f"  {g.name} ({g.governor_type}) — Unassigned")
                if g.available_promotions:
                    lines.append("    Available promotions:")
                    for p in g.available_promotions:
                        lines.append(f"      {p.name} ({p.promotion_type}): {p.description}")

        if gov.available_to_appoint:
            lines.append(f"\nAvailable to appoint ({len(gov.available_to_appoint)}):")
            for g in gov.available_to_appoint:
                lines.append(f"  {g.name} — {g.title} ({g.governor_type})")

        lines.append("\nUse appoint_governor/assign_governor/promote_governor(governor_type, promotion_type).")
        return "\n".join(lines)

    @staticmethod
    def narrate_unit_promotions(status: lq.UnitPromotionStatus) -> str:
        if not status.promotions:
            return f"No promotions available for {status.unit_type} (id:{status.unit_id})."
        lines = [f"Promotions for {status.unit_type} (id:{status.unit_id}):"]
        for p in status.promotions:
            lines.append(f"  {p.name} ({p.promotion_type}): {p.description}")
        lines.append("\nUse promote_unit(unit_id, promotion_type) to apply.")
        return "\n".join(lines)

    @staticmethod
    def narrate_city_states(status: lq.EnvoyStatus) -> str:
        lines = [f"Envoy tokens available: {status.tokens_available}"]
        if not status.city_states:
            lines.append("No known city-states.")
        else:
            lines.append(f"\n{len(status.city_states)} known city-states:")
            for cs in status.city_states:
                suz = f" (Suzerain: {cs.suzerain_name})" if cs.suzerain_id >= 0 else ""
                can = " [can send]" if cs.can_send_envoy and status.tokens_available > 0 else ""
                lines.append(f"  {cs.name} ({cs.city_state_type}) — {cs.envoys_sent} envoys{suz}{can} [player {cs.player_id}]")
        if status.tokens_available > 0:
            lines.append("\nUse send_envoy(city_state_player_id) to send an envoy.")
        return "\n".join(lines)

    @staticmethod
    def narrate_pantheon_status(status: lq.PantheonStatus) -> str:
        lines = []
        if status.has_pantheon:
            lines.append(f"Pantheon: {status.current_belief_name} ({status.current_belief})")
            lines.append(f"Faith: {status.faith_balance:.0f}")
        else:
            lines.append(f"No pantheon selected. Faith: {status.faith_balance:.0f}")
            if status.available_beliefs:
                lines.append(f"\n{len(status.available_beliefs)} available beliefs:")
                for b in status.available_beliefs:
                    lines.append(f"  {b.name} ({b.belief_type}): {b.description}")
                lines.append("\nUse choose_pantheon(belief_type) to found a pantheon.")
            else:
                lines.append("No beliefs available (all taken or insufficient faith).")
        return "\n".join(lines)

    @staticmethod
    def narrate_dedications(status: lq.DedicationStatus) -> str:
        era_names = {0: "Ancient", 1: "Classical", 2: "Medieval", 3: "Renaissance",
                     4: "Industrial", 5: "Modern", 6: "Atomic", 7: "Information"}
        era_name = era_names.get(status.era, f"Era {status.era}")
        lines = [
            f"{status.age_type} Age — {era_name} Era",
            f"Era Score: {status.era_score} (Dark: {status.dark_threshold}, Golden: {status.golden_threshold})",
        ]
        if status.active:
            lines.append(f"\nActive dedications: {', '.join(status.active)}")
        if status.selections_allowed > 0:
            lines.append(f"\n{status.selections_allowed} dedication(s) to choose:")
            for c in status.choices:
                desc = c.golden_desc if status.age_type in ("Golden", "Heroic") else (
                    c.dark_desc if status.age_type == "Dark" else c.normal_desc)
                lines.append(f"  [{c.index}] {c.name}: {desc}")
            lines.append("\nUse choose_dedication(dedication_index=N) to select.")
        elif not status.active:
            lines.append("\nNo dedications available or required.")
        return "\n".join(lines)

    @staticmethod
    def narrate_district_advisor(placements: list[lq.DistrictPlacement], district_type: str) -> str:
        if not placements:
            return f"No valid placement tiles for {district_type}."
        lines = [f"{district_type} placement options ({len(placements)} tiles):"]
        for i, p in enumerate(placements, 1):
            adj_parts = [f"{v} {k}" for k, v in p.adjacency.items()]
            adj_str = ", ".join(adj_parts) if adj_parts else "no adjacency"
            lines.append(f"  #{i} ({p.x},{p.y}) Adj: +{p.total_adjacency} ({adj_str}) — {p.terrain_desc}")
        return "\n".join(lines)

    @staticmethod
    def narrate_purchasable_tiles(tiles: list[lq.PurchasableTile]) -> str:
        if not tiles:
            return "No purchasable tiles."
        lines = [f"{len(tiles)} purchasable tiles:"]
        for t in tiles:
            res_str = ""
            if t.resource:
                cls_tag = {"strategic": "*", "luxury": "+", "bonus": ""}.get(t.resource_class or "", "")
                res_str = f" [{t.resource}{cls_tag}]"
            lines.append(f"  ({t.x},{t.y}): {t.cost}g — {t.terrain}{res_str}")
        return "\n".join(lines)

    @staticmethod
    def narrate_great_people(gp: list[lq.GreatPersonInfo]) -> str:
        if not gp:
            return "No Great People in timeline."
        lines = [f"{len(gp)} Great People:"]
        for g in gp:
            progress = f"{g.player_points}/{g.cost}"
            recruit_tag = " [CAN RECRUIT]" if g.can_recruit else ""
            entry = f"  {g.class_name}: {g.individual_name} ({g.era_name}) — {g.claimant} — your points: {progress}{recruit_tag}"
            if g.ability:
                entry += f"\n    Ability: {g.ability}"
            # Show patronize costs (skip INT_MAX values which mean unavailable)
            costs = []
            if 0 < g.gold_cost < 2_000_000_000:
                costs.append(f"{g.gold_cost}g")
            if 0 < g.faith_cost < 2_000_000_000:
                costs.append(f"{g.faith_cost}f")
            if costs:
                entry += f"\n    Patronize: {' / '.join(costs)}"
            lines.append(entry)
        return "\n".join(lines)

    @staticmethod
    def narrate_trade_routes(status: lq.TradeRouteStatus) -> str:
        lines = [f"Trade Routes: {status.active_count}/{status.capacity} active"]
        on_route = [t for t in status.traders if t.on_route]
        idle = [t for t in status.traders if not t.on_route]
        if on_route:
            lines.append(f"\nOn route ({len(on_route)}):")
            for t in on_route:
                origin = t.route_origin or "?"
                dest = t.route_dest or "?"
                # Owner label
                if t.is_domestic:
                    label = "Domestic"
                elif t.is_city_state:
                    label = f"City-State"
                else:
                    label = t.route_owner or "?"
                parts = [f"  Trader (id:{t.unit_id}) {origin} -> {dest} ({label})"]
                # Yields
                yields = []
                if t.origin_yields:
                    yields.append(t.origin_yields)
                if t.dest_yields:
                    yields.append(f"-> dest: {t.dest_yields}")
                if yields:
                    parts.append(" | " + " ".join(yields))
                # Flags
                flags = []
                if t.has_quest:
                    flags.append("[QUEST]")
                if t.pressure_out > 0 and t.religion_out:
                    flags.append(f"{t.religion_out} -> {t.pressure_out}")
                if t.pressure_in > 0 and t.religion_in:
                    flags.append(f"{t.religion_in} <- {t.pressure_in}")
                if flags:
                    parts.append(" | " + " ".join(flags))
                lines.append("".join(parts))
        if idle:
            lines.append(f"\nIdle ({len(idle)}):")
            for t in idle:
                lines.append(f"  Trader (id:{t.unit_id}) at ({t.x},{t.y}) — needs trade_route or teleport")
        if not status.traders:
            lines.append("\nNo trader units.")
        free_slots = status.capacity - status.active_count
        if free_slots > 0:
            lines.append(f"\n{free_slots} free route slot(s) — build/buy a Trader to fill.")
        if status.ghost_count > 0:
            engine_total = status.active_count + status.ghost_count
            lines.append(f"\nWARNING: {status.ghost_count} ghost route record(s) in engine "
                         f"(engine reports {engine_total}, only {status.active_count} have living traders).")
        return "\n".join(lines)

    @staticmethod
    def narrate_trade_destinations(dests: list[lq.TradeDestination]) -> str:
        if not dests:
            return "No valid trade route destinations. Check that your trader is in a city and has moves."
        domestic = [d for d in dests if d.is_domestic]
        foreign = [d for d in dests if not d.is_domestic]
        lines = [f"{len(dests)} trade route destinations:"]

        def _fmt_dest(d: lq.TradeDestination, show_owner: bool = False) -> str:
            owner = f" ({d.owner_name})" if show_owner and d.owner_name else ""
            parts = [f"  {d.city_name}{owner} at ({d.x},{d.y})"]
            # Yields
            yields = []
            if d.origin_yields:
                yields.append(d.origin_yields)
            if d.dest_yields:
                yields.append(f"-> dest: {d.dest_yields}")
            if yields:
                parts.append(" | " + " ".join(yields))
            # Flags
            flags = []
            if d.has_quest:
                flags.append("[QUEST]")
            if d.has_trading_post:
                flags.append("Trading Post")
            if d.pressure_out > 0 and d.religion_out:
                flags.append(f"{d.religion_out} -> {d.pressure_out}")
            if d.pressure_in > 0 and d.religion_in:
                flags.append(f"{d.religion_in} <- {d.pressure_in}")
            if flags:
                parts.append(" | " + " ".join(flags))
            return "".join(parts)

        if domestic:
            lines.append("\nDomestic (food + production to destination):")
            for d in domestic:
                lines.append(_fmt_dest(d))
        if foreign:
            lines.append("\nInternational (gold to origin):")
            for d in foreign:
                lines.append(_fmt_dest(d, show_owner=True))
        # Summarize city-state quests
        quest_cs = [d.city_name for d in dests if d.has_quest]
        if quest_cs:
            lines.append(f"\nCity-state quests (send trade route for envoy): {', '.join(quest_cs)}")
        lines.append("\nUse execute_unit_action with action='trade_route', target_x=X, target_y=Y")
        return "\n".join(lines)

    @staticmethod
    def narrate_world_congress(status: lq.WorldCongressStatus) -> str:
        lines = []
        if status.is_in_session:
            lines.append("World Congress: IN SESSION (vote required!)")
            costs_str = "/".join(str(c) for c in status.favor_costs[1:]) if len(status.favor_costs) > 1 else "10/30/60/100/150"
            lines.append(f"Favor: {status.favor} | Max votes per resolution: {status.max_votes} (1 free, extras cost favor: {costs_str})")
        else:
            if status.turns_until_next >= 0:
                lines.append(f"World Congress: Next session in {status.turns_until_next} turns")
            else:
                lines.append("World Congress: Not yet convened")
            lines.append(f"Favor: {status.favor}")

        if status.resolutions:
            lines.append("")
            for i, r in enumerate(status.resolutions, 1):
                if status.is_in_session:
                    lines.append(f"Resolution #{i}: {r.name} (hash: {r.resolution_hash})")
                    lines.append(f"  Target type: {r.target_kind}")
                    if r.effect_a:
                        lines.append(f"  Option A: {r.effect_a}")
                    if r.effect_b:
                        lines.append(f"  Option B: {r.effect_b}")
                    if r.possible_targets:
                        targets_str = ", ".join(f"[{j}] {t}" for j, t in enumerate(r.possible_targets))
                        lines.append(f"  Targets: {targets_str}")
                    lines.append(f"  -> vote_world_congress(resolution_hash={r.resolution_hash}, option=1or2, target_index=N, num_votes=1)")
                else:
                    outcome = "A" if r.winner == 0 else "B" if r.winner == 1 else "?"
                    effect = r.effect_a if r.winner == 0 else r.effect_b if r.winner == 1 else ""
                    chosen = f" ({r.chosen_thing})" if r.chosen_thing else ""
                    lines.append(f"  {r.name} — Outcome {outcome}{chosen}: {effect}")

        if status.proposals:
            lines.append("\nProposals:")
            for p in status.proposals:
                lines.append(f"  {p.sender_name} -> {p.target_name}: {p.description}")

        return "\n".join(lines)

    @staticmethod
    def narrate_victory_progress(vp: lq.VictoryProgress) -> str:
        if not vp.players:
            return "No victory data available."

        lines = ["=== VICTORY PROGRESS ===", ""]

        # Find our player (player_id 0 typically, or first non-Unmet)
        us = next((p for p in vp.players if p.name != "Unmet"), None)

        # --- Science Victory ---
        lines.append("SCIENCE VICTORY (launch 4 space projects = 50 VP)")
        sci_sorted = sorted(vp.players, key=lambda p: (p.science_vp, p.techs_researched), reverse=True)
        for p in sci_sorted:
            marker = " <--" if us and p.player_id == us.player_id else ""
            lines.append(f"  {p.name}: {p.science_vp}/{p.science_vp_needed} VP | {p.techs_researched} techs{marker}")

        # --- Domination Victory ---
        lines.append("")
        lines.append("DOMINATION (own all original capitals)")
        for p in vp.players:
            holds = vp.capitals_held.get(p.name, True)
            status = "holds own capital" if holds else "CAPITAL LOST"
            marker = " <--" if us and p.player_id == us.player_id else ""
            lines.append(f"  {p.name}: {status} | military {p.military_strength}{marker}")

        # --- Culture Victory ---
        lines.append("")
        lines.append("CULTURE (your tourists > every civ's domestic tourists)")
        if us:
            lines.append(f"  Our domestic tourists: {us.staycationers}")
            for name, our_tourists in vp.our_tourists_from.items():
                their_dom = vp.their_staycationers.get(name, 0)
                gap = their_dom - our_tourists
                status = "DOMINANT" if gap <= 0 else f"need {gap} more"
                lines.append(f"  vs {name}: {our_tourists}/{their_dom} tourists ({status})")

        # --- Religious Victory ---
        lines.append("")
        lines.append("RELIGION (your religion majority in all civs)")
        for p in vp.players:
            rel = vp.religion_majority.get(p.name, "none")
            rel_short = rel.replace("RELIGION_", "").title() if rel != "none" else "none"
            founded = " (FOUNDED)" if p.has_religion else ""
            marker = " <--" if us and p.player_id == us.player_id else ""
            lines.append(f"  {p.name}: majority={rel_short}{founded} | {p.religion_cities} cities converted{marker}")

        # --- Diplomatic Victory ---
        lines.append("")
        lines.append("DIPLOMATIC (20 VP from World Congress)")
        diplo_sorted = sorted(vp.players, key=lambda p: p.diplomatic_vp, reverse=True)
        for p in diplo_sorted:
            marker = " <--" if us and p.player_id == us.player_id else ""
            lines.append(f"  {p.name}: {p.diplomatic_vp}/20 VP{marker}")

        # --- Score Victory ---
        lines.append("")
        lines.append("SCORE (highest at turn 500)")
        score_sorted = sorted(vp.players, key=lambda p: p.score, reverse=True)
        for p in score_sorted:
            marker = " <--" if us and p.player_id == us.player_id else ""
            lines.append(f"  {p.name}: {p.score}{marker}")

        # --- Rival Intelligence ---
        lines.append("")
        lines.append("RIVAL INTELLIGENCE")
        for p in sorted(vp.players, key=lambda p: p.score, reverse=True):
            marker = " <--" if us and p.player_id == us.player_id else ""
            lines.append(
                f"  {p.name}: {p.num_cities} cities | "
                f"Sci {p.science_yield:.0f} Cul {p.culture_yield:.0f} Gold {p.gold_yield:+.0f} | "
                f"Mil {p.military_strength}{marker}"
            )

        # --- Victory Path Assessment ---
        if us:
            lines.append("")
            lines.append("VICTORY ASSESSMENT")
            assessments: list[tuple[str, int, str]] = []  # (type, viability 0-100, reason)

            # Science: assess by tech count relative to leaders and science VP progress
            sci_leader = max((p for p in vp.players), key=lambda p: p.techs_researched)
            sci_gap = sci_leader.techs_researched - us.techs_researched
            if us.science_vp > 0:
                assessments.append(("Science", 80, f"Space race started ({us.science_vp}/{us.science_vp_needed} VP)"))
            elif sci_gap <= 5:
                assessments.append(("Science", 60, f"Tech leader (gap: {sci_gap} techs behind {sci_leader.name})"))
            elif sci_gap <= 15:
                assessments.append(("Science", 30, f"Behind in tech (gap: {sci_gap} techs behind {sci_leader.name})"))
            else:
                assessments.append(("Science", 10, f"Far behind in tech ({sci_gap} behind {sci_leader.name})"))

            # Domination: check our military vs rivals, and do we hold all our capitals?
            mil_leader = max((p for p in vp.players), key=lambda p: p.military_strength)
            our_holds = vp.capitals_held.get(us.name, True)
            if not our_holds:
                assessments.append(("Domination", 5, "CAPITAL LOST — defensive priority!"))
            elif us.military_strength >= mil_leader.military_strength * 0.8:
                rivals_with_caps = sum(1 for name, holds in vp.capitals_held.items() if holds and name != us.name)
                assessments.append(("Domination", 40, f"Strong military ({us.military_strength}), {rivals_with_caps} capitals to capture"))
            else:
                assessments.append(("Domination", 15, f"Military too weak ({us.military_strength} vs leader {mil_leader.military_strength})"))

            # Culture: compare our tourists vs their staycationers
            if vp.our_tourists_from:
                culture_gaps = []
                for name, our_tourists in vp.our_tourists_from.items():
                    their_dom = vp.their_staycationers.get(name, 0)
                    culture_gaps.append(their_dom - our_tourists)
                max_gap = max(culture_gaps) if culture_gaps else 999
                if max_gap <= 0:
                    assessments.append(("Culture", 95, "CULTURALLY DOMINANT over all civs!"))
                elif max_gap <= 10:
                    assessments.append(("Culture", 70, f"Close to cultural victory (max gap: {max_gap})"))
                elif max_gap <= 30:
                    assessments.append(("Culture", 40, f"Tourism growing (max gap: {max_gap})"))
                else:
                    assessments.append(("Culture", 15, f"Large tourism gap (max gap: {max_gap})"))
            else:
                assessments.append(("Culture", 20, "No tourism data"))

            # Religion: check if we founded one
            if us.has_religion:
                total_civs = len([p for p in vp.players if p.name != "Unmet"])
                our_rel = vp.religion_majority.get(us.name, "none")
                converted = sum(1 for rel in vp.religion_majority.values() if rel == our_rel)
                assessments.append(("Religion", min(70, converted * 100 // total_civs),
                                    f"Religion in {converted}/{total_civs} civs"))
            else:
                assessments.append(("Religion", 0, "No founded religion — path closed"))

            # Diplomatic: steady accumulation
            if us.diplomatic_vp >= 15:
                assessments.append(("Diplomatic", 80, f"{us.diplomatic_vp}/20 VP — close!"))
            elif us.diplomatic_vp >= 8:
                assessments.append(("Diplomatic", 50, f"{us.diplomatic_vp}/20 VP — mid-game"))
            else:
                assessments.append(("Diplomatic", 20, f"{us.diplomatic_vp}/20 VP — slow accumulation"))

            # Score: always a fallback
            our_rank = sorted(vp.players, key=lambda p: p.score, reverse=True)
            our_pos = next((i for i, p in enumerate(our_rank) if p.player_id == us.player_id), 0) + 1
            assessments.append(("Score", 50 if our_pos <= 2 else 25, f"Rank #{our_pos} by score"))

            # Sort by viability and display
            assessments.sort(key=lambda a: a[1], reverse=True)
            best = assessments[0]
            for vtype, viability, reason in assessments:
                bar = "#" * (viability // 10) + "-" * (10 - viability // 10)
                rec = " ** RECOMMENDED **" if vtype == best[0] and viability >= 30 else ""
                lines.append(f"  {vtype:12s} [{bar}] {viability}% — {reason}{rec}")

        return "\n".join(lines)

    @staticmethod
    def narrate_notifications(notifs: list[lq.GameNotification]) -> str:
        if not notifs:
            return "No active notifications."

        action_required = [n for n in notifs if n.is_action_required]
        info_notifs = [n for n in notifs if not n.is_action_required]

        lines = []
        if action_required:
            lines.append(f"== Action Required ({len(action_required)}) ==")
            for n in action_required:
                hint = f"  -> Use: {n.resolution_hint}" if n.resolution_hint else ""
                loc = f" at ({n.x},{n.y})" if n.x >= 0 else ""
                lines.append(f"  * {n.message}{loc}{hint}")

        if info_notifs:
            if lines:
                lines.append("")
            lines.append(f"== Notifications ({len(info_notifs)}) ==")
            for n in info_notifs:
                loc = f" at ({n.x},{n.y})" if n.x >= 0 else ""
                lines.append(f"  - {n.message}{loc}")

        return "\n".join(lines)


def _action_result(lines: list[str]) -> str:
    """Parse OK:/ERR: prefixed action responses.

    Scans all lines for the first OK:/ERR: prefix, since LuaEvent
    callbacks (e.g. ShowIngameUI → BulkHide debug prints) can inject
    spurious output before the actual result line.
    """
    if not lines:
        return "Action completed (no response)."
    for line in lines:
        if line.startswith("OK:"):
            return line[3:]
        if line.startswith("ERR:"):
            return f"Error: {line[4:]}"
    # No OK/ERR found — return all lines for debugging
    return "\n".join(lines)


def _format_attack_followup(lines: list[str]) -> str:
    """Format the GameCore follow-up read after an attack."""
    parts = []
    for line in lines:
        if line.startswith("UNIT|"):
            fields = line.split("|")
            if len(fields) >= 3:
                parts.append(f"{fields[1]} {fields[2]}")
    if not parts:
        return "Target eliminated"
    return ", ".join(parts)
