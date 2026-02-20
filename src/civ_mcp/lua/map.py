"""Map domain — Lua builders and parsers."""

from __future__ import annotations

from civ_mcp.lua._helpers import SENTINEL, _bail, _bail_lua, _lua_get_city, _lua_get_unit
from civ_mcp.lua.models import DistrictPlacement, FogBoundary, MinimapData, NearbyResource, OwnedResource, PurchasableTile, ResourceStockpile, SettleCandidate, StrategicMapData, TileInfo, UnclaimedResource

# --- Shared Lua fragments for settle-scan scoring (used by two builders) ---

_SETTLE_PREAMBLE = """
local allCities = {}
for i = 0, 62 do
    if Players[i] and Players[i]:IsAlive() then
        local cities = Players[i]:GetCities()
        if cities then
            for _, c in cities:Members() do
                table.insert(allCities, {x=c:GetX(), y=c:GetY()})
            end
        end
    end
end
local classPrefix = {RESOURCECLASS_STRATEGIC="S", RESOURCECLASS_LUXURY="L", RESOURCECLASS_BONUS="B"}
local function resVisible(resEntry)
    if not resEntry.PrereqTech then return true end
    local t = GameInfo.Technologies[resEntry.PrereqTech]
    return t and pTech:HasTech(t.Index)
end
local candidates = {}
"""

# Scoring body — expects cx, cy, cPlot, vis, me, allCities, classPrefix, resVisible in scope.
# Appends to `candidates` table.
_SETTLE_SCORE_BODY = """
                local tooClose = false
                for _, city in ipairs(allCities) do
                    if Map.GetPlotDistance(cx, cy, city.x, city.y) <= 3 then tooClose = true; break end
                end
                if not tooClose then
                    local totalF, totalP, totalG = 0, 0, 0
                    local resList = {}
                    local luxCount, stratCount = 0, 0
                    for ry = -3, 3 do
                        for rx = -3, 3 do
                            local tx, ty = cx + rx, cy + ry
                            local tPlot = Map.GetPlot(tx, ty)
                            if tPlot and Map.GetPlotDistance(cx, cy, tx, ty) <= 3 and vis:IsRevealed(tPlot:GetIndex()) then
                                totalF = totalF + tPlot:GetYield(0)
                                totalP = totalP + tPlot:GetYield(1)
                                totalG = totalG + tPlot:GetYield(2)
                                local rIdx = tPlot:GetResourceType()
                                if rIdx >= 0 then
                                    local resEntry = GameInfo.Resources[rIdx]
                                    if resVisible(resEntry) then
                                        local rName = resEntry.ResourceType:gsub("RESOURCE_", "")
                                        local prefix = classPrefix[resEntry.ResourceClassType] or "B"
                                        table.insert(resList, prefix .. ":" .. rName)
                                        if prefix == "L" then luxCount = luxCount + 1
                                        elseif prefix == "S" then stratCount = stratCount + 1 end
                                    end
                                end
                            end
                        end
                    end
                    local waterType = "none"
                    if cPlot:IsFreshWater() then waterType = "fresh"
                    elseif cPlot:IsCoastalLand() then waterType = "coast" end
                    local defScore = 0
                    if cPlot:IsHills() then defScore = defScore + 2 end
                    if cPlot:IsRiver() then defScore = defScore + 1 end
                    for ady = -1, 1 do
                        for adx = -1, 1 do
                            if adx ~= 0 or ady ~= 0 then
                                local ap = Map.GetPlot(cx + adx, cy + ady)
                                if ap and ap:IsHills() and Map.GetPlotDistance(cx, cy, cx+adx, cy+ady) == 1 then defScore = defScore + 1 end
                            end
                        end
                    end
                    local score = totalF * 2 + totalP * 2 + totalG + luxCount * 4 + stratCount * 3 + defScore
                    if waterType == "fresh" then score = score + 5
                    elseif waterType == "coast" then score = score + 3 end
                    local friendlyP, enemyP = 1.0, 0
                    for pi = 0, 62 do
                        local pp = Players[pi]
                        if pp ~= nil and pp:IsAlive() and pp:IsMajor() then
                            local pcc = pp:GetCities()
                            if pcc then
                                local capC = pcc:GetCapitalCity()
                                local capI = capC and capC:GetID() or -1
                                for _, pc in pcc:Members() do
                                    local pd = Map.GetPlotDistance(cx, cy, pc:GetX(), pc:GetY())
                                    if pd > 0 and pd <= 9 then
                                        local raw = pc:GetPopulation() * (10 - pd) / 10
                                        if pc:GetID() == capI then raw = raw * 1.5 end
                                        if pi == me then friendlyP = friendlyP + raw
                                        else enemyP = enemyP + raw end
                                    end
                                end
                            end
                        end
                    end
                    local loyP = friendlyP - enemyP
                    local minPr = math.min(friendlyP, enemyP)
                    local loyPT = 10 * loyP / (minPr + 0.5)
                    if loyPT < -20 then loyPT = -20 end
                    if loyPT > 20 then loyPT = 20 end
                    if loyPT < 0 then score = score + loyPT * 2 end
                    table.insert(candidates, {x=cx, y=cy, score=score, f=totalF, p=totalP, water=waterType, def=defScore, res=table.concat(resList, ","), loy=loyPT})
                end
"""

def _settle_output(limit: int) -> str:
    return f"""
table.sort(candidates, function(a, b) return a.score > b.score end)
for i = 1, math.min({limit}, #candidates) do
    local c = candidates[i]
    print("SETTLE|" .. c.x .. "," .. c.y .. "|" .. c.score .. "|" .. c.f .. "|" .. c.p .. "|" .. c.water .. "|" .. c.def .. "|" .. c.res .. "|" .. string.format("%.1f", c.loy))
end
if #candidates == 0 then print("NONE") end
print("{SENTINEL}")
"""


def build_map_area_query(center_x: int, center_y: int, radius: int = 2) -> str:
    return f"""
local cx, cy, r = {center_x}, {center_y}, {radius}
local me = Game.GetLocalPlayer()
local vis = PlayersVisibility[me]
local pTech = Players[me]:GetTechs()
local function resVisible(resEntry)
    if not resEntry.PrereqTech then return true end
    local t = GameInfo.Technologies[resEntry.PrereqTech]
    return t and pTech:HasTech(t.Index)
end
for dy = -r, r do
    for dx = -r, r do
        local x, y = cx + dx, cy + dy
        local plot = Map.GetPlot(x, y)
        if plot then
            local plotIdx = plot:GetIndex()
            local revealed = vis:IsRevealed(plotIdx)
            local visible = vis:IsVisible(plotIdx)
            if revealed then
                local terrain = GameInfo.Terrains[plot:GetTerrainType()].TerrainType
                local hills = plot:IsHills() and "1" or "0"
                local river = plot:IsRiver() and "1" or "0"
                local coastal = plot:IsCoastalLand() and "1" or "0"
                local owner = plot:GetOwner()
                local featureIdx = plot:GetFeatureType()
                local feature = "none"
                if featureIdx >= 0 then feature = GameInfo.Features[featureIdx].FeatureType end
                local resource = "none"
                local resIdx = plot:GetResourceType()
                if resIdx >= 0 then
                    local resEntry = GameInfo.Resources[resIdx]
                    if resVisible(resEntry) then
                        resource = resEntry.ResourceType .. ":" .. (resEntry.ResourceClassType or "")
                    end
                end
                local imp = "none"
                local freshWater = "0"
                local yields = "0,0,0,0,0,0"
                local unitStr = "none"
                local visTag = "revealed"
                if visible then
                    visTag = "visible"
                    local impIdx = plot:GetImprovementType()
                    if impIdx >= 0 then
                        imp = GameInfo.Improvements[impIdx].ImprovementType
                        if plot:IsImprovementPillaged() then imp = imp .. ":PILLAGED" end
                    end
                    freshWater = plot:IsFreshWater() and "1" or "0"
                    yields = plot:GetYield(0) .. "," .. plot:GetYield(1) .. "," .. plot:GetYield(2) .. "," .. plot:GetYield(3) .. "," .. plot:GetYield(4) .. "," .. plot:GetYield(5)
                    local uParts = {{}}
                    for i = 0, 63 do
                        if i ~= me and Players[i] and Players[i]:IsAlive() then
                            local units = Players[i]:GetUnits()
                            if units then
                                for _, u in units:Members() do
                                    if u:GetX() == x and u:GetY() == y then
                                        local entry = GameInfo.Units[u:GetType()]
                                        local ut = entry and entry.UnitType or "UNKNOWN"
                                        local label = ""
                                        if i == 63 then label = "Barbarian"
                                        else
                                            local oCfg = PlayerConfigurations[i]
                                            label = Locale.Lookup(oCfg:GetCivilizationShortDescription())
                                        end
                                        table.insert(uParts, label .. " " .. ut:gsub("UNIT_", ""))
                                    end
                                end
                            end
                        end
                    end
                    if #uParts > 0 then unitStr = table.concat(uParts, ";") end
                end
                local distName = "none"
                local distIdx = plot:GetDistrictType()
                if distIdx >= 0 then
                    local dInfo = GameInfo.Districts[distIdx]
                    if dInfo then distName = dInfo.DistrictType end
                end
                print(x .. "," .. y .. "|" .. terrain .. "|" .. feature .. "|" .. resource .. "|" .. hills .. "|" .. river .. "|" .. coastal .. "|" .. imp .. "|" .. owner .. "|" .. unitStr .. "|" .. visTag .. "|" .. freshWater .. "|" .. yields .. "|" .. distName)
            end
        end
    end
end
print("{SENTINEL}")
"""


def build_strategic_map_query() -> str:
    """GameCore context: fog boundary per city + unclaimed luxury/strategic resources."""
    return f"""
local me = Game.GetLocalPlayer()
local vis = PlayersVisibility[me]
local pTech = Players[me]:GetTechs()
local w, h = Map.GetGridSize()
-- Hex direction offsets (NE, E, SE, SW, W, NW) for offset coords
local dirs = {{{{0,-1}},{{1,0}},{{0,1}},{{-1,1}},{{-1,0}},{{0,-1}}}}
-- Actually use precise ray-cast: step along each cardinal hex direction
-- For offset coordinates, direction deltas depend on row parity
-- Simplified: use angular sectors by scanning radius rings
for _, c in Players[me]:GetCities():Members() do
    local cx, cy = c:GetX(), c:GetY()
    local nm = Locale.Lookup(c:GetName())
    -- For 6 directions, scan along a ray and find first unrevealed tile
    -- Directions: N(0,-1), NE(+1,-1), SE(+1,+1), S(0,+1), SW(-1,+1), NW(-1,-1) approx
    local dirVecs = {{{{0,-1}},{{1,-1}},{{1,1}},{{0,1}},{{-1,1}},{{-1,-1}}}}
    local fogDists = {{}}
    for _, dv in ipairs(dirVecs) do
        local fogDist = -1
        for dist = 3, 15 do
            local tx = cx + dv[1] * dist
            local ty = cy + dv[2] * dist
            local plot = Map.GetPlot(tx, ty)
            if plot then
                if not vis:IsRevealed(plot:GetIndex()) then
                    fogDist = dist
                    break
                end
            else
                fogDist = dist
                break
            end
        end
        table.insert(fogDists, fogDist)
    end
    print("FOG|" .. nm .. "|" .. cx .. "," .. cy .. "|" .. table.concat(fogDists, ","))
end
-- Pass 2: unclaimed luxury/strategic resources on revealed land
for y = 0, h - 1 do
    for x = 0, w - 1 do
        local plot = Map.GetPlot(x, y)
        if plot and vis:IsRevealed(plot:GetIndex()) and plot:GetOwner() == -1 then
            local resIdx = plot:GetResourceType()
            if resIdx >= 0 then
                local res = GameInfo.Resources[resIdx]
                if res and res.ResourceClassType ~= "RESOURCECLASS_BONUS" then
                    -- Check tech visibility
                    local visible = true
                    if res.PrereqTech then
                        local t = GameInfo.Technologies[res.PrereqTech]
                        if t and not pTech:HasTech(t.Index) then visible = false end
                    end
                    if visible then
                        print("UNCLAIMED|" .. res.ResourceType .. "|" .. x .. "," .. y .. "|" .. res.ResourceClassType)
                    end
                end
            end
        end
    end
end
print("{SENTINEL}")
"""


def parse_strategic_map_response(lines: list[str]) -> StrategicMapData:
    """Parse FOG| and UNCLAIMED| lines from strategic map query."""
    fog_boundaries: list[FogBoundary] = []
    unclaimed: list[UnclaimedResource] = []

    for line in lines:
        if line.startswith("FOG|"):
            parts = line.split("|")
            if len(parts) >= 4:
                cx, cy = parts[2].split(",")
                dists = [int(d) for d in parts[3].split(",")]
                fog_boundaries.append(FogBoundary(
                    city_name=parts[1],
                    city_x=int(cx),
                    city_y=int(cy),
                    fog_distances=dists,
                ))
        elif line.startswith("UNCLAIMED|"):
            parts = line.split("|")
            if len(parts) >= 4:
                rx, ry = parts[2].split(",")
                unclaimed.append(UnclaimedResource(
                    resource_type=parts[1],
                    x=int(rx),
                    y=int(ry),
                    resource_class=parts[3],
                ))

    return StrategicMapData(fog_boundaries=fog_boundaries, unclaimed_resources=unclaimed)


def parse_minimap_response(lines: list[str]) -> MinimapData:
    """Parse SIZE| and ROW| lines from minimap query."""
    width, height = 0, 0
    rows: dict[int, str] = {}
    for line in lines:
        if line.startswith("SIZE|"):
            parts = line.split("|")
            width = int(parts[1])
            height = int(parts[2])
        elif line.startswith("ROW|"):
            parts = line.split("|", 2)
            if len(parts) >= 3:
                rows[int(parts[1])] = parts[2]
    return MinimapData(width=width, height=height, rows=rows)


def build_found_city(unit_index: int) -> str:
    return f"""
{_lua_get_unit(unit_index)}
if not UnitManager.CanStartOperation(unit, UnitOperationTypes.FOUND_CITY, nil, true) then
    {_bail("ERR:CANNOT_FOUND|Unit cannot found cities (not a settler or no moves)")}
end
local x, y = unit:GetX(), unit:GetY()
local plot = Map.GetPlot(x, y)
if plot:IsWater() then {_bail("ERR:CANNOT_FOUND|Cannot found city on water")} end
if plot:IsMountain() then {_bail("ERR:CANNOT_FOUND|Cannot found city on mountain")} end
for i = 0, 62 do
    if Players[i] and Players[i]:IsAlive() then
        local cities = Players[i]:GetCities()
        if cities then
            for _, c in cities:Members() do
                local dist = Map.GetPlotDistance(x, y, c:GetX(), c:GetY())
                if dist <= 3 then
                    {_bail_lua('"ERR:CANNOT_FOUND|Too close to " .. Locale.Lookup(c:GetName()) .. " (settler at " .. x .. "," .. y .. ", distance " .. dist .. ", need > 3)"')}
                end
            end
        end
    end
end
local params = {{}}
params[UnitOperationTypes.PARAM_X] = x
params[UnitOperationTypes.PARAM_Y] = y
pcall(function() LuaEvents.DiplomacyActionView_ShowIngameUI() end)
UnitManager.RequestOperation(unit, UnitOperationTypes.FOUND_CITY, params)
print("OK:FOUNDED|" .. x .. "," .. y)
print("{SENTINEL}")
"""


def build_verify_city_at(x: int, y: int) -> str:
    """Check if a city exists at the given coordinates."""
    return f"""
local plot = Map.GetPlot({x}, {y})
if plot and plot:IsCity() then
    print("OK:CITY_EXISTS")
else
    print("OK:NO_CITY")
end
print("{SENTINEL}")
"""


def parse_verify_city_at(lines: list[str]) -> bool:
    """Return True if a city was found at the coordinates."""
    for line in lines:
        if "CITY_EXISTS" in line:
            return True
    return False


def build_settle_advisor_query(unit_index: int) -> str:
    """Scan radius 5 around settler for valid + scored settle candidates.

    Scores by weighted yields, water bonus, defense, and resource value.
    Resources are classified (S=strategic, L=luxury, B=bonus).
    Returns top 5 candidates sorted by score.
    """
    return f"""
local me = Game.GetLocalPlayer()
local unit = UnitManager.GetUnit(me, {unit_index})
if unit == nil then print("NONE"); print("{SENTINEL}"); return end
local sx, sy = unit:GetX(), unit:GetY()
local vis = PlayersVisibility[me]
local pTech = Players[me]:GetTechs()
{_SETTLE_PREAMBLE}
for dy = -5, 5 do
    for dx = -5, 5 do
        local cx, cy = sx + dx, sy + dy
        local cPlot = Map.GetPlot(cx, cy)
        if cPlot and vis:IsVisible(cPlot:GetIndex()) and not cPlot:IsWater() and not cPlot:IsMountain() then
{_SETTLE_SCORE_BODY}
        end
    end
end
{_settle_output(5)}
"""


def build_minimap_query() -> str:
    """GameCore context: minimal per-tile data for ASCII minimap rendering.

    For each tile on the map, outputs one compact line:
    x,y|owner|terrain_char|visibility
    terrain_char: ~ water, ^ mountain, # hills, T forest/jungle, . flat, * resource
    visibility: V=visible, R=revealed(fog), U=unexplored
    """
    return f"""
local me = Game.GetLocalPlayer()
local vis = PlayersVisibility[me]
local pTech = Players[me]:GetTechs()
local w, h = Map.GetGridSize()
print("SIZE|" .. w .. "|" .. h)
for y = 0, h - 1 do
    local row = {{}}
    for x = 0, w - 1 do
        local plot = Map.GetPlot(x, y)
        if not plot then
            table.insert(row, "?")
        elseif not vis:IsRevealed(plot:GetIndex()) then
            table.insert(row, " ")
        else
            local ch = "."
            if plot:IsWater() then ch = "~"
            elseif plot:IsMountain() then ch = "^"
            elseif plot:IsHills() then ch = "#"
            else
                local feat = plot:GetFeatureType()
                if feat >= 0 then
                    local f = GameInfo.Features[feat]
                    if f and (f.FeatureType == "FEATURE_FOREST" or f.FeatureType == "FEATURE_JUNGLE") then ch = "T" end
                end
            end
            local owner = plot:GetOwner()
            if owner == me then
                -- Our city on this tile?
                local isCity = plot:IsCity()
                if isCity then ch = "O"
                else ch = string.upper(ch) end
            elseif owner >= 0 and owner ~= 63 then
                local isCity = plot:IsCity()
                if isCity then ch = "X"
                else ch = string.lower(ch) end
            elseif owner == 63 then
                ch = "!"
            end
            -- Resource marker (only if not already a special char, and tech-visible)
            if ch == "." or ch == "#" then
                local resIdx = plot:GetResourceType()
                if resIdx >= 0 then
                    local res = GameInfo.Resources[resIdx]
                    if res then
                        local techOk = true
                        if res.PrereqTech then
                            local t = GameInfo.Technologies[res.PrereqTech]
                            if t and not pTech:HasTech(t.Index) then techOk = false end
                        end
                        if techOk then
                            if res.ResourceClassType == "RESOURCECLASS_LUXURY" then ch = "+"
                            elseif res.ResourceClassType == "RESOURCECLASS_STRATEGIC" then ch = "*" end
                        end
                    end
                end
            end
            table.insert(row, ch)
        end
    end
    print("ROW|" .. y .. "|" .. table.concat(row, ""))
end
print("{SENTINEL}")
"""


def build_global_settle_scan() -> str:
    """GameCore context: scan all revealed, unowned tiles for settle viability.

    Reuses the same scoring logic and SETTLE| output format as
    build_settle_advisor_query, but searches the entire revealed map
    rather than a radius around a settler. Returns top 10 candidates.
    """
    return f"""
local me = Game.GetLocalPlayer()
local vis = PlayersVisibility[me]
local pTech = Players[me]:GetTechs()
local w, h = Map.GetGridSize()
{_SETTLE_PREAMBLE}
for y = 0, h - 1 do
    for x = 0, w - 1 do
        local cx, cy = x, y
        local cPlot = Map.GetPlot(cx, cy)
        if cPlot and vis:IsRevealed(cPlot:GetIndex()) and not cPlot:IsWater() and not cPlot:IsMountain() then
{_SETTLE_SCORE_BODY}
        end
    end
end
{_settle_output(10)}
"""


def build_empire_resources_query() -> str:
    """Scan owned tiles for resources, stockpile counts, and nearby unclaimed.

    Returns STOCKPILE lines for strategic resource amounts/caps,
    OWNED lines for resources on player-owned tiles, and
    NEARBY lines for unclaimed resources within 5 tiles of cities.
    Runs in InGame context for GetResourceStockpileCap/GetResourceAccumulationPerTurn.
    """
    return f"""
local me = Game.GetLocalPlayer()
local vis = PlayersVisibility[me]
local pRes = Players[me]:GetResources()
local classMap = {{RESOURCECLASS_STRATEGIC="strategic", RESOURCECLASS_LUXURY="luxury", RESOURCECLASS_BONUS="bonus"}}
-- Stockpile info for strategic and luxury resources
for row in GameInfo.Resources() do
    if pRes:IsResourceVisible(row.Index) then
        local cls = classMap[row.ResourceClassType]
        if cls == "strategic" then
            local amt = pRes:GetResourceAmount(row.Index)
            local cap = pRes:GetResourceStockpileCap(row.Index)
            local accum = pRes:GetResourceAccumulationPerTurn(row.Index)
            local demand = pRes:GetUnitResourceDemandPerTurn(row.Index)
            local imported = pRes:GetResourceImportPerTurn(row.Index)
            local rName = row.ResourceType:gsub("RESOURCE_", "")
            print("STOCKPILE|" .. rName .. "|" .. amt .. "|" .. cap .. "|" .. accum .. "|" .. demand .. "|" .. imported)
        elseif cls == "luxury" then
            local amt = pRes:GetResourceAmount(row.Index)
            if amt > 0 then
                local rName = row.ResourceType:gsub("RESOURCE_", "")
                print("LUXURY_OWNED|" .. rName .. "|" .. amt)
            end
        end
    end
end
local myCities = {{}}
local seen = {{}}
for _, c in Players[me]:GetCities():Members() do
    table.insert(myCities, {{name=Locale.Lookup(c:GetName()), x=c:GetX(), y=c:GetY()}})
end
-- Scan all owned tiles
local mapW, mapH = Map.GetGridSize()
for x = 0, mapW - 1 do
    for y = 0, mapH - 1 do
        local plot = Map.GetPlot(x, y)
        if plot and plot:GetOwner() == me then
            local rIdx = plot:GetResourceType()
            if rIdx >= 0 and pRes:IsResourceVisible(rIdx) then
                local resEntry = GameInfo.Resources[rIdx]
                local rName = resEntry.ResourceType:gsub("RESOURCE_", "")
                local rClass = classMap[resEntry.ResourceClassType] or "bonus"
                local impIdx = plot:GetImprovementType()
                local improved = "0"
                if impIdx >= 0 then improved = "1" end
                print("OWNED|" .. rName .. "|" .. rClass .. "|" .. improved .. "|" .. x .. "," .. y)
                seen[x .. "," .. y] = true
            end
        end
    end
end
-- Scan radius 5 around each city for unowned visible resources
for _, city in ipairs(myCities) do
    for dy = -5, 5 do
        for dx = -5, 5 do
            local tx, ty = city.x + dx, city.y + dy
            local key = tx .. "," .. ty
            if not seen[key] then
                local tPlot = Map.GetPlot(tx, ty)
                if tPlot and vis:IsRevealed(tPlot:GetIndex()) and tPlot:GetOwner() ~= me then
                    local rIdx = tPlot:GetResourceType()
                    if rIdx >= 0 and pRes:IsResourceVisible(rIdx) then
                        local resEntry = GameInfo.Resources[rIdx]
                        local rName = resEntry.ResourceType:gsub("RESOURCE_", "")
                        local rClass = classMap[resEntry.ResourceClassType] or "bonus"
                        local dist = Map.GetPlotDistance(city.x, city.y, tx, ty)
                        print("NEARBY|" .. rName .. "|" .. rClass .. "|" .. tx .. "," .. ty .. "|" .. city.name .. "|" .. dist)
                        seen[key] = true
                    end
                end
            end
        end
    end
end
print("{SENTINEL}")
"""


def build_district_advisor_query(city_id: int, district_type: str) -> str:
    """Find valid tiles for a district with adjacency bonuses (InGame context).

    Uses hardcoded adjacency formulas for common districts rather than
    parsing 157 Adjacency_YieldChanges rows in Lua.
    """
    return f"""
{_lua_get_city(city_id)}
local pTech = Players[Game.GetLocalPlayer()]:GetTechs()
local dist = GameInfo.Districts["{district_type}"]
if dist == nil then {_bail(f"ERR:DISTRICT_NOT_FOUND|{district_type}")} end
local bq = pCity:GetBuildQueue()
if not bq:CanProduce(dist.Hash, true) then
    {_bail(f"ERR:CANNOT_PRODUCE|{district_type} cannot be produced in this city")}
end
local targets = CityManager.GetOperationTargets(pCity, CityOperationTypes.BUILD, {{[CityOperationTypes.PARAM_DISTRICT_TYPE] = dist.Hash}})
if targets == nil then {_bail("ERR:NO_TARGETS|No valid placement targets found")} end
local plotIndices = {{}}
for k, v in pairs(targets) do
    if type(v) == "table" then
        for _, idx in ipairs(v) do table.insert(plotIndices, idx) end
    end
end
if #plotIndices == 0 then {_bail("ERR:NO_TILES|No valid placement tiles found")} end
local results = {{}}
local dType = "{district_type}"
for _, pIdx in ipairs(plotIndices) do
    local plot = Map.GetPlotByIndex(pIdx)
    if plot and not plot:IsWater() and not plot:IsImpassable() and not plot:IsMountain() then
        local px, py = plot:GetX(), plot:GetY()
        local adj_s, adj_p, adj_g, adj_f, adj_c = 0, 0, 0, 0, 0
        local mountains, jungles, forests, districts, rivers = 0, 0, 0, 0, 0
        local wonders, mines, quarries, harbors, aqueducts, ent_complex = 0, 0, 0, 0, 0, 0
        local geothermal, reefs, nat_wonders, sea_resources = 0, 0, 0, 0
        local isRiver = plot:IsRiver()
        if isRiver then rivers = 1 end
        for d = 0, 5 do
            local adj = Map.GetAdjacentPlot(px, py, d)
            if adj then
                if adj:IsMountain() then mountains = mountains + 1 end
                local feat = adj:GetFeatureType()
                if feat >= 0 then
                    local fInfo = GameInfo.Features[feat]
                    if fInfo then
                        local fn = fInfo.FeatureType
                        if fn == "FEATURE_JUNGLE" then jungles = jungles + 1
                        elseif fn == "FEATURE_FOREST" then forests = forests + 1
                        elseif fn == "FEATURE_GEOTHERMAL_FISSURE" then geothermal = geothermal + 1
                        elseif fn == "FEATURE_REEF" then reefs = reefs + 1
                        elseif fInfo.NaturalWonder then nat_wonders = nat_wonders + 1
                        end
                    end
                end
                local distId = adj:GetDistrictType()
                if distId >= 0 then
                    districts = districts + 1
                    local dInfo = GameInfo.Districts[distId]
                    if dInfo then
                        local dn = dInfo.DistrictType
                        if dn == "DISTRICT_HARBOR" then harbors = harbors + 1
                        elseif dn == "DISTRICT_AQUEDUCT" then aqueducts = aqueducts + 1
                        elseif dn == "DISTRICT_ENTERTAINMENT_COMPLEX" or dn == "DISTRICT_WATER_ENTERTAINMENT_COMPLEX" then ent_complex = ent_complex + 1
                        end
                    end
                end
                local imp = adj:GetImprovementType()
                if imp >= 0 then
                    local iInfo = GameInfo.Improvements[imp]
                    if iInfo then
                        local in2 = iInfo.ImprovementType
                        if in2 == "IMPROVEMENT_MINE" then mines = mines + 1
                        elseif in2 == "IMPROVEMENT_QUARRY" then quarries = quarries + 1
                        end
                    end
                end
                local res = adj:GetResourceType()
                if res >= 0 then
                    local rInfo = GameInfo.Resources[res]
                    if rInfo and adj:IsWater() then
                        local rTechOk = true
                        if rInfo.PrereqTech then
                            local rt = GameInfo.Technologies[rInfo.PrereqTech]
                            if rt and not pTech:HasTech(rt.Index) then rTechOk = false end
                        end
                        if rTechOk then sea_resources = sea_resources + 1 end
                    end
                end
                local wid = adj:GetWonderType()
                if wid >= 0 then wonders = wonders + 1 end
            end
        end
        if dType == "DISTRICT_CAMPUS" then
            adj_s = mountains + math.floor(jungles / 2) + geothermal * 2 + reefs * 2 + nat_wonders * 2
        elseif dType == "DISTRICT_HOLY_SITE" then
            adj_f = mountains + math.floor(forests / 2) + nat_wonders * 2
        elseif dType == "DISTRICT_INDUSTRIAL_ZONE" then
            adj_p = mines + quarries + aqueducts * 2
        elseif dType == "DISTRICT_COMMERCIAL_HUB" then
            if rivers > 0 then adj_g = adj_g + 2 end
            adj_g = adj_g + harbors * 2
        elseif dType == "DISTRICT_THEATER" then
            adj_c = wonders + ent_complex * 2
        elseif dType == "DISTRICT_HARBOR" then
            adj_g = sea_resources
        end
        local total = adj_s + adj_p + adj_g + adj_f + adj_c
        local terrain = ""
        local tInfo = GameInfo.Terrains[plot:GetTerrainType()]
        if tInfo then terrain = Locale.Lookup(tInfo.Name) end
        if plot:IsHills() then terrain = terrain .. " Hills" end
        local fInfo2 = nil
        if plot:GetFeatureType() >= 0 then fInfo2 = GameInfo.Features[plot:GetFeatureType()] end
        if fInfo2 then terrain = terrain .. " " .. Locale.Lookup(fInfo2.Name) end
        table.insert(results, {{x=px, y=py, s=adj_s, p=adj_p, g=adj_g, f=adj_f, c=adj_c, total=total, terrain=terrain}})
    end
end
table.sort(results, function(a, b) return a.total > b.total end)
for i = 1, math.min(#results, 10) do
    local r = results[i]
    print("DPLOT|" .. r.x .. "," .. r.y .. "|" .. r.s .. "|" .. r.p .. "|" .. r.g .. "|" .. r.f .. "|" .. r.c .. "|" .. r.total .. "|" .. r.terrain)
end
print("{SENTINEL}")
"""


def build_purchasable_tiles_query(city_id: int) -> str:
    """List tiles a city can purchase with gold (InGame context)."""
    return f"""
{_lua_get_city(city_id)}
local pTech = Players[me]:GetTechs()
local targets = CityManager.GetCommandTargets(pCity, CityCommandTypes.PURCHASE, {{[CityCommandTypes.PARAM_PLOT_PURCHASE] = 1}})
if targets == nil then {_bail("ERR:NO_TARGETS|No purchasable tiles found")} end
local plotIndices = {{}}
for k, v in pairs(targets) do
    if type(v) == "table" then
        for _, idx in ipairs(v) do table.insert(plotIndices, idx) end
    end
end
if #plotIndices == 0 then {_bail("ERR:NO_TILES|No purchasable tiles")} end
local results = {{}}
for _, pIdx in ipairs(plotIndices) do
    local plot = Map.GetPlotByIndex(pIdx)
    if plot then
        local px, py = plot:GetX(), plot:GetY()
        local cost = pCity:GetGold():GetPlotPurchaseCost(px, py)
        if cost > 0 then
            local terrain = ""
            local tInfo = GameInfo.Terrains[plot:GetTerrainType()]
            if tInfo then terrain = Locale.Lookup(tInfo.Name) end
            if plot:IsHills() then terrain = terrain .. " Hills" end
            local resName, resClass = "", ""
            local res = plot:GetResourceType()
            if res >= 0 then
                local rInfo = GameInfo.Resources[res]
                if rInfo then
                    local rTechOk = true
                    if rInfo.PrereqTech then
                        local rt = GameInfo.Technologies[rInfo.PrereqTech]
                        if rt and not pTech:HasTech(rt.Index) then rTechOk = false end
                    end
                    if rTechOk then
                        resName = Locale.Lookup(rInfo.Name)
                        local rc = rInfo.ResourceClassType
                        if rc == "RESOURCECLASS_STRATEGIC" then resClass = "strategic"
                        elseif rc == "RESOURCECLASS_LUXURY" then resClass = "luxury"
                        else resClass = "bonus" end
                    end
                end
            end
            local sortKey = 0
            if resClass == "luxury" then sortKey = 3
            elseif resClass == "strategic" then sortKey = 2
            elseif resClass == "bonus" then sortKey = 1 end
            table.insert(results, {{x=px, y=py, cost=cost, terrain=terrain, res=resName, cls=resClass, sk=sortKey}})
        end
    end
end
table.sort(results, function(a, b)
    if a.sk ~= b.sk then return a.sk > b.sk end
    return a.cost < b.cost
end)
for i = 1, math.min(#results, 15) do
    local r = results[i]
    print("PTILE|" .. r.x .. "," .. r.y .. "|" .. r.cost .. "|" .. r.terrain .. "|" .. r.res .. "|" .. r.cls)
end
print("{SENTINEL}")
"""


def build_purchase_tile(city_id: int, x: int, y: int) -> str:
    """Buy a tile for a city with gold (InGame context)."""
    return f"""
{_lua_get_city(city_id)}
local cost = pCity:GetGold():GetPlotPurchaseCost({x}, {y})
if cost <= 0 then {_bail(f"ERR:NOT_PURCHASABLE|Tile ({x},{y}) is not purchasable by this city")} end
local balance = Players[me]:GetTreasury():GetGoldBalance()
if balance < cost then
    {_bail_lua('"ERR:INSUFFICIENT_GOLD|Need " .. cost .. " gold, have " .. math.floor(balance)')}
end
local tParams = {{}}
tParams[CityCommandTypes.PARAM_PLOT_PURCHASE] = 1
tParams[CityCommandTypes.PARAM_X] = {x}
tParams[CityCommandTypes.PARAM_Y] = {y}
CityManager.RequestCommand(pCity, CityCommandTypes.PURCHASE, tParams)
print("OK:TILE_PURCHASED|({x},{y})|cost:" .. cost)
print("{SENTINEL}")
"""


def parse_map_response(lines: list[str]) -> list[TileInfo]:
    tiles = []
    for line in lines:
        parts = line.split("|")
        if len(parts) < 9:
            continue
        x_str, y_str = parts[0].split(",")
        unit_list = None
        if len(parts) > 9 and parts[9] != "none":
            unit_list = parts[9].split(";")
        visibility = "visible"
        if len(parts) > 10:
            visibility = parts[10]
        is_fresh_water = False
        if len(parts) > 11:
            is_fresh_water = parts[11] == "1"
        yields = None
        if len(parts) > 12 and parts[12] != "0,0,0,0,0,0":
            yield_parts = parts[12].split(",")
            if len(yield_parts) == 6:
                yields = tuple(int(float(y)) for y in yield_parts)
        elif len(parts) > 12 and visibility == "visible":
            # Visible tile with all-zero yields — still valid
            yields = (0, 0, 0, 0, 0, 0)
        # Parse resource field — may contain "RESOURCE_X:RESOURCECLASS_Y" or "none"
        resource_name = None
        resource_class = None
        if parts[3] != "none":
            res_parts = parts[3].split(":", 1)
            resource_name = res_parts[0]
            if len(res_parts) > 1:
                _CLASS_MAP = {
                    "RESOURCECLASS_STRATEGIC": "strategic",
                    "RESOURCECLASS_LUXURY": "luxury",
                    "RESOURCECLASS_BONUS": "bonus",
                }
                resource_class = _CLASS_MAP.get(res_parts[1])
        # Parse improvement — may have :PILLAGED suffix
        imp_raw = parts[7]
        imp_name = None
        imp_pillaged = False
        if imp_raw != "none":
            if imp_raw.endswith(":PILLAGED"):
                imp_name = imp_raw[:-9]  # strip ":PILLAGED"
                imp_pillaged = True
            else:
                imp_name = imp_raw
        tiles.append(TileInfo(
            x=int(x_str),
            y=int(y_str),
            terrain=parts[1],
            feature=None if parts[2] == "none" else parts[2],
            resource=resource_name,
            is_hills=parts[4] == "1",
            is_river=parts[5] == "1",
            is_coastal=parts[6] == "1",
            improvement=imp_name,
            owner_id=int(parts[8]),
            visibility=visibility,
            is_fresh_water=is_fresh_water,
            yields=yields,
            units=unit_list,
            resource_class=resource_class,
            is_pillaged=imp_pillaged,
            district=None if (len(parts) <= 13 or parts[13] == "none") else parts[13],
        ))
    return tiles


def parse_settle_advisor_response(lines: list[str]) -> list[SettleCandidate]:
    candidates = []
    for line in lines:
        if line == "NONE":
            break
        if not line.startswith("SETTLE|"):
            continue
        parts = line.split("|")
        if len(parts) < 8:
            continue
        x_str, y_str = parts[1].split(",")
        resources = [r for r in parts[7].split(",") if r] if parts[7] else []
        lux = sum(1 for r in resources if r.startswith("L:"))
        strat = sum(1 for r in resources if r.startswith("S:"))
        candidates.append(SettleCandidate(
            x=int(x_str),
            y=int(y_str),
            score=float(parts[2]),
            total_food=int(parts[3]),
            total_prod=int(parts[4]),
            water_type=parts[5],
            resources=resources,
            defense_score=int(parts[6]),
            luxury_count=lux,
            strategic_count=strat,
            loyalty_pressure=float(parts[8]) if len(parts) > 8 else 0.0,
        ))
    return candidates


def build_stockpile_query() -> str:
    """Lightweight strategic resource stockpile query (InGame context).

    Only emits STOCKPILE lines — no tile scanning. Used for turn snapshots.
    """
    return f"""
local me = Game.GetLocalPlayer()
local pRes = Players[me]:GetResources()
for row in GameInfo.Resources() do
    if row.ResourceClassType == "RESOURCECLASS_STRATEGIC" and pRes:IsResourceVisible(row.Index) then
        local amt = pRes:GetResourceAmount(row.Index)
        local cap = pRes:GetResourceStockpileCap(row.Index)
        local accum = pRes:GetResourceAccumulationPerTurn(row.Index)
        local demand = pRes:GetUnitResourceDemandPerTurn(row.Index)
        local imported = pRes:GetResourceImportPerTurn(row.Index)
        local rName = row.ResourceType:gsub("RESOURCE_", "")
        print("STOCKPILE|" .. rName .. "|" .. amt .. "|" .. cap .. "|" .. accum .. "|" .. demand .. "|" .. imported)
    end
end
print("{SENTINEL}")
"""


def parse_stockpile_response(lines: list[str]) -> list[ResourceStockpile]:
    """Parse STOCKPILE lines into ResourceStockpile objects."""
    stockpiles = []
    for line in lines:
        if line.startswith("STOCKPILE|"):
            parts = line.split("|")
            if len(parts) < 7:
                continue
            stockpiles.append(ResourceStockpile(
                name=parts[1],
                amount=int(parts[2]),
                cap=int(parts[3]),
                per_turn=int(parts[4]),
                demand=int(parts[5]),
                imported=int(parts[6]),
            ))
    return stockpiles


def parse_empire_resources_response(
    lines: list[str],
) -> tuple[list[ResourceStockpile], list[OwnedResource], list[NearbyResource], dict[str, int]]:
    """Returns (stockpiles, owned_tiles, nearby_unclaimed, luxury_counts)."""
    stockpiles = []
    owned = []
    nearby = []
    luxuries: dict[str, int] = {}
    for line in lines:
        if line.startswith("STOCKPILE|"):
            parts = line.split("|")
            if len(parts) < 7:
                continue
            stockpiles.append(ResourceStockpile(
                name=parts[1],
                amount=int(parts[2]),
                cap=int(parts[3]),
                per_turn=int(parts[4]),
                demand=int(parts[5]),
                imported=int(parts[6]),
            ))
        elif line.startswith("LUXURY_OWNED|"):
            parts = line.split("|")
            if len(parts) >= 3:
                luxuries[parts[1]] = int(parts[2])
        elif line.startswith("OWNED|"):
            parts = line.split("|")
            if len(parts) < 5:
                continue
            x_str, y_str = parts[4].split(",")
            owned.append(OwnedResource(
                name=parts[1],
                resource_class=parts[2],
                improved=parts[3] == "1",
                x=int(x_str),
                y=int(y_str),
            ))
        elif line.startswith("NEARBY|"):
            parts = line.split("|")
            if len(parts) < 6:
                continue
            x_str, y_str = parts[3].split(",")
            nearby.append(NearbyResource(
                name=parts[1],
                resource_class=parts[2],
                x=int(x_str),
                y=int(y_str),
                nearest_city=parts[4],
                distance=int(parts[5]),
            ))
    return stockpiles, owned, nearby, luxuries


def parse_district_advisor_response(lines: list[str]) -> list[DistrictPlacement]:
    """Parse DPLOT| lines from build_district_advisor_query."""
    results: list[DistrictPlacement] = []
    for line in lines:
        if line.startswith("DPLOT|"):
            parts = line.split("|")
            if len(parts) >= 9:
                coords = parts[1].split(",")
                adjacency: dict[str, int] = {}
                s, p, g, f, c = int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5]), int(parts[6])
                if s: adjacency["science"] = s
                if p: adjacency["production"] = p
                if g: adjacency["gold"] = g
                if f: adjacency["faith"] = f
                if c: adjacency["culture"] = c
                results.append(DistrictPlacement(
                    x=int(coords[0]),
                    y=int(coords[1]),
                    adjacency=adjacency,
                    total_adjacency=int(parts[7]),
                    terrain_desc=parts[8],
                ))
    return results


def parse_purchasable_tiles_response(lines: list[str]) -> list[PurchasableTile]:
    """Parse PTILE| lines from build_purchasable_tiles_query."""
    results: list[PurchasableTile] = []
    for line in lines:
        if line.startswith("PTILE|"):
            parts = line.split("|")
            if len(parts) >= 6:
                coords = parts[1].split(",")
                results.append(PurchasableTile(
                    x=int(coords[0]),
                    y=int(coords[1]),
                    cost=int(parts[2]),
                    terrain=parts[3],
                    resource=parts[4] if parts[4] else None,
                    resource_class=parts[5] if parts[5] else None,
                ))
    return results
