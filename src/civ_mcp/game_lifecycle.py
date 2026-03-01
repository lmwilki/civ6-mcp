"""Game lifecycle — popup dismissal, save/load, raw Lua execution."""

from __future__ import annotations

import logging

from civ_mcp import lua as lq
from civ_mcp.connection import GameConnection

log = logging.getLogger(__name__)


async def dismiss_popup(conn: GameConnection) -> str:
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
    # NOTE: ExclusivePopupManager popups (NaturalDisaster, NaturalWonder,
    # WonderBuilt, EraComplete, RockBand, ProjectBuilt) are handled ONLY in
    # Phase 2 via Close() in their own Lua state.  Phase 1's SetHide() breaks
    # Phase 2's IsHidden check without releasing the PopupManager lock.
    popup_names = [
        "InGamePopup",
        "GenericPopup",
        "PopupDialog",
        "BoostUnlockedPopup",
        "GreatWorkShowcase",
        "WorldCongressPopup",
        "WorldCongressIntro",
    ]
    checks = []
    for name in popup_names:
        checks.append(
            f'do local c = ContextPtr:LookUpControl("/InGame/{name}") '
            f"if c and not c:IsHidden() then "
            f"  pcall(function() UIManager:DequeuePopup(c) end) "
            f"  pcall(function() Input.PopContext() end) "
            f"  c:SetHide(true) "
            f'  print("DISMISSED|{name}") '
            f"end end"
        )
    # LeaderScene 3D model: SetHide does NOT clear the C++ 3D viewport.
    # Must fire Events.HideLeaderScreen() to unload the 3D leader model.
    checks.append(
        'do local ls = ContextPtr:LookUpControl("/InGame/LeaderScene") '
        "if ls and not ls:IsHidden() then "
        "  pcall(function() Events.HideLeaderScreen() end) "
        "  ls:SetHide(true) "
        '  print("DISMISSED|LeaderScene") '
        "end end"
    )
    # Diplomacy screens: report only, do NOT close sessions.
    # Force-closing sessions via DiplomacyManager.CloseSession() bypasses
    # the C++ engine's session lifecycle callbacks, leaving the AI diplomacy
    # subsystem in an inconsistent state that causes turn processing hangs
    # (confirmed across Games 1-5).  Use respond_to_diplomacy() instead.
    checks.append(
        'do local dv = ContextPtr:LookUpControl("/InGame/DiplomacyActionView") '
        "if dv and not dv:IsHidden() then "
        '  print("PENDING|DiplomacyActionView") '
        "end end"
    )
    # NOTE: DiplomacyDealView is NOT dismissed here — it represents an
    # incoming trade deal offer that the agent must accept/reject via
    # get_pending_trades + respond_to_trade.  Dismissing it silently kills
    # the offer (e.g. incoming delegations from other civs).
    checks.append(
        'do local ddv = ContextPtr:LookUpControl("/InGame/DiplomacyDealView") '
        "if ddv and not ddv:IsHidden() then "
        '  print("PENDING|DiplomacyDealView") '
        "end end"
    )
    # Camera reset for cinematic mode
    checks.append(
        "local mode = UI.GetInterfaceMode() "
        "if mode == InterfaceModeTypes.CINEMATIC then "
        '  pcall(function() UI.ClearTemporaryPlotVisibility("NaturalDisaster") end) '
        '  pcall(function() UI.ClearTemporaryPlotVisibility("NaturalWonder") end) '
        "  pcall(function() Events.StopAllCameraAnimations() end) "
        "  pcall(function() UILens.RestoreActiveLens() end) "
        "  UI.SetInterfaceMode(InterfaceModeTypes.SELECTION) "
        '  print("DISMISSED|cinematic_camera") '
        "end"
    )
    pending_deal = False
    pending_diplomacy = False
    try:
        lua = " ".join(checks) + f' print("{lq.SENTINEL}")'
        lines = await conn.execute_write(lua)
        for line in lines:
            if line.startswith("DISMISSED|"):
                dismissed.append(line.split("|", 1)[1])
            elif line.startswith("PENDING|"):
                if "DiplomacyDealView" in line:
                    pending_deal = True
                elif "DiplomacyActionView" in line:
                    pending_diplomacy = True
    except Exception as e:
        log.debug("Phase 1 dismiss failed: %s", e)

    # Pre-check: single InGame call to detect visible ExclusivePopupManager
    # popups.  Phase 2 scans ~30 Lua states individually (~450ms each = ~13.5s)
    # to find these.  This pre-check costs one round-trip (~500ms) and skips
    # Phase 2+3 entirely when no ExclusivePopups are active (>99% of calls).
    exclusive_popup_names = [
        "NaturalWonderPopup",
        "NaturalDisasterPopup",
        "WonderBuiltPopup",
        "EraCompletePopup",
        "HistoricMoments",
        "MomentPopup",
        "ProjectBuiltPopup",
        "RockBandPopup",
        "RockBandMoviePopup",
    ]
    any_exclusive_visible = False
    try:
        precheck_lua = (
            " ".join(
                f'do local c = ContextPtr:LookUpControl("/InGame/{n}") '
                f'if c and not c:IsHidden() then print("EXCL_VISIBLE") end end'
                for n in exclusive_popup_names
            )
            + f' print("{lq.SENTINEL}")'
        )
        precheck_lines = await conn.execute_write(precheck_lua)
        any_exclusive_visible = any("EXCL_VISIBLE" in l for l in precheck_lines)
    except Exception as e:
        log.debug("ExclusivePopup pre-check failed (will run Phase 2): %s", e)
        any_exclusive_visible = True  # fail-open: scan if pre-check errors

    if any_exclusive_visible:
        log.info("ExclusivePopup visible — running Phase 2 state scan")

        # Phase 2: Close ExclusivePopupManager popups in their own Lua states.
        # These need Close() in their OWN state to release the engine lock —
        # Phase 1's SetHide() does NOT release this lock.
        popup_keywords = ("Popup", "Wonder", "Moment", "Era", "Disaster")
        popup_states = {
            idx: n
            for idx, n in conn.lua_states.items()
            if any(kw in n for kw in popup_keywords)
        }
        log.debug("Phase 2 popup states: %s", popup_states)
        for state_idx, name in popup_states.items():
            # Loop to drain the ExclusivePopupManager's engine queue —
            # each Close() pops the next event, so we keep closing until
            # the popup stays hidden (max 20 to avoid infinite loops).
            for _drain in range(20):
                try:
                    lines = await conn.execute_in_state(
                        state_idx,
                        "pcall(function() if m_kQueuedPopups then m_kQueuedPopups = {} end end); "
                        "if not ContextPtr:IsHidden() then "
                        "  local ok = pcall(Close); "
                        "  if not ok then pcall(OnClose) end; "
                        '  print("DISMISSED") '
                        "end; "
                        'print("---END---")',
                    )
                    if any("DISMISSED" in l for l in lines):
                        dismissed.append(name)
                    else:
                        break  # popup stayed hidden, queue drained
                except Exception as e:
                    log.debug(
                        "Popup check failed for %s (state %d): %s",
                        name,
                        state_idx,
                        e,
                    )
                    break

        # Phase 3: Fallback — if InGame still sees visible ExclusivePopups,
        # probe state indexes to find and close them.  Handles cases where
        # lua_states from the handshake is incomplete (truncated LSQ).
        try:
            check_lua = (
                " ".join(
                    f'do local c = ContextPtr:LookUpControl("/InGame/{n}") '
                    f'if c and not c:IsHidden() then print("STILL_VISIBLE|{n}") end end'
                    for n in exclusive_popup_names
                )
                + f' print("{lq.SENTINEL}")'
            )
            still_visible = await conn.execute_write(check_lua)
            remaining = [
                l.split("|", 1)[1]
                for l in still_visible
                if l.startswith("STILL_VISIBLE|")
            ]
            if remaining:
                log.info(
                    "Phase 3: ExclusivePopups still visible after Phase 2: %s "
                    "(probing state indexes...)",
                    remaining,
                )
                for probe_idx in range(50, 200):
                    if probe_idx in popup_states:
                        continue
                    if not remaining:
                        break
                    try:
                        probe_lines = await conn.execute_in_state(
                            probe_idx,
                            'print(ContextPtr:GetID()); print("---END---")',
                            timeout=1.0,
                        )
                        state_name = probe_lines[0] if probe_lines else ""
                        if state_name not in remaining:
                            continue
                        close_lines = await conn.execute_in_state(
                            probe_idx,
                            "pcall(function() if m_kQueuedPopups then m_kQueuedPopups = {} end end); "
                            "local ok = pcall(Close); "
                            "if not ok then pcall(OnClose) end; "
                            "ContextPtr:SetHide(true); "
                            'print("DISMISSED"); '
                            'print("---END---")',
                            timeout=2.0,
                        )
                        if any("DISMISSED" in l for l in close_lines):
                            dismissed.append(
                                f"{state_name} (probed state {probe_idx})"
                            )
                            remaining.remove(state_name)
                            conn.lua_states[probe_idx] = state_name
                            log.info(
                                "Phase 3: Dismissed %s at state %d",
                                state_name,
                                probe_idx,
                            )
                    except Exception:
                        pass
        except Exception as e:
            log.debug("Phase 3 probe failed: %s", e)

    if dismissed:
        msg = f"Dismissed: {', '.join(dismissed)}"
        if pending_diplomacy:
            msg += ". Also: diplomacy session active — use respond_to_diplomacy."
        if pending_deal:
            msg += " (incoming trade deal pending — use get_pending_trades)"
        return msg
    if pending_diplomacy:
        return "Diplomacy session active — use respond_to_diplomacy to handle it."
    if pending_deal:
        return "No popups to dismiss (incoming trade deal pending — use get_pending_trades)."
    return "No popups to dismiss."


# ------------------------------------------------------------------
# Save / Load
# ------------------------------------------------------------------


async def quicksave(conn: GameConnection) -> str:
    """Trigger a quicksave."""
    lines = await conn.execute_write(
        f"local gf = {{}}; "
        f'gf.Name = "quicksave"; '
        f"gf.Location = SaveLocations.LOCAL_STORAGE; "
        f"gf.Type = SaveTypes.SINGLE_PLAYER; "
        f"gf.IsAutosave = false; "
        f"gf.IsQuicksave = true; "
        f"Network.SaveGame(gf); "
        f'print("OK|quicksave"); '
        f'print("{lq.SENTINEL}")'
    )
    if any("OK|" in l for l in lines):
        return "Quicksave triggered."
    return "Quicksave may have failed: " + " ".join(lines)


async def save_game(conn: GameConnection, name: str) -> str:
    """Create a named save. Used for MCP per-turn autosaves."""
    lines = await conn.execute_write(
        f"local gf = {{}}; "
        f'gf.Name = "{name}"; '
        f"gf.Location = SaveLocations.LOCAL_STORAGE; "
        f"gf.Type = SaveTypes.SINGLE_PLAYER; "
        f"gf.IsAutosave = false; "
        f"gf.IsQuicksave = false; "
        f"Network.SaveGame(gf); "
        f'print("OK|{name}"); '
        f'print("{lq.SENTINEL}")'
    )
    if any("OK|" in l for l in lines):
        return f"Saved: {name}"
    return f"Save may have failed: {' '.join(lines)}"


def cleanup_old_autosaves(keep: int = 10) -> None:
    """Delete MCP autosaves older than the most recent `keep` saves."""
    import glob
    import os

    from .game_launcher import SINGLE_SAVE_DIR

    pattern = os.path.join(SINGLE_SAVE_DIR, "MCP_AutoSave_*.Civ6Save")
    saves = glob.glob(pattern)
    if len(saves) <= keep:
        return
    saves.sort(key=os.path.getmtime, reverse=True)
    for old in saves[keep:]:
        try:
            os.remove(old)
            log.debug("Deleted old MCP autosave: %s", old)
        except OSError as e:
            log.debug("Failed to delete %s: %s", old, e)


async def list_saves(conn: GameConnection) -> str:
    """List available saves (normal + autosave + quicksave).

    Uses filesystem scan (reliable — finds all save types including
    autosaves and quicksaves). Falls back to Lua query if filesystem
    scan finds nothing.
    """
    result = _list_saves_filesystem()
    if "No saves found" not in result:
        return result

    # Fallback: Lua-based query (may miss autosaves/quicksaves)
    lua_result = await _list_saves_lua(conn)
    if lua_result is not None:
        return lua_result
    return result


async def _list_saves_lua(conn: GameConnection) -> str | None:
    """Try Lua-based save enumeration. Returns None on failure."""
    try:
        await conn.execute_write(
            f"if not ExposedMembers then ExposedMembers = {{}} end; "
            f"ExposedMembers.MCPSaveList = nil; "
            f"ExposedMembers.MCPSaveQueryDone = false; "
            f"local function OnResults(fileList, qid) "
            f"  ExposedMembers.MCPSaveList = fileList; "
            f"  ExposedMembers.MCPSaveQueryDone = true; "
            f"  UI.CloseFileListQuery(qid); "
            f"  LuaEvents.FileListQueryResults.Remove(OnResults); "
            f"end; "
            f"LuaEvents.FileListQueryResults.Add(OnResults); "
            f"local opts = SaveLocationOptions.NORMAL + SaveLocationOptions.AUTOSAVE + SaveLocationOptions.QUICKSAVE + SaveLocationOptions.LOAD_METADATA; "
            f"UI.QuerySaveGameList(SaveLocations.LOCAL_STORAGE, SaveTypes.SINGLE_PLAYER, opts); "
            f'print("QUERY_SENT"); '
            f'print("{lq.SENTINEL}")'
        )

        import asyncio

        for _ in range(20):
            await asyncio.sleep(0.25)
            check_lines = await conn.execute_write(
                f"if ExposedMembers.MCPSaveQueryDone then "
                f"  local fl = ExposedMembers.MCPSaveList; "
                f"  if fl and #fl > 0 then "
                f'    print("COUNT|" .. #fl); '
                f"    for i, s in ipairs(fl) do "
                f'      if i <= 20 then print("SAVE|" .. i .. "|" .. tostring(s.Name)) end '
                f"    end "
                f'  else print("EMPTY") end '
                f'else print("PENDING") end; '
                f'print("{lq.SENTINEL}")'
            )
            if any(l.startswith("COUNT|") or l == "EMPTY" for l in check_lines):
                results = [l for l in check_lines if l.startswith("SAVE|")]
                if not results:
                    return None  # empty — fall through to filesystem
                lines_out = ["Available saves (use load_save with the index number):"]
                for r in results:
                    parts = r.split("|", 2)
                    idx = parts[1]
                    name = parts[2] if len(parts) > 2 else "?"
                    lines_out.append(f"  {idx}. {name}")
                return "\n".join(lines_out)
    except Exception:
        pass
    return None  # timed out or error — fall through to filesystem


def _list_saves_filesystem() -> str:
    """Scan the save directory on disk (always works)."""
    import glob
    import os

    from .game_launcher import SAVE_DIR

    save_base = os.path.dirname(SAVE_DIR)  # .../Saves/Single
    all_saves: list[tuple[float, str]] = []

    # Autosaves
    for f in glob.glob(os.path.join(SAVE_DIR, "*.Civ6Save")):
        all_saves.append((os.path.getmtime(f), os.path.basename(f)))

    # Normal saves (parent directory)
    for f in glob.glob(os.path.join(save_base, "*.Civ6Save")):
        all_saves.append((os.path.getmtime(f), os.path.basename(f)))

    all_saves.sort(reverse=True)  # newest first
    if not all_saves:
        return "No saves found on filesystem."

    lines = ["Available saves (filesystem scan, sorted by date):"]
    for i, (_mtime, name) in enumerate(all_saves[:25], 1):
        lines.append(f"  {i}. {name.replace('.Civ6Save', '')}")
    return "\n".join(lines)


async def load_save(conn: GameConnection, save_index: int) -> str:
    """Load a save by index from the most recent list_saves() query.

    The game will reload — the FireTuner connection stays alive but
    all Lua state is wiped. Wait a few seconds after calling this.
    """
    lines = await conn.execute_write(
        f"if not ExposedMembers or not ExposedMembers.MCPSaveList then "
        f'  print("ERR:NO_SAVE_LIST"); print("{lq.SENTINEL}"); return '
        f"end; "
        f"local fl = ExposedMembers.MCPSaveList; "
        f"local idx = {save_index}; "
        f"if idx < 1 or idx > #fl then "
        f'  print("ERR:INDEX_OUT_OF_RANGE|" .. #fl); print("{lq.SENTINEL}"); return '
        f"end; "
        f"local save = fl[idx]; "
        f'print("LOADING|" .. tostring(save.Name)); '
        f'print("{lq.SENTINEL}"); '
        f"Network.LeaveGame(); "
        f"Network.LoadGame(save, ServerType.SERVER_TYPE_NONE)"
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


async def load_game_save(conn: GameConnection, save_name: str) -> str:
    """Load a save by name — no list_saves() prerequisite.

    Two-tier approach:
    1. Lua: query save list, find by name, load in one async operation.
    2. Filesystem: verify file exists, use OCR menu navigation (slow but
       reliable — works for autosaves and quicksaves that Lua can't find).
    """
    import asyncio

    # Tier 1: Lua query-match-load
    try:
        await conn.execute_write(
            f"if not ExposedMembers then ExposedMembers = {{}} end; "
            f"ExposedMembers.MCPLoadResult = nil; "
            f"ExposedMembers.MCPLoadDone = false; "
            f"local function OnResults(fileList, qid) "
            f"  UI.CloseFileListQuery(qid); "
            f"  LuaEvents.FileListQueryResults.Remove(OnResults); "
            f"  for i, s in ipairs(fileList) do "
            f'    if s.Name == "{save_name}" then '
            f'      ExposedMembers.MCPLoadResult = "FOUND"; '
            f"      ExposedMembers.MCPLoadDone = true; "
            f"      Network.LeaveGame(); "
            f"      Network.LoadGame(s, ServerType.SERVER_TYPE_NONE); "
            f"      return "
            f"    end "
            f"  end; "
            f'  ExposedMembers.MCPLoadResult = "NOT_FOUND"; '
            f"  ExposedMembers.MCPLoadDone = true; "
            f"end; "
            f"LuaEvents.FileListQueryResults.Add(OnResults); "
            f"local opts = SaveLocationOptions.NORMAL + SaveLocationOptions.AUTOSAVE "
            f"  + SaveLocationOptions.QUICKSAVE + SaveLocationOptions.LOAD_METADATA; "
            f"UI.QuerySaveGameList(SaveLocations.LOCAL_STORAGE, SaveTypes.SINGLE_PLAYER, opts); "
            f'print("QUERY_SENT"); '
            f'print("{lq.SENTINEL}")'
        )

        for _ in range(20):
            await asyncio.sleep(0.25)
            check = await conn.execute_write(
                f"if ExposedMembers.MCPLoadDone then "
                f'  print("RESULT|" .. tostring(ExposedMembers.MCPLoadResult)) '
                f'else print("PENDING") end; '
                f'print("{lq.SENTINEL}")'
            )
            for line in check:
                if line == "RESULT|FOUND":
                    return (
                        f"Loading save: {save_name}. Game will reload — "
                        f"wait ~10 seconds then call get_game_overview to verify."
                    )
                if line == "RESULT|NOT_FOUND":
                    break  # fall through to Tier 2
            else:
                continue
            break  # NOT_FOUND — try filesystem

        log.info("Lua query did not find '%s', trying filesystem", save_name)
    except Exception:
        log.debug("Lua load_game_save failed", exc_info=True)

    # Tier 2: Filesystem verify + OCR menu load
    import os

    from .game_launcher import SAVE_DIR, SINGLE_SAVE_DIR

    auto_path = os.path.join(SAVE_DIR, f"{save_name}.Civ6Save")
    single_path = os.path.join(SINGLE_SAVE_DIR, f"{save_name}.Civ6Save")

    if not os.path.exists(auto_path) and not os.path.exists(single_path):
        return (
            f"Error: Save '{save_name}' not found in Lua query or on filesystem. "
            f"Check the name and try list_saves() to see available saves."
        )

    # File exists but Lua couldn't find it — use restart_and_load (OCR menu nav)
    from . import game_launcher

    log.info("Falling back to restart_and_load for '%s'", save_name)
    return await game_launcher.restart_and_load(save_name)


async def execute_lua(
    conn: GameConnection, code: str, context: str = "gamecore"
) -> str:
    """Escape hatch: run arbitrary Lua code."""
    if context == "ingame":
        lines = await conn.execute_write(code)
    elif context.isdigit():
        lines = await conn.execute_in_state(int(context), code)
    else:
        lines = await conn.execute_read(code)
    return "\n".join(lines) if lines else "(no output)"
