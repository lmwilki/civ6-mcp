"""End-turn state machine — snapshot, blocker resolution, turn advancement."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import civ_mcp.narrate as nr
from civ_mcp import lua as lq
from civ_mcp.connection import LuaError

if TYPE_CHECKING:
    from civ_mcp.game_state import GameState

log = logging.getLogger(__name__)


async def _get_turn_number(gs: GameState) -> int | None:
    """Read the current game turn number."""
    try:
        lines = await gs.conn.execute_read(
            'print(Game.GetCurrentGameTurn()); print("---END---")'
        )
        if lines:
            return int(lines[0])
    except (LuaError, ValueError, IndexError):
        pass
    return None


async def _check_victory_proximity(gs: GameState) -> list[lq.TurnEvent]:
    """Lightweight per-turn check for foreign victory threats."""
    events: list[lq.TurnEvent] = []
    lines = await gs.conn.execute_write(lq.build_victory_proximity_query())
    for line in lines:
        if line.startswith("REL_THREAT|"):
            parts = line.split("|")
            if len(parts) >= 4:
                civ_name, rel_name = parts[1], parts[2]
                count, total = int(parts[3]), int(parts[4])
                if count >= total:
                    events.append(
                        lq.TurnEvent(
                            priority=1,
                            category="victory",
                            message=f"!!! RELIGIOUS VICTORY IMMINENT: {civ_name}'s {rel_name} is majority in ALL {total} civilizations!",
                        )
                    )
                elif count >= total - 1:
                    events.append(
                        lq.TurnEvent(
                            priority=1,
                            category="victory",
                            message=f"!! RELIGIOUS VICTORY THREAT: {civ_name}'s {rel_name} is majority in {count}/{total} civilizations!",
                        )
                    )
        elif line.startswith("DIPLO_THREAT|"):
            parts = line.split("|")
            if len(parts) >= 3:
                events.append(
                    lq.TurnEvent(
                        priority=1,
                        category="victory",
                        message=f"!! DIPLOMATIC VICTORY THREAT: {parts[1]} has {parts[2]}/20 Diplomatic Victory Points!",
                    )
                )
        elif line.startswith("SCI_THREAT|"):
            parts = line.split("|")
            if len(parts) >= 4:
                vp, needed = int(parts[2]), int(parts[3])
                if vp >= needed - 1:
                    events.append(
                        lq.TurnEvent(
                            priority=1,
                            category="victory",
                            message=f"!! SCIENCE VICTORY IMMINENT: {parts[1]} has {vp}/{needed} space race projects!",
                        )
                    )
                elif vp >= 1:
                    events.append(
                        lq.TurnEvent(
                            priority=2,
                            category="victory",
                            message=f"Science race: {parts[1]} has {vp}/{needed} space race projects.",
                        )
                    )
    return events


async def execute_end_turn(gs: GameState) -> str:
    """End the turn with snapshot-diff event detection."""
    # 0. Game-over check — don't try to advance a finished game
    gameover = await gs.check_game_over()
    if gameover is not None:
        vtype = gameover.victory_type.replace("VICTORY_", "").replace("_", " ").title()
        if gameover.is_defeat:
            return (
                f"GAME OVER — DEFEAT. {gameover.winner_name} won a {vtype} victory. "
                f"The game has ended. Use load_save to reload an earlier save, or start a new game."
            )
        else:
            return (
                f"GAME OVER — VICTORY! You won a {vtype} victory! The game has ended."
            )

    # Record turn number at entry so we can detect external advancement
    # (e.g. game auto-ends turn when skip_remaining_units finishes all moves)
    turn_at_entry = await _get_turn_number(gs)

    # 1. Diplomacy sessions block turn advancement
    sessions = await gs.get_diplomacy_sessions()
    if sessions:
        session_info = []
        for s in sessions:
            phase = "goodbye" if s.buttons == "GOODBYE" else "active"
            session_info.append(f"{s.other_civ_name} ({s.other_leader_name}) [{phase}]")
        return (
            f"Cannot end turn: diplomacy encounter pending with {', '.join(session_info)}. "
            f"Use respond_to_diplomacy to handle it."
        )

    # 1b. Check for incoming trade deal offers (e.g. delegations from other civs)
    try:
        deals = await gs.get_pending_deals()
        if deals:
            return (
                "Cannot end turn: incoming trade deal pending.\n"
                + nr.narrate_pending_deals(deals)
            )
    except Exception:
        log.debug("Pending deal check failed", exc_info=True)

    # 2. Pre-dismiss any ExclusivePopupManager popups (wonder, disaster, era)
    # that may hold engine locks blocking turn advancement.
    try:
        pre_dismiss = await gs.dismiss_popup()
        if "Dismissed" in pre_dismiss:
            log.info("Pre-turn popup dismissed: %s", pre_dismiss)
    except Exception:
        log.debug("Pre-turn dismiss failed", exc_info=True)

    # 2b. World Congress gate — if WC fires this turn and no handler is
    #     registered, block end_turn and tell the agent to vote first.
    #     The WC session opens+closes within ACTION_ENDTURN synchronously,
    #     so we MUST register a handler BEFORE sending ACTION_ENDTURN.
    try:
        wc_status = await gs.get_world_congress()
        if wc_status.turns_until_next <= 0 or wc_status.is_in_session:
            handler_lines = await gs.conn.execute_write(
                f'print(__civmcp_wc_handler and "HANDLER_SET" or "NO_HANDLER"); '
                f'print("{lq.SENTINEL}")'
            )
            handler_set = any("HANDLER_SET" in l for l in handler_lines)
            if not handler_set:
                n_res = len(wc_status.resolutions) if wc_status.resolutions else 0
                return (
                    f"World Congress fires this turn ({n_res} resolution(s), {wc_status.favor} favor). "
                    f"Use get_world_congress() to review resolutions and targets, "
                    f"then queue_wc_votes() to register your votes, "
                    f"then call end_turn() again."
                )
    except Exception:
        log.debug("WC imminence check failed", exc_info=True)

    # 3. Check ALL EndTurnBlocking notifications at once, auto-resolve soft
    #    blockers, and report remaining hard blockers in a single message.
    for _round in range(3):
        try:
            blocking_lines = await gs.conn.execute_write(
                lq.build_end_turn_blocking_query()
            )
            blockers = lq.parse_end_turn_blocking(blocking_lines)
            if not blockers:
                break  # nothing blocking

            resolved_any = False
            hard_blockers: list[tuple[str, str]] = []

            for blocking_type, blocking_msg in blockers:
                # --- Auto-resolvable soft blockers ---

                if blocking_type == "ENDTURN_BLOCKING_GOVERNOR_IDLE":
                    await gs.conn.execute_write(
                        f"local me = Game.GetLocalPlayer(); "
                        f"local list = NotificationManager.GetList(me); "
                        f"if list then "
                        f"  for _, nid in ipairs(list) do "
                        f"    local e = NotificationManager.Find(me, nid); "
                        f"    if e and not e:IsDismissed() then "
                        f"      local bt = e:GetEndTurnBlocking(); "
                        f"      if bt and bt == EndTurnBlockingTypes.ENDTURN_BLOCKING_GOVERNOR_IDLE then "
                        f"        pcall(function() NotificationManager.SendActivated(me, nid) end); "
                        f"        pcall(function() NotificationManager.Dismiss(me, nid) end) "
                        f"      end "
                        f"    end "
                        f"  end "
                        f"end; "
                        f'print("OK"); print("{lq.SENTINEL}")'
                    )
                    resolved_any = True
                    continue

                if blocking_type == "ENDTURN_BLOCKING_CONSIDER_GOVERNMENT_CHANGE":
                    await gs.conn.execute_write(
                        f"local me = Game.GetLocalPlayer(); "
                        f"Players[me]:GetCulture():SetGovernmentChangeConsidered(true); "
                        f'print("OK"); print("{lq.SENTINEL}")'
                    )
                    resolved_any = True
                    continue

                if blocking_type == "ENDTURN_BLOCKING_WORLD_CONGRESS_LOOK":
                    await gs.conn.execute_write(
                        f"local me = Game.GetLocalPlayer(); "
                        f"UI.RequestPlayerOperation(me, PlayerOperations.WORLD_CONGRESS_LOOKED_AT_AVAILABLE, {{}}); "
                        f"local list = NotificationManager.GetList(me); "
                        f"if list then "
                        f"  for _, nid in ipairs(list) do "
                        f"    pcall(function() "
                        f"      local e = NotificationManager.Find(me, nid); "
                        f"      if e and not e:IsDismissed() then "
                        f"        local bt = e:GetEndTurnBlocking(); "
                        f"        if bt and bt == EndTurnBlockingTypes.ENDTURN_BLOCKING_WORLD_CONGRESS_LOOK then "
                        f"          NotificationManager.Dismiss(me, nid) "
                        f"        end "
                        f"      end "
                        f"    end) "
                        f"  end "
                        f"end; "
                        f'local i = ContextPtr:LookUpControl("/InGame/WorldCongressIntro"); '
                        f"if i then i:SetHide(true) end; "
                        f'local p = ContextPtr:LookUpControl("/InGame/WorldCongressPopup"); '
                        f"if p then p:SetHide(true) end; "
                        f'print("OK"); print("{lq.SENTINEL}")'
                    )
                    resolved_any = True
                    continue

                if blocking_type == "ENDTURN_BLOCKING_WORLD_CONGRESS_SESSION":
                    # NEVER auto-resolve session blockers — the agent must
                    # call get_world_congress() and vote_world_congress()
                    # to deploy diplomatic favor strategically.
                    hard_blockers.append((blocking_type, blocking_msg))
                    continue

                # Catch-all for any other World Congress blocking types
                # (e.g. special session proposals, emergency discussions)
                # Replicates the game UI's "Pass" button: LOOKED_AT_AVAILABLE
                # + dismiss all WC-related blocking notifications.
                if "WORLD_CONGRESS" in blocking_type:
                    try:
                        wc_dismiss_lines = await gs.conn.execute_write(
                            f"local me = Game.GetLocalPlayer(); "
                            f"UI.RequestPlayerOperation(me, PlayerOperations.WORLD_CONGRESS_LOOKED_AT_AVAILABLE, {{}}); "
                            f"local dismissed = 0; "
                            f"local list = NotificationManager.GetList(me); "
                            f"if list then "
                            f"  for _, nid in ipairs(list) do "
                            f"    pcall(function() "
                            f"      local e = NotificationManager.Find(me, nid); "
                            f"      if e and not e:IsDismissed() then "
                            f"        local bt = e:GetEndTurnBlocking(); "
                            f"        if bt and bt ~= 0 then "
                            f"          for k, v in pairs(EndTurnBlockingTypes) do "
                            f'            if v == bt and k:find("WORLD_CONGRESS") then '
                            f"              NotificationManager.Dismiss(me, nid); "
                            f"              dismissed = dismissed + 1; "
                            f"              break "
                            f"            end "
                            f"          end "
                            f"        end "
                            f"      end "
                            f"    end) "
                            f"  end "
                            f"end; "
                            f'local i = ContextPtr:LookUpControl("/InGame/WorldCongressIntro"); '
                            f"if i then i:SetHide(true) end; "
                            f'local p = ContextPtr:LookUpControl("/InGame/WorldCongressPopup"); '
                            f"if p then p:SetHide(true) end; "
                            f'print("DISMISSED:" .. dismissed); print("{lq.SENTINEL}")'
                        )
                        if any(
                            "DISMISSED:" in l and not l.endswith(":0")
                            for l in wc_dismiss_lines
                        ):
                            resolved_any = True
                            log.info("Auto-dismissed WC blocker: %s", blocking_type)
                            continue
                    except Exception:
                        log.debug("WC catch-all auto-resolve failed", exc_info=True)
                    hard_blockers.append((blocking_type, blocking_msg))
                    continue

                if blocking_type == "ENDTURN_BLOCKING_CONSIDER_DISLOYAL_CITY":
                    try:
                        result = await gs.resolve_city_capture("keep")
                        if "Error" not in result:
                            log.info("Auto-kept disloyal city: %s", result)
                            resolved_any = True
                            continue
                    except Exception:
                        log.debug("Disloyal city auto-resolve failed", exc_info=True)
                    hard_blockers.append((blocking_type, blocking_msg))
                    continue

                if blocking_type == "ENDTURN_BLOCKING_CONSIDER_RAZE_CITY":
                    try:
                        result = await gs.resolve_city_capture("keep")
                        if "Error" not in result:
                            log.info("Auto-kept captured city: %s", result)
                            resolved_any = True
                            continue
                    except Exception:
                        log.debug("Captured city auto-resolve failed", exc_info=True)
                    hard_blockers.append((blocking_type, blocking_msg))
                    continue

                if blocking_type == "ENDTURN_BLOCKING_GIVE_INFLUENCE_TOKEN":
                    try:
                        envoy_lines = await gs.conn.execute_write(
                            f"local me = Game.GetLocalPlayer(); "
                            f"local inf = Players[me]:GetInfluence(); "
                            f"local tokens = inf:GetTokensToGive(); "
                            f"if tokens == 0 then "
                            f"  inf:SetGivingTokensConsidered(true); "
                            f'  print("AUTO_RESOLVED"); '
                            f'else print("HAS_TOKENS|" .. tokens); end; '
                            f'print("{lq.SENTINEL}")'
                        )
                        if any("AUTO_RESOLVED" in l for l in envoy_lines):
                            resolved_any = True
                            continue
                    except Exception:
                        log.debug("Envoy auto-resolve failed", exc_info=True)
                    hard_blockers.append((blocking_type, blocking_msg))
                    continue

                if blocking_type == "ENDTURN_BLOCKING_PRODUCTION":
                    try:
                        corruption_lines = await gs.conn.execute_write(
                            f"local me = Game.GetLocalPlayer(); "
                            f"local corrupted = {{}}; "
                            f"for i, c in Players[me]:GetCities():Members() do "
                            f"  local bq = c:GetBuildQueue(); "
                            f"  if bq:GetSize() > 0 and bq:GetCurrentProductionTypeHash() == 0 then "
                            f'    table.insert(corrupted, Locale.Lookup(c:GetName()) .. " (id:" .. c:GetID() .. ")") '
                            f"  end "
                            f"end; "
                            f"if #corrupted > 0 then "
                            f'  print("CORRUPTED|" .. table.concat(corrupted, ",")) '
                            f'else print("CLEAN") end; '
                            f'print("{lq.SENTINEL}")'
                        )
                        is_corrupted = any(
                            cl.startswith("CORRUPTED|") for cl in corruption_lines
                        )
                        if is_corrupted:
                            city_names = next(
                                cl.split("|", 1)[1]
                                for cl in corruption_lines
                                if cl.startswith("CORRUPTED|")
                            )
                            dismiss_lines = await gs.conn.execute_write(
                                f"local me = Game.GetLocalPlayer(); "
                                f"local dismissed = 0; "
                                f"local list = NotificationManager.GetList(me); "
                                f"if list then "
                                f"  for _, nid in ipairs(list) do "
                                f"    local e = NotificationManager.Find(me, nid); "
                                f"    if e and not e:IsDismissed() then "
                                f"      local bt = e:GetEndTurnBlocking(); "
                                f"      if bt and bt == EndTurnBlockingTypes.ENDTURN_BLOCKING_PRODUCTION then "
                                f"        NotificationManager.Dismiss(me, nid); dismissed = dismissed + 1 "
                                f"      end "
                                f"    end "
                                f"  end "
                                f"end; "
                                f'print("DISMISSED|" .. dismissed); '
                                f'print("{lq.SENTINEL}")'
                            )
                            if any(
                                "DISMISSED|" in l and not l.endswith("|0")
                                for l in dismiss_lines
                            ):
                                log.info(
                                    "Auto-dismissed corrupted production for: %s",
                                    city_names,
                                )
                                resolved_any = True
                                continue
                    except Exception:
                        log.debug("Corruption check failed", exc_info=True)
                    hard_blockers.append((blocking_type, blocking_msg))
                    continue

                # --- Stale research/civic notifications ---
                # If tech/civic is already set but the notification persists,
                # force-dismiss it (set_research may have been called but
                # the notification wasn't cleared — e.g. before MCP restart).
                if blocking_type in (
                    "ENDTURN_BLOCKING_RESEARCH",
                    "ENDTURN_BLOCKING_CIVIC",
                ):
                    try:
                        dismiss_lua = (
                            f"local me = Game.GetLocalPlayer() "
                            f"local pTechs = Players[me]:GetTechs() "
                            f"local pCulture = Players[me]:GetCulture() "
                            f"local researching = pTechs:GetResearchingTech() "
                            f"local civicing = pCulture:GetProgressingCivic() "
                            f"local isSet = false "
                            f'if "{blocking_type}" == "ENDTURN_BLOCKING_RESEARCH" and researching >= 0 then isSet = true end '
                            f'if "{blocking_type}" == "ENDTURN_BLOCKING_CIVIC" and civicing >= 0 then isSet = true end '
                            f"if isSet then "
                            f"  local list = NotificationManager.GetList(me) "
                            f"  if list then "
                            f"    for _, nid in ipairs(list) do "
                            f"      local e = NotificationManager.Find(me, nid) "
                            f"      if e and not e:IsDismissed() then "
                            f"        local bt = e:GetEndTurnBlocking() "
                            f"        if bt and bt == EndTurnBlockingTypes.{blocking_type} then "
                            f"          pcall(function() NotificationManager.SendActivated(me, nid) end) "
                            f"          pcall(function() NotificationManager.Dismiss(me, nid) end) "
                            f"        end "
                            f"      end "
                            f"    end "
                            f"  end "
                            f'  print("AUTO_CLEARED") '
                            f'else print("NOT_SET") end '
                            f'print("{lq.SENTINEL}")'
                        )
                        result_lines = await gs.conn.execute_write(dismiss_lua)
                        if any("AUTO_CLEARED" in l for l in result_lines):
                            resolved_any = True
                            continue
                    except Exception:
                        log.debug(
                            "Research/civic notification auto-clear failed",
                            exc_info=True,
                        )
                    # Research/civic was unset — add diagnostic hint
                    kind = "tech" if "RESEARCH" in blocking_type else "civic"
                    enhanced_msg = (
                        (
                            f"{blocking_msg} (no {kind} selected — "
                            f"this can happen after diplomacy events or tech completion)"
                        )
                        if blocking_msg
                        else (
                            f"No {kind} selected — "
                            f"this can happen after diplomacy events or tech completion"
                        )
                    )
                    hard_blockers.append((blocking_type, enhanced_msg))
                    continue

                # --- Stale promotion notifications ---
                # GameCore SetPromotion doesn't clear InGame notification.
                # If no units actually need promotion, auto-dismiss.
                # NOTE: exp:CanPromote() is nil in InGame — must use GameCore (execute_read).
                if blocking_type == "ENDTURN_BLOCKING_UNIT_PROMOTION":
                    try:
                        # Step 1: GameCore check — CanPromote() works here.
                        # Mirrors build_unit_promotions_query logic across all units.
                        check_lines = await gs.conn.execute_read(
                            f"local me = Game.GetLocalPlayer(); "
                            f"local anyNeed = false; "
                            f"local prereqMap = {{}}; "
                            f"for row in GameInfo.UnitPromotionPrereqs() do "
                            f"  local pt = row.UnitPromotion; "
                            f"  if not prereqMap[pt] then prereqMap[pt] = {{}} end; "
                            f"  table.insert(prereqMap[pt], row.PrereqUnitPromotion) "
                            f"end; "
                            f"for i, u in Players[me]:GetUnits():Members() do "
                            f"  if u:GetX() ~= -9999 then "
                            f"    local exp = u:GetExperience(); "
                            f"    if exp then "
                            f"      local xp = exp:GetExperiencePoints(); "
                            f"      local thresh = exp:GetExperienceForNextLevel(); "
                            f"      if xp >= thresh then "
                            f"        local ui = GameInfo.Units[u:GetType()]; "
                            f'        local promClass = ui and ui.PromotionClass or ""; '
                            f'        if promClass ~= "" then '
                            f"          for promo in GameInfo.UnitPromotions() do "
                            f"            if promo.PromotionClass == promClass "
                            f"               and not exp:HasPromotion(promo.Index) then "
                            f"              local prereqs = prereqMap[promo.UnitPromotionType]; "
                            f"              local prereqMet = true; "
                            f"              if prereqs and #prereqs > 0 then "
                            f"                prereqMet = false; "
                            f"                for _, reqType in ipairs(prereqs) do "
                            f"                  local reqInfo = GameInfo.UnitPromotions[reqType]; "
                            f"                  if reqInfo and exp:HasPromotion(reqInfo.Index) then "
                            f"                    prereqMet = true; break "
                            f"                  end "
                            f"                end "
                            f"              end; "
                            f"              if prereqMet then "
                            f"                local canP = false; "
                            f"                pcall(function() canP = exp:CanPromote(promo.Index) end); "
                            f"                if canP then anyNeed = true; break end "
                            f"              end "
                            f"            end "
                            f"          end "
                            f"        end "
                            f"      end "
                            f"    end "
                            f"  end; "
                            f"  if anyNeed then break end "
                            f"end; "
                            f'print(anyNeed and "NEEDS_PROMO" or "NO_PROMO_NEEDED"); '
                            f'print("{lq.SENTINEL}")'
                        )
                        needs_promo = any("NEEDS_PROMO" in l for l in check_lines)
                        if not needs_promo:
                            # Step 2: InGame dismiss — NotificationManager is InGame-only.
                            await gs.conn.execute_write(
                                f"local me = Game.GetLocalPlayer(); "
                                f"local list = NotificationManager.GetList(me); "
                                f"if list then "
                                f"  for _, nid in ipairs(list) do "
                                f"    local e = NotificationManager.Find(me, nid); "
                                f"    if e and not e:IsDismissed() then "
                                f"      local bt = e:GetEndTurnBlocking(); "
                                f"      if bt and bt == EndTurnBlockingTypes.ENDTURN_BLOCKING_UNIT_PROMOTION then "
                                f"        pcall(function() NotificationManager.SendActivated(me, nid) end); "
                                f"        pcall(function() NotificationManager.Dismiss(me, nid) end) "
                                f"      end "
                                f"    end "
                                f"  end "
                                f"end; "
                                f'print("{lq.SENTINEL}")'
                            )
                            resolved_any = True
                            continue
                    except Exception:
                        log.debug(
                            "Promotion notification auto-clear failed", exc_info=True
                        )
                    hard_blockers.append((blocking_type, blocking_msg))
                    continue

                # --- Units blocking: auto-skip if all have 0 moves ---
                if blocking_type == "ENDTURN_BLOCKING_UNITS":
                    try:
                        check_lua = (
                            f"local me = Game.GetLocalPlayer(); "
                            f"local anyMoves = false; "
                            f"for _, u in Players[me]:GetUnits():Members() do "
                            f"  if u:GetX() ~= -9999 and u:GetMovesRemaining() > 0 then "
                            f"    anyMoves = true; break end end; "
                            f"if not anyMoves then "
                            f"  for _, u in Players[me]:GetUnits():Members() do "
                            f"    if u:GetX() ~= -9999 then UnitManager.FinishMoves(u) end "
                            f'  end; print("AUTO_SKIPPED") '
                            f'else print("UNITS_NEED_ORDERS") end; '
                            f'print("{lq.SENTINEL}")'
                        )
                        skip_lines = await gs.conn.execute_read(check_lua)
                        if any("AUTO_SKIPPED" in l for l in skip_lines):
                            resolved_any = True
                            continue
                    except Exception:
                        log.debug("Auto-skip 0-move units failed", exc_info=True)
                    hard_blockers.append((blocking_type, blocking_msg))
                    continue

                # --- Unrecognized blocker → always hard ---
                hard_blockers.append((blocking_type, blocking_msg))

            # If we have hard blockers, check if turn advanced externally
            # (e.g. game auto-end-turn after skip_remaining_units)
            if hard_blockers:
                turn_now = await _get_turn_number(gs)
                if (
                    turn_now is not None
                    and turn_at_entry is not None
                    and turn_now > turn_at_entry
                ):
                    log.info(
                        "Turn advanced externally (%s -> %s), skipping blocker report",
                        turn_at_entry,
                        turn_now,
                    )
                    break  # fall through to snapshot/diff flow

                # Ask the game if turn can actually end despite our blockers.
                # Safe here — we haven't started AI processing yet (pre-end-turn phase).
                try:
                    can_end_lines = await gs.conn.execute_write(
                        f"local can = UI.CanEndTurn(); "
                        f'print(can and "CAN_END" or "CANNOT_END"); '
                        f'print("{lq.SENTINEL}")'
                    )
                    if any(l == "CAN_END" for l in can_end_lines):
                        log.info(
                            "UI.CanEndTurn()=true despite blockers %s — proceeding",
                            [bt for bt, _ in hard_blockers],
                        )
                        break  # fall through to end_turn request
                except Exception:
                    log.debug("UI.CanEndTurn check failed", exc_info=True)

                lines_out: list[str] = ["Cannot end turn — resolve these blockers:"]
                for bt, bm in hard_blockers:
                    hint = lq.BLOCKING_TOOL_MAP.get(
                        bt, "Resolve the blocking notification"
                    )
                    display = (
                        bt.replace("ENDTURN_BLOCKING_", "").replace("_", " ").title()
                    )
                    line = f"  - {display}"
                    if bm:
                        line += f" ({bm})"
                    line += f"  ->  {hint}"
                    lines_out.append(line)
                return "\n".join(lines_out)

            # All blockers were soft-resolved — loop to re-check
            if resolved_any:
                continue
            break  # no blockers left
        except Exception:
            log.debug("Blocking check failed, proceeding anyway", exc_info=True)
            break

    # Take pre-turn snapshot
    try:
        snap_before = await gs._take_snapshot()
    except Exception:
        log.debug("Pre-turn snapshot failed", exc_info=True)
        snap_before = gs._last_snapshot

    # Pre-turn threat scan (for fog-of-war direction tracking)
    threats_before: list[lq.ThreatInfo] = []
    try:
        pre_threat_lines = await gs.conn.execute_read(
            lq.build_threat_scan_query()
        )
        threats_before = lq.parse_threat_scan_response(pre_threat_lines)
    except Exception:
        log.debug("Pre-turn threat scan failed", exc_info=True)

    turn_before = snap_before.turn if snap_before else await _get_turn_number(gs)

    # Request end turn
    lua = lq.build_end_turn()
    await gs.conn.execute_write(lua)

    # Poll for turn advancement using GameCore-only queries.
    # CRITICAL: Do NOT send InGame queries while AI civs are processing
    # their turns.  InGame queries (diplomacy sessions, UI.CanEndTurn,
    # popup dismissal) force context switches that can stall the AI
    # diplomacy subsystem, causing infinite hangs (seen in Games 1-5).
    turn_after = None
    advanced = False

    # Phase 1: Quick check (4s) — turn sometimes advances within 1-2s
    for _ in range(8):
        await asyncio.sleep(0.5)
        turn_after = await _get_turn_number(gs)
        if (
            turn_after is not None
            and turn_before is not None
            and turn_after > turn_before
        ):
            advanced = True
            break

    # Phase 2: Slow polling (30s) — AI can take 5-30s on large maps.
    # GameCore-only: _get_turn_number uses execute_read (GameCore context).
    if not advanced:
        for delay in [2.0, 2.0, 3.0, 3.0, 5.0, 5.0, 5.0, 5.0]:
            await asyncio.sleep(delay)
            turn_after = await _get_turn_number(gs)
            if (
                turn_after is not None
                and turn_before is not None
                and turn_after > turn_before
            ):
                advanced = True
                break

    # Phase 3: After 34s, now safe to check InGame state.
    # AI processing either completed (blocker is on our side) or is
    # truly hung.  Do ONE round of InGame checks, not a loop.
    if not advanced:
        # Check for AI diplomatic proposals
        try:
            mid_sessions = await gs.get_diplomacy_sessions()
            if mid_sessions:
                # DiplomacyActionView text can take 1-2s to populate after session
                # opens during AI processing. If text is empty, retry once.
                if any(not s.dialogue_text for s in mid_sessions):
                    await asyncio.sleep(2.0)
                    mid_sessions = await gs.get_diplomacy_sessions()
                session_info = []
                for s in mid_sessions:
                    phase = (
                        "deal"
                        if s.deal_summary
                        else ("goodbye" if s.buttons == "GOODBYE" else "active")
                    )
                    session_info.append(
                        f"{s.other_civ_name} ({s.other_leader_name}) [{phase}]"
                    )
                has_deal = any(s.deal_summary for s in mid_sessions)
                lines = [
                    f"Turn paused — AI diplomatic proposal from {', '.join(session_info)}.",
                ]
                for s in mid_sessions:
                    if s.dialogue_text:
                        lines.append(f'{s.other_civ_name} says: "{s.dialogue_text}"')
                    if s.reason_text:
                        lines.append(f"Reason: {s.reason_text}")
                    if s.deal_summary:
                        lines.append(f"Deal from {s.other_civ_name}: {s.deal_summary}")
                if has_deal:
                    lines.append(
                        "Use respond_to_trade(other_player_id=X, accept=True/False) to handle it, then end_turn again."
                    )
                else:
                    lines.append(
                        "Use respond_to_diplomacy to handle it, then end_turn again."
                    )
                return "\n".join(lines)
        except Exception:
            log.debug("Mid-turn diplomacy check failed", exc_info=True)

        # Check for incoming trade deals
        try:
            mid_deals = await gs.get_pending_deals()
            if mid_deals:
                return (
                    "Turn paused — incoming trade deal:\n"
                    + nr.narrate_pending_deals(mid_deals)
                )
        except Exception:
            log.debug("Mid-turn deal check failed", exc_info=True)

        # Single popup dismiss attempt (NOT a loop — looped dismissal
        # during AI processing was a primary cause of AI hangs).
        try:
            dismissed = await gs.dismiss_popup()
            if "Dismissed" in dismissed:
                log.info("Post-timeout popup dismissed: %s", dismissed)
                await gs.conn.execute_write(lua)
                for _ in range(5):
                    await asyncio.sleep(2.0)
                    turn_after = await _get_turn_number(gs)
                    if (
                        turn_after is not None
                        and turn_before is not None
                        and turn_after > turn_before
                    ):
                        advanced = True
                        break
        except Exception:
            log.debug("Post-timeout dismiss failed", exc_info=True)

    if not advanced:
        # Final verification — turn may have slipped through
        await asyncio.sleep(2.0)
        turn_after = await _get_turn_number(gs)
        if (
            turn_after is not None
            and turn_before is not None
            and turn_after > turn_before
        ):
            advanced = True

    if not advanced:
        # Check if game ended during turn transition (victory/defeat)
        gameover = await gs.check_game_over()
        if gameover is not None:
            vtype = (
                gameover.victory_type.replace("VICTORY_", "").replace("_", " ").title()
            )
            if gameover.is_defeat:
                return (
                    f"GAME OVER — DEFEAT. {gameover.winner_name} won a {vtype} victory. "
                    f"The game has ended. Use load_save to reload an earlier save, or start a new game."
                )
            else:
                return (
                    f"GAME OVER — VICTORY! You won a {vtype} victory! "
                    f"The game has ended."
                )

        # Provide specific blocker info instead of generic message
        details: list[str] = []
        try:
            sessions = await gs.get_diplomacy_sessions()
            if sessions:
                names = [s.other_civ_name for s in sessions]
                details.append(f"Open diplomacy session with: {', '.join(names)}")
        except Exception:
            pass
        try:
            blocking_lines = await gs.conn.execute_write(
                lq.build_end_turn_blocking_query()
            )
            blockers = lq.parse_end_turn_blocking(blocking_lines)
            for bt, bm in blockers:
                display = bt.replace("ENDTURN_BLOCKING_", "").replace("_", " ").title()
                details.append(f"Blocker: {display}" + (f" ({bm})" if bm else ""))
        except Exception:
            pass
        if details:
            return f"End turn blocked (turn {turn_after or turn_before}): {'; '.join(details)}"
        return f"End turn requested (turn is still {turn_after or turn_before}). Check get_pending_diplomacy or dismiss_popup."

    # Take post-turn snapshot and diff
    try:
        snap_after = await gs._take_snapshot()
        gs._last_snapshot = snap_after
    except Exception:
        log.debug("Post-turn snapshot failed", exc_info=True)
        return f"Turn {turn_before} -> {turn_after}"

    events: list[lq.TurnEvent] = []
    if snap_before:
        events = gs._diff_snapshots(snap_before, snap_after)

    # Query active notifications
    notifications: list[lq.GameNotification] = []
    try:
        notif_lines = await gs.conn.execute_write(lq.build_notifications_query())
        notifications = lq.parse_notifications_response(notif_lines)
    except Exception:
        log.debug("Notification query failed", exc_info=True)

    # Check for pending trade deals (AI may propose during their turn)
    try:
        deals = await gs.get_pending_deals()
        if deals:
            events.append(
                lq.TurnEvent(
                    priority=2,
                    category="diplomacy",
                    message=nr.narrate_pending_deals(deals),
                )
            )
    except Exception:
        log.debug("Trade deal check failed", exc_info=True)

    # Threat scan — check for hostile units near cities
    threats: list[lq.ThreatInfo] = []
    try:
        threat_lines = await gs.conn.execute_read(lq.build_threat_scan_query())
        threats = lq.parse_threat_scan_response(threat_lines)
        for t in threats:
            rs_str = f" RS:{t.ranged_strength}" if t.ranged_strength > 0 else ""
            events.append(
                lq.TurnEvent(
                    priority=2,
                    category="unit",
                    message=f"THREAT: {t.unit_type} CS:{t.combat_strength}{rs_str} HP:{t.hp}/{t.max_hp} spotted {t.distance} tiles away at ({t.x},{t.y})",
                )
            )
    except Exception:
        log.debug("Threat scan failed", exc_info=True)

    # Fog-of-war direction tracking — diff pre/post threats
    if threats_before:
        try:
            disappeared, _, _ = lq.diff_threats(threats_before, threats)
            if disappeared:
                positions = [(t.x, t.y) for t in disappeared]
                fog_lines = await gs.conn.execute_read(
                    lq.build_fog_neighbor_query(positions)
                )
                fog_dirs = lq.parse_fog_neighbor_response(fog_lines)
                for t in disappeared:
                    dirs = fog_dirs.get((t.x, t.y), [])
                    if dirs:
                        dir_str = "/".join(dirs)
                        msg = (
                            f"LOST CONTACT: {t.owner_name} {t.unit_type} "
                            f"HP:{t.hp}/{t.max_hp} last seen at ({t.x},{t.y}) "
                            f"— likely moved {dir_str} into fog"
                        )
                    else:
                        msg = (
                            f"VANISHED: {t.owner_name} {t.unit_type} "
                            f"HP:{t.hp}/{t.max_hp} last at ({t.x},{t.y}) "
                            f"— no adjacent fog (killed or garrisoned?)"
                        )
                    events.append(
                        lq.TurnEvent(priority=1, category="unit", message=msg)
                    )
        except Exception:
            log.debug("Fog direction tracking failed", exc_info=True)

    events.sort(key=lambda e: e.priority)

    # Victory proximity check (every turn — lightweight)
    try:
        victory_events = await _check_victory_proximity(gs)
        events.extend(victory_events)
    except Exception:
        log.debug("Victory proximity check failed", exc_info=True)

    # Every 10 turns: full victory progress snapshot
    if turn_after is not None and turn_after % 10 == 0:
        try:
            vp = await gs.get_victory_progress()
            summary = nr.narrate_victory_progress(vp)
            events.append(
                lq.TurnEvent(
                    priority=3,
                    category="victory",
                    message=f"10-TURN VICTORY SNAPSHOT (T{turn_after}):\n{summary}",
                )
            )
        except Exception:
            log.debug("10-turn victory check failed", exc_info=True)

    # Growth alerts from post-turn city state
    if snap_after:
        for cs in snap_after.cities.values():
            if cs.food_surplus < 0:
                events.append(
                    lq.TurnEvent(
                        priority=1,
                        category="city",
                        message=f"STARVING: {cs.name} ({cs.food_surplus:+.1f} food/t) — will lose population!",
                    )
                )
            elif cs.food_surplus == 0 and cs.turns_to_grow <= 0:
                events.append(
                    lq.TurnEvent(
                        priority=2,
                        category="city",
                        message=f"STAGNANT: {cs.name} (0 food surplus) — needs farm, granary, or trade route",
                    )
                )
            elif cs.turns_to_grow > 15:
                events.append(
                    lq.TurnEvent(
                        priority=3,
                        category="city",
                        message=f"SLOW GROWTH: {cs.name} ({cs.turns_to_grow}t to next pop, {cs.food_surplus:+.1f}/t)",
                    )
                )

    events.sort(key=lambda e: e.priority)
    return gs._build_turn_report(
        turn_before,
        turn_after,
        events,
        notifications,
        snap_after.stockpiles if snap_after else None,
    )
