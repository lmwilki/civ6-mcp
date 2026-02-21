"""High-level game state API with server-side narration.

Wraps GameConnection + lua into typed async methods that return
both structured data and human-readable narrated text. Has ZERO MCP
dependency — enabling multi-agent architectures where specialist servers
import the same GameState class but expose different tool subsets.
"""

from __future__ import annotations

import asyncio
import logging
import re

from civ_mcp import lua as lq
from civ_mcp.connection import GameConnection
from civ_mcp.narrate import narrate_combat_estimate, narrate_settle_candidates

log = logging.getLogger(__name__)


class GameState:
    """High-level async API for Civ 6 game state + actions."""

    def __init__(self, connection: GameConnection):
        self.conn = connection
        self._last_snapshot: lq.TurnSnapshot | None = None
        self._game_identity: tuple[str, int] | None = None  # (civ_type, seed)

    async def get_game_identity(self) -> tuple[str, int]:
        """Return (civ_type_lower, random_seed) for the current game. Cached."""
        if self._game_identity is not None:
            return self._game_identity
        code = (
            "local me = Game.GetLocalPlayer() "
            "local cfg = PlayerConfigurations[me] "
            'print("GAMESEED|" .. cfg:GetCivilizationTypeName() '
            '.. "|" .. tostring(GameConfiguration.GetValue("GAME_SYNC_RANDOM_SEED"))) '
            'print("---END---")'
        )
        lines = await self.conn.execute_write(code)
        for line in lines:
            if line.startswith("GAMESEED|"):
                parts = line.split("|")
                civ = parts[1].replace("CIVILIZATION_", "").lower()
                seed = int(parts[2])
                self._game_identity = (civ, seed)
                return self._game_identity
        return ("unknown", 0)

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

    async def get_rival_snapshot(self) -> list[lq.RivalSnapshot]:
        """Lightweight per-rival stats for diary entries."""
        lines = await self.conn.execute_write(lq.build_rival_snapshot_query())
        return lq.parse_rival_snapshot_response(lines)

    async def check_game_over(self) -> lq.GameOverStatus | None:
        """Check if the game has ended (victory/defeat screen showing)."""
        try:
            lines = await self.conn.execute_write(lq.build_gameover_check())
            return lq.parse_gameover_response(lines)
        except Exception:
            log.debug("Game-over check failed", exc_info=True)
            return None

    async def get_units(self) -> list[lq.UnitInfo]:
        lines = await self.conn.execute_write(lq.build_units_query())
        return lq.parse_units_response(lines)

    async def get_spies(self) -> list[lq.SpyInfo]:
        lines = await self.conn.execute_write(lq.build_get_spies_query())
        return lq.parse_spies_response(lines)

    async def spy_travel(self, unit_index: int, target_x: int, target_y: int) -> str:
        lua = lq.build_spy_travel(unit_index, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def spy_mission(
        self, unit_index: int, mission_type: str, target_x: int, target_y: int
    ) -> str:
        lua = lq.build_spy_mission(unit_index, mission_type, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

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
    ) -> tuple[
        list[lq.ResourceStockpile],
        list[lq.OwnedResource],
        list[lq.NearbyResource],
        dict[str, int],
    ]:
        # InGame context needed for GetResourceStockpileCap etc.
        lines = await self.conn.execute_write(lq.build_empire_resources_query())
        return lq.parse_empire_resources_response(lines)

    # ------------------------------------------------------------------
    # Action methods (run in InGame context for UnitManager access)
    # ------------------------------------------------------------------

    async def move_unit(self, unit_index: int, target_x: int, target_y: int) -> str:
        lua = lq.build_move_unit(unit_index, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        # Post-move: read actual position from GameCore (move is async in InGame)
        if result.startswith("MOVING_TO") or result.startswith("CAPTURE_MOVE"):
            try:
                pos_lines = await self.conn.execute_read(
                    lq.build_unit_position_query(unit_index)
                )
                for line in pos_lines:
                    if line.startswith("POS|") and "GONE" not in line:
                        parts = line.split("|")
                        now_x, now_y = int(parts[1]), int(parts[2])
                        result += f"|now_at:{now_x},{now_y}"
                        from_match = re.search(r"\|from:(\d+),(\d+)", result)
                        if from_match:
                            from_x = int(from_match.group(1))
                            from_y = int(from_match.group(2))
                            if now_x == from_x and now_y == from_y:
                                result += "|BLOCKED (unit did not move — impassable terrain, border, or no path)"
                            else:
                                tgt_match = re.search(
                                    r"(?:MOVING_TO|CAPTURE_MOVE)\|(\d+),(\d+)", result
                                )
                                if tgt_match:
                                    tx, ty = (
                                        int(tgt_match.group(1)),
                                        int(tgt_match.group(2)),
                                    )
                                    if (now_x, now_y) != (tx, ty):
                                        result += f"|STOPPED_MID_PATH (moves exhausted)"
                        break
            except Exception:
                pass
        return result

    async def attack_unit(self, unit_index: int, target_x: int, target_y: int) -> str:
        # Pre-attack: dismiss any blocking popups that would silently eat the attack
        try:
            await self.dismiss_popup()
        except Exception:
            pass
        # Pre-attack: run combat estimator
        estimate_str = ""
        est: lq.CombatEstimate | None = None
        try:
            est_lua = lq.build_combat_estimate_query(unit_index, target_x, target_y)
            est_lines = await self.conn.execute_write(est_lua)
            est = lq.parse_combat_estimate(est_lines, 0, 0)
            if est:
                estimate_str = narrate_combat_estimate(est) + "\n"
        except Exception as e:
            log.debug("Combat estimate failed: %s", e)
        lua = lq.build_attack_unit(unit_index, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        # Follow up with GameCore read for actual post-combat HP
        if result.startswith("RANGE_ATTACK") or result.startswith("MELEE_ATTACK"):
            try:
                followup = await self.conn.execute_read(
                    lq.build_attack_followup_query(target_x, target_y)
                )
                followup_str = _format_attack_followup(followup)

                # Calculate damage from pre-attack HP vs post-combat HP
                pre_hp = _extract_pre_hp(result)
                post_hp = _extract_post_hp(followup)
                damage_info = ""
                if pre_hp is not None and post_hp is not None:
                    damage_info = f"|damage dealt:{pre_hp - post_hp}"
                elif pre_hp is not None and followup_str == "Target eliminated":
                    damage_info = f"|damage dealt:{pre_hp}"

                result += damage_info + "\n  Post-combat: " + followup_str

                # Warn if target HP unchanged (popup may have blocked the attack)
                actual_pre = (
                    pre_hp if pre_hp is not None else (est.defender_hp if est else None)
                )
                if actual_pre is not None and est and est.est_damage_to_defender > 0:
                    if (
                        followup_str != "Target eliminated"
                        and post_hp is not None
                        and post_hp >= actual_pre
                    ):
                        result += (
                            "\n  !! WARNING: Target HP unchanged — attack may have been "
                            "blocked by a popup. Run dismiss_popup then retry."
                        )
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
                    lq.build_attack_followup_query(target_x, target_y)
                )
                followup_str = _format_attack_followup(followup)

                pre_hp = _extract_pre_hp(result)
                post_hp = _extract_post_hp(followup)
                damage_info = ""
                if pre_hp is not None and post_hp is not None:
                    damage_info = f"|damage dealt:{pre_hp - post_hp}"
                elif pre_hp is not None and followup_str == "Target eliminated":
                    damage_info = f"|damage dealt:{pre_hp}"

                result += damage_info + "\n  Post-combat: " + followup_str
            except Exception as e:
                log.debug("City attack followup failed: %s", e)
        return result

    async def resolve_city_capture(self, action: str) -> str:
        lua = lq.build_resolve_city_capture(action)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def found_city(self, unit_index: int) -> str:
        # Pre-dismiss any blocking popups (tech completion, era change, etc.)
        try:
            await self.dismiss_popup()
        except Exception:
            pass

        lua = lq.build_found_city(unit_index)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)

        if result.startswith("FOUNDED|"):
            # Extract coordinates from "FOUNDED|x,y"
            parts = result.split("|")[1].split(",")
            x, y = int(parts[0]), int(parts[1])
            # Verify city was actually created (RequestOperation is async)
            verify_lua = lq.build_verify_city_at(x, y)
            verify_lines = await self.conn.execute_read(verify_lua)
            verified = lq.parse_verify_city_at(verify_lines)
            if not verified:
                # Retry once — popup may have blocked the async operation
                try:
                    await self.dismiss_popup()
                    lines = await self.conn.execute_write(lua)
                    retry_result = _action_result(lines)
                    if retry_result.startswith("FOUNDED|"):
                        verify_lines = await self.conn.execute_read(verify_lua)
                        if lq.parse_verify_city_at(verify_lines):
                            result = retry_result
                            verified = True
                except Exception:
                    log.debug(
                        "found_city retry after popup dismiss failed", exc_info=True
                    )
                if not verified:
                    result = (
                        f"Error: FOUND_FAILED|Founding at {x},{y} was requested but "
                        "city did not appear despite popup dismissal."
                    )

        # On settle failure, run the settle advisor to suggest alternatives
        if result.startswith("Error: CANNOT_FOUND") or result.startswith(
            "Error: FOUND_FAILED"
        ):
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
        if candidates:
            return narrate_settle_candidates(candidates)
        # Auto-fallback to global scan when no local candidates
        try:
            global_candidates = await self.get_global_settle_scan()
            if global_candidates:
                header = "No valid settle locations within 5 tiles. Best sites on revealed map:\n"
                return header + narrate_settle_candidates(global_candidates[:5])
        except Exception:
            log.debug("Global settle fallback failed", exc_info=True)
        return "No valid settle locations found within 5 tiles or on revealed map."

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
        self,
        city_id: int,
        item_type: str,
        item_name: str,
        target_x: int | None = None,
        target_y: int | None = None,
    ) -> str:
        lua = lq.build_produce_item(city_id, item_type, item_name, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)

        # If CanStartOperation failed but CanProduce passed, verify via readback
        if any("MAYBE:" in l for l in lines):
            try:
                verify_lines = await self.conn.execute_read(
                    lq.build_verify_production(city_id, item_name)
                )
                if any("CONFIRMED" in l for l in verify_lines):
                    turns = ""
                    for vl in verify_lines:
                        if vl.startswith("CONFIRMED|"):
                            turns = vl.split("|", 1)[1]
                    return f"PRODUCING|{item_name}|{turns} (bypassed stale CanStartOperation)"
                else:
                    return (
                        f"Error: CANNOT_START|{item_name} cannot start "
                        f"(CanProduce=true but RequestOperation failed)"
                    )
            except Exception:
                log.debug("Production readback failed", exc_info=True)
                return f"Error: CANNOT_START|{item_name} (readback failed)"

        return result

    async def purchase_item(
        self,
        city_id: int,
        item_type: str,
        item_name: str,
        yield_type: str = "YIELD_GOLD",
    ) -> str:
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
        result = _action_result(lines)
        if "OK:RESEARCHING" in result:
            # Verify InGame actually accepted it (desync check)
            verify = await self.conn.execute_read(
                f"local me = Game.GetLocalPlayer(); "
                f"print(Players[me]:GetTechs():GetResearchingTech()); "
                f'print("{lq.SENTINEL}")'
            )
            gc_tech = (
                int(verify[0]) if verify and verify[0].lstrip("-").isdigit() else -1
            )
            if gc_tech == -1:
                # InGame silently failed — fall back to GameCore
                gc_lua = lq.build_set_research_gamecore(tech_name)
                gc_lines = await self.conn.execute_read(gc_lua)
                return _action_result(gc_lines)
        return result

    async def set_civic(self, civic_name: str) -> str:
        lua = lq.build_set_civic(civic_name)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        if "OK:PROGRESSING" in result:
            # Verify InGame actually accepted it (desync check)
            verify = await self.conn.execute_read(
                f"local me = Game.GetLocalPlayer(); "
                f"print(Players[me]:GetCulture():GetProgressingCivic()); "
                f'print("{lq.SENTINEL}")'
            )
            gc_civic = (
                int(verify[0]) if verify and verify[0].lstrip("-").isdigit() else -1
            )
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
        # Capture dialogue text BEFORE response to detect goodbye phase
        pre_sessions = await self.get_diplomacy_sessions()
        pre_text = ""
        for s in pre_sessions:
            if s.other_player_id == other_player_id:
                pre_text = s.dialogue_text
                break

        # Phase 1: Send AddResponse only (no CloseSession — engine handles lifecycle)
        lua = lq.build_diplomacy_respond(other_player_id, response.upper())
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)

        # EXIT and error paths return immediately
        if "SESSION_CLOSED" in result or result.startswith("Error"):
            return result

        # Phase 2: Give engine ~9 frames (0.3s at 30fps) to process the
        # response and transition/close the session, then check state in
        # a separate TCP round-trip (same-frame checks see stale state).
        await asyncio.sleep(0.3)
        check_lines = await self.conn.execute_write(
            lq.build_check_diplomacy_session_state(other_player_id)
        )
        if not any("SESSION_OPEN" in l for l in check_lines):
            return f"OK:RESPONDED|{response.upper()}|SESSION_CLOSED"

        # Phase 3: Session still open — check if dialogue text changed.
        # If unchanged, we're in the goodbye phase. Auto-close.
        post_sessions = await self.get_diplomacy_sessions()
        post_text = ""
        for s in post_sessions:
            if s.other_player_id == other_player_id:
                post_text = s.dialogue_text
                break

        if not post_sessions:
            # Session disappeared between checks (race condition)
            return f"OK:RESPONDED|{response.upper()}|SESSION_CLOSED"

        if post_text == pre_text:
            # Dialogue unchanged → goodbye phase. Force close.
            log.info(
                "Goodbye phase detected (text unchanged) for player %d — auto-closing",
                other_player_id,
            )
            close_lua = lq.build_diplomacy_respond(other_player_id, "EXIT")
            await self.conn.execute_write(close_lua)
            return f"OK:RESPONDED|{response.upper()}|SESSION_CLOSED (auto-closed goodbye phase)"

        # Include the new dialogue text so the agent can see what the leader said
        post_reason = ""
        for s in post_sessions:
            if s.other_player_id == other_player_id:
                post_reason = s.reason_text
                break
        dialogue_note = f'\nLeader says: "{post_text}"'
        if post_reason:
            dialogue_note += f'\nReason/agenda: "{post_reason}"'
        return f"OK:RESPONDED|{response.upper()}|SESSION_CONTINUES{dialogue_note}"

    async def send_diplomatic_action(self, other_player_id: int, action: str) -> str:
        if action.upper() == "OPEN_BORDERS":
            # Session-based OPEN_BORDERS causes AI turn hang.
            # Route through the trade deal API instead (mutual open borders).
            return await self.propose_trade(
                other_player_id,
                offer_items=[{"type": "AGREEMENT", "subtype": "OPEN_BORDERS"}],
                request_items=[{"type": "AGREEMENT", "subtype": "OPEN_BORDERS"}],
            )
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
        result = _action_result(lines)
        if result.startswith("Error"):
            return result
        # War state is async — verify with a second round-trip
        verify_lines = await self.conn.execute_write(
            lq.build_check_war_state(other_player_id)
        )
        at_peace = any("AT_PEACE" in l for l in verify_lines)
        name = result.split("|", 1)[1] if "|" in result else f"player {other_player_id}"
        if at_peace:
            return f"ACCEPTED|Peace established with {name}"
        else:
            return f"REJECTED|{name} rejected your peace offer"

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
        result = _action_result(lines)
        if not result.startswith("Error"):
            # Post-verify: RequestPolicyChanges can silently no-op (e.g. during era transitions)
            status = await self.get_policies()
            slot_map = {s.slot_index: s.current_policy for s in status.slots}
            mismatches = [
                f"slot {idx} (wanted {pol}, got {slot_map.get(idx) or 'EMPTY'})"
                for idx, pol in assignments.items()
                if slot_map.get(idx) != pol
            ]
            if mismatches:
                result += (
                    f"\nWARN:SILENT_FAILURE — engine rejected: {', '.join(mismatches)}. "
                    "Try a different policy or retry next turn."
                )
        return result

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
        lines = await self.conn.execute_read(lua)  # GameCore context
        result = _action_result(lines)
        # GameCore SetPromotion doesn't clear the InGame NEEDS_PROMOTION
        # notification, which blocks end_turn until dismissed.
        # Must use SendActivated + Dismiss (not just Dismiss) and skip
        # the CanUserDismiss() check which returns false for these.
        # Only dismiss if NO units still have pending promotions.
        if not result.startswith("Error"):
            try:
                await self.conn.execute_write(
                    f"local me = Game.GetLocalPlayer(); "
                    f"local anyNeed = false; "
                    f"for i, u in Players[me]:GetUnits():Members() do "
                    f"  if u:GetX() ~= -9999 then "
                    f"    local ok, exp = pcall(function() return u:GetExperience() end); "
                    f"    if ok and exp then "
                    f"      local xp = exp:GetExperiencePoints(); "
                    f"      local threshold = exp:GetExperienceForNextLevel(); "
                    f"      if xp >= threshold then "
                    f"        local promoCount = 0; "
                    f"        local ok2, pl = pcall(function() return exp:GetPromotions() end); "
                    f"        if ok2 and pl then promoCount = #pl end; "
                    f"        local lvl = 1; "
                    f"        local ok3, l = pcall(function() return exp:GetLevel() end); "
                    f"        if ok3 and l then lvl = l end; "
                    f"        if promoCount < lvl then anyNeed = true end "
                    f"      end "
                    f"    end "
                    f"  end "
                    f"  if anyNeed then break end "
                    f"end; "
                    f"if not anyNeed then "
                    f"  local list = NotificationManager.GetList(me); "
                    f"  if list then "
                    f"    for _, nid in ipairs(list) do "
                    f"      local e = NotificationManager.Find(me, nid); "
                    f"      if e and not e:IsDismissed() then "
                    f"        local bt = e:GetEndTurnBlocking(); "
                    f"        if bt and bt == EndTurnBlockingTypes.ENDTURN_BLOCKING_UNIT_PROMOTION then "
                    f"          pcall(function() NotificationManager.SendActivated(me, nid) end); "
                    f"          pcall(function() NotificationManager.Dismiss(me, nid) end) "
                    f"        end "
                    f"      end "
                    f"    end "
                    f"  end "
                    f"end; "
                    f'print("OK"); print("{lq.SENTINEL}")'
                )
            except Exception:
                pass  # non-fatal — end_turn blocker handler will catch it
        return result

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
        result = _action_result(lines)
        if result.startswith("OK:ENVOY_SENT"):
            # Verify token actually decremented (async race condition workaround)
            await asyncio.sleep(0.1)
            try:
                verify_lines = await self.conn.execute_write(
                    f"local me = Game.GetLocalPlayer(); "
                    f"print(Players[me]:GetInfluence():GetTokensToGive()); "
                    f'print("{lq.SENTINEL}")'
                )
                if verify_lines and verify_lines[0].strip().lstrip("-").isdigit():
                    actual = int(verify_lines[0].strip())
                    result += f" (verified remaining: {actual})"
            except Exception:
                log.debug("Envoy verification failed", exc_info=True)
        return result

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
    # Religion founding methods (InGame context)
    # ------------------------------------------------------------------

    async def get_religion_founding_status(self) -> lq.ReligionFoundingStatus:
        lua = lq.build_religion_beliefs_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_religion_beliefs_response(lines)

    async def found_religion(
        self, religion_type: str, follower_belief: str, founder_belief: str
    ) -> str:
        lua = lq.build_found_religion(religion_type, follower_belief, founder_belief)
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

    async def get_district_advisor(
        self, city_id: int, district_type: str
    ) -> list[lq.DistrictPlacement]:
        lua = lq.build_district_advisor_query(city_id, district_type)
        lines = await self.conn.execute_write(lua)
        return lq.parse_district_advisor_response(lines)

    async def get_wonder_advisor(
        self, city_id: int, wonder_name: str
    ) -> list[lq.WonderPlacement]:
        lua = lq.build_wonder_advisor_query(city_id, wonder_name)
        lines = await self.conn.execute_write(lua)
        return lq.parse_wonder_advisor_response(lines)

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

    async def patronize_great_person(
        self, individual_id: int, yield_type: str = "YIELD_GOLD"
    ) -> str:
        lua = lq.build_patronize_great_person(individual_id, yield_type)
        lines = await self.conn.execute_write(lua)
        return lines[0] if lines else "No response"

    async def get_religion_status(self) -> lq.ReligionStatus:
        lines = await self.conn.execute_write(lq.build_religion_status_query())
        return lq.parse_religion_status_response(lines)

    async def reject_great_person(self, individual_id: int) -> str:
        lua = lq.build_reject_great_person(individual_id)
        lines = await self.conn.execute_write(lua)
        return lines[0] if lines else "No response"

    # ------------------------------------------------------------------
    # Trade route methods (InGame context)
    # ------------------------------------------------------------------

    async def get_trade_routes(self) -> lq.TradeRouteStatus:
        lua = lq.build_trade_routes_query()
        lines = await self.conn.execute_write(
            lua
        )  # InGame context (GetOutgoingRoutes is InGame-only)
        return lq.parse_trade_routes_response(lines)

    async def get_trade_destinations(
        self, unit_index: int
    ) -> list[lq.TradeDestination]:
        lua = lq.build_trade_destinations_query(unit_index)
        lines = await self.conn.execute_write(lua)
        return lq.parse_trade_destinations_response(lines)

    async def make_trade_route(
        self, unit_index: int, target_x: int, target_y: int
    ) -> str:
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

    async def spread_religion(self, unit_index: int) -> str:
        lua = lq.build_spread_religion(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Trader teleport (InGame context)
    # ------------------------------------------------------------------

    async def teleport_to_city(
        self, unit_index: int, target_x: int, target_y: int
    ) -> str:
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

    async def vote_world_congress(
        self, resolution_hash: int, option: int, target_index: int, num_votes: int
    ) -> str:
        lua = lq.build_congress_vote(resolution_hash, option, target_index, num_votes)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def submit_congress(self) -> str:
        lua = lq.build_congress_submit()
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def queue_wc_votes(self, votes: list[dict]) -> str:
        """Store agent voting preferences and register WC event handler."""
        lua = lq.build_register_wc_voter(votes=votes)
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

    async def _take_snapshot(
        self, overview: lq.GameOverview | None = None
    ) -> lq.TurnSnapshot:
        """Capture current game state for diffing."""
        if overview is None:
            ov_lines = await self.conn.execute_write(lq.build_overview_query())
            overview = lq.parse_overview_response(ov_lines)

        unit_lines = await self.conn.execute_read(lq.build_units_query())
        units = lq.parse_units_response(unit_lines)

        city_lines = await self.conn.execute_write(lq.build_cities_query())
        cities, _ = lq.parse_cities_response(city_lines)

        try:
            stk_lines = await self.conn.execute_write(lq.build_stockpile_query())
            stockpiles = lq.parse_stockpile_response(stk_lines)
        except Exception:
            log.debug("Stockpile query failed", exc_info=True)
            stockpiles = []

        return lq.TurnSnapshot(
            turn=overview.turn,
            units={u.unit_id: u for u in units},
            cities={
                c.city_id: lq.CitySnapshot(
                    city_id=c.city_id,
                    name=c.name,
                    population=c.population,
                    currently_building=c.currently_building,
                    food_surplus=c.food_surplus,
                    turns_to_grow=c.turns_to_grow,
                )
                for c in cities
            },
            current_research=overview.current_research,
            current_civic=overview.current_civic,
            stockpiles=stockpiles,
        )

    @staticmethod
    def _diff_snapshots(
        before: lq.TurnSnapshot, after: lq.TurnSnapshot
    ) -> list[lq.TurnEvent]:
        """Compare two snapshots and generate events."""
        events: list[lq.TurnEvent] = []

        # --- Unit events ---
        for uid, ub in before.units.items():
            if uid not in after.units:
                events.append(
                    lq.TurnEvent(
                        priority=1,
                        category="unit",
                        message=f"Your {ub.name} ({ub.unit_type}) was killed! Last seen at ({ub.x},{ub.y}).",
                    )
                )
            else:
                ua = after.units[uid]
                dmg = ub.health - ua.health
                if dmg > 0:
                    events.append(
                        lq.TurnEvent(
                            priority=2,
                            category="unit",
                            message=f"Your {ua.name} ({ua.unit_type}) took {dmg} damage! HP: {ua.health}/{ua.max_health} at ({ua.x},{ua.y}).",
                        )
                    )
                elif dmg < 0:
                    events.append(
                        lq.TurnEvent(
                            priority=3,
                            category="unit",
                            message=f"Your {ua.name} ({ua.unit_type}) healed {-dmg} HP. HP: {ua.health}/{ua.max_health}.",
                        )
                    )

        for uid, ua in after.units.items():
            if uid not in before.units:
                events.append(
                    lq.TurnEvent(
                        priority=3,
                        category="unit",
                        message=f"New unit: {ua.name} ({ua.unit_type}) at ({ua.x},{ua.y}).",
                    )
                )

        # --- City events ---
        for cid, cb in before.cities.items():
            if cid not in after.cities:
                events.append(
                    lq.TurnEvent(
                        priority=1,
                        category="city",
                        message=f"City {cb.name} was lost!",
                    )
                )
            else:
                ca = after.cities[cid]
                if ca.population > cb.population:
                    events.append(
                        lq.TurnEvent(
                            priority=3,
                            category="city",
                            message=f"{ca.name} grew to population {ca.population}.",
                        )
                    )
                if (
                    cb.currently_building != "NONE"
                    and ca.currently_building != cb.currently_building
                ):
                    events.append(
                        lq.TurnEvent(
                            priority=2,
                            category="city",
                            message=f"{ca.name} finished building {cb.currently_building}. Now: {ca.currently_building if ca.currently_building != 'NONE' else 'nothing (queue empty)'}.",
                        )
                    )

        for cid, ca in after.cities.items():
            if cid not in before.cities:
                events.append(
                    lq.TurnEvent(
                        priority=2,
                        category="city",
                        message=f"New city founded: {ca.name}!",
                    )
                )

        # --- Research/civic events ---
        if (
            before.current_research != "None"
            and after.current_research != before.current_research
        ):
            events.append(
                lq.TurnEvent(
                    priority=2,
                    category="research",
                    message=f"Research complete: {before.current_research}! Now: {after.current_research}.",
                )
            )

        if (
            before.current_civic != "None"
            and after.current_civic != before.current_civic
        ):
            events.append(
                lq.TurnEvent(
                    priority=2,
                    category="civic",
                    message=f"Civic complete: {before.current_civic}! Now: {after.current_civic}.",
                )
            )

        # --- Stockpile events ---
        before_stk = {s.name: s for s in before.stockpiles}
        after_stk = {s.name: s for s in after.stockpiles}
        for name, sa in after_stk.items():
            sb = before_stk.get(name)
            if sb and sb.amount > 0 and sa.amount == 0:
                net = sa.per_turn - sa.demand + sa.imported
                events.append(
                    lq.TurnEvent(
                        priority=2,
                        category="resources",
                        message=f"DEPLETED: {name} stockpile hit 0 ({net:+d}/t) — units requiring {name} may be disbanded.",
                    )
                )

        events.sort(key=lambda e: e.priority)
        return events

    @staticmethod
    def _build_turn_report(
        turn_before: int,
        turn_after: int,
        events: list[lq.TurnEvent],
        notifications: list[lq.GameNotification],
        stockpiles: list[lq.ResourceStockpile] | None = None,
    ) -> str:
        """Format turn events and notifications into a scannable report."""
        lines = [f"Turn {turn_before} -> {turn_after}"]

        if stockpiles:
            visible = [
                s for s in stockpiles if s.amount > 0 or s.per_turn > 0 or s.demand > 0
            ]
            if visible:
                parts = []
                for s in visible:
                    net = s.per_turn - s.demand + s.imported
                    parts.append(f"{s.name} {s.amount}/{s.cap} ({net:+d}/t)")
                lines.append(f"Resources: {', '.join(parts)}")

        if events:
            lines.append("")
            lines.append("== Events ==")
            icons = {1: "!!!", 2: ">>", 3: "--"}
            for e in events:
                icon = icons.get(e.priority, "--")
                lines.append(f"  {icon} {e.message}")

        # Use the enriched is_action_required field from the parser
        action_required = [n for n in notifications if n.is_action_required]
        # Only show informational notifications from the last 2 turns — older ones
        # are stale (e.g. "Wonder Completed" from 3 turns ago) and clutter the report.
        recent_cutoff = (turn_after or 0) - 2
        info_notifs = [
            n
            for n in notifications
            if not n.is_action_required and n.turn >= recent_cutoff
        ]

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
        from civ_mcp.end_turn import execute_end_turn

        return await execute_end_turn(self)

    async def dismiss_popup(self) -> str:
        """Dismiss any blocking popup or UI overlay."""
        from civ_mcp.game_lifecycle import dismiss_popup

        return await dismiss_popup(self.conn)

    async def quicksave(self) -> str:
        """Create a quick-save."""
        from civ_mcp.game_lifecycle import quicksave

        return await quicksave(self.conn)

    async def list_saves(self) -> str:
        """List available save files."""
        from civ_mcp.game_lifecycle import list_saves

        return await list_saves(self.conn)

    async def load_save(self, save_index: int) -> str:
        """Load a save file by index."""
        from civ_mcp.game_lifecycle import load_save

        return await load_save(self.conn, save_index)

    async def execute_lua(self, code: str, context: str = "gamecore") -> str:
        """Escape hatch: run arbitrary Lua code."""
        from civ_mcp.game_lifecycle import execute_lua

        return await execute_lua(self.conn, code, context)


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


def _extract_pre_hp(result: str) -> int | None:
    """Extract pre-attack enemy HP from attack result line."""
    import re

    # Ranged/city: pre_hp:80/100
    m = re.search(r"pre_hp:(\d+)/", result)
    if m:
        return int(m.group(1))
    # Melee: enemy HP:100 -> 80/100
    m = re.search(r"enemy HP:(\d+) ->", result)
    if m:
        return int(m.group(1))
    return None


def _extract_post_hp(followup_lines: list[str]) -> int | None:
    """Extract post-combat enemy HP from followup query lines.

    Followup format: UNIT|UNIT_TYPE|hp/max|owner:N
    Returns HP of first unit found (None if eliminated).
    """
    for line in followup_lines:
        if line.startswith("UNIT|"):
            parts = line.split("|")
            if len(parts) >= 3:
                hp_part = parts[2].split("/")[0]
                try:
                    return int(hp_part)
                except ValueError:
                    pass
    return None
