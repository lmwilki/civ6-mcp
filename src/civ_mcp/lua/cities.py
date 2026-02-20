"""Cities domain — Lua builders and parsers."""

from __future__ import annotations

from civ_mcp.lua._helpers import SENTINEL, _ITEM_PARAM_MAP, _ITEM_TABLE_MAP, _bail, _bail_lua, _lua_get_city
from civ_mcp.lua.models import CityInfo, ProductionOption


def build_cities_query() -> str:
    return f"""
local me = Game.GetLocalPlayer()
local hashName = {{}}
for u in GameInfo.Units() do hashName[u.Hash] = u.UnitType end
for b in GameInfo.Buildings() do hashName[b.Hash] = b.BuildingType end
for d in GameInfo.Districts() do hashName[d.Hash] = d.DistrictType end
for p in GameInfo.Projects() do hashName[p.Hash] = p.ProjectType end
local cityCoords = {{}}
for i, c in Players[me]:GetCities():Members() do
    local nm = Locale.Lookup(c:GetName())
    local bq = c:GetBuildQueue()
    local producing = "nothing"
    local turnsLeft = 0
    if bq:GetSize() > 0 then
        local h = bq:GetCurrentProductionTypeHash()
        if h == 0 then
            producing = "CORRUPTED_QUEUE"
        else
            producing = hashName[h] or "UNKNOWN"
        end
        turnsLeft = bq:GetTurnsLeft()
    end
    local g = c:GetGrowth()
    -- City defense info
    local defStr, garHP, garMax, wallHP, wallMax = 0, 0, 0, 0, 0
    local ccIdx = GameInfo.Districts["DISTRICT_CITY_CENTER"].Index
    for _, d in c:GetDistricts():Members() do
        if d:GetType() == ccIdx then
            local ok, _ = pcall(function()
                defStr = d:GetDefenseStrength() or 0
                garMax = d:GetMaxDamage(DefenseTypes.DISTRICT_GARRISON) or 0
                garHP = garMax - (d:GetDamage(DefenseTypes.DISTRICT_GARRISON) or 0)
                wallMax = d:GetMaxDamage(DefenseTypes.DISTRICT_OUTER) or 0
                wallHP = wallMax - (d:GetDamage(DefenseTypes.DISTRICT_OUTER) or 0)
            end)
            break
        end
    end
    local cityTargets = {{}}
    if wallMax > 0 then
        local cx, cy = c:GetX(), c:GetY()
        for dy = -2, 2 do for dx = -2, 2 do
            local tx, ty = cx + dx, cy + dy
            local d = Map.GetPlotDistance(cx, cy, tx, ty)
            if d >= 1 and d <= 2 then
                local pu = Map.GetUnitsAt(tx, ty)
                if pu then for other in pu:Units() do
                    if other:GetOwner() ~= me then
                        local eInfo = GameInfo.Units[other:GetType()]
                        local eName = eInfo and eInfo.UnitType or "UNKNOWN"
                        local eHP = other:GetMaxDamage() - other:GetDamage()
                        table.insert(cityTargets, eName .. "@" .. tx .. "," .. ty .. "(" .. eHP .. "hp)")
                    end
                end end
            end
        end end
    end
    local pillDistricts = {{}}
    local distLocs = {{}}
    for _, d in c:GetDistricts():Members() do
        local dInfo = GameInfo.Districts[d:GetType()]
        if dInfo and dInfo.DistrictType ~= "DISTRICT_CITY_CENTER" then
            table.insert(distLocs, dInfo.DistrictType .. "@" .. d:GetX() .. "," .. d:GetY())
        end
        if d:IsPillaged() then
            if dInfo then table.insert(pillDistricts, dInfo.DistrictType) end
        end
    end
    local pillBuildings = {{}}
    local pBuildings = c:GetBuildings()
    for bldg in GameInfo.Buildings() do
        if pBuildings:HasBuilding(bldg.Index) and pBuildings:IsPillaged(bldg.Index) then
            table.insert(pillBuildings, bldg.BuildingType)
        end
    end
    table.insert(cityCoords, {{name=nm, x=c:GetX(), y=c:GetY()}})
    local loy, loyMax, loyPT, loyFlip = 100, 100, 0, 0
    local cult = c:GetCulturalIdentity()
    if cult then
        loy = cult:GetLoyalty()
        loyMax = cult:GetMaxLoyalty()
        loyPT = cult:GetLoyaltyPerTurn()
        loyFlip = cult:GetTurnsToConversion()
    end
    local garrisonUnit = ""
    local garFound = false
    local garUnitsAt = Map.GetUnitsAt(c:GetX(), c:GetY())
    if garUnitsAt then
        for gu in garUnitsAt:Units() do
            if not garFound and gu:GetOwner() == me then
                local guInfo = GameInfo.Units[gu:GetType()]
                if guInfo then
                    local fc = guInfo.FormationClass
                    if fc == "FORMATION_CLASS_LAND_COMBAT" or fc == "FORMATION_CLASS_NAVAL_COMBAT" then
                        garrisonUnit = guInfo.UnitType
                        garFound = true
                    end
                end
            end
        end
    end
    print(c:GetID() .. "|" .. nm .. "|" .. c:GetX() .. "," .. c:GetY() .. "|" .. c:GetPopulation() .. "|" .. string.format("%.1f|%.1f|%.1f|%.1f|%.1f|%.1f", c:GetYield(0), c:GetYield(1), c:GetYield(2), c:GetYield(3), c:GetYield(4), c:GetYield(5)) .. "|" .. string.format("%.1f", g:GetHousing()) .. "|" .. g:GetAmenities() .. "|" .. g:GetTurnsUntilGrowth() .. "|" .. producing .. "|" .. turnsLeft .. "|" .. defStr .. "|" .. garHP .. "/" .. garMax .. "|" .. wallHP .. "/" .. wallMax .. "|" .. table.concat(cityTargets, ";") .. "|" .. table.concat(pillDistricts, ";") .. "|" .. table.concat(distLocs, ";") .. "|" .. string.format("%.1f|%.1f|%.1f|%d", loy, loyMax, loyPT, loyFlip) .. "|" .. string.format("%.1f|%.1f|%d", g:GetFoodSurplus(), g:GetFood(), g:GetGrowthThreshold()) .. "|" .. table.concat(pillBuildings, ";") .. "|" .. garrisonUnit)
end
for i = 1, #cityCoords do for j = i + 1, #cityCoords do
    local d = Map.GetPlotDistance(cityCoords[i].x, cityCoords[i].y, cityCoords[j].x, cityCoords[j].y)
    print("DIST|" .. cityCoords[i].name .. "|" .. cityCoords[j].name .. "|" .. d)
end end
print("{SENTINEL}")
"""


def build_city_attack(city_id: int, target_x: int, target_y: int) -> str:
    """InGame context: fire city ranged attack at a target tile."""
    return f"""
{_lua_get_city(city_id)}
local cx, cy = pCity:GetX(), pCity:GetY()
local dist = Map.GetPlotDistance(cx, cy, {target_x}, {target_y})
if dist > 2 then {_bail_lua('"ERR:OUT_OF_RANGE|City range is 2, target is at distance " .. dist')} end
local enemy = nil
local pu = Map.GetUnitsAt({target_x}, {target_y})
if pu then for other in pu:Units() do if other:GetOwner() ~= me then enemy = other end end end
if not enemy then {_bail("ERR:NO_ENEMY|No hostile unit at target tile")} end
local eInfo = GameInfo.Units[enemy:GetType()]
local eName = eInfo and eInfo.UnitType or "UNKNOWN"
local eHP = enemy:GetMaxDamage() - enemy:GetDamage()
local params = {{}}
params[CityCommandTypes.PARAM_X] = {target_x}
params[CityCommandTypes.PARAM_Y] = {target_y}
local canAttack = CityManager.CanStartCommand(pCity, CityCommandTypes.RANGE_ATTACK, true, params, false)
if not canAttack then
    local ccIdx = GameInfo.Districts["DISTRICT_CITY_CENTER"].Index
    local hasWalls = false
    for _, d in pCity:GetDistricts():Members() do
        if d:GetType() == ccIdx then
            local wHP = d:GetMaxDamage(DefenseTypes.DISTRICT_OUTER)
            if wHP and wHP > 0 then hasWalls = true end
            break
        end
    end
    if not hasWalls then
        {_bail("ERR:NO_WALLS|City has no walls — build Ancient Walls first")}
    else
        {_bail("ERR:ALREADY_FIRED|City already fired this turn or LOS blocked")}
    end
end
CityManager.RequestCommand(pCity, CityCommandTypes.RANGE_ATTACK, params)
print("OK:CITY_RANGE_ATTACK|" .. Locale.Lookup(pCity:GetName()) .. " -> " .. eName .. "@{target_x},{target_y}|pre_hp:" .. eHP .. "/" .. enemy:GetMaxDamage())
print("{SENTINEL}")
"""


def build_resolve_city_capture(action: str) -> str:
    """InGame context: resolve a 'Keep or Free City' / 'Raze City' blocker.

    action: 'keep', 'reject', 'raze', 'liberate_founder', 'liberate_previous'
    Tries GetNextRebelledCity first (loyalty flip), then GetNextCapturedCity (conquest).
    """
    directive_map = {
        "keep": "CityDestroyDirectives.KEEP",
        "reject": "CityDestroyDirectives.REJECT",
        "raze": "CityDestroyDirectives.RAZE",
        "liberate_founder": "CityDestroyDirectives.LIBERATE_FOUNDER",
        "liberate_previous": "CityDestroyDirectives.LIBERATE_PREVIOUS_OWNER",
    }
    directive = directive_map.get(action)
    if not directive:
        valid = ", ".join(directive_map.keys())
        return _bail(f"ERR:INVALID_ACTION|Valid actions: {valid}")

    return f"""
local me = Game.GetLocalPlayer()
local player = Players[me]
local city = player:GetCities():GetNextRebelledCity()
local source = "rebelled"
if city == nil then
    city = player:GetCities():GetNextCapturedCity()
    source = "captured"
end
if city == nil then {_bail("ERR:NO_PENDING_CITY|No rebelled or captured city pending decision")} end
local name = Locale.Lookup(city:GetName())
local pop = city:GetPopulation()
local cid = city:GetID()
local params = {{}}
params[UnitOperationTypes.PARAM_FLAGS] = {directive}
local canDo = CityManager.CanStartCommand(city, CityCommandTypes.DESTROY, params)
if not canDo then {_bail_lua(f'"ERR:CANNOT_{action.upper()}|Cannot {action} " .. name .. " (CanStartCommand returned false)"')} end
CityManager.RequestCommand(city, CityCommandTypes.DESTROY, params)
print("OK:{action.upper()}|" .. name .. " (pop " .. pop .. ", id:" .. cid .. ", " .. source .. ")")
print("{SENTINEL}")
"""


def build_city_production_query(city_id: int) -> str:
    """Returns Lua that lists what the city can produce. Actual production setting
    needs the item type, so this is a two-step process: list, then set."""
    return f"""
{_lua_get_city(city_id)}
local bq = pCity:GetBuildQueue()
local goldIdx = GameInfo.Yields["YIELD_GOLD"].Index
local cityGold = pCity:GetGold()
local function getGoldCost(hash, isUnit)
    local ok, cost = pcall(function()
        if isUnit then
            return cityGold:GetPurchaseCost(goldIdx, hash, MilitaryFormationTypes.STANDARD_MILITARY_FORMATION)
        else
            return cityGold:GetPurchaseCost(goldIdx, hash, -1)
        end
    end)
    if ok and cost and cost > 0 then return math.floor(cost) end
    return -1
end
print("UNITS:")
for unit in GameInfo.Units() do
    if bq:CanProduce(unit.Hash, true) then
        local t = bq:GetTurnsLeft(unit.Hash)
        local gc = getGoldCost(unit.Hash, true)
        print("UNIT|" .. unit.UnitType .. "|" .. unit.Cost .. "|" .. t .. "|" .. gc)
    end
end
print("BUILDINGS:")
for bldg in GameInfo.Buildings() do
    if bq:CanProduce(bldg.Hash, true) then
        local t = bq:GetTurnsLeft(bldg.Hash)
        local gc = -1
        if not bldg.IsWonder then
            gc = getGoldCost(bldg.Hash, false)
        end
        print("BUILDING|" .. bldg.BuildingType .. "|" .. bldg.Cost .. "|" .. t .. "|" .. gc)
    end
end
print("DISTRICTS:")
for dist in GameInfo.Districts() do
    if bq:CanProduce(dist.Hash, true) then
        local t = bq:GetTurnsLeft(dist.Hash)
        print("DISTRICT|" .. dist.DistrictType .. "|" .. dist.Cost .. "|" .. t .. "|-1")
    end
end
print("PROJECTS:")
for proj in GameInfo.Projects() do
    if bq:CanProduce(proj.Hash, true) then
        local t = bq:GetTurnsLeft(proj.Hash)
        print("PROJECT|" .. proj.ProjectType .. "|" .. proj.Cost .. "|" .. t .. "|-1")
    end
end
print("{SENTINEL}")
"""


def build_produce_item(
    city_id: int, item_type: str, item_name: str,
    target_x: int | None = None, target_y: int | None = None,
) -> str:
    """Set production for a city via CityManager.RequestOperation (InGame context).

    item_type is UNIT/BUILDING/DISTRICT, item_name is e.g. UNIT_WARRIOR.
    Uses .Hash for item refs and VALUE_REPLACE_AT position 0 to replace current production.
    For districts, pass target_x/target_y to specify placement tile.
    """
    table_name = _ITEM_TABLE_MAP.get(item_type.upper(), "Units")
    param_key = _ITEM_PARAM_MAP.get(item_type.upper(), "PARAM_UNIT_TYPE")
    # Extra params for district placement
    xy_params = ""
    xy_check_params = ""
    if target_x is not None and target_y is not None:
        xy_params = f"tParams[CityOperationTypes.PARAM_X] = {target_x}\ntParams[CityOperationTypes.PARAM_Y] = {target_y}"
        xy_check_params = f"tCheck[CityOperationTypes.PARAM_X] = {target_x}\ntCheck[CityOperationTypes.PARAM_Y] = {target_y}"
    return f"""
{_lua_get_city(city_id)}
local item = GameInfo.{table_name}["{item_name}"]
if item == nil then {_bail(f"ERR:ITEM_NOT_FOUND|{item_name}")} end
local bq = pCity:GetBuildQueue()
local isCorrupted = bq:GetSize() > 0 and bq:GetCurrentProductionTypeHash() == 0
if not bq:CanProduce(item.Hash, true) then
    {_bail(f"ERR:CANNOT_PRODUCE|{item_name} cannot be produced in this city")}
end
local tCheck = {{}}
tCheck[CityOperationTypes.{param_key}] = item.Hash
{xy_check_params}
local canStart = CityManager.CanStartOperation(pCity, CityOperationTypes.BUILD, tCheck, true)
local tParams = {{}}
tParams[CityOperationTypes.{param_key}] = item.Hash
{xy_params}
if isCorrupted then
    tParams[CityOperationTypes.PARAM_INSERT_MODE] = CityOperationTypes.VALUE_EXCLUSIVE
else
    tParams[CityOperationTypes.PARAM_INSERT_MODE] = CityOperationTypes.VALUE_REPLACE_AT
    tParams[CityOperationTypes.PARAM_QUEUE_DESTINATION_LOCATION] = 0
end
CityManager.RequestOperation(pCity, CityOperationTypes.BUILD, tParams)
if canStart then
    local turnsLeft = bq:GetTurnsLeft(item.Hash)
    print("OK:PRODUCING|{item_name}|" .. turnsLeft .. " turns")
else
    print("MAYBE:PRODUCING|{item_name}|canStart=false")
end
print("{SENTINEL}")
"""


def build_verify_production(city_id: int, item_name: str) -> str:
    """GameCore readback: verify production was set after RequestOperation.

    Uses CurrentlyBuilding() (GameCore) instead of GetCurrentProductionTypeHash()
    which is InGame-only and returns nil in GameCore context.
    """
    return f"""
local me = Game.GetLocalPlayer()
local pCity = Players[me]:GetCities():FindID({city_id} % 65536)
if pCity == nil then print("NOT_FOUND"); print("{SENTINEL}"); return end
local bq = pCity:GetBuildQueue()
local cur = bq:CurrentlyBuilding()
if cur == "{item_name}" then
    print("CONFIRMED|" .. bq:GetTurnsLeft() .. " turns")
else
    print("NOT_SET|current=" .. tostring(cur) .. "|expected={item_name}")
end
print("{SENTINEL}")
"""


def build_purchase_item(city_id: int, item_type: str, item_name: str, yield_type: str = "YIELD_GOLD") -> str:
    """Purchase a unit or building with gold/faith via CityManager.RequestCommand (InGame context)."""
    itype = item_type.upper()
    table_name = _ITEM_TABLE_MAP.get(itype)
    param_key = _ITEM_PARAM_MAP.get(itype)
    if table_name is None or param_key is None:
        return _bail(f"ERR:INVALID_TYPE|Can only purchase UNIT or BUILDING, got {item_type}")
    return f"""
{_lua_get_city(city_id)}
local item = GameInfo.{table_name}["{item_name}"]
if item == nil then {_bail(f"ERR:ITEM_NOT_FOUND|{item_name}")} end
local yieldRow = GameInfo.Yields["{yield_type}"]
if yieldRow == nil then {_bail(f"ERR:YIELD_NOT_FOUND|{yield_type}")} end
local tParams = {{}}
tParams[CityCommandTypes.{param_key}] = item.Hash
tParams[CityCommandTypes.PARAM_YIELD_TYPE] = yieldRow.Index
if "{itype}" == "UNIT" then
    tParams[CityCommandTypes.PARAM_MILITARY_FORMATION_TYPE] = MilitaryFormationTypes.STANDARD_MILITARY_FORMATION
    local cx, cy = pCity:GetX(), pCity:GetY()
    local targetClass = item.FormationClass
    local existing = Map.GetUnitsAt(cx, cy)
    if existing and existing:GetCount() > 0 then
        for u in existing:Units() do
            if u:GetOwner() == me then
                local uDef = GameInfo.Units[u:GetType()]
                if uDef and uDef.FormationClass == targetClass then
                    {_bail_lua(f'"ERR:STACKING_CONFLICT|Cannot purchase {item_name} — " .. uDef.UnitType .. " already on city tile. Move it first."')}
                end
            end
        end
    end
end
local cost = pCity:GetGold():GetPurchaseCost(yieldRow.Index, item.Hash, MilitaryFormationTypes.STANDARD_MILITARY_FORMATION)
local isFaith = ("{yield_type}" == "YIELD_FAITH")
local balance
if isFaith then
    balance = Players[me]:GetReligion():GetFaithBalance()
else
    balance = Players[me]:GetTreasury():GetGoldBalance()
end
local suffix = isFaith and "f" or "g"
local canBuy, results = CityManager.CanStartCommand(pCity, CityCommandTypes.PURCHASE, false, tParams, true)
if not canBuy then
    local reasons = {{}}
    if results then
        for _,v in pairs(results) do
            if type(v) == "table" then
                for _,msg in pairs(v) do if type(msg) == "string" then table.insert(reasons, msg) end end
            elseif type(v) == "string" then table.insert(reasons, v)
            end
        end
    end
    if cost > balance then
        table.insert(reasons, 1, "costs " .. math.floor(cost) .. suffix .. " but you only have " .. math.floor(balance) .. suffix)
    end
    local reason = #reasons > 0 and table.concat(reasons, "; ") or "unknown"
    {_bail_lua('"ERR:CANNOT_PURCHASE|" .. reason')}
end
CityManager.RequestCommand(pCity, CityCommandTypes.PURCHASE, tParams)
print("OK:PURCHASED|{item_name}|cost=" .. math.floor(cost) .. suffix .. " (had " .. math.floor(balance) .. suffix .. ")")
print("{SENTINEL}")
"""


def build_city_yield_focus_query(city_id: int) -> str:
    """Get current yield focus settings for a city (InGame context)."""
    return f"""
{_lua_get_city(city_id)}
local citz = pCity:GetCitizens()
local yields = {{"YIELD_FOOD", "YIELD_PRODUCTION", "YIELD_GOLD", "YIELD_SCIENCE", "YIELD_CULTURE", "YIELD_FAITH"}}
for _, yName in ipairs(yields) do
    local yRow = GameInfo.Yields[yName]
    if yRow then
        local favored = citz:IsFavoredYield(yRow.Index)
        local disfavored = citz:IsDisfavoredYield(yRow.Index)
        local status = "neutral"
        if favored then status = "favored" elseif disfavored then status = "disfavored" end
        print("FOCUS|" .. yName .. "|" .. status)
    end
end
print("{SENTINEL}")
"""


def build_set_yield_focus(city_id: int, yield_type: str) -> str:
    """Set or clear a yield focus for a city (InGame context).

    Uses CityManager.RequestCommand with CityCommandTypes.SET_FOCUS.
    yield_type="DEFAULT" clears all focus. Otherwise sets the given yield as favored.
    PARAM_FLAGS: 1 = toggle favored, 0 = toggle disfavored.
    """
    if yield_type.upper() == "DEFAULT":
        # Clear all focus by toggling off any currently favored/disfavored yields
        return f"""
{_lua_get_city(city_id)}
local citz = pCity:GetCitizens()
local cleared = false
for yRow in GameInfo.Yields() do
    if citz:IsFavoredYield(yRow.Index) then
        local tp = {{}}
        tp[CityCommandTypes.PARAM_YIELD_TYPE] = yRow.Index
        tp[CityCommandTypes.PARAM_FLAGS] = 1
        CityManager.RequestCommand(pCity, CityCommandTypes.SET_FOCUS, tp)
        cleared = true
    end
    if citz:IsDisfavoredYield(yRow.Index) then
        local tp = {{}}
        tp[CityCommandTypes.PARAM_YIELD_TYPE] = yRow.Index
        tp[CityCommandTypes.PARAM_FLAGS] = 0
        CityManager.RequestCommand(pCity, CityCommandTypes.SET_FOCUS, tp)
        cleared = true
    end
end
if cleared then print("OK:FOCUS_CLEARED|All yield focus cleared")
else print("OK:FOCUS_CLEARED|No focus was set") end
print("{SENTINEL}")
"""
    yield_name = yield_type.upper()
    if not yield_name.startswith("YIELD_"):
        yield_name = f"YIELD_{yield_name}"
    return f"""
{_lua_get_city(city_id)}
local yRow = GameInfo.Yields["{yield_name}"]
if yRow == nil then {_bail(f"ERR:YIELD_NOT_FOUND|{yield_name}")} end
local citz = pCity:GetCitizens()
-- Clear existing favored focus first
for yr in GameInfo.Yields() do
    if citz:IsFavoredYield(yr.Index) then
        local tp = {{}}
        tp[CityCommandTypes.PARAM_YIELD_TYPE] = yr.Index
        tp[CityCommandTypes.PARAM_FLAGS] = 1
        CityManager.RequestCommand(pCity, CityCommandTypes.SET_FOCUS, tp)
    end
end
-- Set new focus
local tParams = {{}}
tParams[CityCommandTypes.PARAM_YIELD_TYPE] = yRow.Index
tParams[CityCommandTypes.PARAM_FLAGS] = 1
CityManager.RequestCommand(pCity, CityCommandTypes.SET_FOCUS, tParams)
print("OK:FOCUS_SET|{yield_name}|favored")
print("{SENTINEL}")
"""


def parse_cities_response(lines: list[str]) -> tuple[list[CityInfo], list[str]]:
    """Returns (cities, distance_lines) where distance_lines are 'A|B|N' strings."""
    cities = []
    distances: list[str] = []
    for line in lines:
        if line.startswith("DIST|"):
            p = line.split("|")
            if len(p) >= 4:
                distances.append(f"{p[1]} <-> {p[2]}: {p[3]} tiles")
            continue
        parts = line.split("|")
        if len(parts) < 14:
            continue
        x_str, y_str = parts[2].split(",")
        def _split_hp(s: str) -> tuple[int, int]:
            if "/" in s:
                a, b = s.split("/")
                return int(a), int(b)
            return 0, 0

        def_str = int(parts[15]) if len(parts) > 15 and parts[15].isdigit() else 0
        gar_hp, gar_max = _split_hp(parts[16]) if len(parts) > 16 else (0, 0)
        wall_hp, wall_max = _split_hp(parts[17]) if len(parts) > 17 else (0, 0)
        cities.append(CityInfo(
            city_id=int(parts[0]),
            name=parts[1],
            x=int(x_str),
            y=int(y_str),
            population=int(parts[3]),
            food=float(parts[4]),
            production=float(parts[5]),
            gold=float(parts[6]),
            science=float(parts[7]),
            culture=float(parts[8]),
            faith=float(parts[9]),
            housing=float(parts[10]),
            amenities=int(parts[11]),
            turns_to_grow=int(parts[12]),
            currently_building=parts[13],
            production_turns_left=int(parts[14]) if len(parts) > 14 else 0,
            defense_strength=def_str,
            garrison_hp=gar_hp,
            garrison_max_hp=gar_max,
            wall_hp=wall_hp,
            wall_max_hp=wall_max,
            attack_targets=[t for t in (parts[18].split(";") if len(parts) > 18 else []) if t],
            pillaged_districts=[d for d in (parts[19].split(";") if len(parts) > 19 else []) if d],
            districts=[d for d in (parts[20].split(";") if len(parts) > 20 else []) if d],
            loyalty=float(parts[21]) if len(parts) > 21 else 100.0,
            loyalty_max=float(parts[22]) if len(parts) > 22 else 100.0,
            loyalty_per_turn=float(parts[23]) if len(parts) > 23 else 0.0,
            turns_to_loyalty_flip=int(parts[24]) if len(parts) > 24 else 0,
            food_surplus=float(parts[25]) if len(parts) > 25 else 0.0,
            food_stored=float(parts[26]) if len(parts) > 26 else 0.0,
            growth_threshold=int(parts[27]) if len(parts) > 27 else 0,
            pillaged_buildings=[b for b in (parts[28].split(";") if len(parts) > 28 else []) if b],
            garrison_unit=parts[29] if len(parts) > 29 else "",
        ))
    return cities, distances


def parse_city_production_response(lines: list[str]) -> list[ProductionOption]:
    """Parse available production options from build_city_production_query query."""
    options = []
    for line in lines:
        if line.startswith(("UNITS:", "BUILDINGS:", "DISTRICTS:", "PROJECTS:")):
            continue
        parts = line.split("|")
        if len(parts) >= 3 and parts[0] in ("UNIT", "BUILDING", "DISTRICT", "PROJECT"):
            options.append(ProductionOption(
                category=parts[0],
                item_name=parts[1],
                cost=int(parts[2]),
                turns=int(parts[3]) if len(parts) > 3 else 0,
                gold_cost=int(parts[4]) if len(parts) > 4 else -1,
            ))
    return options
