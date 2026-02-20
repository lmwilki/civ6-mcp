"""Victory domain — Lua builders and parsers."""

from __future__ import annotations

from civ_mcp.lua._helpers import SENTINEL
from civ_mcp.lua.models import DemographicEntry, VictoryPlayerProgress, VictoryProgress


def build_victory_proximity_query() -> str:
    """InGame: lightweight check for foreign victory threats. Safe for every turn."""
    return f"""
local me = Game.GetLocalPlayer()
local pDiplo = Players[me]:GetDiplomacy()
local relCount = {{}}
local relOwner = {{}}
local totalMajors = 0
for i = 0, 62 do
    local p = Players[i]
    if p and p:IsMajor() and p:IsAlive() then
        totalMajors = totalMajors + 1
        local majRel = p:GetReligion():GetReligionInMajorityOfCities()
        if majRel >= 0 then
            relCount[majRel] = (relCount[majRel] or 0) + 1
            if not relOwner[majRel] then
                local creator = -1
                for j = 0, 62 do
                    if Players[j] and Players[j]:IsAlive() and Players[j]:GetReligion():GetReligionTypeCreated() == majRel then creator = j end
                end
                if creator >= 0 and creator ~= me then
                    local rEntry = GameInfo.Religions[majRel]
                    local relName = rEntry and Locale.Lookup(rEntry.Name) or "Unknown"
                    if pDiplo:HasMet(creator) then
                        local cfg = PlayerConfigurations[creator]
                        relOwner[majRel] = Locale.Lookup(cfg:GetCivilizationShortDescription()) .. "|" .. relName
                    else
                        relOwner[majRel] = "Unknown civilization|" .. relName
                    end
                end
            end
        end
        if i ~= me and pDiplo:HasMet(i) then
            local okDvp, dvp = pcall(function() return p:GetStats():GetDiplomaticVictoryPoints() end)
            if okDvp and dvp and dvp >= 15 then
                local cfg = PlayerConfigurations[i]
                print("DIPLO_THREAT|" .. Locale.Lookup(cfg:GetCivilizationShortDescription()) .. "|" .. dvp)
            end
            local okSvp, svp = pcall(function() return p:GetStats():GetScienceVictoryPoints() end)
            if okSvp and svp and svp > 0 then
                local cfg = PlayerConfigurations[i]
                local needed = 50
                pcall(function() needed = p:GetStats():GetScienceVictoryPointsTotalNeeded() end)
                print("SCI_THREAT|" .. Locale.Lookup(cfg:GetCivilizationShortDescription()) .. "|" .. svp .. "|" .. needed)
            end
        end
    end
end
for relId, count in pairs(relCount) do
    if relOwner[relId] then
        print("REL_THREAT|" .. relOwner[relId] .. "|" .. count .. "|" .. totalMajors)
    end
end
print("{SENTINEL}")
"""


def build_victory_progress_query() -> str:
    """Build a Lua query for victory progress of all players (InGame context).

    Outputs lines:
      PLAYER|pid|name|score|sciVP|sciNeeded|diploVP|tourism|milStr|techs|civics|relCities|staycationers|hasReligion
      CULTURE|civName|ourTourists|theirStaycationers|dominant
      CAPITAL|civName|holdsOwn
      RELMAJ|civName|religionName
    """
    return f"""
local me = Game.GetLocalPlayer()
local pDiplo = Players[me]:GetDiplomacy()
local pCul = Players[me]:GetCulture()

local dPop, dMil, dFood, dGold, dLand, dProd = {{}}, {{}}, {{}}, {{}}, {{}}, {{}}
for i = 0, 62 do
    local p = Players[i]
    if p and p:IsMajor() and p:IsAlive() then
        local met = pDiplo:HasMet(i) or i == me
        if met then
            local cfg = PlayerConfigurations[i]
            local name = Locale.Lookup(cfg:GetCivilizationShortDescription())
            local st = p:GetStats()
            local sciVP = st:GetScienceVictoryPoints()
            local sciNeeded = st:GetScienceVictoryPointsTotalNeeded()
            local diploVP = st:GetDiplomaticVictoryPoints()
            local tourism = st:GetTourism()
            local milStr = st:GetMilitaryStrength()
            local techs = st:GetNumTechsResearched()
            local civics = st:GetNumCivicsCompleted()
            local relCities = st:GetNumCitiesFollowingReligion()
            local stay = p:GetCulture():GetStaycationers()
            local hasRel = p:GetReligion():GetReligionTypeCreated() >= 0
            local nCities = 0; for _ in p:GetCities():Members() do nCities = nCities + 1 end
            local pSci = p:GetTechs():GetScienceYield()
            local pCulYield = p:GetCulture():GetCultureYield()
            local pGold2 = p:GetTreasury():GetGoldYield() - p:GetTreasury():GetTotalMaintenance()
            -- Space race: count spaceports
            local spaceports = 0
            for _, city in p:GetCities():Members() do
                for _, d in city:GetDistricts():Members() do
                    local dInfo = GameInfo.Districts[d:GetType()]
                    if dInfo and dInfo.DistrictType == "DISTRICT_SPACEPORT" and d:IsComplete() then
                        spaceports = spaceports + 1
                    end
                end
            end
            print("PLAYER|" .. i .. "|" .. name .. "|" .. p:GetScore() .. "|" .. sciVP .. "|" .. sciNeeded .. "|" .. diploVP .. "|" .. tourism .. "|" .. milStr .. "|" .. techs .. "|" .. civics .. "|" .. relCities .. "|" .. stay .. "|" .. tostring(hasRel) .. "|" .. nCities .. "|" .. string.format("%.1f", pSci) .. "|" .. string.format("%.1f", pCulYield) .. "|" .. string.format("%.1f", pGold2))
            print("SPACE|" .. name .. "|" .. spaceports .. "|" .. sciVP .. "/" .. sciNeeded)
            if i ~= me then
                local ourTourists = pCul:GetTouristsFrom(i)
                local theirStay = p:GetCulture():GetStaycationers()
                local dominant = pCul:IsDominantOver(i)
                print("CULTURE|" .. name .. "|" .. ourTourists .. "|" .. theirStay .. "|" .. tostring(dominant))
            end
            local cap = p:GetCities():GetCapitalCity()
            local holdsOwn = cap and cap:IsOriginalCapital() or false
            print("CAPITAL|" .. name .. "|" .. tostring(holdsOwn))
            local majRel = p:GetReligion():GetReligionInMajorityOfCities()
            local relName = "none"
            if majRel >= 0 then
                local r = GameInfo.Religions[majRel]
                if r then relName = r.ReligionType end
            end
            print("RELMAJ|" .. name .. "|" .. relName)
            local createdRel = p:GetReligion():GetReligionTypeCreated()
            if createdRel >= 0 then
                local rEntry = GameInfo.Religions[createdRel]
                local fName = rEntry and Locale.Lookup(rEntry.Name) or "Unknown"
                print("RELFOUNDED|" .. name .. "|" .. fName)
            end
        end
        -- Demographics: collect for ALL alive majors (anonymized aggregates)
        local totalPop = 0
        local totalFood, totalProd = 0, 0
        local ownedPlots = 0
        for _, c in p:GetCities():Members() do
            totalPop = totalPop + c:GetPopulation()
            totalFood = totalFood + c:GetYield(0)
            totalProd = totalProd + c:GetYield(1)
            local ok, pp = pcall(function() return Map.GetCityPlots():GetPurchasedPlots(c) end)
            if ok and pp then ownedPlots = ownedPlots + #pp end
        end
        local milVal = p:GetStats():GetMilitaryStrength()
        local netGold = p:GetTreasury():GetGoldYield() - p:GetTreasury():GetTotalMaintenance()
        table.insert(dPop, {{v=totalPop, mine=(i==me)}})
        table.insert(dMil, {{v=milVal, mine=(i==me)}})
        table.insert(dFood, {{v=totalFood, mine=(i==me)}})
        table.insert(dGold, {{v=netGold, mine=(i==me)}})
        table.insert(dLand, {{v=ownedPlots, mine=(i==me)}})
        table.insert(dProd, {{v=totalProd, mine=(i==me)}})
    end
end
local function emitDemo(label, arr)
    table.sort(arr, function(a, b) return a.v > b.v end)
    local best, worst, total = arr[1].v, arr[#arr].v, 0
    local myRank, myVal = 0, 0
    for idx, e in ipairs(arr) do
        total = total + e.v
        if e.mine then myRank = idx; myVal = e.v end
    end
    local avg = total / #arr
    print("DEMO|" .. label .. "|" .. myRank .. "|" .. string.format("%.1f", myVal) .. "|" .. string.format("%.1f", best) .. "|" .. string.format("%.1f", avg) .. "|" .. string.format("%.1f", worst))
end
emitDemo("Population", dPop)
emitDemo("Soldiers", dMil)
emitDemo("CropYield", dFood)
emitDemo("GNP", dGold)
emitDemo("Land", dLand)
emitDemo("Goods", dProd)
local nMajors = 0
local nRels = 0
for i = 0, 62 do
    if Players[i] and Players[i]:IsMajor() and Players[i]:IsAlive() then
        nMajors = nMajors + 1
        if Players[i]:GetReligion():GetReligionTypeCreated() >= 0 then nRels = nRels + 1 end
    end
end
print("RELSLOTS|" .. nRels .. "|" .. (math.floor(nMajors / 2) + 1))
print("{SENTINEL}")
"""


def parse_victory_progress_response(lines: list[str]) -> VictoryProgress:
    """Parse victory progress from Lua output."""
    players: list[VictoryPlayerProgress] = []
    our_tourists: dict[str, int] = {}
    their_stay: dict[str, int] = {}
    capitals: dict[str, bool] = {}
    rel_majority: dict[str, str] = {}
    rel_founded_names: dict[str, str] = {}
    religions_founded = 0
    religions_max = 0
    demographics: dict[str, DemographicEntry] = {}

    for line in lines:
        if line.startswith("PLAYER|"):
            p = line.split("|")
            if len(p) < 14:
                continue
            players.append(
                VictoryPlayerProgress(
                    player_id=int(p[1]),
                    name=p[2],
                    score=int(float(p[3])),
                    science_vp=int(float(p[4])),
                    science_vp_needed=int(float(p[5])),
                    diplomatic_vp=int(float(p[6])),
                    tourism=int(float(p[7])),
                    military_strength=int(float(p[8])),
                    techs_researched=int(float(p[9])),
                    civics_completed=int(float(p[10])),
                    religion_cities=int(float(p[11])),
                    staycationers=int(float(p[12])),
                    has_religion=p[13] == "true",
                    num_cities=int(float(p[14])) if len(p) > 14 else 0,
                    science_yield=float(p[15]) if len(p) > 15 else 0.0,
                    culture_yield=float(p[16]) if len(p) > 16 else 0.0,
                    gold_yield=float(p[17]) if len(p) > 17 else 0.0,
                )
            )
        elif line.startswith("SPACE|"):
            p = line.split("|")
            if len(p) >= 4:
                sp_name = p[1]
                sp_ports = int(p[2])
                sp_prog = p[3]
                for pl in players:
                    if pl.name == sp_name:
                        pl.spaceports = sp_ports
                        pl.space_progress = sp_prog
                        break
        elif line.startswith("CULTURE|"):
            p = line.split("|")
            if len(p) >= 5:
                our_tourists[p[1]] = int(p[2])
                their_stay[p[1]] = int(p[3])
        elif line.startswith("CAPITAL|"):
            p = line.split("|")
            if len(p) >= 3:
                capitals[p[1]] = p[2] == "true"
        elif line.startswith("RELMAJ|"):
            p = line.split("|")
            if len(p) >= 3:
                rel_majority[p[1]] = p[2]
        elif line.startswith("RELFOUNDED|"):
            p = line.split("|")
            if len(p) >= 3:
                rel_founded_names[p[1]] = p[2]
        elif line.startswith("RELSLOTS|"):
            p = line.split("|")
            if len(p) >= 3:
                religions_founded = int(p[1])
                religions_max = int(p[2])
        elif line.startswith("DEMO|"):
            p = line.split("|")
            if len(p) >= 6:
                demographics[p[1]] = DemographicEntry(
                    rank=int(p[2]),
                    value=float(p[3]),
                    best=float(p[4]),
                    average=float(p[5]),
                    worst=float(p[6]) if len(p) > 6 else float(p[5]),
                )

    return VictoryProgress(
        players=players,
        our_tourists_from=our_tourists,
        their_staycationers=their_stay,
        capitals_held=capitals,
        religion_majority=rel_majority,
        religion_founded_names=rel_founded_names,
        religions_founded=religions_founded,
        religions_max=religions_max,
        demographics=demographics,
    )
