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
        lines = await self.conn.execute_read(lq.build_overview_query())
        ov = lq.parse_overview_response(lines)
        # Bootstrap: capture baseline snapshot for first end_turn diff
        if self._last_snapshot is None:
            try:
                self._last_snapshot = await self._take_snapshot(ov)
            except Exception:
                log.debug("Failed to bootstrap snapshot", exc_info=True)
        return ov

    async def get_units(self) -> list[lq.UnitInfo]:
        lines = await self.conn.execute_read(lq.build_units_query())
        return lq.parse_units_response(lines)

    async def get_cities(self) -> list[lq.CityInfo]:
        lines = await self.conn.execute_write(lq.build_cities_query())
        return lq.parse_cities_response(lines)

    async def get_map_area(
        self, center_x: int, center_y: int, radius: int = 2
    ) -> list[lq.TileInfo]:
        lines = await self.conn.execute_read(
            lq.build_map_area_query(center_x, center_y, radius)
        )
        return lq.parse_map_response(lines)

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
        lua = lq.build_attack_unit(unit_index, target_x, target_y)
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
        return _action_result(lines)

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

    async def get_pending_deals(self) -> list[lq.PendingDeal]:
        lua = lq.build_pending_deals_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_pending_deals_response(lines)

    async def respond_to_deal(self, other_player_id: int, accept: bool) -> str:
        lua = lq.build_respond_to_deal(other_player_id, accept)
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
            ov_lines = await self.conn.execute_read(lq.build_overview_query())
            overview = lq.parse_overview_response(ov_lines)

        unit_lines = await self.conn.execute_read(lq.build_units_query())
        units = lq.parse_units_response(unit_lines)

        city_lines = await self.conn.execute_write(lq.build_cities_query())
        cities = lq.parse_cities_response(city_lines)

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

        # 1. Dismiss popups first — they can block everything else
        await self.dismiss_popup()

        # 2. Diplomacy sessions block turn advancement
        sessions = await self.get_diplomacy_sessions()
        if sessions:
            names = [f"{s.other_civ_name} ({s.other_leader_name})" for s in sessions]
            return f"Cannot end turn: diplomacy encounter pending with {', '.join(names)}. Use diplomacy_respond to handle it."

        # 3. Check for EndTurnBlocking notifications — turn will silently fail without resolving these
        #    Some blockers (like government change) can be auto-resolved with a retry loop.
        for _ in range(3):
            try:
                blocking_lines = await self.conn.execute_write(lq.build_end_turn_blocking_query())
                blocking_type, blocking_msg = lq.parse_end_turn_blocking(blocking_lines)
                if not blocking_type:
                    break  # no blocker

                # Auto-resolve: government change consideration
                if blocking_type == "ENDTURN_BLOCKING_CONSIDER_GOVERNMENT_CHANGE":
                    await self.conn.execute_write(
                        f'local me = Game.GetLocalPlayer(); '
                        f'Players[me]:GetCulture():SetGovernmentChangeConsidered(true); '
                        f'print("OK"); print("{lq.SENTINEL}")'
                    )
                    continue  # re-check for more blockers

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
            # Turn didn't advance — try dismissing popups that appeared mid-turn
            for _ in range(2):
                dismissed = await self.dismiss_popup()
                if "Dismissed" in dismissed:
                    await self.conn.execute_write(lua)
                    await asyncio.sleep(1.0)
                    turn_after = await self._get_turn_number()
                    if turn_after is not None and turn_before is not None and turn_after > turn_before:
                        advanced = True
                        break

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
                events.append(lq.TurnEvent(
                    priority=2, category="unit",
                    message=f"THREAT: {t.unit_desc} spotted {t.distance} tiles from {t.city_name} at ({t.x},{t.y})",
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
        """Scan all known popup states and dismiss any visible ones.

        Dynamically searches conn.lua_states for states whose name contains
        'Popup', 'Wonder', or 'Moment', then calls OnClose() in each visible one.
        """
        popup_keywords = ("Popup", "Wonder", "Moment")
        dismissed = []
        for state_idx, name in self.conn.lua_states.items():
            if not any(kw in name for kw in popup_keywords):
                continue
            try:
                lines = await self.conn.execute_in_state(
                    state_idx,
                    'if not ContextPtr:IsHidden() then OnClose(); print("DISMISSED") end; print("---END---")',
                )
                if any("DISMISSED" in l for l in lines):
                    dismissed.append(name)
            except (LuaError, Exception) as e:
                log.debug("Popup check failed for %s (state %d): %s", name, state_idx, e)
        # Also check InGame child popups (not separate states)
        ingame_popups = (
            "InGamePopup", "GenericPopup", "PopupDialog",
            "BoostUnlockedPopup", "GreatWorkShowcase",
        )
        for popup_name in ingame_popups:
            try:
                lua = (
                    f'local c = ContextPtr:LookUpControl("/InGame/{popup_name}"); '
                    f'if c and not c:IsHidden() then c:SetHide(true); print("DISMISSED") end; '
                    f'print("---END---")'
                )
                lines = await self.conn.execute_write(lua)
                if any("DISMISSED" in l for l in lines):
                    dismissed.append(popup_name)
            except Exception as e:
                log.debug("InGame popup check failed for %s: %s", popup_name, e)
        if dismissed:
            return f"Dismissed: {', '.join(dismissed)}"
        return "No popups to dismiss."

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
            f"Gold: {ov.gold:.0f} ({ov.gold_per_turn:+.0f}/turn) | Science: {ov.science_yield:.1f} | Culture: {ov.culture_yield:.1f} | Faith: {ov.faith:.0f}",
            f"Research: {ov.current_research} | Civic: {ov.current_civic}",
            f"Cities: {ov.num_cities} | Units: {ov.num_units}",
        ]
        if ov.rankings:
            all_scores = [(ov.civ_name, ov.score)] + [(r.civ_name, r.score) for r in ov.rankings]
            all_scores.sort(key=lambda x: x[1], reverse=True)
            rank_strs = [f"{name} {score}" for name, score in all_scores]
            lines.append(f"Rankings: {' > '.join(rank_strs)}")
        return "\n".join(lines)

    @staticmethod
    def narrate_units(units: list[lq.UnitInfo]) -> str:
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
            lines.append(
                f"  {u.name} ({u.unit_type}) at ({u.x},{u.y}) —{strength} "
                f"moves {u.moves_remaining}/{u.max_moves}{charges}{status}{promo_flag} "
                f"[id:{u.unit_id}, idx:{u.unit_index}]"
            )
            if u.targets:
                for t in u.targets:
                    lines.append(f"    >> CAN ATTACK: {t}")
        return "\n".join(lines)

    @staticmethod
    def narrate_cities(cities: list[lq.CityInfo]) -> str:
        if not cities:
            return "No cities."
        lines = [f"{len(cities)} cities:"]
        for c in cities:
            building = c.currently_building if c.currently_building not in ("NONE", "nothing") else "nothing"
            prod_str = f"Building: {building}"
            if building != "nothing" and c.production_turns_left > 0:
                prod_str += f" ({c.production_turns_left} turns)"
            lines.append(
                f"  {c.name} (pop {c.population}) at ({c.x},{c.y}) — "
                f"Food {c.food:.0f} Prod {c.production:.0f} Gold {c.gold:.0f} "
                f"Sci {c.science:.0f} Cul {c.culture:.0f} | "
                f"Housing {c.housing:.0f} Amenities {c.amenities} | "
                f"Growth in {c.turns_to_grow} turns | {prod_str} "
                f"[id:{c.city_id}]"
            )
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
                parts.append(f"({t.improvement.replace('IMPROVEMENT_', '')})")
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
                status = "improved" if r.improved else "UNIMPROVED"
                lines.append(f"  {r.name} — {status} at ({r.x},{r.y})")
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
            lines.append(f"  {c.civ_name} ({c.leader_name}) — {c.diplomatic_state} ({c.relationship_score:+d}){war_str} [player {c.player_id}]")
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
            lines.append("  Respond with: POSITIVE (friendly) or NEGATIVE (dismissive)")
        return "\n".join(lines)

    @staticmethod
    def narrate_tech_civics(tc: lq.TechCivicStatus) -> str:
        lines = []
        if tc.current_research != "None":
            lines.append(f"Researching: {tc.current_research} ({tc.current_research_turns} turns)")
        else:
            lines.append("No technology being researched!")
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

        if gov.available_to_appoint:
            lines.append(f"\nAvailable to appoint ({len(gov.available_to_appoint)}):")
            for g in gov.available_to_appoint:
                lines.append(f"  {g.name} — {g.title} ({g.governor_type})")

        lines.append("\nUse appoint_governor(governor_type) to appoint, assign_governor(governor_type, city_id) to assign.")
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
            lines.append(f"  {g.class_name}: {g.individual_name} ({g.era_name}) — {g.claimant} — your points: {progress}")
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
    """Parse OK:/ERR: prefixed action responses."""
    if not lines:
        return "Action completed (no response)."
    result = lines[0]
    if result.startswith("OK:"):
        return result[3:]
    if result.startswith("ERR:"):
        return f"Error: {result[4:]}"
    return result
