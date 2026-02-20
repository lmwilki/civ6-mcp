"""Diplomacy domain — Lua builders and parsers."""

from __future__ import annotations

from civ_mcp.lua._helpers import SENTINEL, _bail, _bail_lua, _lua_close_diplo_session
from civ_mcp.lua.models import CivInfo, DealItem, DealOptions, DiplomacyModifier, DiplomacySession, PendingDeal, VisibleCity


def build_diplomacy_query() -> str:
    """Rich diplomacy query — runs in InGame context for GetDiplomaticAI access."""
    return f"""
local me = Game.GetLocalPlayer()
local pDiplo = Players[me]:GetDiplomacy()
local pVis = PlayersVisibility[me]
local states = {{"ALLIED","DECLARED_FRIEND","FRIENDLY","NEUTRAL","UNFRIENDLY","DENOUNCED","WAR"}}
local checkActions = {{"DIPLOACTION_DIPLOMATIC_DELEGATION","DIPLOACTION_DECLARE_FRIENDSHIP","DIPLOACTION_DENOUNCE","DIPLOACTION_RESIDENT_EMBASSY","DIPLOACTION_OPEN_BORDERS","DIPLOACTION_MAKE_ALLIANCE"}}
for i = 0, 62 do
    if i ~= me and Players[i] and Players[i]:IsAlive() and Players[i]:IsMajor() then
        local cfg = PlayerConfigurations[i]
        local civName = Locale.Lookup(cfg:GetCivilizationShortDescription())
        local leaderName = Locale.Lookup(cfg:GetLeaderName())
        local met = pDiplo:HasMet(i) and "1" or "0"
        local war = pDiplo:IsAtWarWith(i) and "1" or "0"
        if pDiplo:HasMet(i) then
            local ai = Players[i]:GetDiplomaticAI()
            local stateIdx = ai:GetDiplomaticStateIndex(me)
            local stateName = states[stateIdx + 1] or tostring(stateIdx)
            local grievances = pDiplo:GetGrievancesAgainst(i)
            local vis = pDiplo:GetVisibilityOn(i)
            local hasDel = pDiplo:HasDelegationAt(i) and "1" or "0"
            local hasEmb = pDiplo:HasEmbassyAt(i) and "1" or "0"
            local theyDel = Players[i]:GetDiplomacy():HasDelegationAt(me) and "1" or "0"
            local theyEmb = Players[i]:GetDiplomacy():HasEmbassyAt(me) and "1" or "0"
            print("CIV|" .. i .. "|" .. civName .. "|" .. leaderName .. "|" .. met .. "|" .. war .. "|" .. stateName .. "|" .. grievances .. "|" .. vis .. "|" .. hasDel .. "|" .. hasEmb .. "|" .. theyDel .. "|" .. theyEmb)
            local okMil, milStr = pcall(function() return Players[i]:GetStats():GetMilitaryStrength() end)
            local okMyMil, myMilStr = pcall(function() return Players[me]:GetStats():GetMilitaryStrength() end)
            if okMil and okMyMil then print("MILITARY|" .. i .. "|" .. (milStr or 0) .. "|" .. (myMilStr or 0)) end
            local nCivCities = 0
            for _, ec in Players[i]:GetCities():Members() do
                nCivCities = nCivCities + 1
                local ecx, ecy = ec:GetX(), ec:GetY()
                if pVis:IsRevealed(ecx, ecy) then
                    local ecName = Locale.Lookup(ec:GetName())
                    local ecPop = ec:GetPopulation()
                    local ecLoy, ecLoyPT = 100, 0
                    local ecCult = ec:GetCulturalIdentity()
                    if ecCult then ecLoy = ecCult:GetLoyalty(); ecLoyPT = ecCult:GetLoyaltyPerTurn() end
                    local ecWalls, ecDef = 0, 0
                    pcall(function()
                        for _, d in ec:GetDistricts():Members() do
                            local di = GameInfo.Districts[d:GetType()]
                            if di and di.DistrictType == "DISTRICT_CITY_CENTER" then
                                ecWalls = d:GetMaxDamage(DefenseTypes.DISTRICT_OUTER) or 0
                                ecDef = ec:GetStrengthValue() or 0
                                break
                            end
                        end
                    end)
                    print("ECITY|" .. i .. "|" .. ecName:gsub("|","/") .. "|" .. ecx .. "," .. ecy .. "|" .. ecPop .. "|" .. string.format("%.0f|%.1f", ecLoy, ecLoyPT) .. "|" .. ecWalls .. "|" .. ecDef)
                end
            end
            print("CIVCITIES|" .. i .. "|" .. nCivCities)
            local mods = ai:GetDiplomaticModifiers(me)
            if mods then
                for _, mod in ipairs(mods) do
                    local txt = tostring(mod.Text):gsub("|", "/")
                    print("MOD|" .. i .. "|" .. mod.Score .. "|" .. txt)
                end
            end
            if stateIdx == 0 then
                local ok3, aType = pcall(function() return pDiplo:GetAllianceType(i) end)
                if ok3 and aType and aType >= 0 then
                    local aNames = {{"RESEARCH","CULTURAL","ECONOMIC","MILITARY","RELIGIOUS"}}
                    local aLevel = 1
                    pcall(function() aLevel = pDiplo:GetAllianceLevel(i) or 1 end)
                    print("ALLIANCE|" .. i .. "|" .. (aNames[aType+1] or tostring(aType)) .. "|" .. aLevel)
                end
            end
            local avail = {{}}
            for _, aName in ipairs(checkActions) do
                local ok2, valid = pcall(function() return pDiplo:IsDiplomaticActionValid(aName, i, false) end)
                if ok2 and valid then table.insert(avail, (aName:gsub("DIPLOACTION_", ""))) end
            end
            if #avail > 0 then print("ACTIONS|" .. i .. "|" .. table.concat(avail, ",")) end
            local okPact, hasPact = pcall(function() return Players[i]:GetDiplomacy():HasDefensivePact(me) end)
            if okPact and hasPact then print("PACT|" .. i .. "|DEFENSIVE") end
        else
            print("CIV|" .. i .. "|Unmet Civilization|Unknown Leader|" .. met .. "|" .. war .. "|UNKNOWN|0|0|0|0|0|0")
        end
    end
end
-- Scan for third-party defensive pacts
for i = 0, 62 do
    if i ~= me and Players[i] and Players[i]:IsAlive() and Players[i]:IsMajor() and pDiplo:HasMet(i) then
        for j = i+1, 62 do
            if j ~= me and Players[j] and Players[j]:IsAlive() and Players[j]:IsMajor() and pDiplo:HasMet(j) then
                local okP, hp = pcall(function() return Players[i]:GetDiplomacy():HasDefensivePact(j) end)
                if okP and hp then print("PACT|" .. i .. "|" .. j .. "|DEFENSIVE") end
            end
        end
    end
end
print("{SENTINEL}")
"""


def build_diplomacy_session_query() -> str:
    """Check for open diplomacy sessions and return choices (InGame context).

    Also reads the DiplomacyActionView UI controls to capture the leader's
    actual dialogue text, reason/agenda subtext, and visible button labels.
    Button info helps detect goodbye phase (only "Goodbye" button visible).
    """
    return f"""
local me = Game.GetLocalPlayer()
local found = false
local dialogueText = ""
local reasonText = ""
local ctrl1 = ContextPtr:LookUpControl("/InGame/DiplomacyActionView/LeaderResponseText")
local ctrl2 = ContextPtr:LookUpControl("/InGame/DiplomacyActionView/LeaderReasonText")
if ctrl1 then local ok, t = pcall(ctrl1.GetText, ctrl1); if ok and t and t ~= "" then dialogueText = t end end
if ctrl2 then local ok, t = pcall(ctrl2.GetText, ctrl2); if ok and t and t ~= "" then reasonText = t end end
local btnTexts = {{}}
for _, path in ipairs({{
    "/InGame/DiplomacyActionView/SelectionStack/Selection1Button/SelectionText",
    "/InGame/DiplomacyActionView/SelectionStack/Selection2Button/SelectionText",
}}) do
    local btn = ContextPtr:LookUpControl(path)
    if btn then
        local par = btn:GetParent()
        if par and not par:IsHidden() then
            local ok, t = pcall(btn.GetText, btn)
            if ok and t and t ~= "" then btnTexts[#btnTexts + 1] = t end
        end
    end
end
local goodbyeBtn = ContextPtr:LookUpControl("/InGame/DiplomacyActionView/GoodbyeButton")
if goodbyeBtn and not goodbyeBtn:IsHidden() then btnTexts[#btnTexts + 1] = "GOODBYE" end
local buttonInfo = table.concat(btnTexts, ";")
for i = 0, 62 do
    if i ~= me and Players[i] and Players[i]:IsAlive() then
        local sid = DiplomacyManager.FindOpenSessionID(me, i)
        if sid and sid >= 0 then
            local cfg = PlayerConfigurations[i]
            local civName = Locale.Lookup(cfg:GetCivilizationShortDescription())
            local leaderName = Locale.Lookup(cfg:GetLeaderName())
            print("SESSION|" .. sid .. "|" .. i .. "|" .. civName .. "|" .. leaderName .. "|" .. dialogueText .. "|" .. reasonText .. "|" .. buttonInfo)
            found = true
        end
    end
end
if not found then print("NONE") end
print("{SENTINEL}")
"""


def build_diplomacy_choices_query(other_player_id: int) -> str:
    """Get available dialogue choices for an open session with a specific player."""
    return f"""
local me = Game.GetLocalPlayer()
local sid = DiplomacyManager.FindOpenSessionID(me, {other_player_id})
if sid == nil or sid < 0 then {_bail("ERR:NO_SESSION")} end
print("SESSION|" .. sid)
local ctrl = ContextPtr:LookUpControl("/InGame/DiplomacyActionView")
local isVisible = ctrl and not ctrl:IsHidden() or false
print("VISIBLE|" .. tostring(isVisible))
for row in GameInfo.DiplomacySelections() do
    if string.find(row.Type, "FIRST_MEET") or string.find(row.Type, "GREETING") or string.find(row.Type, "DECLARE_FRIEND") or string.find(row.Type, "DENOUNCE") then
        local text = Locale.Lookup(row.Text)
        print("CHOICE|" .. row.Type .. "|" .. row.Key .. "|" .. text)
    end
end
print("{SENTINEL}")
"""


def build_diplomacy_respond(other_player_id: int, response: str) -> str:
    """Respond to a diplomacy session.

    response is 'POSITIVE', 'NEGATIVE', or 'EXIT'.
    EXIT closes the session directly (last-resort for orphaned sessions).
    POSITIVE/NEGATIVE sends AddResponse only — does NOT call CloseSession.
    The C++ engine handles session lifecycle through its own callbacks.
    Caller must check session state in a SEPARATE call to allow the engine
    time to process the response (same-frame checks see stale state).
    """
    return f"""
local me = Game.GetLocalPlayer()
local sid = DiplomacyManager.FindOpenSessionID(me, {other_player_id})
if sid == nil or sid < 0 then {_bail("ERR:NO_SESSION")} end
if "{response}" == "EXIT" then
    DiplomacyManager.CloseSession(sid)
    LuaEvents.DiplomacyActionView_ShowIngameUI()
    pcall(function() Events.HideLeaderScreen() end)
    print("OK:SESSION_CLOSED")
    print("{SENTINEL}"); return
end
DiplomacyManager.AddResponse(sid, me, "{response}")
print("OK:RESPONSE_SENT|{response}")
print("{SENTINEL}")
"""


def build_check_diplomacy_session_state(other_player_id: int) -> str:
    """Check if a diplomacy session is still open after AddResponse.

    Must be called in a SEPARATE TCP round-trip from AddResponse to give
    the C++ engine time to process the response and transition/close
    the session naturally.  Returns SESSION_OPEN or SESSION_CLOSED.
    """
    return f"""
local me = Game.GetLocalPlayer()
local sid = DiplomacyManager.FindOpenSessionID(me, {other_player_id})
if sid and sid >= 0 then
    print("SESSION_OPEN|" .. sid)
else
    pcall(function() LuaEvents.DiplomacyActionView_ShowIngameUI() end)
    pcall(function() Events.HideLeaderScreen() end)
    print("SESSION_CLOSED")
end
print("{SENTINEL}")
"""


def build_send_diplo_action(other_player_id: int, action_name: str) -> str:
    """Send a proactive diplomatic action and detect acceptance/rejection.

    action_name is e.g. DIPLOMATIC_DELEGATION, DECLARE_FRIENDSHIP, DENOUNCE,
    RESIDENT_EMBASSY, OPEN_BORDERS.

    Key discovery: RequestSession uses DIFFERENT action strings from DIPLOACTION_ names:
    - DECLARE_FRIENDSHIP -> session string "DECLARE_FRIEND" (not "DECLARE_FRIENDSHIP")
    - Others use same name as action_name

    Flow: RequestSession -> 2x AddResponse(POSITIVE) -> CloseSession
    No AddStatement needed (that crashes on mismatched session types).
    """
    # Map action_name to the correct RequestSession string
    # Game source: DiplomacyActionView.lua line 472 uses "DECLARE_FRIEND"
    session_string_map = {
        "DECLARE_FRIENDSHIP": "DECLARE_FRIEND",
        "DIPLOMATIC_DELEGATION": "DIPLOMATIC_DELEGATION",
        "RESIDENT_EMBASSY": "RESIDENT_EMBASSY",
        "DENOUNCE": "DENOUNCE",
        "OPEN_BORDERS": "OPEN_BORDERS",
    }
    session_str = session_string_map.get(action_name, action_name)

    return f"""
local me = Game.GetLocalPlayer()
local pDiplo = Players[me]:GetDiplomacy()
local target = {other_player_id}
local action = "{action_name}"
local fullAction = "DIPLOACTION_" .. action
-- Validate first
local valid, results = pDiplo:IsDiplomaticActionValid(fullAction, target, true)
if not valid then
    local reasons = "unknown"
    if results and results.FailureReasons then
        local parts = {{}}
        for _, r in ipairs(results.FailureReasons) do
            table.insert(parts, Locale.Lookup(r))
        end
        reasons = table.concat(parts, "; ")
    end
    {_bail_lua('"ERR:INVALID|" .. reasons')}
end
-- Capture pre-state
local preDel = pDiplo:HasDelegationAt(target)
local preEmb = pDiplo:HasEmbassyAt(target)
local preGold = Players[me]:GetTreasury():GetGoldBalance()
local preVis = pDiplo:GetVisibilityOn(target)
-- Clean stale session for THIS target only (not all session IDs).
-- Mass-closing sessions via IsSessionIDOpen loop corrupts AI diplomacy state.
local staleSid = DiplomacyManager.FindOpenSessionID(me, target)
if staleSid and staleSid >= 0 then
    DiplomacyManager.CloseSession(staleSid)
end
-- Open session with the correct action string
DiplomacyManager.RequestSession(me, target, "{session_str}")
local sid = DiplomacyManager.FindOpenSessionID(me, target)
if sid and sid >= 0 then
    -- Send 2 positive responses (dialogue + acceptance)
    DiplomacyManager.AddResponse(sid, me, "POSITIVE")
    DiplomacyManager.AddResponse(sid, me, "POSITIVE")
    -- Don't force-close; ShowIngameUI below handles UI restoration.
    -- The C++ engine handles session lifecycle through its own callbacks.
else
    -- Some actions are fire-and-forget (no session created)
    -- This is normal for some action types
end
-- Restore UI (ShowIngameUI undoes HideIngameUI from RequestSession)
LuaEvents.DiplomacyActionView_ShowIngameUI()
pcall(function() Events.HideLeaderScreen() end)
-- Check post-state to detect acceptance/rejection
local postDel = pDiplo:HasDelegationAt(target)
local postEmb = pDiplo:HasEmbassyAt(target)
local postGold = Players[me]:GetTreasury():GetGoldBalance()
local name = Locale.Lookup(PlayerConfigurations[target]:GetCivilizationShortDescription())
if action == "DIPLOMATIC_DELEGATION" then
    if postDel and not preDel then
        print("OK:ACCEPTED|" .. name .. " accepted your delegation (cost " .. string.format("%.0f", preGold - postGold) .. " gold)")
    else
        print("OK:REJECTED|" .. name .. " rejected your delegation")
    end
elseif action == "RESIDENT_EMBASSY" then
    if postEmb and not preEmb then
        print("OK:ACCEPTED|" .. name .. " accepted your embassy")
    else
        print("OK:REJECTED|" .. name .. " rejected your embassy")
    end
elseif action == "DECLARE_FRIENDSHIP" then
    local ai = Players[target]:GetDiplomaticAI()
    local postState = ai:GetDiplomaticStateIndex(me)
    if postState == 1 then
        print("OK:ACCEPTED|" .. name .. " accepted your friendship declaration")
    else
        local modTotal = 0
        local modDetails = {{}}
        pcall(function()
            local mods = ai:GetDiplomaticModifiers(me)
            if mods then
                for _, m in ipairs(mods) do
                    local score = m.Score or 0
                    modTotal = modTotal + score
                    local text = m.Text or ""
                    if text ~= "" then text = Locale.Lookup(text) end
                    if text ~= "" and score ~= 0 then
                        table.insert(modDetails, text .. " " .. string.format("%+d", score))
                    end
                end
            end
        end)
        local detail = ""
        if #modDetails > 0 then
            detail = " Modifiers: " .. table.concat(modDetails, ", ") .. " (total: " .. string.format("%+d", modTotal) .. ")."
        end
        print("OK:REJECTED|" .. name .. " did not accept friendship." .. detail .. " Try again after more positive interactions.")
    end
elseif action == "DENOUNCE" then
    print("OK:SENT|Denounced " .. name)
elseif action == "OPEN_BORDERS" then
    local postVis = pDiplo:GetVisibilityOn(target)
    if postVis > preVis then
        print("OK:ACCEPTED|" .. name .. " accepted open borders")
    else
        local modTotal = 0
        pcall(function()
            local ai2 = Players[target]:GetDiplomaticAI()
            local mods = ai2:GetDiplomaticModifiers(me)
            if mods then for _, m in ipairs(mods) do modTotal = modTotal + (m.Score or 0) end end
        end)
        print("OK:REJECTED|" .. name .. " did not accept open borders (modifier total: " .. string.format("%+d", modTotal) .. "). Improve relations first.")
    end
else
    print("OK:SENT|" .. action .. " sent to " .. name)
end
print("{SENTINEL}")
"""


def build_deal_options_query(other_player_id: int) -> str:
    """Show what both sides can trade — resources, gold, favor, agreements (InGame)."""
    return f"""
local me = Game.GetLocalPlayer()
local target = {other_player_id}
local pDiplo = Players[me]:GetDiplomacy()
if not Players[target] or not Players[target]:IsAlive() then {_bail(f"ERR:INVALID_PLAYER|Player {other_player_id} not found")} end
if not pDiplo:HasMet(target) then {_bail(f"ERR:NOT_MET|Have not met player {other_player_id}")} end
local name = Locale.Lookup(PlayerConfigurations[target]:GetCivilizationShortDescription())
print("CIV|" .. target .. "|" .. name:gsub("|","/"))
local ourGold = math.floor(Players[me]:GetTreasury():GetGoldBalance())
local ourGPT = math.floor(Players[me]:GetTreasury():GetGoldYield() - Players[me]:GetTreasury():GetTotalMaintenance())
local ourFavor = 0
pcall(function() ourFavor = math.floor(Players[me]:GetFavor() or 0) end)
local theirGold = math.floor(Players[target]:GetTreasury():GetGoldBalance())
local theirGPT = math.floor(Players[target]:GetTreasury():GetGoldYield() - Players[target]:GetTreasury():GetTotalMaintenance())
local theirFavor = 0
pcall(function() theirFavor = math.floor(Players[target]:GetFavor() or 0) end)
print("ECON|" .. ourGold .. "|" .. ourGPT .. "|" .. ourFavor .. "|" .. theirGold .. "|" .. theirGPT .. "|" .. theirFavor)
for row in GameInfo.Resources() do
    local ourAmt = Players[me]:GetResources():GetResourceAmount(row.Index)
    local theirAmt = Players[target]:GetResources():GetResourceAmount(row.Index)
    if ourAmt > 0 or theirAmt > 0 then
        local rClass = row.ResourceClassType or ""
        local rName = Locale.Lookup(row.Name)
        print("RES|" .. rName:gsub("|","/") .. "|" .. row.ResourceType .. "|" .. rClass .. "|" .. ourAmt .. "|" .. theirAmt)
    end
end
local hasOB = false
pcall(function() hasOB = pDiplo:HasOpenBordersFrom(target) end)
if not hasOB then pcall(function() hasOB = pDiplo:GetVisibilityOn(target) >= 2 end) end
print("OB|" .. (hasOB and "1" or "0"))
local ai = Players[target]:GetDiplomaticAI()
local stateIdx = ai:GetDiplomaticStateIndex(me)
local hasDiploService = false
pcall(function()
    local civic = GameInfo.Civics["CIVIC_DIPLOMATIC_SERVICE"]
    if civic then hasDiploService = Players[me]:GetCulture():HasCivic(civic.Index) end
end)
local allianceEligible = (stateIdx == 1 and hasDiploService)
local currentAlliance = ""
if stateIdx == 0 then
    local ok3, aType = pcall(function() return pDiplo:GetAllianceType(target) end)
    if ok3 and aType and aType >= 0 then
        local aNames = {{"RESEARCH","CULTURAL","ECONOMIC","MILITARY","RELIGIOUS"}}
        currentAlliance = aNames[aType+1] or ""
    end
end
print("ALLIANCE|" .. (allianceEligible and "1" or "0") .. "|" .. currentAlliance)
print("{SENTINEL}")
"""


def parse_deal_options_response(lines: list[str]) -> DealOptions:
    """Parse the deal options query response."""
    opts = DealOptions(other_player_id=0, other_civ_name="")
    for line in lines:
        if line.startswith("CIV|"):
            parts = line.split("|")
            if len(parts) >= 3:
                opts.other_player_id = int(parts[1])
                opts.other_civ_name = parts[2]
        elif line.startswith("ECON|"):
            parts = line.split("|")
            if len(parts) >= 7:
                opts.our_gold = int(parts[1])
                opts.our_gpt = int(parts[2])
                opts.our_favor = int(parts[3])
                opts.their_gold = int(parts[4])
                opts.their_gpt = int(parts[5])
                opts.their_favor = int(parts[6])
        elif line.startswith("RES|"):
            parts = line.split("|")
            if len(parts) >= 6:
                name = parts[1]
                res_type = parts[2]
                res_class = parts[3]
                our_amt = int(parts[4])
                their_amt = int(parts[5])
                is_luxury = "LUXURY" in res_class
                is_strategic = "STRATEGIC" in res_class
                if our_amt > 0:
                    label = f"{name} x{our_amt}" if our_amt > 1 else name
                    if is_luxury:
                        opts.our_luxuries.append(label)
                    elif is_strategic:
                        opts.our_strategics.append(label)
                if their_amt > 0:
                    label = f"{name} x{their_amt}" if their_amt > 1 else name
                    if is_luxury:
                        opts.their_luxuries.append(label)
                    elif is_strategic:
                        opts.their_strategics.append(label)
        elif line.startswith("OB|"):
            opts.has_open_borders = line.split("|")[1] == "1"
        elif line.startswith("ALLIANCE|"):
            parts = line.split("|")
            if len(parts) >= 3:
                opts.alliance_eligible = parts[1] == "1"
                if parts[2]:
                    opts.current_alliance = parts[2]
    return opts


def build_pending_deals_query() -> str:
    """Scan all met players for incoming trade deal offers (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pDiplo = Players[me]:GetDiplomacy()
for i = 0, 62 do
    if i ~= me and Players[i] and Players[i]:IsAlive() and Players[i]:IsMajor() and pDiplo:HasMet(i) then
        local sid = DiplomacyManager.FindOpenSessionID(me, i)
        if sid and sid >= 0 then
        local ok, deal = pcall(function() return DealManager.GetWorkingDeal(DealDirection.INCOMING, me, i) end)
        if ok and deal then
            local count = deal:GetItemCount()
            if count and count > 0 then
                local cfg = PlayerConfigurations[i]
                local civName = Locale.Lookup(cfg:GetCivilizationShortDescription())
                local leaderName = Locale.Lookup(cfg:GetLeaderName())
                print("DEAL|" .. i .. "|" .. civName:gsub("|","/") .. "|" .. leaderName:gsub("|","/"))
                for item in deal:Items() do
                    local fromID = item:GetFromPlayerID()
                    local iType = item:GetType()
                    local subType = item:GetSubType()
                    local amount = item:GetAmount() or 0
                    local duration = item:GetDuration() or 0
                    local valueType = item:GetValueType() or -1
                    local typeName = "UNKNOWN"
                    local itemName = "Unknown"
                    if iType == DealItemTypes.GOLD then
                        typeName = "GOLD"
                        if duration > 0 then itemName = "Gold per turn" else itemName = "Gold (lump sum)" end
                    elseif iType == DealItemTypes.RESOURCES then
                        typeName = "RESOURCE"
                        local res = GameInfo.Resources[valueType]
                        if res then itemName = Locale.Lookup(res.Name) else itemName = "Resource#" .. tostring(valueType) end
                    elseif iType == DealItemTypes.AGREEMENTS then
                        typeName = "AGREEMENT"
                        if subType == DealAgreementTypes.OPEN_BORDERS then itemName = "Open Borders"
                        elseif subType == DealAgreementTypes.JOINT_WAR then itemName = "Joint War"
                        elseif subType == DealAgreementTypes.ALLIANCE then
                            local aNames = {{"Research","Cultural","Economic","Military","Religious"}}
                            itemName = (valueType >= 0 and valueType < 5 and aNames[valueType+1] or "Unknown") .. " Alliance"
                        else itemName = "Agreement#" .. tostring(subType) end
                    elseif iType == DealItemTypes.FAVOR then
                        typeName = "FAVOR"
                        itemName = "Diplomatic Favor"
                    elseif iType == DealItemTypes.CITIES then
                        typeName = "CITY"
                        itemName = "City"
                    elseif iType == DealItemTypes.GREATWORK then
                        typeName = "GREAT_WORK"
                        itemName = "Great Work"
                    end
                    local fromTag = "THEM"
                    if fromID == me then fromTag = "US" end
                    print("ITEM|" .. i .. "|" .. fromTag .. "|" .. typeName .. "|" .. itemName:gsub("|","/") .. "|" .. amount .. "|" .. duration)
                end
            end
        end
        end
    end
end
print("{SENTINEL}")
"""


def build_respond_to_deal(other_player_id: int, accept: bool) -> str:
    """Accept or reject a pending trade deal (InGame context)."""
    action = "DealProposalAction.ACCEPTED" if accept else "DealProposalAction.REJECTED"
    verb = "ACCEPTED" if accept else "REJECTED"
    return f"""
local me = Game.GetLocalPlayer()
local target = {other_player_id}
local sid = DiplomacyManager.FindOpenSessionID(me, target)
if not sid or sid < 0 then {_bail(f"ERR:NO_DEAL|No active deal session with player {other_player_id}")} end
DealManager.SendWorkingDeal({action}, me, target)
{_lua_close_diplo_session()}
local name = Locale.Lookup(PlayerConfigurations[target]:GetCivilizationShortDescription())
print("OK:DEAL_{verb}|" .. name)
print("{SENTINEL}")
"""


def _lua_deal_item(from_var: str, item: dict) -> str:
    """Generate Lua snippet to add one item to the working deal.

    from_var: Lua variable name for the player ID (e.g. "me" or "target").
    item: dict with keys type, amount, and optionally name, duration.
    """
    t = item["type"].upper()
    amount = item.get("amount", 0)
    duration = item.get("duration", 0)

    if t == "GOLD":
        return (
            f"do local gi = deal:AddItemOfType(DealItemTypes.GOLD, {from_var}) "
            f"if gi then gi:SetAmount({amount}) gi:SetDuration({duration}) end end"
        )
    elif t == "RESOURCE":
        res_name = item["name"]
        res_amount = item.get("amount", 1)
        res_duration = item.get("duration", 30)
        return (
            f'do local res = GameInfo.Resources["{res_name}"] '
            f"if res then local ri = deal:AddItemOfType(DealItemTypes.RESOURCES, {from_var}) "
            f"if ri then ri:SetValueType(res.Index) ri:SetAmount({res_amount}) "
            f"ri:SetDuration({res_duration}) end end end"
        )
    elif t == "FAVOR":
        return (
            f"do local fi = deal:AddItemOfType(DealItemTypes.FAVOR, {from_var}) "
            f"if fi then fi:SetAmount({amount}) end end"
        )
    elif t == "AGREEMENT":
        subtype = item["subtype"]  # "OPEN_BORDERS", "JOINT_WAR", "ALLIANCE"
        return (
            f"do local ai = deal:AddItemOfType(DealItemTypes.AGREEMENTS, {from_var}) "
            f"if ai then ai:SetSubType(DealAgreementTypes.{subtype}) end end"
        )
    else:
        return f'-- unsupported deal item type: {t}'


def build_propose_trade(
    other_player_id: int,
    offer_items: list[dict],
    request_items: list[dict],
) -> str:
    """Build a trade deal proposal and send it (InGame context).

    offer_items: items we give to them (from us).
    request_items: items we want from them.
    Each item dict: {type: GOLD|RESOURCE|FAVOR|AGREEMENT, amount: int, name: str, duration: int, subtype: str}
    """
    offer_lua = " ".join(_lua_deal_item("me", item) for item in offer_items)
    request_lua = " ".join(_lua_deal_item("target", item) for item in request_items)

    return f"""
local me = Game.GetLocalPlayer()
local target = {other_player_id}
local pDiplo = Players[me]:GetDiplomacy()
if not pDiplo:HasMet(target) then {_bail("ERR:NOT_MET|Have not met player " + str(other_player_id))} end
if pDiplo:IsAtWarWith(target) then {_bail("ERR:AT_WAR|Cannot trade while at war")} end
local name = Locale.Lookup(PlayerConfigurations[target]:GetCivilizationShortDescription())
if not DealManager.HasPendingDeal(me, target) then
    DealManager.ClearWorkingDeal(DealDirection.OUTGOING, me, target)
end
local deal = DealManager.GetWorkingDeal(DealDirection.OUTGOING, me, target)
if not deal then {_bail("ERR:NO_DEAL_OBJECT|Failed to get working deal")} end
{offer_lua}
{request_lua}
DiplomacyManager.RequestSession(me, target, "MAKE_DEAL")
DealManager.SendWorkingDeal(DealProposalAction.PROPOSED, me, target)
local sid = DiplomacyManager.FindOpenSessionID(me, target)
local result = "PROPOSED"
if sid and sid >= 0 then
    local ok, respDeal = pcall(function()
        return DealManager.GetWorkingDeal(DealDirection.INCOMING, me, target)
    end)
    if ok and respDeal and respDeal:GetItemCount() and respDeal:GetItemCount() > 0 then
        DealManager.SendWorkingDeal(DealProposalAction.ACCEPTED, me, target)
        result = "ACCEPTED"
    else
        result = "REJECTED"
    end
    {_lua_close_diplo_session()}
end
print("OK:" .. result .. "|Trade " .. result:lower() .. " with " .. name)
print("{SENTINEL}")
"""


def build_form_alliance(other_player_id: int, alliance_type: str) -> str:
    """Form an alliance with another civilization (InGame context).

    alliance_type: MILITARY, RESEARCH, CULTURAL, ECONOMIC, RELIGIOUS
    """
    alliance_key = f"ALLIANCE_{alliance_type.upper()}"
    return f"""
local me = Game.GetLocalPlayer()
local target = {other_player_id}
local allianceRow = GameInfo.Alliances["{alliance_key}"]
local type_idx = allianceRow and allianceRow.Index or 0
local pDiplo = Players[me]:GetDiplomacy()
if not Players[target] or not Players[target]:IsAlive() then {_bail("ERR:INVALID_PLAYER|Player not found")} end
if not pDiplo:HasMet(target) then {_bail("ERR:NOT_MET|Have not met this civilization")} end
if pDiplo:IsAtWarWith(target) then {_bail("ERR:AT_WAR|Cannot ally while at war")} end
local ai = Players[target]:GetDiplomaticAI()
local stateIdx = ai:GetDiplomaticStateIndex(me)
if stateIdx == 0 then {_bail("ERR:ALREADY_ALLIED|Already in an alliance")} end
if stateIdx ~= 1 then {_bail("ERR:NOT_FRIENDS|Must be declared friends first")} end
local hasDiploService = false
pcall(function()
    local civic = GameInfo.Civics["CIVIC_DIPLOMATIC_SERVICE"]
    if civic then hasDiploService = Players[me]:GetCulture():HasCivic(civic.Index) end
end)
if not hasDiploService then {_bail("ERR:NO_CIVIC|Diplomatic Service civic required for alliances")} end
local name = Locale.Lookup(PlayerConfigurations[target]:GetCivilizationShortDescription())
if not DealManager.HasPendingDeal(me, target) then
    DealManager.ClearWorkingDeal(DealDirection.OUTGOING, me, target)
end
local deal = DealManager.GetWorkingDeal(DealDirection.OUTGOING, me, target)
if not deal then {_bail("ERR:NO_DEAL_OBJECT|Failed to get working deal")} end
do local ai_item = deal:AddItemOfType(DealItemTypes.AGREEMENTS, me)
if ai_item then ai_item:SetSubType(DealAgreementTypes.ALLIANCE) pcall(function() ai_item:SetValueType(type_idx) end) end end
DiplomacyManager.RequestSession(me, target, "MAKE_DEAL")
DealManager.SendWorkingDeal(DealProposalAction.PROPOSED, me, target)
local sid = DiplomacyManager.FindOpenSessionID(me, target)
local result = "PROPOSED"
if sid and sid >= 0 then
    local ok, respDeal = pcall(function()
        return DealManager.GetWorkingDeal(DealDirection.INCOMING, me, target)
    end)
    if ok and respDeal then
        local itemCount = 0
        pcall(function() itemCount = respDeal:GetItemCount() or 0 end)
        if itemCount > 0 then
            DealManager.SendWorkingDeal(DealProposalAction.ACCEPTED, me, target)
            result = "ACCEPTED"
        else
            result = "REJECTED"
        end
    else
        result = "REJECTED"
    end
    {_lua_close_diplo_session()}
end
local postState = Players[target]:GetDiplomaticAI():GetDiplomaticStateIndex(me)
if postState == 0 then
    local aNames = {{"RESEARCH","CULTURAL","ECONOMIC","MILITARY","RELIGIOUS"}}
    local typeName = "{alliance_type}"
    local ok3, aType = pcall(function() return pDiplo:GetAllianceType(target) end)
    if ok3 and aType and aType >= 0 then typeName = aNames[aType+1] or typeName end
    print("OK:ACCEPTED|" .. typeName .. " alliance formed with " .. name)
else
    if result == "REJECTED" then
        print("OK:REJECTED|" .. name .. " rejected the " .. "{alliance_type}" .. " alliance proposal")
    else
        print("OK:FAILED|Alliance proposal sent but status unclear (state=" .. tostring(postState) .. ")")
    end
end
print("{SENTINEL}")
"""


def build_propose_peace(other_player_id: int) -> str:
    """Propose white peace to a civilization we're at war with (InGame context).

    Session type is "MAKE_PEACE" (not "PROPOSE_PEACE_DEAL" which silently fails).
    After sending the deal, close the session with NEGATIVE+CloseSession loop,
    then ShowIngameUI + Events.HideLeaderScreen() to restore HUD and dismiss 3D leader.
    """
    return f"""
local me = Game.GetLocalPlayer()
local target = {other_player_id}
local pDiplo = Players[me]:GetDiplomacy()
if not pDiplo:IsAtWarWith(target) then {_bail("ERR:NOT_AT_WAR|Not at war with player " + str(other_player_id))} end
local canPeace = pDiplo:CanMakePeaceWith(target)
if not canPeace then {_bail("ERR:CANNOT_MAKE_PEACE|10-turn war cooldown or other restriction")} end
local name = Locale.Lookup(PlayerConfigurations[target]:GetCivilizationShortDescription())
DiplomacyManager.RequestSession(me, target, "MAKE_PEACE")
local sid = DiplomacyManager.FindOpenSessionID(me, target)
if not sid or sid < 0 then {_bail("ERR:NO_SESSION|Failed to open peace deal session")} end
DealManager.ClearWorkingDeal(DealDirection.OUTGOING, me, target)
DealManager.SendWorkingDeal(DealProposalAction.PROPOSED, me, target)
{_lua_close_diplo_session()}
print("OK:PROPOSED|" .. name)
print("{SENTINEL}")
"""


def build_check_war_state(other_player_id: int) -> str:
    """Check if we're still at war with a player (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local atWar = Players[me]:GetDiplomacy():IsAtWarWith({other_player_id})
print(atWar and "AT_WAR" or "AT_PEACE")
print("{SENTINEL}")
"""


def parse_diplomacy_response(lines: list[str]) -> list[CivInfo]:
    civs: dict[int, CivInfo] = {}
    for line in lines:
        if line.startswith("CIV|"):
            parts = line.split("|")
            if len(parts) < 13:
                continue
            pid = int(parts[1])
            total_score = 0  # will sum modifiers below
            civs[pid] = CivInfo(
                player_id=pid,
                civ_name=parts[2],
                leader_name=parts[3],
                has_met=parts[4] == "1",
                is_at_war=parts[5] == "1",
                diplomatic_state=parts[6],
                grievances=int(parts[7]),
                access_level=int(parts[8]),
                has_delegation=parts[9] == "1",
                has_embassy=parts[10] == "1",
                they_have_delegation=parts[11] == "1",
                they_have_embassy=parts[12] == "1",
                modifiers=[],
                available_actions=[],
            )
        elif line.startswith("MOD|"):
            parts = line.split("|")
            if len(parts) >= 4:
                pid = int(parts[1])
                if pid in civs:
                    civs[pid].modifiers.append(DiplomacyModifier(
                        score=int(parts[2]),
                        text=parts[3],
                    ))
                    civs[pid].relationship_score += int(parts[2])
        elif line.startswith("ALLIANCE|"):
            parts = line.split("|")
            if len(parts) >= 3:
                pid = int(parts[1])
                if pid in civs:
                    civs[pid].alliance_type = parts[2]
                    if len(parts) >= 4:
                        try:
                            civs[pid].alliance_level = int(parts[3])
                        except ValueError:
                            pass
        elif line.startswith("MILITARY|"):
            parts = line.split("|")
            if len(parts) >= 4:
                pid = int(parts[1])
                if pid in civs:
                    try:
                        civs[pid].military_strength = int(parts[2])
                        civs[pid]._our_military = int(parts[3])  # type: ignore[attr-defined]
                    except ValueError:
                        pass
        elif line.startswith("ECITY|"):
            parts = line.split("|")
            if len(parts) >= 9:
                pid = int(parts[1])
                if pid in civs:
                    xy = parts[3].split(",")
                    try:
                        vc = VisibleCity(
                            name=parts[2],
                            x=int(xy[0]),
                            y=int(xy[1]),
                            population=int(parts[4]),
                            loyalty=float(parts[5]),
                            loyalty_per_turn=float(parts[6]),
                            has_walls=int(parts[7]) > 0,
                            defense_strength=int(parts[8]),
                        )
                        civs[pid].visible_cities.append(vc)
                    except (ValueError, IndexError):
                        pass
        elif line.startswith("CIVCITIES|"):
            parts = line.split("|")
            if len(parts) >= 3:
                pid = int(parts[1])
                if pid in civs:
                    civs[pid].num_cities = int(parts[2])
        elif line.startswith("ACTIONS|"):
            parts = line.split("|")
            if len(parts) >= 3:
                pid = int(parts[1])
                if pid in civs:
                    civs[pid].available_actions = parts[2].split(",")
        elif line.startswith("PACT|"):
            parts = line.split("|")
            if len(parts) == 3:
                # PACT|pid|DEFENSIVE — pact between us and pid
                pid = int(parts[1])
                if pid in civs:
                    # Mark that this civ has a defensive pact (with us)
                    pass  # We don't track pacts with us specially
            elif len(parts) == 4:
                # PACT|pid1|pid2|DEFENSIVE — third-party pact
                pid1, pid2 = int(parts[1]), int(parts[2])
                if pid1 in civs:
                    civs[pid1].defensive_pacts.append(pid2)
                if pid2 in civs:
                    civs[pid2].defensive_pacts.append(pid1)
    return list(civs.values())


def parse_diplomacy_sessions(lines: list[str]) -> list[DiplomacySession]:
    """Parse open diplomacy session output."""
    sessions = []
    for line in lines:
        if line == "NONE":
            break
        if line.startswith("SESSION|"):
            parts = line.split("|")
            if len(parts) >= 5:
                sessions.append(DiplomacySession(
                    session_id=int(parts[1]),
                    other_player_id=int(parts[2]),
                    other_civ_name=parts[3],
                    other_leader_name=parts[4],
                    choices=[],
                    dialogue_text=parts[5] if len(parts) > 5 else "",
                    reason_text=parts[6] if len(parts) > 6 else "",
                    buttons=parts[7] if len(parts) > 7 else "",
                ))
    return sessions


def parse_pending_deals_response(lines: list[str]) -> list[PendingDeal]:
    """Parse DEAL| and ITEM| lines from build_pending_deals_query."""
    deals: dict[int, PendingDeal] = {}
    for line in lines:
        if line.startswith("DEAL|"):
            parts = line.split("|")
            if len(parts) >= 4:
                pid = int(parts[1])
                deals[pid] = PendingDeal(
                    other_player_id=pid,
                    other_player_name=parts[2],
                    other_leader_name=parts[3],
                )
        elif line.startswith("ITEM|"):
            parts = line.split("|")
            if len(parts) >= 7:
                pid = int(parts[1])
                if pid not in deals:
                    continue
                is_from_us = parts[2] == "US"
                item = DealItem(
                    from_player_id=-1 if is_from_us else pid,
                    from_player_name="Us" if is_from_us else deals[pid].other_player_name,
                    item_type=parts[3],
                    name=parts[4],
                    amount=int(parts[5]),
                    duration=int(parts[6]),
                    is_from_us=is_from_us,
                )
                if is_from_us:
                    deals[pid].items_from_us.append(item)
                else:
                    deals[pid].items_from_them.append(item)
    return list(deals.values())
