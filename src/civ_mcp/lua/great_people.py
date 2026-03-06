"""Great People domain — Lua builders and parsers."""

from __future__ import annotations

from civ_mcp.lua._helpers import SENTINEL, _bail, _bail_lua, _int, _lua_get_unit
from civ_mcp.lua.models import GPAdvisorCity, GPAdvisorResult, GreatPersonInfo


def build_great_people_query() -> str:
    """Get available Great People and recruitment progress (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local gp = Game.GetGreatPeople()
if gp == nil then {_bail("ERR:NO_GP_SYSTEM|Great People system not available")} end
local timeline = gp:GetTimeline()
if timeline == nil then {_bail("ERR:NO_TIMELINE|No great people timeline")} end
local function getAbility(ind)
    if ind.ActionEffectTextOverride and ind.ActionEffectTextOverride ~= "" then
        local ok, t = pcall(Locale.Lookup, ind.ActionEffectTextOverride)
        if ok and t and t ~= "" and t ~= ind.ActionEffectTextOverride then return t end
    end
    local locKey = "LOC_GREATPERSON_" .. string.gsub(ind.GreatPersonIndividualType, "GREAT_PERSON_INDIVIDUAL_", "") .. "_ACTIVE"
    local ok2, t2 = pcall(Locale.Lookup, locKey)
    if ok2 and t2 and t2 ~= locKey and t2 ~= "" then return t2 end
    local parts = {{}}
    for mod in GameInfo.GreatPersonIndividualActionModifiers() do
        if mod.GreatPersonIndividualType == ind.GreatPersonIndividualType then
            local mrow = GameInfo.Modifiers[mod.ModifierId]
            if mrow then
                local args = {{}}
                for arg in GameInfo.ModifierArguments() do
                    if arg.ModifierId == mod.ModifierId then args[arg.Name] = arg.Value end
                end
                local amt = args["Amount"] or ""
                local yt = args["YieldType"] and string.gsub(args["YieldType"], "YIELD_", "") or ""
                local mt = mrow.ModifierType
                local matched = false
                if string.find(mt, "ADJACENT") and string.find(mt, "YIELD") and amt ~= "" then
                    local feat = args["FeatureType"] and string.gsub(args["FeatureType"], "FEATURE_", "") or "feature"
                    table.insert(parts, "+" .. amt .. " " .. yt .. " per adjacent " .. feat .. " tile")
                    matched = true
                elseif string.find(mt, "GRANT_YIELD") and amt ~= "" then
                    table.insert(parts, "+" .. amt .. " " .. yt)
                    matched = true
                elseif string.find(mt, "GRANT_PRODUCTION") and amt ~= "" then
                    table.insert(parts, "+" .. amt .. " production toward current build")
                    matched = true
                elseif string.find(mt, "GRANT_INFLUENCE") and amt ~= "" then
                    table.insert(parts, "+" .. amt .. " envoy tokens")
                    matched = true
                elseif string.find(mt, "GRANT_UNIT") then
                    local ut = args["UnitType"] or ""
                    if ut ~= "" then
                        local uRow = GameInfo.Units[ut]
                        table.insert(parts, "free " .. (uRow and Locale.Lookup(uRow.Name) or ut:gsub("UNIT_", "")))
                    else
                        table.insert(parts, "free military unit")
                    end
                    matched = true
                elseif string.find(mt, "RANDOM_TECHNOLOGY_BOOST") then
                    local era = args["StartEraType"] or args["EraType"] or ""
                    era = era:gsub("ERA_", "")
                    if era ~= "" then
                        table.insert(parts, (amt ~= "" and amt or "1") .. " random eurekas from " .. era .. " era onward")
                    else
                        table.insert(parts, (amt ~= "" and amt or "1") .. " random eurekas")
                    end
                    matched = true
                elseif string.find(mt, "GRANT_TECH") then
                    table.insert(parts, "free tech boost")
                    matched = true
                elseif string.find(mt, "GOVERNOR") then
                    table.insert(parts, "+" .. (amt ~= "" and amt or "1") .. " governor title(s)")
                    matched = true
                elseif string.find(mt, "GREAT_WORK") or string.find(mt, "CREATE_GREAT_WORK") then
                    local gwType = args["GreatWorkType"] or ""
                    if gwType ~= "" then
                        table.insert(parts, "creates " .. gwType:gsub("GREATWORK_", ""))
                    else
                        table.insert(parts, "creates great work")
                    end
                    matched = true
                elseif string.find(mt, "GRANT_RESOURCE") then
                    local resType = args["ResourceType"] or ""
                    table.insert(parts, "+" .. (amt ~= "" and amt or "1") .. " " .. resType:gsub("RESOURCE_", ""))
                    matched = true
                elseif string.find(mt, "ADJUST_SCIENCE") and amt ~= "" then
                    table.insert(parts, "+" .. amt .. " science to adjacent tiles")
                    matched = true
                elseif string.find(mt, "ADJUST_CULTURE") and amt ~= "" then
                    table.insert(parts, "+" .. amt .. " culture to adjacent tiles")
                    matched = true
                elseif string.find(mt, "TOURISM") and amt ~= "" then
                    table.insert(parts, "+" .. amt .. " tourism")
                    matched = true
                elseif string.find(mt, "ADJUST_POPULATION") and amt ~= "" then
                    table.insert(parts, "+" .. amt .. " population in city")
                    matched = true
                end
                if not matched then
                    local desc = mt:gsub("MODIFIER_PLAYER_", ""):gsub("MODIFIER_", "")
                    if amt ~= "" then desc = desc .. " (amount=" .. amt .. ")" end
                    table.insert(parts, desc)
                end
            end
        end
    end
    for mod in GameInfo.GreatPersonIndividualBirthModifiers() do
        if mod.GreatPersonIndividualType == ind.GreatPersonIndividualType then
            local mrow = GameInfo.Modifiers[mod.ModifierId]
            if mrow then
                local mt = mrow.ModifierType
                if string.find(mt, "COMBAT_STRENGTH") then table.insert(parts, "combat bonus to nearby units (passive)")
                elseif string.find(mt, "MOVEMENT") then table.insert(parts, "movement bonus to nearby units (passive)")
                else
                    table.insert(parts, mt:gsub("MODIFIER_", "") .. " (passive)")
                end
            end
        end
    end
    if ind.GreatWorkCollection and type(ind.GreatWorkCollection) == "table" then
        local n = 0
        for _ in pairs(ind.GreatWorkCollection) do n = n + 1 end
        if n > 0 then table.insert(parts, "creates " .. n .. " Great Works") end
    end
    if #parts > 0 then return table.concat(parts, ", ") end
    return ""
end
for _, entry in ipairs(timeline) do
    if entry.Class ~= nil and entry.Individual ~= nil then
    local classInfo = GameInfo.GreatPersonClasses[entry.Class]
    local indivInfo = GameInfo.GreatPersonIndividuals[entry.Individual]
    if classInfo and indivInfo then
        local className = Locale.Lookup(classInfo.Name)
        local indivName = Locale.Lookup(indivInfo.Name)
        local eraInfo = GameInfo.Eras[entry.Era]
        local eraName = eraInfo and Locale.Lookup(eraInfo.Name) or "Unknown"
        local claimant = "Unclaimed"
        if entry.Claimant and entry.Claimant >= 0 then
            local cfg = PlayerConfigurations[entry.Claimant]
            if cfg then claimant = Locale.Lookup(cfg:GetCivilizationShortDescription()) end
        end
        local myPoints = 0
        local threshold = entry.Cost or 0
        local pGP = Players[me]:GetGreatPeoplePoints()
        if pGP then
            myPoints = pGP:GetPointsTotal(entry.Class)
        end
        local ability = getAbility(indivInfo)
        local goldCost = 0
        local faithCost = 0
        local canRecruit = false
        pcall(function()
            goldCost = gp:GetPatronizeCost(me, entry.Individual, 2)
            faithCost = gp:GetPatronizeCost(me, entry.Individual, 5)
            canRecruit = gp:CanRecruitPerson(me, entry.Individual)
        end)
        local costStr = "gold:" .. goldCost .. ",faith:" .. faithCost .. ",recruit:" .. tostring(canRecruit)
        print("GP|" .. className .. "|" .. indivName .. "|" .. eraName .. "|" .. threshold .. "|" .. claimant .. "|" .. myPoints .. "|" .. ability .. "|" .. costStr .. "|" .. entry.Individual)
    end
    end
end
print("{SENTINEL}")
"""


def build_recruit_great_person(individual_id: int) -> str:
    """Recruit a Great Person with accumulated GP points (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local gp = Game.GetGreatPeople()
if not gp:CanRecruitPerson(me, {individual_id}) then
    local ind = GameInfo.GreatPersonIndividuals[{individual_id}]
    local name = ind and Locale.Lookup(ind.Name) or "unknown"
    {_bail_lua('"ERR:CANNOT_RECRUIT|Not enough GP points to recruit " .. name')}
end
local kParams = {{}}
kParams[PlayerOperations.PARAM_GREAT_PERSON_INDIVIDUAL_TYPE] = {individual_id}
UI.RequestPlayerOperation(me, PlayerOperations.RECRUIT_GREAT_PERSON, kParams)
local ind = GameInfo.GreatPersonIndividuals[{individual_id}]
local name = ind and Locale.Lookup(ind.Name) or "unknown"
print("OK:RECRUITED|" .. name)
print("{SENTINEL}")
"""


def build_patronize_great_person(
    individual_id: int, yield_type: str = "YIELD_GOLD"
) -> str:
    """Buy a Great Person with gold or faith (InGame context)."""
    yield_idx = 2 if yield_type == "YIELD_GOLD" else 5  # YieldTypes.GOLD=2, FAITH=5
    return f"""
local me = Game.GetLocalPlayer()
local gp = Game.GetGreatPeople()
if not gp:CanPatronizePerson(me, {individual_id}, {yield_idx}) then
    local ind = GameInfo.GreatPersonIndividuals[{individual_id}]
    local name = ind and Locale.Lookup(ind.Name) or "unknown"
    local cost = gp:GetPatronizeCost(me, {individual_id}, {yield_idx})
    {_bail_lua(f'"ERR:CANNOT_PATRONIZE|Cannot buy " .. name .. " (cost: " .. cost .. " {yield_type.replace("YIELD_", "").lower()})"')}
end
local kParams = {{}}
kParams[PlayerOperations.PARAM_GREAT_PERSON_INDIVIDUAL_TYPE] = {individual_id}
kParams[PlayerOperations.PARAM_YIELD_TYPE] = {yield_idx}
UI.RequestPlayerOperation(me, PlayerOperations.PATRONIZE_GREAT_PERSON, kParams)
local ind = GameInfo.GreatPersonIndividuals[{individual_id}]
local name = ind and Locale.Lookup(ind.Name) or "unknown"
local cost = gp:GetPatronizeCost(me, {individual_id}, {yield_idx})
print("OK:PATRONIZED|" .. name .. "|cost:" .. cost .. " {yield_type.replace("YIELD_", "").lower()}")
print("{SENTINEL}")
"""


def build_reject_great_person(individual_id: int) -> str:
    """Pass on a Great Person (costs faith). InGame context."""
    return f"""
local me = Game.GetLocalPlayer()
local gp = Game.GetGreatPeople()
if not gp:CanRejectPerson(me, {individual_id}) then
    local ind = GameInfo.GreatPersonIndividuals[{individual_id}]
    local name = ind and Locale.Lookup(ind.Name) or "unknown"
    {_bail_lua('"ERR:CANNOT_REJECT|Cannot reject " .. name')}
end
local cost = gp:GetRejectCost(me, {individual_id})
local kParams = {{}}
kParams[PlayerOperations.PARAM_GREAT_PERSON_INDIVIDUAL_TYPE] = {individual_id}
UI.RequestPlayerOperation(me, PlayerOperations.REJECT_GREAT_PERSON, kParams)
local ind = GameInfo.GreatPersonIndividuals[{individual_id}]
local name = ind and Locale.Lookup(ind.Name) or "unknown"
print("OK:REJECTED|" .. name .. "|faith_cost:" .. cost)
print("{SENTINEL}")
"""


def build_activate_great_person(unit_index: int) -> str:
    """Activate a Great Person on their matching district (InGame context).

    Great Prophets use UNITOPERATION_FOUND_RELIGION instead of the generic
    UNITCOMMAND_ACTIVATE_GREAT_PERSON used by all other Great People.
    """
    return f"""
{_lua_get_unit(unit_index)}
local uInfo = GameInfo.Units[unit:GetType()]
local uName = uInfo and uInfo.UnitType or "UNKNOWN"
local ux, uy = unit:GetX(), unit:GetY()

-- Great Prophets use a different activation path
if uName == "UNIT_GREAT_PROPHET" then
    local opRow = GameInfo.UnitOperations["UNITOPERATION_FOUND_RELIGION"]
    if not opRow then {_bail("ERR:CANNOT_ACTIVATE|UNITOPERATION_FOUND_RELIGION not found in GameInfo")} end
    local params = {{}}
    params[UnitOperationTypes.PARAM_X] = ux
    params[UnitOperationTypes.PARAM_Y] = uy
    local canStart = UnitManager.CanStartOperation(unit, opRow.Hash, nil, params, true)
    if not canStart then
        {_bail('ERR:CANNOT_ACTIVATE|Great Prophet must be on a completed Holy Site with moves remaining (at " .. ux .. "," .. uy .. ")')}
    end
    UnitManager.RequestOperation(unit, opRow.Hash, params)
    print("OK:GP_ACTIVATED|" .. Locale.Lookup(unit:GetName()) .. " (" .. uName .. ") founded religion at " .. ux .. "," .. uy)
    print("{SENTINEL}"); return
end

-- All other Great People: standard activation command
local cmdHash = GameInfo.UnitCommands["UNITCOMMAND_ACTIVATE_GREAT_PERSON"].Hash
local can, failTable = UnitManager.CanStartCommand(unit, cmdHash, nil, true)
if not can then
    -- Extract game's own requirement strings from the failure table.
    -- Structure: top-level strings are category names (skip); nested tables hold
    -- sequential string arrays — requirements ("Must be...") and effect descriptions.
    local requirements = {{}}
    if failTable then
        for _, v in pairs(failTable) do
            if type(v) == "table" then
                for _, s in pairs(v) do
                    if type(s) == "string" and s ~= "" then
                        -- Strip icon codes like [ICON_GreatWork_Artifact]
                        local clean = s:gsub("%[ICON_[^%]]*%]", ""):gsub("%s+", " "):match("^%s*(.-)%s*$")
                        if clean and clean ~= "" then
                            table.insert(requirements, clean)
                        end
                    end
                end
            end
        end
    end
    -- Also gather valid activation tiles as a fallback hint
    local gp = unit:GetGreatPerson()
    local charges = gp and gp:GetActionCharges() or -1
    local validTiles = {{}}
    if gp then
        local ok, plots = pcall(function() return gp:GetActivationHighlightPlots() end)
        if ok and plots then
            for i = 1, math.min(#plots, 5) do
                local vPlot = Map.GetPlotByIndex(plots[i])
                if vPlot then
                    local vdt = vPlot:GetDistrictType()
                    local vdtName = "none"
                    if vdt >= 0 then
                        local vdInfo = GameInfo.Districts[vdt]
                        if vdInfo then vdtName = vdInfo.DistrictType end
                    end
                    table.insert(validTiles, vPlot:GetX() .. "," .. vPlot:GetY() .. "=" .. vdtName)
                end
            end
        end
    end
    local reqStr = #requirements > 0 and " Requirements: " .. table.concat(requirements, "; ") or ""
    local tilesStr = #validTiles > 0 and " Valid tiles: " .. table.concat(validTiles, "; ") or " No valid activation tiles found."
    local classStr = ""
    local classHint = ""
    pcall(function()
        local gpClass = uInfo and uInfo.GreatPersonClass or nil
        if gpClass then
            classStr = " class=" .. gpClass
            if gpClass == "GREAT_PERSON_CLASS_WRITER" or gpClass == "GREAT_PERSON_CLASS_ARTIST" or gpClass == "GREAT_PERSON_CLASS_MUSICIAN" then
                classHint = " Hint: Must be on a city center with an empty Great Work slot of the matching type."
            end
        end
    end)
    {_bail_lua('"ERR:CANNOT_ACTIVATE|" .. Locale.Lookup(unit:GetName()) .. " (" .. uName .. ")" .. classStr .. " at (" .. ux .. "," .. uy .. ") charges=" .. charges .. "." .. reqStr .. tilesStr .. classHint')}
end
-- Track charges before activation to compute remaining
local chargesBefore = -1
pcall(function() chargesBefore = unit:GetGreatPerson():GetActionCharges() end)
UnitManager.RequestCommand(unit, cmdHash, {{}})
-- Report remaining charges so agent knows whether to activate again
local remCharges = -1
pcall(function()
    local gp2 = unit:GetGreatPerson()
    if gp2 then
        remCharges = gp2:GetActionCharges() or 0
        -- If GetActionCharges still returns 0 and we had charges before,
        -- the activation consumed one charge
        if remCharges == 0 and chargesBefore > 0 then
            remCharges = chargesBefore - 1
        end
    end
end)
local chargeStr = ""
if remCharges > 0 then chargeStr = " charges_remaining=" .. remCharges .. " — activate again to use next charge" end
print("OK:GP_ACTIVATED|" .. Locale.Lookup(unit:GetName()) .. " (" .. uName .. ") at " .. ux .. "," .. uy .. chargeStr)
print("{SENTINEL}")
"""


def parse_great_people_response(lines: list[str]) -> list[GreatPersonInfo]:
    """Parse GP| lines from build_great_people_query."""
    results: list[GreatPersonInfo] = []
    for line in lines:
        if line.startswith("GP|"):
            parts = line.split("|")
            if len(parts) >= 7:
                ability = parts[7] if len(parts) >= 8 else ""
                gold_cost = 0
                faith_cost = 0
                can_recruit = False
                individual_id = 0
                if len(parts) >= 10:
                    cost_str = parts[8]  # "gold:X,faith:Y,recruit:true/false"
                    for kv in cost_str.split(","):
                        k, _, v = kv.partition(":")
                        if k == "gold":
                            gold_cost = _int(v) if v else 0
                        elif k == "faith":
                            faith_cost = _int(v) if v else 0
                        elif k == "recruit":
                            can_recruit = v == "true"
                    individual_id = _int(parts[9])
                results.append(
                    GreatPersonInfo(
                        class_name=parts[1],
                        individual_name=parts[2],
                        era_name=parts[3],
                        cost=_int(parts[4]),
                        claimant=parts[5],
                        player_points=_int(parts[6]),
                        ability=ability,
                        gold_cost=gold_cost,
                        faith_cost=faith_cost,
                        can_recruit=can_recruit,
                        individual_id=individual_id,
                    )
                )
    return results


def build_gp_advisor_query(unit_index: int) -> str:
    """InGame context: list candidate cities for a Great Person activation.

    Reports each city that has the matching district, with activation
    eligibility, distance from GP, city yield, and great work slot info.
    """
    sentinel = SENTINEL
    return f"""
{_lua_get_unit(unit_index)}
local uInfo = GameInfo.Units[unit:GetType()]
if not uInfo then {_bail("ERR:UNIT_INFO_NOT_FOUND")} end
local gpClass = ""
pcall(function() gpClass = uInfo.GreatPersonClass end)
if gpClass == "" then {_bail("ERR:NOT_A_GREAT_PERSON")} end
local classToDistrict = {{
    GREAT_PERSON_CLASS_SCIENTIST = "DISTRICT_CAMPUS",
    GREAT_PERSON_CLASS_ENGINEER = "DISTRICT_INDUSTRIAL_ZONE",
    GREAT_PERSON_CLASS_MERCHANT = "DISTRICT_COMMERCIAL_HUB",
    GREAT_PERSON_CLASS_WRITER = "DISTRICT_THEATER",
    GREAT_PERSON_CLASS_ARTIST = "DISTRICT_THEATER",
    GREAT_PERSON_CLASS_MUSICIAN = "DISTRICT_THEATER",
    GREAT_PERSON_CLASS_PROPHET = "DISTRICT_HOLY_SITE",
    GREAT_PERSON_CLASS_GENERAL = "DISTRICT_ENCAMPMENT",
    GREAT_PERSON_CLASS_ADMIRAL = "DISTRICT_HARBOR",
}}
local classToYield = {{
    GREAT_PERSON_CLASS_SCIENTIST = "YIELD_SCIENCE",
    GREAT_PERSON_CLASS_ENGINEER = "YIELD_PRODUCTION",
    GREAT_PERSON_CLASS_MERCHANT = "YIELD_GOLD",
    GREAT_PERSON_CLASS_WRITER = "YIELD_CULTURE",
    GREAT_PERSON_CLASS_ARTIST = "YIELD_CULTURE",
    GREAT_PERSON_CLASS_MUSICIAN = "YIELD_CULTURE",
    GREAT_PERSON_CLASS_PROPHET = "YIELD_FAITH",
    GREAT_PERSON_CLASS_GENERAL = "YIELD_PRODUCTION",
    GREAT_PERSON_CLASS_ADMIRAL = "YIELD_GOLD",
}}
local targetDist = classToDistrict[gpClass]
if not targetDist then {_bail("ERR:UNKNOWN_GP_CLASS")} end
local charges = -1
local gp = unit:GetGreatPerson()
if gp then pcall(function() charges = gp:GetActionCharges() end) end
print("GP_INFO|" .. Locale.Lookup(unit:GetName()) .. "|" .. gpClass .. "|" .. targetDist .. "|" .. unit:GetX() .. "|" .. unit:GetY() .. "|" .. charges)
local validPlotSet = {{}}
if gp then
    pcall(function()
        local plots = gp:GetActivationHighlightPlots()
        if plots then
            for _, pIdx in ipairs(plots) do validPlotSet[pIdx] = true end
        end
    end)
end
local yieldType = classToYield[gpClass]
local yieldIdx = -1
if yieldType then pcall(function() yieldIdx = GameInfo.Yields[yieldType].Index end) end
local isCultural = gpClass == "GREAT_PERSON_CLASS_WRITER" or gpClass == "GREAT_PERSON_CLASS_ARTIST" or gpClass == "GREAT_PERSON_CLASS_MUSICIAN"
local targetDistInfo = GameInfo.Districts[targetDist]
if not targetDistInfo then {_bail("ERR:DISTRICT_NOT_FOUND")} end
for i, city in Players[me]:GetCities():Members() do
    pcall(function()
        local districts = city:GetDistricts()
        if districts:HasDistrict(targetDistInfo.Index, true) then
            local dObj = districts:GetDistrict(targetDistInfo.Index)
            if dObj then
                local dx, dy = dObj:GetX(), dObj:GetY()
                local pPlot = Map.GetPlot(dx, dy)
                local plotIdx = pPlot:GetIndex()
                local canAct = validPlotSet[plotIdx] == true
                local dist = Map.GetPlotDistance(unit:GetX(), unit:GetY(), dx, dy)
                local cityYield = 0
                if yieldIdx >= 0 then
                    pcall(function() cityYield = city:GetYield(yieldIdx) end)
                end
                local slotsFree = -1
                local slotsTotal = -1
                if isCultural then
                    pcall(function()
                        local bldgs = city:GetBuildings()
                        local free = 0
                        local total = 0
                        for bld in GameInfo.Buildings() do
                            if bldgs:HasBuilding(bld.Index) then
                                for s = 0, 5 do
                                    local ok2, gwType = pcall(function() return bldgs:GetGreatWorkSlotType(bld.Index, s) end)
                                    if ok2 and gwType and gwType >= 0 then
                                        total = total + 1
                                        local ok3, gw = pcall(function() return bldgs:GetGreatWorkInSlot(bld.Index, s) end)
                                        if not ok3 or not gw or gw < 0 then
                                            free = free + 1
                                        end
                                    end
                                end
                            end
                        end
                        slotsFree = free
                        slotsTotal = total
                    end)
                end
                local cn = (Locale.Lookup(city:GetName()):gsub("|", "/"))
                print("GP_CITY|" .. cn .. "|" .. city:GetID() .. "|" .. dx .. "|" .. dy .. "|" .. tostring(canAct) .. "|" .. dist .. "|" .. cityYield .. "|" .. slotsFree .. "|" .. slotsTotal)
            end
        end
    end)
end
print("{sentinel}")
"""


def parse_gp_advisor_response(lines: list[str]) -> GPAdvisorResult | None:
    """Parse GP_INFO and GP_CITY lines from build_gp_advisor_query."""
    gp_name = ""
    gp_class = ""
    target_district = ""
    gp_x = 0
    gp_y = 0
    charges = -1
    cities: list[GPAdvisorCity] = []

    for line in lines:
        if line.startswith("GP_INFO|"):
            parts = line.split("|")
            if len(parts) >= 7:
                gp_name = parts[1]
                gp_class = parts[2]
                target_district = parts[3]
                gp_x = int(parts[4])
                gp_y = int(parts[5])
                charges = int(parts[6])
        elif line.startswith("GP_CITY|"):
            parts = line.split("|")
            if len(parts) >= 10:
                try:
                    cities.append(
                        GPAdvisorCity(
                            city_name=parts[1],
                            city_id=int(parts[2]),
                            district_x=int(parts[3]),
                            district_y=int(parts[4]),
                            can_activate=parts[5] == "true",
                            distance=int(parts[6]),
                            city_yield=_int(parts[7]),
                            slots_free=int(parts[8]),
                            slots_total=int(parts[9]),
                        )
                    )
                except (ValueError, IndexError):
                    continue

    if not gp_name:
        return None
    return GPAdvisorResult(
        gp_name=gp_name,
        gp_class=gp_class,
        target_district=target_district,
        gp_x=gp_x,
        gp_y=gp_y,
        charges=charges,
        cities=cities,
    )
