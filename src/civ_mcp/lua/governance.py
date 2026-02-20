"""Governance domain — Lua builders and parsers."""

from __future__ import annotations

from civ_mcp.lua._helpers import SENTINEL, _bail, _bail_lua, _lua_get_city, _lua_get_unit, _lua_get_unit_gamecore
from civ_mcp.lua.models import AppointedGovernor, CityStateInfo, DedicationChoice, DedicationStatus, EnvoyStatus, GovernmentStatus, GovernorInfo, GovernorPromotion, GovernorStatus, PolicyInfo, PolicySlot, PromotionOption, UnitPromotionStatus


def build_policies_query() -> str:
    """Read current government, policy slots, and available policies (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pCulture = Players[me]:GetCulture()
local govIdx = pCulture:GetCurrentGovernment()
local govName = "None"
local govType = "NONE"
if govIdx and govIdx >= 0 then
    local govEntry = GameInfo.Governments[govIdx]
    if govEntry then
        govName = Locale.Lookup(govEntry.Name)
        govType = govEntry.GovernmentType
    end
end
local numSlots = pCulture:GetNumPolicySlots()
print("GOV|" .. govType .. "|" .. govName:gsub("|","/") .. "|" .. numSlots)
local slotNames = {{[0]="SLOT_ECONOMIC", [1]="SLOT_MILITARY", [2]="SLOT_DIPLOMATIC", [3]="SLOT_WILDCARD", [4]="SLOT_WILDCARD"}}
for s = 0, numSlots - 1 do
    local slotType = slotNames[pCulture:GetSlotType(s)] or ("SLOT_" .. pCulture:GetSlotType(s))
    local policyIdx = pCulture:GetSlotPolicy(s)
    local policyType = "NONE"
    local policyName = "Empty"
    if policyIdx >= 0 then
        local pe = GameInfo.Policies[policyIdx]
        if pe then
            policyType = pe.PolicyType
            policyName = Locale.Lookup(pe.Name)
        end
    end
    print("SLOT|" .. s .. "|" .. slotType .. "|" .. policyType .. "|" .. policyName:gsub("|","/"))
end
for policy in GameInfo.Policies() do
    if pCulture:IsPolicyUnlocked(policy.Index) then
        local canSlot = false
        for s = 0, numSlots - 1 do
            if pCulture:CanSlotPolicy(policy.Index, s) then
                canSlot = true
                break
            end
        end
        if canSlot then
            local slotType = "SLOT_WILDCARD"
            if policy.GovernmentSlotType then slotType = policy.GovernmentSlotType end
            local name = Locale.Lookup(policy.Name)
            local desc = Locale.Lookup(policy.Description):gsub("|", "/"):gsub("\\n", " ")
            print("AVAIL|" .. policy.PolicyType .. "|" .. name:gsub("|","/") .. "|" .. desc .. "|" .. slotType)
        end
    end
end
print("{SENTINEL}")
"""


def build_set_policies(assignments: dict[int, str]) -> str:
    """Set policy cards in government slots (InGame context).

    assignments maps slot_index -> policy_type string.
    Two-step: UNLOCK_POLICIES first, then RequestPolicyChanges.
    """
    add_entries = []
    for slot_idx, policy_type in assignments.items():
        add_entries.append(
            f'local pe_{slot_idx} = GameInfo.Policies["{policy_type}"]; '
            f'if pe_{slot_idx} == nil then {_bail(f"ERR:POLICY_NOT_FOUND|{policy_type}")} end; '
            f'local sType_{slot_idx} = pCulture:GetSlotType({slot_idx}); '
            f'local pSlot_{slot_idx} = slotTypeMap[pe_{slot_idx}.GovernmentSlotType] or -1; '
            f'if sType_{slot_idx} < 2 and pSlot_{slot_idx} ~= sType_{slot_idx} then '
            f'local sName = slotNames[sType_{slot_idx}] or "unknown"; '
            f'local pType = pe_{slot_idx}.GovernmentSlotType or "unknown"; '
            f'{_bail_lua(f""" "ERR:SLOT_MISMATCH|{policy_type} (" .. pType .. ") cannot go in slot {slot_idx} (" .. sName .. ")" """)} end; '
            f'addList[{slot_idx}] = pe_{slot_idx}.Hash'
        )
    add_lua = " ".join(add_entries)

    return f"""
local me = Game.GetLocalPlayer()
local pCulture = Players[me]:GetCulture()
local numSlots = pCulture:GetNumPolicySlots()
if numSlots <= 0 then {_bail("ERR:NO_GOVERNMENT|No government selected")} end
local slotNames = {{[0]="Economic", [1]="Military", [2]="Diplomatic", [3]="Wildcard", [4]="Wildcard"}}
local slotTypeMap = {{SLOT_ECONOMIC=0, SLOT_MILITARY=1, SLOT_DIPLOMATIC=2, SLOT_WILDCARD=3, SLOT_GREAT_PERSON=4}}
UI.RequestPlayerOperation(me, PlayerOperations.UNLOCK_POLICIES, {{}})
local clearList = {{}}
for s = 0, numSlots - 1 do table.insert(clearList, s) end
local addList = {{}}
{add_lua}
pCulture:RequestPolicyChanges(clearList, addList)
print("OK:POLICIES_SET|Policies updated. Use get_policies to verify.")
print("{SENTINEL}")
"""


def build_governors_query() -> str:
    """Read governor status, appointed governors, and available types (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pGovs = Players[me]:GetGovernors()
local pts = pGovs:GetGovernorPoints()
local spent = pGovs:GetGovernorPointsSpent()
local canAppoint = pGovs:CanAppoint() and "1" or "0"
print("STATUS|" .. pts .. "|" .. spent .. "|" .. canAppoint)
local appointedTypes = {{}}
for row in GameInfo.Governors() do
    if row.TransitionStrength and row.TransitionStrength > 0 and pGovs:HasGovernor(row.Hash) then
        appointedTypes[row.GovernorType] = true
        local g = pGovs:GetGovernor(row.Hash)
        local gName = Locale.Lookup(row.Name)
        local gTitle = Locale.Lookup(row.Title)
        local cityID = -1
        local cityName = "Unassigned"
        local established = "0"
        local turnsLeft = 0
        local assignedCity = g:GetAssignedCity()
        if assignedCity then
            cityID = assignedCity:GetID()
            cityName = Locale.Lookup(assignedCity:GetName())
            established = g:IsEstablished() and "1" or "0"
            if not g:IsEstablished() then turnsLeft = g:GetTurnsToEstablish() end
        end
        print("APPOINTED|" .. row.GovernorType .. "|" .. gName:gsub("|","/") .. "|" .. gTitle:gsub("|","/") .. "|" .. cityID .. "|" .. cityName:gsub("|","/") .. "|" .. established .. "|" .. turnsLeft)
        for promo in GameInfo.GovernorPromotionSets() do
            if promo.GovernorType == row.GovernorType then
                local promoRow = GameInfo.GovernorPromotions[promo.GovernorPromotion]
                if promoRow and not g:HasPromotion(promoRow.Index) then
                    local pName = Locale.Lookup(promoRow.Name)
                    local pDesc = Locale.Lookup(promoRow.Description)
                    print("GOV_PROMO|" .. row.GovernorType .. "|" .. promoRow.GovernorPromotionType .. "|" .. pName:gsub("|","/") .. "|" .. pDesc:gsub("|","/"))
                end
            end
        end
    end
end
for gov in GameInfo.Governors() do
    if gov.TransitionStrength and gov.TransitionStrength > 0 and not appointedTypes[gov.GovernorType] then
        local gName = Locale.Lookup(gov.Name)
        local gTitle = Locale.Lookup(gov.Title)
        print("AVAILABLE|" .. gov.GovernorType .. "|" .. gName:gsub("|","/") .. "|" .. gTitle:gsub("|","/"))
    end
end
print("{SENTINEL}")
"""


def build_appoint_governor(governor_type: str) -> str:
    """Appoint a new governor (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pGovs = Players[me]:GetGovernors()
if not pGovs:CanAppoint() then {_bail("ERR:CANNOT_APPOINT|No governor points available")} end
local gov = GameInfo.Governors["{governor_type}"]
if gov == nil then {_bail(f"ERR:GOVERNOR_NOT_FOUND|{governor_type}")} end
if PlayerOperations.APPOINT_GOVERNOR == nil then {_bail("ERR:API_MISSING|PlayerOperations.APPOINT_GOVERNOR is nil")} end
if PlayerOperations.PARAM_GOVERNOR_TYPE == nil then {_bail("ERR:API_MISSING|PlayerOperations.PARAM_GOVERNOR_TYPE is nil")} end
local prePts = pGovs:GetGovernorPointsSpent()
local params = {{}}
params[PlayerOperations.PARAM_GOVERNOR_TYPE] = gov.Index
UI.RequestPlayerOperation(me, PlayerOperations.APPOINT_GOVERNOR, params)
local postPts = pGovs:GetGovernorPointsSpent()
if postPts > prePts then
    print("OK:APPOINTED|" .. Locale.Lookup(gov.Name) .. " (" .. Locale.Lookup(gov.Title) .. ")")
else
    print("OK:APPOINT_REQUESTED|" .. Locale.Lookup(gov.Name) .. " — verify with get_governors()")
end
print("{SENTINEL}")
"""


def build_assign_governor(governor_type: str, city_id: int) -> str:
    """Assign a governor to a city (InGame context)."""
    return f"""
{_lua_get_city(city_id)}
local gov = GameInfo.Governors["{governor_type}"]
if gov == nil then {_bail(f"ERR:GOVERNOR_NOT_FOUND|{governor_type}")} end
if PlayerOperations.ASSIGN_GOVERNOR == nil then {_bail("ERR:API_MISSING|PlayerOperations.ASSIGN_GOVERNOR is nil")} end
local params = {{}}
params[PlayerOperations.PARAM_GOVERNOR_TYPE] = gov.Index
params[PlayerOperations.PARAM_CITY_DEST] = pCity:GetID()
params[PlayerOperations.PARAM_PLAYER_ONE] = me
UI.RequestPlayerOperation(me, PlayerOperations.ASSIGN_GOVERNOR, params)
print("OK:ASSIGNED|" .. Locale.Lookup(gov.Name) .. " to " .. Locale.Lookup(pCity:GetName()))
print("{SENTINEL}")
"""


def build_promote_governor(governor_type: str, promotion_type: str) -> str:
    """Promote a governor with a new ability (InGame context).

    Uses PROMOTE_GOVERNOR operation (NOT APPOINT_GOVERNOR).
    Both governor and promotion use .Index (NOT .Hash).
    Source: GovernorDetailsPanel.lua — SetVoid1(m_GovernorIndex), SetVoid2(kPromotion.Index)
    """
    return f"""
local me = Game.GetLocalPlayer()
local pGovs = Players[me]:GetGovernors()
local gov = GameInfo.Governors["{governor_type}"]
if gov == nil then {_bail(f"ERR:GOVERNOR_NOT_FOUND|{governor_type}")} end
if not pGovs:HasGovernor(gov.Hash) then {_bail(f"ERR:NOT_APPOINTED|{governor_type} not appointed")} end
if not pGovs:CanPromoteGovernor(gov.Hash) then {_bail("ERR:CANNOT_PROMOTE|No governor points or no promotions available")} end
local promo = GameInfo.GovernorPromotions["{promotion_type}"]
if promo == nil then {_bail(f"ERR:PROMOTION_NOT_FOUND|{promotion_type}")} end
local g = pGovs:GetGovernor(gov.Hash)
if g:HasPromotion(promo.Index) then {_bail(f"ERR:ALREADY_PROMOTED|{promotion_type} already earned")} end
local params = {{}}
params[PlayerOperations.PARAM_GOVERNOR_TYPE] = gov.Index
params[PlayerOperations.PARAM_GOVERNOR_PROMOTION_TYPE] = promo.Index
UI.RequestPlayerOperation(me, PlayerOperations.PROMOTE_GOVERNOR, params)
print("OK:PROMOTED|" .. Locale.Lookup(gov.Name) .. " with " .. Locale.Lookup(promo.Name))
print("{SENTINEL}")
"""


def build_unit_promotions_query(unit_index: int) -> str:
    """List available promotions for a unit (GameCore context)."""
    return f"""
{_lua_get_unit_gamecore(unit_index)}
local x, y = unit:GetX(), unit:GetY()
if x == -9999 then {_bail("ERR:UNIT_CONSUMED")} end
local typeIdx = unit:GetType()
if typeIdx == nil then {_bail("ERR:UNIT_NO_TYPE")} end
local info = GameInfo.Units[typeIdx]
local ut = info and info.UnitType or "UNKNOWN"
local promClass = info and info.PromotionClass or ""
print("UNIT|" .. {unit_index} .. "|" .. (unit:GetID() % 65536) .. "|" .. ut)
local exp = unit:GetExperience()
local prereqMap = {{}}
for row in GameInfo.UnitPromotionPrereqs() do
    local pt = row.UnitPromotion
    if not prereqMap[pt] then prereqMap[pt] = {{}} end
    table.insert(prereqMap[pt], row.PrereqUnitPromotion)
end
for promo in GameInfo.UnitPromotions() do
    if promo.PromotionClass == promClass then
        if not exp:HasPromotion(promo.Index) then
            local prereqs = prereqMap[promo.UnitPromotionType]
            local prereqMet = true
            if prereqs and #prereqs > 0 then
                prereqMet = false
                for _, reqType in ipairs(prereqs) do
                    local reqInfo = GameInfo.UnitPromotions[reqType]
                    if reqInfo and exp:HasPromotion(reqInfo.Index) then
                        prereqMet = true
                        break
                    end
                end
            end
            if prereqMet then
                local canPromote = false
                pcall(function() canPromote = exp:CanPromote(promo.Index) end)
                if canPromote then
                    local name = Locale.Lookup(promo.Name)
                    local desc = Locale.Lookup(promo.Description):gsub("|","/"):gsub("\\n"," ")
                    print("PROMO|" .. promo.UnitPromotionType .. "|" .. name:gsub("|","/") .. "|" .. desc)
                end
            end
        end
    end
end
print("{SENTINEL}")
"""


def build_promote_unit(unit_index: int, promotion_type: str) -> str:
    """Apply a promotion to a unit (GameCore context).

    Uses GameCore SetPromotion because InGame RequestCommand(PROMOTE)
    silently fails (persistent bug across Games 1, 4, and 5).
    """
    return f"""
{_lua_get_unit_gamecore(unit_index)}
local x, y = unit:GetX(), unit:GetY()
if x == -9999 then {_bail("ERR:UNIT_CONSUMED")} end
local promo = GameInfo.UnitPromotions["{promotion_type}"]
if promo == nil then {_bail(f"ERR:PROMOTION_NOT_FOUND|{promotion_type}")} end
local exp = unit:GetExperience()
if exp == nil then {_bail("ERR:NO_EXPERIENCE|Unit has no experience object")} end
local canPromote = false
pcall(function() canPromote = exp:CanPromote(promo.Index) end)
if not canPromote then {_bail("ERR:CANNOT_PROMOTE|Unit cannot receive this promotion (wrong class, missing prereq, or insufficient XP)")} end
if exp:HasPromotion(promo.Index) then {_bail(f"ERR:ALREADY_HAS_PROMOTION|{promotion_type}")} end
exp:SetPromotion(promo.Index)
if not exp:HasPromotion(promo.Index) then {_bail("ERR:PROMOTION_FAILED|SetPromotion did not apply")} end
pcall(function() exp:ChangeStoredPromotions(-1) end)
pcall(function() unit:SetDamage(0) end)
UnitManager.FinishMoves(unit)
local promoName = Locale.Lookup(promo.Name)
print("OK:PROMOTED|" .. promoName)
print("{SENTINEL}")
"""


def build_city_states_query() -> str:
    """List known city-states with envoy info (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pInfluence = Players[me]:GetInfluence()
local pDiplo = Players[me]:GetDiplomacy()
print("TOKENS|" .. pInfluence:GetTokensToGive())
local csTypeMap = {{}}
csTypeMap["LEADER_MINOR_CIV_SCIENTIFIC"] = "Scientific"
csTypeMap["LEADER_MINOR_CIV_CULTURAL"] = "Cultural"
csTypeMap["LEADER_MINOR_CIV_MILITARISTIC"] = "Militaristic"
csTypeMap["LEADER_MINOR_CIV_RELIGIOUS"] = "Religious"
csTypeMap["LEADER_MINOR_CIV_TRADE"] = "Trade"
csTypeMap["LEADER_MINOR_CIV_INDUSTRIAL"] = "Industrial"
for i = 0, 62 do
    if Players[i] and Players[i]:IsAlive() and Players[i]:IsMajor() == false and Players[i]:IsBarbarian() == false and pDiplo:HasMet(i) then
        local cfg = PlayerConfigurations[i]
        local name = Locale.Lookup(cfg:GetPlayerName())
        local leaderType = cfg:GetLeaderTypeName() or ""
        local csType = "Unknown"
        local leader = GameInfo.Leaders[leaderType]
        if leader and leader.InheritFrom then
            csType = csTypeMap[leader.InheritFrom] or leader.InheritFrom
        end
        local csInfluence = Players[i]:GetInfluence()
        local envoys = csInfluence:GetTokensReceived(me)
        local suzID = csInfluence:GetSuzerain() or -1
        local suzName = "None"
        if suzID >= 0 and suzID ~= 63 then
            local sCfg = PlayerConfigurations[suzID]
            if sCfg then suzName = Locale.Lookup(sCfg:GetCivilizationShortDescription()) end
        end
        local canSend = pInfluence:CanGiveTokensToPlayer(i) and "1" or "0"
        print("CS|" .. i .. "|" .. name:gsub("|","/") .. "|" .. csType .. "|" .. envoys .. "|" .. suzID .. "|" .. suzName:gsub("|","/") .. "|" .. canSend)
    end
end
print("{SENTINEL}")
"""


def build_send_envoy(city_state_player_id: int) -> str:
    """Send an envoy to a city-state (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pInfluence = Players[me]:GetInfluence()
if pInfluence:GetTokensToGive() <= 0 then {_bail("ERR:NO_ENVOYS|No envoy tokens available")} end
if not pInfluence:CanGiveTokensToPlayer({city_state_player_id}) then
    {_bail(f"ERR:CANNOT_SEND|Cannot send envoy to player {city_state_player_id}")}
end
local params = {{}}
params[PlayerOperations.PARAM_PLAYER_ONE] = {city_state_player_id}
params[PlayerOperations.PARAM_FLAGS] = 0
UI.RequestPlayerOperation(me, PlayerOperations.GIVE_INFLUENCE_TOKEN, params)
local cfg = PlayerConfigurations[{city_state_player_id}]
local name = cfg and Locale.Lookup(cfg:GetPlayerName()) or "Unknown"
print("OK:ENVOY_SENT|" .. name)
print("{SENTINEL}")
"""


def build_unit_upgrade_query(unit_index: int) -> str:
    """Check if a unit can upgrade and get cost/target info (InGame context)."""
    return f"""
{_lua_get_unit(unit_index)}
local info = GameInfo.Units[unit:GetType()]
local ut = info and info.UnitType or "UNKNOWN"
local params = {{}}
local canUpgrade, upgradeResult = UnitManager.CanStartCommand(unit, UnitCommandTypes.UPGRADE, params, true)
local upgCol = info.UpgradeUnitCollection
local upgradeType = ""
if upgCol and #upgCol > 0 then upgradeType = upgCol[1].UpgradeUnit or "" end
if not canUpgrade then
    local reasons = ""
    if upgradeResult then
        for _, v in pairs(upgradeResult) do
            if type(v) == "table" then
                for _, reason in pairs(v) do
                    if type(reason) == "string" then
                        local clean = reason:gsub("%[ICON_[^%]]*%]", ""):gsub("%s+", " ")
                        reasons = reasons .. (reasons ~= "" and "; " or "") .. clean
                    end
                end
            end
        end
    end
    local suffix = upgradeType ~= "" and (" -> " .. upgradeType) or ""
    local msg = ut .. suffix .. (reasons ~= "" and (" | " .. reasons) or " | cannot upgrade (missing tech, resources, gold, or no path)")
    {_bail_lua('"ERR:CANNOT_UPGRADE|" .. msg')}
end
if upgradeType == "" then {_bail_lua('"ERR:NO_UPGRADE_PATH|" .. ut .. " has no upgrade"')} end
local upInfo = GameInfo.Units[upgradeType]
local upName = upInfo and Locale.Lookup(upInfo.Name) or upgradeType
local gold = Players[me]:GetTreasury():GetGoldBalance()
local cost = 0
pcall(function() cost = unit:GetUpgradeCost() end)
print("UPGRADE|" .. ut .. "|" .. upgradeType .. "|" .. upName:gsub("|","/") .. "|" .. math.floor(cost) .. "|" .. math.floor(gold))
print("{SENTINEL}")
"""


def build_upgrade_unit(unit_index: int) -> str:
    """Execute unit upgrade (InGame context)."""
    return f"""
{_lua_get_unit(unit_index)}
local info = GameInfo.Units[unit:GetType()]
local ut = info and info.UnitType or "UNKNOWN"
local upgCol = info and info.UpgradeUnitCollection
local upType = (upgCol and #upgCol > 0) and upgCol[1].UpgradeUnit or ""
local params = {{}}
local canUpgrade, upgradeResult = UnitManager.CanStartCommand(unit, UnitCommandTypes.UPGRADE, params, true)
if not canUpgrade then
    local cost = 0
    pcall(function() cost = unit:GetUpgradeCost() end)
    local gold = Players[me]:GetTreasury():GetGoldBalance()
    local detail = ut
    if upType ~= "" then detail = detail .. " -> " .. upType end
    detail = detail .. " | cost:" .. math.floor(cost) .. "g have:" .. math.floor(gold) .. "g"
    if upgradeResult then
        for _, v in pairs(upgradeResult) do
            if type(v) == "table" then
                for _, reason in pairs(v) do
                    if type(reason) == "string" then
                        local clean = reason:gsub("%[ICON_[^%]]*%]", ""):gsub("%s+", " ")
                        detail = detail .. " | " .. clean
                    end
                end
            end
        end
    end
    {_bail_lua('"ERR:CANNOT_UPGRADE|" .. detail')}
end
if upType == "" then upType = "UNKNOWN" end
UnitManager.RequestCommand(unit, UnitCommandTypes.UPGRADE, params)
print("OK:UPGRADED|" .. ut .. " -> " .. upType)
print("{SENTINEL}")
"""


def build_dedications_query() -> str:
    """Read current era age, available dedications, and active ones."""
    return f"""
local me = Game.GetLocalPlayer()
local pEras = Game.GetEras()
local age = "Normal"
if pEras:HasHeroicGoldenAge(me) then age = "Heroic"
elseif pEras:HasGoldenAge(me) then age = "Golden"
elseif pEras:HasDarkAge(me) then age = "Dark" end
local era = pEras:GetCurrentEra()
local darkT = pEras:GetPlayerDarkAgeThreshold(me) or 0
local goldT = pEras:GetPlayerGoldenAgeThreshold(me) or 0
local allowed = pEras:GetPlayerNumAllowedCommemorations(me)
local score = pEras:GetPlayerCurrentScore(me)
print("STATUS|" .. age .. "|" .. era .. "|" .. score .. "|" .. darkT .. "|" .. goldT .. "|" .. allowed)
-- Active commemorations
local active = pEras:GetPlayerActiveCommemorations(me)
if active then
    for _, a in ipairs(active) do
        local row = GameInfo.CommemorationTypes[a]
        if row then print("ACTIVE|" .. row.CommemorationType) end
    end
end
-- Available choices
local choices = pEras:GetPlayerCommemorateChoices(me)
if choices then
    for _, idx in ipairs(choices) do
        local row = GameInfo.CommemorationTypes[idx]
        if row then
            local norm = row.NormalAgeBonusDescription and Locale.Lookup(row.NormalAgeBonusDescription) or ""
            local gold = row.GoldenAgeBonusDescription and Locale.Lookup(row.GoldenAgeBonusDescription) or ""
            local dark = row.DarkAgeBonusDescription and Locale.Lookup(row.DarkAgeBonusDescription) or ""
            print("CHOICE|" .. idx .. "|" .. row.CommemorationType .. "|" .. norm .. "|" .. gold .. "|" .. dark)
        end
    end
end
print("{SENTINEL}")
"""


def build_choose_dedication(dedication_index: int) -> str:
    """Select a dedication/commemoration by its index."""
    return f"""
local me = Game.GetLocalPlayer()
local pEras = Game.GetEras()
local allowed = pEras:GetPlayerNumAllowedCommemorations(me)
if allowed <= 0 then {_bail("ERR:NO_DEDICATION_NEEDED|No dedication selection required (already chosen or not available)")} end
local row = GameInfo.CommemorationTypes[{dedication_index}]
if not row then {_bail(f"ERR:INVALID_INDEX|Dedication index {dedication_index} not found")} end
local params = {{}}
params[PlayerOperations.PARAM_COMMEMORATION_TYPE] = {dedication_index}
UI.RequestPlayerOperation(me, PlayerOperations.COMMEMORATE, params)
print("OK:DEDICATION_CHOSEN|" .. row.CommemorationType)
print("{SENTINEL}")
"""


def build_available_governments_query() -> str:
    """List unlocked governments with slot info (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pCulture = Players[me]:GetCulture()
local curGov = pCulture:GetCurrentGovernment()
for row in GameInfo.Governments() do
    local unlocked = pCulture:IsGovernmentUnlocked(row.Index)
    if unlocked then
        local isCurrent = (row.Index == curGov)
        local slots = {{}}
        for slotRow in GameInfo.Government_SlotCounts() do
            if slotRow.GovernmentType == row.GovernmentType then
                for i = 1, slotRow.NumSlots do
                    table.insert(slots, slotRow.GovernmentSlotType)
                end
            end
        end
        local slotStr = table.concat(slots, ",")
        local name = Locale.Lookup(row.Name)
        local bonus = ""
        if row.BonusType then
            local bRow = GameInfo.GovernmentBonuses and GameInfo.GovernmentBonuses[row.BonusType]
            if bRow then bonus = Locale.Lookup(bRow.Description or "") end
        end
        local tag = isCurrent and "CURRENT" or "AVAILABLE"
        print("GOV|" .. row.GovernmentType .. "|" .. row.Index .. "|" .. tag .. "|" .. name .. "|" .. slotStr .. "|" .. bonus)
    end
end
print("{SENTINEL}")
"""


def build_change_government(gov_type: str) -> str:
    """Switch government type (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pCulture = Players[me]:GetCulture()
local row = GameInfo.Governments["{gov_type}"]
if row == nil then {_bail(f"ERR:GOV_NOT_FOUND|{gov_type}")} end
if not pCulture:IsGovernmentUnlocked(row.Index) then {_bail(f"ERR:GOV_LOCKED|{gov_type} is not unlocked")} end
if row.Index == pCulture:GetCurrentGovernment() then {_bail(f"ERR:ALREADY_CURRENT|{gov_type} is already your government")} end
pCulture:SetGovernmentChangeConsidered(true)
pCulture:RequestChangeGovernment(row.Index)
print("OK:GOVERNMENT_CHANGED|{gov_type}|" .. Locale.Lookup(row.Name))
print("{SENTINEL}")
"""


def parse_policies_response(lines: list[str]) -> GovernmentStatus:
    """Parse GOV|, SLOT|, AVAIL| lines from build_policies_query."""
    gov_name = "None"
    gov_type = "NONE"
    slots: list[PolicySlot] = []
    available: list[PolicyInfo] = []

    for line in lines:
        if line.startswith("GOV|"):
            parts = line.split("|")
            if len(parts) >= 4:
                gov_type = parts[1]
                gov_name = parts[2]
        elif line.startswith("SLOT|"):
            parts = line.split("|")
            if len(parts) >= 5:
                policy_type = None if parts[3] == "NONE" else parts[3]
                policy_name = None if parts[4] == "Empty" else parts[4]
                slots.append(PolicySlot(
                    slot_index=int(parts[1]),
                    slot_type=parts[2],
                    current_policy=policy_type,
                    current_policy_name=policy_name,
                ))
        elif line.startswith("AVAIL|"):
            parts = line.split("|")
            if len(parts) >= 5:
                available.append(PolicyInfo(
                    policy_type=parts[1],
                    name=parts[2],
                    description=parts[3],
                    slot_type=parts[4],
                ))

    return GovernmentStatus(
        government_name=gov_name,
        government_type=gov_type,
        slots=slots,
        available_policies=available,
    )


def parse_governors_response(lines: list[str]) -> GovernorStatus:
    """Parse STATUS|, APPOINTED|, GOV_PROMO|, AVAILABLE| lines from build_governors_query."""
    pts_avail = 0
    pts_spent = 0
    can_appoint = False
    appointed: list[AppointedGovernor] = []
    available: list[GovernorInfo] = []
    # Collect promotions keyed by governor_type, then attach after
    promos_by_gov: dict[str, list[GovernorPromotion]] = {}

    for line in lines:
        if line.startswith("STATUS|"):
            parts = line.split("|")
            if len(parts) >= 4:
                pts_avail = int(parts[1])
                pts_spent = int(parts[2])
                can_appoint = parts[3] == "1"
        elif line.startswith("APPOINTED|"):
            parts = line.split("|")
            if len(parts) >= 7:
                appointed.append(AppointedGovernor(
                    governor_type=parts[1],
                    name=parts[2],
                    assigned_city_id=int(parts[4]),
                    assigned_city_name=parts[5],
                    is_established=parts[6] == "1",
                    turns_to_establish=int(parts[7]) if len(parts) >= 8 else 0,
                ))
        elif line.startswith("GOV_PROMO|"):
            parts = line.split("|")
            if len(parts) >= 5:
                gov_type = parts[1]
                promos_by_gov.setdefault(gov_type, []).append(GovernorPromotion(
                    promotion_type=parts[2],
                    name=parts[3],
                    description=parts[4],
                ))
        elif line.startswith("AVAILABLE|"):
            parts = line.split("|")
            if len(parts) >= 4:
                available.append(GovernorInfo(
                    governor_type=parts[1],
                    name=parts[2],
                    title=parts[3],
                ))

    # Attach promotions to their governors
    for gov in appointed:
        gov.available_promotions = promos_by_gov.get(gov.governor_type, [])

    return GovernorStatus(
        points_available=pts_avail,
        points_spent=pts_spent,
        can_appoint=can_appoint,
        appointed=appointed,
        available_to_appoint=available,
    )


def parse_unit_promotions_response(lines: list[str]) -> UnitPromotionStatus:
    """Parse UNIT| and PROMO| lines from build_unit_promotions_query."""
    unit_id = 0
    unit_index = 0
    unit_type = "UNKNOWN"
    promotions: list[PromotionOption] = []

    for line in lines:
        if line.startswith("ERR:"):
            raise ValueError(line[4:])
        if line.startswith("UNIT|"):
            parts = line.split("|")
            if len(parts) >= 4:
                unit_id = int(parts[1])
                unit_index = int(parts[2])
                unit_type = parts[3]
        elif line.startswith("PROMO|"):
            parts = line.split("|")
            if len(parts) >= 4:
                promotions.append(PromotionOption(
                    promotion_type=parts[1],
                    name=parts[2],
                    description=parts[3],
                ))

    return UnitPromotionStatus(
        unit_id=unit_id,
        unit_index=unit_index,
        unit_type=unit_type,
        promotions=promotions,
    )


def parse_city_states_response(lines: list[str]) -> EnvoyStatus:
    """Parse TOKENS| and CS| lines from build_city_states_query."""
    tokens = 0
    city_states: list[CityStateInfo] = []

    for line in lines:
        if line.startswith("TOKENS|"):
            tokens = int(line.split("|")[1])
        elif line.startswith("CS|"):
            parts = line.split("|")
            if len(parts) >= 8:
                city_states.append(CityStateInfo(
                    player_id=int(parts[1]),
                    name=parts[2],
                    city_state_type=parts[3],
                    envoys_sent=int(parts[4]),
                    suzerain_id=int(parts[5]),
                    suzerain_name=parts[6],
                    can_send_envoy=parts[7] == "1",
                ))

    return EnvoyStatus(tokens_available=tokens, city_states=city_states)


def parse_dedications_response(lines: list[str]) -> DedicationStatus:
    """Parse STATUS|, ACTIVE|, and CHOICE| lines from build_dedications_query."""
    age_type = "Normal"
    era = 0
    era_score = 0
    dark_threshold = 0
    golden_threshold = 0
    selections_allowed = 0
    active: list[str] = []
    choices: list[DedicationChoice] = []

    for line in lines:
        if line.startswith("STATUS|"):
            parts = line.split("|")
            if len(parts) >= 7:
                age_type = parts[1]
                era = int(parts[2])
                era_score = int(parts[3])
                dark_threshold = int(parts[4])
                golden_threshold = int(parts[5])
                selections_allowed = int(parts[6])
        elif line.startswith("ACTIVE|"):
            active.append(line.split("|", 1)[1])
        elif line.startswith("CHOICE|"):
            parts = line.split("|", 5)
            if len(parts) >= 6:
                choices.append(DedicationChoice(
                    index=int(parts[1]),
                    name=parts[2],
                    normal_desc=parts[3],
                    golden_desc=parts[4],
                    dark_desc=parts[5],
                ))

    return DedicationStatus(
        age_type=age_type,
        era=era,
        era_score=era_score,
        dark_threshold=dark_threshold,
        golden_threshold=golden_threshold,
        selections_allowed=selections_allowed,
        active=active,
        choices=choices,
    )
