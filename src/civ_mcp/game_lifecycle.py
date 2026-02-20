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

    # Phase 2: ALWAYS check ExclusivePopupManager popups — they need Close()
    # in their OWN Lua state to release engine lock.  Phase 1's SetHide()
    # does NOT release this lock, so we must run Phase 2 even if Phase 1
    # found/hid a popup.  These have their own state index (not accessible
    # from InGame).
    #
    # Phase 1 no longer hides ExclusivePopup types (they were removed from
    # the Phase 1 list), so the IsHidden check here works correctly.
    # We guard with IsHidden to avoid calling Close() on inactive popups,
    # which would corrupt BulkHide counters.
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
                    "Popup check failed for %s (state %d): %s", name, state_idx, e
                )
                break

    # Phase 3: Fallback — if InGame still sees visible ExclusivePopups,
    # probe state indexes to find and close them.  This handles cases where
    # lua_states from the handshake is incomplete (truncated LSQ response).
    exclusive_popup_names = [
        "NaturalWonderPopup",
        "NaturalDisasterPopup",
        "WonderBuiltPopup",
        "EraCompletePopup",
        "ProjectBuiltPopup",
        "RockBandPopup",
        "RockBandMoviePopup",
    ]
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
            l.split("|", 1)[1] for l in still_visible if l.startswith("STILL_VISIBLE|")
        ]
        if remaining:
            log.info(
                "Phase 3: ExclusivePopups still visible after Phase 2: %s "
                "(probing state indexes...)",
                remaining,
            )
            # Probe state indexes 50-200 to find the popup states
            for probe_idx in range(50, 200):
                if probe_idx in popup_states:
                    continue  # already checked in Phase 2
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
                    # Found it! Close the popup
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
                        dismissed.append(f"{state_name} (probed state {probe_idx})")
                        remaining.remove(state_name)
                        # Cache this state for future use
                        conn.lua_states[probe_idx] = state_name
                        log.info(
                            "Phase 3: Dismissed %s at state %d", state_name, probe_idx
                        )
                except Exception:
                    pass  # state doesn't exist or errored
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


async def list_saves(conn: GameConnection) -> str:
    """Query available saves (normal + autosave + quicksave).

    Tries Lua-based in-game query first, falls back to filesystem scan.
    Returns a list of save names. Use load_save(index) to load one.
    """
    result = await _list_saves_lua(conn)
    if result is not None:
        return result

    # Fallback: direct filesystem scan
    return _list_saves_filesystem()


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
