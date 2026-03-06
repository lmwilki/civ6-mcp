"""Trade routes domain — Lua builders and parsers."""

from __future__ import annotations

from civ_mcp.lua._helpers import (
    SENTINEL,
    _LUA_FMT_FLAT,
    _LUA_FMT_Y,
    _LUA_YIELD_LABELS,
    _bail,
    _bail_lua,
    _lua_get_unit,
)
from civ_mcp.lua.models import TradeDestination, TraderInfo, TradeRouteStatus


def build_trade_capacity_check() -> str:
    """Lightweight trade route capacity check (InGame context).

    Returns a single TRCAP|capacity|active line.
    Uses city route records (GetOutgoingRoutes) — the same authoritative source
    as build_trade_routes_query. The per-unit HasTradeRoute() boolean is unreliable
    and causes persistent false "idle route" warnings.
    """
    return """
local me = Game.GetLocalPlayer()
local tr = Players[me]:GetTrade()
local cap = tr:GetOutgoingRouteCapacity()
local active = 0
for _, city in Players[me]:GetCities():Members() do
    pcall(function()
        local routes = city:GetTrade():GetOutgoingRoutes()
        if routes then active = active + #routes end
    end)
end
print("TRCAP|" .. cap .. "|" .. active)
print("{SENTINEL}")
""".replace("{SENTINEL}", SENTINEL)


def build_trade_routes_query() -> str:
    """Get trade route capacity, active routes with enriched data (InGame).

    Reads route records from each city's GetOutgoingRoutes(), cross-references
    with actual trader units to detect ghost routes.  Enriches each route with
    yields, religious pressure, city-state quest status, and trading posts.

    NOTE: Must run in InGame context for GetOutgoingRoutes() and TradeManager.
    """
    return (
        """
local me = Game.GetLocalPlayer()
local pTrade = Players[me]:GetTrade()
local cap = pTrade:GetOutgoingRouteCapacity()
local tm = Game.GetTradeManager()
local qm = Game.GetQuestsManager()
local tradeQI = GameInfo.Quests["QUEST_SEND_TRADE_ROUTE"]
local tradeQIdx = tradeQI and tradeQI.Index or -1
"""
        + _LUA_YIELD_LABELS
        + "\n"
        + _LUA_FMT_Y
        + """
-- Build set of valid trader unit IDs
local traderUIDs = {}
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
local seenRoutes = {}
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
local routedTraders = {}
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
""".replace("{SENTINEL}", SENTINEL)
    )


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
{_LUA_YIELD_LABELS}
{_LUA_FMT_FLAT}
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
if not can then {_bail(f"ERR:CANNOT_TELEPORT|Cannot teleport trader to ({target_x},{target_y}). Is the trader idle (not on an active route)?")} end
UnitManager.RequestOperation(unit, opHash, tParams)
local destCity = CityManager.GetCityAt({target_x}, {target_y})
local destName = destCity and Locale.Lookup(destCity:GetName()) or "({target_x},{target_y})"
print("OK:TELEPORTED|to " .. destName .. " at ({target_x},{target_y})")
print("{SENTINEL}")
"""
