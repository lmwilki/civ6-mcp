"""Economy domain — Lua builders and parsers."""

from __future__ import annotations

from civ_mcp.lua._helpers import SENTINEL, _bail, _bail_lua, _lua_get_unit
from civ_mcp.lua.models import (
    CongressProposal,
    CongressResolution,
    GreatPersonInfo,
    TradeDestination,
    TraderInfo,
    TradeRouteStatus,
    WorldCongressStatus,
)


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
                local amt = ""
                for arg in GameInfo.ModifierArguments() do
                    if arg.ModifierId == mod.ModifierId and arg.Name == "Amount" then amt = arg.Value end
                end
                local mt = mrow.ModifierType
                if string.find(mt, "GRANT_YIELD") and amt ~= "" then
                    local yt = ""
                    for arg in GameInfo.ModifierArguments() do
                        if arg.ModifierId == mod.ModifierId and arg.Name == "YieldType" then yt = string.gsub(arg.Value, "YIELD_", "") end
                    end
                    table.insert(parts, "+" .. amt .. " " .. yt)
                elseif string.find(mt, "GRANT_PRODUCTION") and amt ~= "" then table.insert(parts, "+" .. amt .. " production toward current build")
                elseif string.find(mt, "GRANT_INFLUENCE") and amt ~= "" then table.insert(parts, "+" .. amt .. " envoy tokens")
                elseif string.find(mt, "GRANT_UNIT") then table.insert(parts, "free military unit")
                elseif string.find(mt, "GRANT_TECH") then table.insert(parts, "free tech boost")
                elseif string.find(mt, "ADJUST_SCIENCE") and amt ~= "" then table.insert(parts, "+" .. amt .. " science to adjacent tiles")
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


def build_trade_routes_query() -> str:
    """Get trade route capacity, active routes with enriched data (InGame).

    Reads route records from each city's GetOutgoingRoutes(), cross-references
    with actual trader units to detect ghost routes.  Enriches each route with
    yields, religious pressure, city-state quest status, and trading posts.

    NOTE: Must run in InGame context for GetOutgoingRoutes() and TradeManager.
    """
    return f"""
local me = Game.GetLocalPlayer()
local pTrade = Players[me]:GetTrade()
local cap = pTrade:GetOutgoingRouteCapacity()
local tm = Game.GetTradeManager()
local qm = Game.GetQuestsManager()
local tradeQI = GameInfo.Quests["QUEST_SEND_TRADE_ROUTE"]
local tradeQIdx = tradeQI and tradeQI.Index or -1
local yN = {{"F","P","G","S","C","A"}}
local function fmtY(tbl)
    if not tbl then return "" end
    local s = ""
    for _, e in ipairs(tbl) do
        if e.Amount and e.Amount > 0 then
            local idx = e.YieldIndex + 1
            if idx >= 1 and idx <= 6 then
                local amt = e.Amount
                if amt == math.floor(amt) then amt = math.floor(amt) end
                s = s .. yN[idx] .. amt
            end
        end
    end
    return s
end
-- Build set of valid trader unit IDs
local traderUIDs = {{}}
for _, unit in Players[me]:GetUnits():Members() do
    local x = unit:GetX()
    if x ~= -9999 then
        local uType = unit:GetType()
        if uType then
            local uInfo = GameInfo.Units[uType]
            if uInfo and uInfo.MakeTradeRoute then
                traderUIDs[unit:GetID()] = true
            end
        end
    end
end
-- Collect ALL route records; one route per unique (trader,dest) pair
local seenRoutes = {{}}
local activeCount = 0
local ghostCount = 0
for _, city in Players[me]:GetCities():Members() do
    pcall(function()
        local routes = city:GetTrade():GetOutgoingRoutes()
        if not routes then return end
        for _, r in ipairs(routes) do
            local tid = r.TraderUnitID
            local key = tid .. "_" .. r.DestinationCityPlayer .. "_" .. r.DestinationCityID
            if seenRoutes[key] then return end
            seenRoutes[key] = true
            -- Ghost check: trader unit no longer exists (dead/captured)
            if not traderUIDs[tid] then
                ghostCount = ghostCount + 1
            else
                activeCount = activeCount + 1
                -- Resolve names
                local origCity = Players[r.OriginCityPlayer]:GetCities():FindID(r.OriginCityID)
                local origName = origCity and Locale.Lookup(origCity:GetName()) or "?"
                local destCity = Players[r.DestinationCityPlayer]:GetCities():FindID(r.DestinationCityID)
                local destName = destCity and Locale.Lookup(destCity:GetName()) or "?"
                local isDom = r.DestinationCityPlayer == me
                local ownerName = "Domestic"
                if not isDom then
                    pcall(function()
                        ownerName = Locale.Lookup(PlayerConfigurations[r.DestinationCityPlayer]:GetCivilizationShortDescription())
                    end)
                end
                -- City-state + quest
                local isCS = false
                pcall(function() isCS = Players[r.DestinationCityPlayer]:GetInfluence():CanReceiveInfluence() end)
                local hasQ = false
                if isCS and tradeQIdx >= 0 then
                    pcall(function() hasQ = qm:HasActiveQuestFromPlayer(me, r.DestinationCityPlayer, tradeQIdx) end)
                end
                -- Trading post
                local hasTP = false
                if destCity then pcall(function() hasTP = destCity:GetTrade():HasActiveTradingPost(me) end) end
                -- Religious pressure (bidirectional)
                local pOut, relOut, pIn, relIn = 0, "", 0, ""
                if origCity then
                    local majRel = origCity:GetReligion():GetMajorityReligion()
                    if majRel >= 0 then
                        pcall(function() relOut = Locale.Lookup(GameInfo.Religions[majRel].Name) end)
                        pcall(function()
                            pOut = tm:CalculateDestinationReligiousPressureFromPotentialRoute(r.OriginCityPlayer, r.OriginCityID, r.DestinationCityPlayer, r.DestinationCityID, majRel)
                        end)
                    end
                end
                if destCity then
                    local destRel = destCity:GetReligion():GetMajorityReligion()
                    if destRel >= 0 then
                        pcall(function() relIn = Locale.Lookup(GameInfo.Religions[destRel].Name) end)
                        pcall(function()
                            pIn = tm:CalculateOriginReligiousPressureFromPotentialRoute(r.OriginCityPlayer, r.OriginCityID, r.DestinationCityPlayer, r.DestinationCityID, destRel)
                        end)
                    end
                end
                -- Yields
                local oy = fmtY(r.OriginYields)
                local dy = fmtY(r.DestinationYields)
                print("ROUTE|" .. tid .. "|" .. origName .. "|" .. destName .. "|" .. ownerName .. "|" .. (isDom and "1" or "0") .. "|" .. (isCS and "1" or "0") .. "|" .. (hasQ and "1" or "0") .. "|" .. (hasTP and "1" or "0") .. "|" .. pOut .. "|" .. relOut .. "|" .. pIn .. "|" .. relIn .. "|" .. oy .. "|" .. dy)
            end
        end
    end)
end
-- List idle traders (not on any route)
local routedTraders = {{}}
for k, _ in pairs(seenRoutes) do
    local tid = tonumber(k:match("^(%d+)_"))
    if tid then routedTraders[tid] = true end
end
for _, unit in Players[me]:GetUnits():Members() do
    local x = unit:GetX()
    if x ~= -9999 then
        local uType = unit:GetType()
        if uType then
            local uInfo = GameInfo.Units[uType]
            if uInfo and uInfo.MakeTradeRoute then
                local uid = unit:GetID()
                if not routedTraders[uid] then
                    print("IDLE_TRADER|" .. uid .. "|" .. x .. "," .. unit:GetY())
                end
            end
        end
    end
end
print("TRADE_STATUS|" .. cap .. "|" .. activeCount .. "|" .. ghostCount)
print("{SENTINEL}")
"""


def build_trade_destinations_query(unit_index: int) -> str:
    """List valid trade route destinations with yields, quests, and pressure.

    Tries CanStartOperation first.  If ALL destinations fail (capacity bug
    from stale route counts), falls back to listing reachable cities directly.
    Enriches each destination with yield preview, religious pressure,
    city-state quest status, and trading post info.
    """
    return f"""
{_lua_get_unit(unit_index)}
local opInfo = GameInfo.UnitOperations["UNITOPERATION_MAKE_TRADE_ROUTE"]
if opInfo == nil then {_bail("ERR:NO_TRADE_OP|MAKE_TRADE_ROUTE operation not found")} end
local opHash = opInfo.Hash
local ux, uy = unit:GetX(), unit:GetY()
local tm = Game.GetTradeManager()
local qm = Game.GetQuestsManager()
local tradeQI = GameInfo.Quests["QUEST_SEND_TRADE_ROUTE"]
local tradeQIdx = tradeQI and tradeQI.Index or -1
local yN = {{"F","P","G","S","C","A"}}
-- Calculate* returns flat array of 6 numbers [food,prod,gold,sci,cul,faith]
local function sumFlat(...)
    local s = {{0,0,0,0,0,0}}
    for _, t in ipairs({{...}}) do
        if t then for j = 1, 6 do s[j] = s[j] + (t[j] or 0) end end
    end
    return s
end
local function fmtFlat(arr)
    if not arr then return "" end
    local s = ""
    for j = 1, 6 do
        local v = arr[j]
        if v and v > 0 then
            if v == math.floor(v) then v = math.floor(v) end
            s = s .. yN[j] .. v
        end
    end
    return s
end
-- Find origin city (city the trader is standing in)
local origCity = CityManager.GetCityAt(ux, uy)
local origCID = origCity and origCity:GetID() or 0
local majRel = -1
local relName = ""
if origCity then
    majRel = origCity:GetReligion():GetMajorityReligion()
    if majRel >= 0 then
        pcall(function() relName = Locale.Lookup(GameInfo.Religions[majRel].Name) end)
    end
end
local function enrichDest(i, city, cx, cy, isDom)
    local civ = "Domestic"
    if not isDom then
        pcall(function() civ = Locale.Lookup(PlayerConfigurations[i]:GetCivilizationShortDescription()) end)
    end
    local isCS = false
    pcall(function() isCS = Players[i]:GetInfluence():CanReceiveInfluence() end)
    local hasQ = false
    if isCS and tradeQIdx >= 0 then
        pcall(function() hasQ = qm:HasActiveQuestFromPlayer(me, i, tradeQIdx) end)
    end
    local hasTP = false
    pcall(function() hasTP = city:GetTrade():HasActiveTradingPost(me) end)
    -- Religious pressure (bidirectional)
    local pOut, pIn, relIn = 0, 0, ""
    if majRel >= 0 then
        pcall(function()
            pOut = tm:CalculateDestinationReligiousPressureFromPotentialRoute(me, origCID, i, city:GetID(), majRel)
        end)
    end
    local destRel = city:GetReligion():GetMajorityReligion()
    if destRel >= 0 then
        pcall(function() relIn = Locale.Lookup(GameInfo.Religions[destRel].Name) end)
        pcall(function()
            pIn = tm:CalculateOriginReligiousPressureFromPotentialRoute(me, origCID, i, city:GetID(), destRel)
        end)
    end
    -- Yield preview: Calculate* returns flat arrays of 6 numbers
    local oy, dy = "", ""
    pcall(function()
        local y1 = tm:CalculateOriginYieldsFromPotentialRoute(me, origCID, i, city:GetID())
        local y2 = tm:CalculateOriginYieldsFromPath(me, origCID, i, city:GetID())
        local y3 = tm:CalculateOriginYieldsFromModifiers(me, origCID, i, city:GetID())
        oy = fmtFlat(sumFlat(y1, y2, y3))
    end)
    pcall(function()
        local d1 = tm:CalculateDestinationYieldsFromPotentialRoute(me, origCID, i, city:GetID())
        local d2 = tm:CalculateDestinationYieldsFromPath(me, origCID, i, city:GetID())
        local d3 = tm:CalculateDestinationYieldsFromModifiers(me, origCID, i, city:GetID())
        dy = fmtFlat(sumFlat(d1, d2, d3))
    end)
    print("TDEST|" .. Locale.Lookup(city:GetName()) .. "|" .. civ .. "|" .. cx .. "," .. cy .. "|" .. (isDom and "1" or "0") .. "|" .. (isCS and "1" or "0") .. "|" .. (hasQ and "1" or "0") .. "|" .. (hasTP and "1" or "0") .. "|" .. pOut .. "|" .. relName .. "|" .. pIn .. "|" .. relIn .. "|" .. oy .. "|" .. dy)
end
local found = 0
for i = 0, 62 do
    if Players[i]:IsAlive() and i ~= 63 then
        for _, city in Players[i]:GetCities():Members() do
            local cx, cy = city:GetX(), city:GetY()
            local tParams = {{}}
            tParams[UnitOperationTypes.PARAM_X0] = cx
            tParams[UnitOperationTypes.PARAM_Y0] = cy
            tParams[UnitOperationTypes.PARAM_X1] = ux
            tParams[UnitOperationTypes.PARAM_Y1] = uy
            local can = UnitManager.CanStartOperation(unit, opHash, nil, tParams, true)
            if can then
                enrichDest(i, city, cx, cy, i == me)
                found = found + 1
            end
        end
    end
end
if found == 0 then
    local pTrade = Players[me]:GetTrade()
    local nOut = pTrade:GetNumOutgoingRoutes()
    local capVal = pTrade:GetOutgoingRouteCapacity()
    if nOut >= capVal then
        print("WARN:CAPACITY_FULL|Routes at capacity (" .. nOut .. "/" .. capVal .. "). Trader already on an active route or build Markets/Lighthouses for more slots.")
    else
        print("WARN:CANNOT_START|CanStartOperation blocked all destinations.")
    end
    for i = 0, 62 do
        if Players[i]:IsAlive() and i ~= 63 then
            local atWar = false
            if i ~= me then
                pcall(function()
                    local pDiplo = Players[me]:GetDiplomacy()
                    if pDiplo then atWar = pDiplo:IsAtWarWith(i) end
                end)
            end
            if not atWar then
                for _, city in Players[i]:GetCities():Members() do
                    local cx, cy = city:GetX(), city:GetY()
                    if cx ~= ux or cy ~= uy then
                        enrichDest(i, city, cx, cy, i == me)
                    end
                end
            end
        end
    end
end
print("{SENTINEL}")
"""


def _parse_compact_yields(s: str) -> str:
    """Convert compact yield string like 'F3P2G4' to 'Food:3 Prod:2 Gold:4'.

    Aggregates duplicates (e.g. 'G2G3' -> 'Gold:5') since yield previews
    combine multiple sources (districts, path bonuses, modifiers).
    """
    if not s:
        return ""
    _names = {
        "F": "Food",
        "P": "Prod",
        "G": "Gold",
        "S": "Sci",
        "C": "Cul",
        "A": "Faith",
    }
    totals: dict[str, float] = {}
    i = 0
    while i < len(s):
        letter = s[i]
        i += 1
        num = ""
        while i < len(s) and (s[i].isdigit() or s[i] == "."):
            num += s[i]
            i += 1
        if letter in _names and num:
            totals[letter] = totals.get(letter, 0) + float(num)
    parts = []
    for letter in "FPGSCA":
        if letter in totals:
            val = totals[letter]
            if val == int(val):
                parts.append(f"{_names[letter]}:{int(val)}")
            else:
                parts.append(f"{_names[letter]}:{val}")
    return " ".join(parts)


def parse_trade_routes_response(lines: list[str]) -> TradeRouteStatus:
    """Parse ROUTE|, IDLE_TRADER|, and TRADE_STATUS| lines.

    ROUTE format: ROUTE|uid|orig|dest|owner|isDom|isCS|hasQ|hasTP|pOut|relOut|pIn|relIn|origY|destY
    IDLE format:  IDLE_TRADER|uid|x,y
    STATUS:       TRADE_STATUS|cap|active|ghosts
    """
    capacity = 0
    active = 0
    ghost = 0
    traders: list[TraderInfo] = []
    for line in lines:
        if line.startswith("TRADE_STATUS|"):
            parts = line.split("|")
            if len(parts) >= 4:
                capacity = int(parts[1])
                active = int(parts[2])
                ghost = int(parts[3])
        elif line.startswith("ROUTE|"):
            parts = line.split("|")
            if len(parts) >= 15:
                uid = int(parts[1])
                traders.append(
                    TraderInfo(
                        unit_id=uid,
                        x=0,
                        y=0,  # active traders don't need position
                        has_moves=False,
                        on_route=True,
                        route_origin=parts[2],
                        route_dest=parts[3],
                        route_owner=parts[4],
                        is_domestic=parts[5] == "1",
                        is_city_state=parts[6] == "1",
                        has_quest=parts[7] == "1",
                        origin_yields=_parse_compact_yields(parts[13]),
                        dest_yields=_parse_compact_yields(parts[14]),
                        pressure_out=float(parts[9]) if parts[9] else 0.0,
                        religion_out=parts[10],
                        pressure_in=float(parts[11]) if parts[11] else 0.0,
                        religion_in=parts[12],
                    )
                )
        elif line.startswith("IDLE_TRADER|"):
            parts = line.split("|")
            if len(parts) >= 3:
                uid = int(parts[1])
                xy = parts[2].split(",")
                traders.append(
                    TraderInfo(
                        unit_id=uid,
                        x=int(xy[0]),
                        y=int(xy[1]),
                        has_moves=True,
                        on_route=False,
                    )
                )
    return TradeRouteStatus(
        capacity=capacity, active_count=active, traders=traders, ghost_count=ghost
    )


def parse_trade_destinations_response(lines: list[str]) -> list[TradeDestination]:
    """Parse TDEST| lines with enriched data.

    Format: TDEST|name|owner|x,y|isDom|isCS|hasQ|hasTP|pOut|relOut|pIn|relIn|origY|destY
    """
    results: list[TradeDestination] = []
    for line in lines:
        if line.startswith("TDEST|"):
            parts = line.split("|")
            if len(parts) >= 14:
                coords = parts[3].split(",")
                results.append(
                    TradeDestination(
                        city_name=parts[1],
                        owner_name=parts[2],
                        x=int(coords[0]),
                        y=int(coords[1]),
                        is_domestic=parts[4] == "1",
                        is_city_state=parts[5] == "1",
                        has_quest=parts[6] == "1",
                        has_trading_post=parts[7] == "1",
                        origin_yields=_parse_compact_yields(parts[12]),
                        dest_yields=_parse_compact_yields(parts[13]),
                        pressure_out=float(parts[8]) if parts[8] else 0.0,
                        religion_out=parts[9],
                        pressure_in=float(parts[10]) if parts[10] else 0.0,
                        religion_in=parts[11],
                    )
                )
            elif len(parts) >= 5:
                # Fallback for old format
                coords = parts[3].split(",")
                results.append(
                    TradeDestination(
                        city_name=parts[1],
                        owner_name=parts[2],
                        x=int(coords[0]),
                        y=int(coords[1]),
                        is_domestic=parts[4] == "1",
                    )
                )
    return results


def build_make_trade_route(unit_index: int, target_x: int, target_y: int) -> str:
    """Start a trade route from a trader to a target city (InGame context).

    Uses the same param format as the game's TradeRouteChooser.lua:
      PARAM_X0/Y0 = destination city, PARAM_X1/Y1 = trader origin.
    Checks CanStartOperation first to avoid ghost route desyncs.
    """
    return f"""
{_lua_get_unit(unit_index)}
if unit:GetMovesRemaining() == 0 then {_bail("ERR:NO_MOVES|Trader has no moves remaining")} end
local destCity = CityManager.GetCityAt({target_x}, {target_y})
if destCity == nil then {_bail("ERR:NO_CITY|No city at ({target_x},{target_y})")} end
local opHash = UnitOperationTypes.MAKE_TRADE_ROUTE
local tParams = {{}}
tParams[UnitOperationTypes.PARAM_X0] = {target_x}
tParams[UnitOperationTypes.PARAM_Y0] = {target_y}
tParams[UnitOperationTypes.PARAM_X1] = unit:GetX()
tParams[UnitOperationTypes.PARAM_Y1] = unit:GetY()
if not UnitManager.CanStartOperation(unit, opHash, nil, tParams) then
    local pTrade = Players[me]:GetTrade()
    local nOut = pTrade:GetNumOutgoingRoutes()
    local cap = pTrade:GetOutgoingRouteCapacity()
    if nOut >= cap then
        {_bail_lua('"ERR:CAPACITY_FULL|Trade routes at capacity (" .. nOut .. "/" .. cap .. "). Build Markets/Lighthouses for more slots, or wait for current route to finish."')}
    else
        {_bail(f"ERR:CANNOT_START_ROUTE|CanStartOperation returned false for destination ({target_x},{target_y})")}
    end
end
UnitManager.RequestOperation(unit, opHash, tParams)
local destName = Locale.Lookup(destCity:GetName())
print("OK:TRADE_ROUTE_STARTED|to " .. destName .. " at ({target_x},{target_y})")
print("{SENTINEL}")
"""


def build_teleport_to_city(unit_index: int, target_x: int, target_y: int) -> str:
    """Teleport a trader to a different city to change origin (InGame context).

    Only works when the trader is idle (not on an active route).
    """
    return f"""
{_lua_get_unit(unit_index)}
local opInfo = GameInfo.UnitOperations["UNITOPERATION_TELEPORT_TO_CITY"]
if opInfo == nil then {_bail("ERR:NO_TELEPORT_OP|TELEPORT_TO_CITY operation not found")} end
local opHash = opInfo.Hash
local tParams = {{}}
tParams[UnitOperationTypes.PARAM_X] = {target_x}
tParams[UnitOperationTypes.PARAM_Y] = {target_y}
local can = UnitManager.CanStartOperation(unit, opHash, nil, tParams, true)
if not can then {_bail("ERR:CANNOT_TELEPORT|Cannot teleport trader to ({target_x},{target_y}). Is the trader idle (not on an active route)?")} end
UnitManager.RequestOperation(unit, opHash, tParams)
local destCity = CityManager.GetCityAt({target_x}, {target_y})
local destName = destCity and Locale.Lookup(destCity:GetName()) or "({target_x},{target_y})"
print("OK:TELEPORTED|to " .. destName .. " at ({target_x},{target_y})")
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
    pcall(function()
        local gpClass = uInfo and uInfo.GreatPersonClass or nil
        if gpClass then classStr = " class=" .. gpClass end
    end)
    {_bail_lua('"ERR:CANNOT_ACTIVATE|" .. Locale.Lookup(unit:GetName()) .. " (" .. uName .. ")" .. classStr .. " at (" .. ux .. "," .. uy .. ") charges=" .. charges .. "." .. reqStr .. tilesStr')}
end
UnitManager.RequestCommand(unit, cmdHash, {{}})
-- Report remaining charges so agent knows whether to activate again
local remCharges = -1
pcall(function()
    local gp2 = unit:GetGreatPerson()
    if gp2 then
        remCharges = gp2:GetActionCharges() or 0
        if remCharges == 0 then
            local indIdx = gp2:GetIndividual()
            for ind in GameInfo.GreatPersonIndividuals() do
                if ind.Index == indIdx then
                    remCharges = (ind.ActionCharges or 1) - 1
                    break
                end
            end
        end
    end
end)
local chargeStr = ""
if remCharges > 0 then chargeStr = " charges_remaining=" .. remCharges .. " — activate again to use next charge" end
print("OK:GP_ACTIVATED|" .. Locale.Lookup(unit:GetName()) .. " (" .. uName .. ") at " .. ux .. "," .. uy .. chargeStr)
print("{SENTINEL}")
"""


def build_world_congress_query() -> str:
    """Get World Congress status, resolutions, and proposals (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pDiplo = Players[me]:GetDiplomacy()
local wc = Game.GetWorldCongress()
if not wc then {_bail("ERR:NO_WORLD_CONGRESS|World Congress not available yet")} end
local inSession = wc:IsInSession()
local meeting = wc:GetMeetingStatus()
local turnsLeft = meeting and meeting.TurnsLeft or -1
local favor = Players[me]:GetFavor()
local costs = wc:GetVotesandFavorCost()
local maxVotes = costs.MaxVotes or 5
local costStr = ""
for i = 0, maxVotes do
    if i > 0 then costStr = costStr .. "," end
    costStr = costStr .. tostring(costs[i] or 0)
end
print("WC_STATUS|" .. tostring(inSession) .. "|" .. turnsLeft .. "|" .. favor .. "|" .. maxVotes .. "|" .. costStr)
local ress = wc:GetResolutions()
if ress then
    for _, res in ipairs(ress) do
        local rType = res.Type
        local gRes = nil
        for row in GameInfo.Resolutions() do
            if row.Hash == rType then gRes = row end
        end
        local typeName = gRes and gRes.ResolutionType or ("HASH_" .. tostring(rType))
        local name = gRes and Locale.Lookup(gRes.Name) or "Unknown"
        local targetKind = gRes and (gRes.TargetKind or "") or ""
        local effectA = gRes and gRes.Effect1Description and Locale.Lookup(gRes.Effect1Description) or ""
        local effectB = gRes and gRes.Effect2Description and Locale.Lookup(gRes.Effect2Description) or ""
        local isPassed = "0"
        local winner = -1
        local chosen = ""
        if not inSession then
            isPassed = "1"
            winner = res.Winner or -1
            if res.ChosenThing then
                if res.TargetType == "PlayerType" then
                    local pid = tonumber(res.ChosenThing)
                    if pid and PlayerConfigurations[pid] and pDiplo:HasMet(pid) then
                        chosen = Locale.Lookup(PlayerConfigurations[pid]:GetCivilizationShortDescription())
                    else
                        chosen = "Unmet Player"
                    end
                else
                    chosen = Locale.Lookup(res.ChosenThing)
                end
            end
        end
        local targets = ""
        if res.PossibleTargets then
            local isPlayerType = (res.TargetType == "PlayerType")
            for ti, tgt in ipairs(res.PossibleTargets) do
                if ti > 1 then targets = targets .. "~" end
                local tName = ""
                local tId = tostring(ti - 1)  -- 0-based index as fallback ID
                if isPlayerType then
                    -- PlayerType: targets are player IDs (numbers)
                    local pid = tonumber(tgt)
                    tId = tostring(pid or (ti - 1))
                    if pid and PlayerConfigurations[pid] and pDiplo:HasMet(pid) then
                        tName = Locale.Lookup(PlayerConfigurations[pid]:GetCivilizationShortDescription())
                    else
                        tName = "Unmet Player"
                    end
                else
                    -- Other types (District, Yield, etc.): targets are LOC key strings
                    local ok, resolved = pcall(Locale.Lookup, tostring(tgt))
                    if ok and resolved then tName = resolved
                    else tName = tostring(tgt) end
                end
                targets = targets .. tId .. ":" .. tName
            end
        end
        effectA = effectA:gsub("|", "/"):gsub("~", "-")
        effectB = effectB:gsub("|", "/"):gsub("~", "-")
        name = name:gsub("|", "/"):gsub("~", "-")
        chosen = chosen:gsub("|", "/"):gsub("~", "-")
        print("WC_RES|" .. rType .. "|" .. typeName .. "|" .. name .. "|" .. targetKind .. "|" .. effectA .. "|" .. effectB .. "|" .. isPassed .. "|" .. winner .. "|" .. chosen .. "|" .. targets)
    end
end
if inSession then
    local props = wc:GetProposals()
    if props then
        for _, prop in ipairs(props) do
            local sid = prop.SenderID or -1
            local tid = prop.TargetID or -1
            local sName = sid >= 0 and Locale.Lookup(PlayerConfigurations[sid]:GetCivilizationShortDescription()) or "Unknown"
            local tName = tid >= 0 and Locale.Lookup(PlayerConfigurations[tid]:GetCivilizationShortDescription()) or "Unknown"
            local pType = prop.Type or 0
            local desc = prop.Description and Locale.Lookup(prop.Description) or ""
            desc = desc:gsub("|", "/"):gsub("~", "-")
            sName = sName:gsub("|", "/")
            tName = tName:gsub("|", "/")
            print("WC_PROP|" .. sid .. "|" .. sName .. "|" .. tid .. "|" .. tName .. "|" .. pType .. "|" .. desc)
        end
    end
end
print("{SENTINEL}")
"""


def parse_world_congress_response(lines: list[str]) -> WorldCongressStatus:
    """Parse WC_STATUS / WC_RES / WC_PROP lines into WorldCongressStatus."""
    status = WorldCongressStatus(
        is_in_session=False,
        turns_until_next=-1,
        favor=0,
        max_votes=5,
        favor_costs=[],
        resolutions=[],
        proposals=[],
    )
    for line in lines:
        if line.startswith("WC_STATUS|"):
            parts = line.split("|")
            status.is_in_session = parts[1] == "true"
            status.turns_until_next = int(parts[2])
            status.favor = int(parts[3])
            status.max_votes = int(parts[4])
            if len(parts) > 5 and parts[5]:
                status.favor_costs = [int(x) for x in parts[5].split(",")]
        elif line.startswith("WC_RES|"):
            parts = line.split("|")
            targets = parts[10].split("~") if len(parts) > 10 and parts[10] else []
            status.resolutions.append(
                CongressResolution(
                    resolution_type=parts[2],
                    resolution_hash=int(parts[1]),
                    name=parts[3],
                    target_kind=parts[4],
                    effect_a=parts[5],
                    effect_b=parts[6],
                    possible_targets=targets,
                    is_passed=parts[7] == "1",
                    winner=int(parts[8]),
                    chosen_thing=parts[9],
                )
            )
        elif line.startswith("WC_PROP|"):
            parts = line.split("|")
            status.proposals.append(
                CongressProposal(
                    sender_id=int(parts[1]),
                    sender_name=parts[2],
                    target_id=int(parts[3]),
                    target_name=parts[4],
                    proposal_type=int(parts[5]),
                    description=parts[6] if len(parts) > 6 else "",
                )
            )
    return status


def build_congress_vote(
    resolution_hash: int, option: int, target_index: int, num_votes: int
) -> str:
    """Vote on a World Congress resolution (InGame context).

    option: 1=A, 2=B
    target_index: 0-based index into PossibleTargets
    num_votes: total votes to commit (A.votes + B.votes = this value, allocated to chosen option)
    """
    return f"""
local me = Game.GetLocalPlayer()
local kParams = {{}}
kParams[PlayerOperations.PARAM_RESOLUTION_TYPE] = {resolution_hash}
kParams[PlayerOperations.PARAM_WORLD_CONGRESS_VOTES] = {num_votes}
kParams[PlayerOperations.PARAM_RESOLUTION_OPTION] = {option}
kParams[PlayerOperations.PARAM_RESOLUTION_SELECTION] = {target_index}
UI.RequestPlayerOperation(me, PlayerOperations.WORLD_CONGRESS_RESOLUTION_VOTE, kParams)
print("OK:VOTED|res:{resolution_hash}|option:{option}|target:{target_index}|votes:{num_votes}")
print("{SENTINEL}")
"""


def build_congress_submit() -> str:
    """Submit all World Congress votes and resume turn processing (InGame context).

    Mirrors WorldCongressPopup.lua OnAccept(): submit votes then ACTION_ENDTURN
    to resume turn-segment processing after the WC stage.
    """
    return f"""
local me = Game.GetLocalPlayer()
local intro = ContextPtr:LookUpControl("/InGame/WorldCongressIntro")
if intro then intro:SetHide(true) end
local popup = ContextPtr:LookUpControl("/InGame/WorldCongressPopup")
if popup then popup:SetHide(true) end
UI.RequestPlayerOperation(me, PlayerOperations.WORLD_CONGRESS_SUBMIT_TURN, {{}})
UI.RequestAction(ActionTypes.ACTION_ENDTURN)
print("OK:CONGRESS_SUBMITTED")
print("{SENTINEL}")
"""


def build_register_wc_voter(votes: list[dict] | None = None) -> str:
    """Register a one-shot Events.WorldCongressStage1 handler (InGame context).

    The handler fires during WC turn-segment processing (inside ACTION_ENDTURN),
    casts votes using the player's diplomatic favor, and submits.

    Args:
        votes: Optional list of agent preferences, each dict with keys:
            hash (int) — resolution type hash
            option (int) — 1 for A, 2 for B
            target (int) — player ID for PlayerType resolutions, or raw value
                           for non-player targets. The handler resolves this
                           to the correct 0-based index at runtime.
            votes (int) — max votes to allocate
            If None, handler uses default strategy: spread favor evenly,
            option A, target 0.
    """
    # Build the Lua table literal for agent vote preferences
    if votes:
        entries = []
        for v in votes:
            h = v.get("hash", v.get("resolution_hash", 0))
            o = v.get("option", 1)
            t = v.get("target", v.get("target_index", 0))
            n = v.get("votes", v.get("num_votes", 5))
            entries.append(f'["{h}"] = {{o={o}, t={t}, v={n}}}')
        prefs_lua = "{" + ", ".join(entries) + "}"
    else:
        prefs_lua = "nil"

    return f"""
-- Clean up any stale handler
if __civmcp_wc_handler then
    pcall(function() Events.WorldCongressStage1.Remove(__civmcp_wc_handler) end)
    __civmcp_wc_handler = nil
end

__civmcp_wc_votes = {prefs_lua}

local function handler()
    local me = Game.GetLocalPlayer()
    local wc = Game.GetWorldCongress()
    if not wc or not wc:IsInSession() then return end

    local favor = Players[me]:GetFavor()
    local costs = wc:GetVotesandFavorCost()
    local maxV = costs.MaxVotes or 5
    local ress = wc:GetResolutions()
    if not ress or #ress == 0 then return end

    local prefs = __civmcp_wc_votes
    local nRes = #ress

    for ri, res in ipairs(ress) do
        local rHash = res.Type
        local pref = prefs and prefs[tostring(rHash)]
        local option = pref and pref.o or 1
        local maxWanted = pref and pref.v or maxV

        -- Resolve target: pref.t is a player ID (for PlayerType) or raw value
        -- Find the matching 0-based index in PossibleTargets
        local targetIdx = 0
        if pref and pref.t and res.PossibleTargets then
            local isPlayerType = (res.TargetType == "PlayerType")
            for ti, tgt in ipairs(res.PossibleTargets) do
                if isPlayerType then
                    if tonumber(tgt) == pref.t then targetIdx = ti - 1 end
                else
                    if tostring(tgt) == tostring(pref.t) then targetIdx = ti - 1 end
                end
            end
        end

        local votesForThis = 1
        local costForThis = 0

        -- costs[i] is CUMULATIVE cost for (i+1) total votes
        -- So for v total votes, total cost = costs[v-1]
        if prefs then
            for v = 2, math.min(maxWanted, maxV) do
                local totalCost = costs[v - 1] or 99999
                if totalCost <= favor then
                    costForThis = totalCost
                    votesForThis = v
                else break end
            end
        else
            local resLeft = nRes - ri
            local budgetPerRes = math.floor(favor / (resLeft + 1))
            for v = 2, maxV do
                local totalCost = costs[v - 1] or 99999
                if totalCost <= budgetPerRes then
                    costForThis = totalCost
                    votesForThis = v
                else break end
            end
        end

        favor = favor - costForThis

        local kParams = {{}}
        kParams[PlayerOperations.PARAM_RESOLUTION_TYPE] = rHash
        kParams[PlayerOperations.PARAM_WORLD_CONGRESS_VOTES] = votesForThis
        kParams[PlayerOperations.PARAM_RESOLUTION_OPTION] = option
        kParams[PlayerOperations.PARAM_RESOLUTION_SELECTION] = targetIdx
        UI.RequestPlayerOperation(me, PlayerOperations.WORLD_CONGRESS_RESOLUTION_VOTE, kParams)
    end

    UI.RequestPlayerOperation(me, PlayerOperations.WORLD_CONGRESS_SUBMIT_TURN, {{}})

    __civmcp_wc_votes = nil
    pcall(function() Events.WorldCongressStage1.Remove(__civmcp_wc_handler) end)
    __civmcp_wc_handler = nil
end

__civmcp_wc_handler = handler
Events.WorldCongressStage1.Add(handler)
print("OK:WC_VOTER_REGISTERED")
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
                            gold_cost = int(float(v)) if v else 0
                        elif k == "faith":
                            faith_cost = int(float(v)) if v else 0
                        elif k == "recruit":
                            can_recruit = v == "true"
                    individual_id = int(float(parts[9]))
                results.append(
                    GreatPersonInfo(
                        class_name=parts[1],
                        individual_name=parts[2],
                        era_name=parts[3],
                        cost=int(float(parts[4])),
                        claimant=parts[5],
                        player_points=int(float(parts[6])),
                        ability=ability,
                        gold_cost=gold_cost,
                        faith_cost=faith_cost,
                        can_recruit=can_recruit,
                        individual_id=individual_id,
                    )
                )
    return results
