"""Overview domain — Lua builders and parsers."""

from __future__ import annotations

from civ_mcp.lua._helpers import SENTINEL
from civ_mcp.lua.models import (
    AgentExtras,
    CityRow,
    DiarySnapshot,
    GameOverStatus,
    GameOverview,
    PlayerRow,
    ReligionInfo,
    RivalSnapshot,
    ScoreEntry,
)


def build_overview_query() -> str:
    return f"""
local id = Game.GetLocalPlayer()
local p = Players[id]
local cfg = PlayerConfigurations[id]
local tr = p:GetTreasury()
local te = p:GetTechs()
local cu = p:GetCulture()
local re = p:GetReligion()
local techIdx = te:GetResearchingTech()
local civicIdx = cu:GetProgressingCivic()
local techName = "None"
if techIdx >= 0 then techName = Locale.Lookup(GameInfo.Technologies[techIdx].Name) end
local civicName = "None"
if civicIdx >= 0 then civicName = Locale.Lookup(GameInfo.Civics[civicIdx].Name) end
local nCities = 0; local totalPop = 0; for i, c in p:GetCities():Members() do nCities = nCities + 1; totalPop = totalPop + c:GetPopulation() end
local nUnits = 0; for _ in p:GetUnits():Members() do nUnits = nUnits + 1 end
local myScore = p:GetScore()
local favor = p:GetFavor()
local favorPerTurn = 0
local pDiplo = p:GetDiplomacy()
-- 1. Government tier bonus (govRow.Tier is a string like "GOVERNMENT_TIER_1")
local govIdx = cu:GetCurrentGovernment()
if govIdx >= 0 then
    local govRow = GameInfo.Governments[govIdx]
    if govRow and govRow.Tier then
        local n = tonumber(tostring(govRow.Tier):match("(%d+)$")) or 0
        favorPerTurn = favorPerTurn + math.max(1, n)
    end
end
-- 2. Alliances (level-based, +1 per alliance level)
for i = 0, 62 do
    if i ~= id and Players[i] and Players[i]:IsAlive() and Players[i]:IsMajor() and pDiplo:HasMet(i) then
        local ok, ai = pcall(function() return Players[i]:GetDiplomaticAI() end)
        if ok and ai then
            local ok2, stateIdx = pcall(function() return ai:GetDiplomaticStateIndex(id) end)
            if ok2 and stateIdx then
                local si = tonumber(stateIdx) or -1
                if si == 0 then
                    local ok3, aLvl = pcall(function() return pDiplo:GetAllianceLevel(i) end)
                    favorPerTurn = favorPerTurn + (tonumber(ok3 and aLvl) or 1)
                end
            end
        end
    end
end
-- 3. Suzerainties (+1 each)
for i = 0, 62 do
    if Players[i] and Players[i]:IsAlive() then
        local ok, canRecv = pcall(function() return Players[i]:GetInfluence():CanReceiveInfluence() end)
        if ok and canRecv then
            local suzID = Players[i]:GetInfluence():GetSuzerain()
            if suzID == id then favorPerTurn = favorPerTurn + 1 end
        end
    end
end
print(Game.GetCurrentGameTurn() .. "|" .. id .. "|" .. Locale.Lookup(cfg:GetCivilizationShortDescription()) .. "|" .. Locale.Lookup(cfg:GetLeaderName()) .. "|" .. string.format("%.1f", tr:GetGoldBalance()) .. "|" .. string.format("%.1f", tr:GetGoldYield() - tr:GetTotalMaintenance()) .. "|" .. string.format("%.1f", te:GetScienceYield()) .. "|" .. string.format("%.1f", cu:GetCultureYield()) .. "|" .. string.format("%.1f", re:GetFaithBalance()) .. "|" .. techName .. "|" .. civicName .. "|" .. nCities .. "|" .. nUnits .. "|" .. myScore .. "|" .. favor .. "|" .. favorPerTurn .. "|" .. totalPop)
for i = 0, 62 do
    if i ~= id and Players[i] and Players[i]:IsAlive() and Players[i]:IsMajor() and pDiplo:HasMet(i) then
        local oCfg = PlayerConfigurations[i]
        print("RANK|" .. i .. "|" .. Locale.Lookup(oCfg:GetCivilizationShortDescription()) .. "|" .. Players[i]:GetScore())
    end
end
local pVis = PlayersVisibility[id]
local totalPlots = Map.GetPlotCount()
local revLand, totalLand = 0, 0
for i = 0, totalPlots - 1 do
    local plot = Map.GetPlotByIndex(i)
    if not plot:IsWater() then
        totalLand = totalLand + 1
        if pVis:IsRevealed(plot:GetX(), plot:GetY()) then revLand = revLand + 1 end
    end
end
print("EXPLORE|" .. revLand .. "|" .. totalLand)
local nMajors = 0
local nReligions = 0
for i = 0, 62 do
    if Players[i] and Players[i]:IsMajor() and Players[i]:IsAlive() then
        nMajors = nMajors + 1
        local rType = Players[i]:GetReligion():GetReligionTypeCreated()
        if rType >= 0 then
            nReligions = nReligions + 1
            if i == id or pDiplo:HasMet(i) then
                local rName = "Unknown"
                local rEntry = GameInfo.Religions[rType]
                if rEntry then rName = Locale.Lookup(rEntry.Name) end
                local oCfg = PlayerConfigurations[i]
                local civName = Locale.Lookup(oCfg:GetCivilizationShortDescription())
                print("REL|" .. i .. "|" .. civName .. "|" .. rName)
            end
        end
    end
end
local maxRel = math.floor(nMajors / 2) + 1
print("RELSLOTS|" .. nReligions .. "|" .. maxRel)
local eraManager = Game.GetEras()
local eraIdx = eraManager:GetCurrentEra()
local eraEntry = GameInfo.Eras[eraIdx]
local eraName = eraEntry and Locale.Lookup(eraEntry.Name) or "Unknown"
local eraScore = eraManager:GetPlayerCurrentScore(id)
local darkThresh = eraManager:GetPlayerDarkAgeThreshold(id)
local goldenThresh = eraManager:GetPlayerGoldenAgeThreshold(id)
print("ERA|" .. eraName .. "|" .. eraScore .. "|" .. darkThresh .. "|" .. goldenThresh)
local maxTurns = GameConfiguration.GetValue("GAME_MAX_TURNS") or 0
print("MAXTURNS|" .. maxTurns)
local diffName = "Unknown"
pcall(function()
    local diffHash = PlayerConfigurations[id]:GetHandicapTypeID()
    for d in GameInfo.Difficulties() do
        if GameConfiguration.MakeHash(d.DifficultyType) == diffHash then
            diffName = Locale.Lookup(d.Name)
            break
        end
    end
end)
print("DIFFICULTY|" .. diffName)
print("{SENTINEL}")
"""


def build_gameover_check() -> str:
    """InGame: check if the game is over (EndGameMenu visible).

    TestVictory() is unreliable on the game-over screen (returns false for all
    types because the snapshot may have shifted). Instead we use heuristic
    checks: religious majority, diplo VP >= 20, science VP >= needed, and
    capitals owned for domination.
    """
    return f"""
local egm = ContextPtr:LookUpControl("/InGame/EndGameMenu")
if not egm or egm:IsHidden() then
    print("GAME_ACTIVE")
    print("{SENTINEL}")
    return
end
local me = Game.GetLocalPlayer()
local meAlive = Players[me]:IsAlive()
local winTeam = -1
pcall(function() winTeam = Game.GetWinningTeam() end)
local winnerId = -1
local winnerName = "Unknown"
local winnerLeader = "Unknown"
local victoryType = "Unknown"
if winTeam >= 0 then
    for i = 0, 62 do
        local p = Players[i]
        if p and p:IsMajor() and p:IsAlive() and p:GetTeam() == winTeam then
            winnerId = i
            local cfg = PlayerConfigurations[i]
            winnerName = Locale.Lookup(cfg:GetCivilizationShortDescription())
            winnerLeader = Locale.Lookup(cfg:GetLeaderName())
            break
        end
    end
end
if winnerId >= 0 then
    local wp = Players[winnerId]
    -- Religious: winner's religion is majority in all (or nearly all) major civs
    pcall(function()
        local relCreated = wp:GetReligion():GetReligionTypeCreated()
        if relCreated >= 0 then
            local totalM, convM = 0, 0
            for i = 0, 62 do
                local q = Players[i]
                if q and q:IsMajor() and q:IsAlive() then
                    totalM = totalM + 1
                    if q:GetReligion():GetReligionInMajorityOfCities() == relCreated then convM = convM + 1 end
                end
            end
            if convM >= totalM - 1 then victoryType = "VICTORY_RELIGIOUS" end
        end
    end)
    -- Diplomatic: 20+ diplo VP
    if victoryType == "Unknown" then
        pcall(function()
            local dvp = wp:GetStats():GetDiplomaticVictoryPoints()
            if dvp and dvp >= 20 then victoryType = "VICTORY_DIPLOMATIC" end
        end)
    end
    -- Science: completed space projects
    if victoryType == "Unknown" then
        pcall(function()
            local svp = wp:GetStats():GetScienceVictoryPoints()
            local needed = wp:GetStats():GetScienceVictoryPointsTotalNeeded()
            if svp and needed and svp >= needed then victoryType = "VICTORY_TECHNOLOGY" end
        end)
    end
    -- Domination: owns all original capitals
    if victoryType == "Unknown" then
        pcall(function()
            local caps, owned = 0, 0
            for i = 0, 62 do
                local q = Players[i]
                if q and q:IsMajor() and q:IsAlive() and i ~= winnerId then
                    caps = caps + 1
                    local oCap = q:GetCities():GetOriginalCapital()
                    if oCap and oCap:GetOwner() == winnerId then owned = owned + 1 end
                end
            end
            if caps > 0 and owned >= caps then victoryType = "VICTORY_CONQUEST" end
        end)
    end
end
local isDefeat = winTeam >= 0 and Players[me]:GetTeam() ~= winTeam
local result = isDefeat and "DEFEAT" or "VICTORY"
print("GAME_OVER|" .. result .. "|" .. winnerName .. "|" .. victoryType .. "|" .. (meAlive and "alive" or "dead") .. "|" .. winnerLeader)
print("{SENTINEL}")
"""


def parse_gameover_response(lines: list[str]) -> GameOverStatus | None:
    """Parse game-over check response. Returns None if game is still active."""
    for line in lines:
        if line == "GAME_ACTIVE":
            return None
        if line.startswith("GAME_OVER|"):
            parts = line.split("|")
            return GameOverStatus(
                is_game_over=True,
                is_defeat=parts[1] == "DEFEAT",
                winner_name=parts[2] if len(parts) > 2 else "Unknown",
                winner_leader=parts[5] if len(parts) > 5 else "Unknown",
                victory_type=parts[3] if len(parts) > 3 else "Unknown",
                player_alive=parts[4] == "alive" if len(parts) > 4 else True,
            )
    return None


def parse_overview_response(lines: list[str]) -> GameOverview:
    if not lines:
        raise ValueError("Empty overview response")
    parts = lines[0].split("|")
    if len(parts) < 14:
        raise ValueError(
            f"Overview response has {len(parts)} fields, expected >=14: {lines[0]}"
        )
    rankings: list[ScoreEntry] = []
    explored_land = 0
    total_land = 0
    religions_founded = 0
    religions_max = 0
    our_religion: str | None = None
    founded_religions: list[ReligionInfo] = []
    era_name = ""
    era_score = 0
    era_dark_threshold = 0
    era_golden_threshold = 0
    max_turns = 0
    difficulty = ""
    player_id_parsed = int(parts[1])
    for line in lines[1:]:
        if line.startswith("RANK|"):
            rp = line.split("|")
            if len(rp) >= 4:
                rankings.append(
                    ScoreEntry(
                        player_id=int(rp[1]),
                        civ_name=rp[2],
                        score=int(rp[3]),
                    )
                )
        elif line.startswith("EXPLORE|"):
            ep = line.split("|")
            if len(ep) >= 3:
                explored_land = int(ep[1])
                total_land = int(ep[2])
        elif line.startswith("REL|"):
            rp = line.split("|")
            if len(rp) >= 4:
                ri = ReligionInfo(
                    player_id=int(rp[1]),
                    civ_name=rp[2],
                    religion_name=rp[3],
                )
                founded_religions.append(ri)
                if int(rp[1]) == player_id_parsed:
                    our_religion = rp[3]
        elif line.startswith("RELSLOTS|"):
            rp = line.split("|")
            if len(rp) >= 3:
                religions_founded = int(rp[1])
                religions_max = int(rp[2])
        elif line.startswith("ERA|"):
            ep = line.split("|")
            if len(ep) >= 5:
                era_name = ep[1]
                era_score = int(ep[2])
                era_dark_threshold = int(ep[3])
                era_golden_threshold = int(ep[4])
        elif line.startswith("MAXTURNS|"):
            ep = line.split("|")
            if len(ep) >= 2:
                max_turns = int(ep[1])
        elif line.startswith("DIFFICULTY|"):
            difficulty = line.split("|", 1)[1]
    return GameOverview(
        turn=int(parts[0]),
        player_id=int(parts[1]),
        civ_name=parts[2],
        leader_name=parts[3],
        gold=float(parts[4]),
        gold_per_turn=float(parts[5]),
        science_yield=float(parts[6]),
        culture_yield=float(parts[7]),
        faith=float(parts[8]),
        current_research=parts[9],
        current_civic=parts[10],
        num_cities=int(parts[11]),
        num_units=int(parts[12]),
        score=int(parts[13]) if len(parts) > 13 else 0,
        diplomatic_favor=int(parts[14]) if len(parts) > 14 else 0,
        favor_per_turn=int(float(parts[15])) if len(parts) > 15 else 0,
        total_population=int(parts[16]) if len(parts) > 16 else 0,
        explored_land=explored_land,
        total_land=total_land,
        rankings=rankings if rankings else None,
        religions_founded=religions_founded,
        religions_max=religions_max,
        our_religion=our_religion,
        founded_religions=founded_religions if founded_religions else None,
        era_name=era_name,
        era_score=era_score,
        era_dark_threshold=era_dark_threshold,
        era_golden_threshold=era_golden_threshold,
        max_turns=max_turns,
        difficulty=difficulty,
    )


def build_rival_snapshot_query() -> str:
    """Lightweight per-rival stats for diary power curves. InGame context.

    Output: one RIVAL| line per met major civ (excluding self).
    Format: RIVAL|pid|name|score|cities|pop|sci|cul|gold|mil|techs|civics|faith|sciVP|diploVP|resources
    resources: comma-separated RESOURCE:amount pairs for non-zero stockpiles, e.g. IRON:5,HORSES:2
    """
    return (
        "local me = Game.GetLocalPlayer() "
        "local pDiplo = Players[me]:GetDiplomacy() "
        "for i = 0, 62 do "
        "  if i ~= me and Players[i] and Players[i]:IsMajor() and Players[i]:IsAlive() and pDiplo:HasMet(i) then "
        "    local cfg = PlayerConfigurations[i] "
        "    local name = Locale.Lookup(cfg:GetCivilizationShortDescription()) "
        "    local p = Players[i] "
        "    local score = p:GetScore() "
        "    local nCities, totalPop = 0, 0 "
        "    for _, c in p:GetCities():Members() do nCities = nCities + 1; totalPop = totalPop + c:GetPopulation() end "
        "    local sci = p:GetTechs():GetScienceYield() "
        "    local cul = p:GetCulture():GetCultureYield() "
        "    local gold = p:GetTreasury():GetGoldYield() - p:GetTreasury():GetTotalMaintenance() "
        "    local st = p:GetStats() "
        "    local mil = st:GetMilitaryStrength() "
        "    local techs = st:GetNumTechsResearched() "
        "    local civics = st:GetNumCivicsCompleted() "
        "    local sciVP = st:GetScienceVictoryPoints() "
        "    local diploVP = st:GetDiplomaticVictoryPoints() "
        "    local faith = 0 "
        "    pcall(function() faith = p:GetReligion():GetFaithBalance() end) "
        '    local resStr = "" '
        "    local pRes = p:GetResources() "
        "    for row in GameInfo.Resources() do "
        '      if row.ResourceClassType == "RESOURCECLASS_STRATEGIC" then '
        "        local amt = 0 "
        "        pcall(function() amt = pRes:GetResourceAmount(row.Index) end) "
        "        if amt and amt > 0 then "
        '          local rName = row.ResourceType:gsub("RESOURCE_", "") '
        '          resStr = resStr .. (resStr ~= "" and "," or "") .. rName .. ":" .. amt '
        "        end "
        "      end "
        "    end "
        '    print("RIVAL|" .. i .. "|" .. name .. "|" .. score .. "|" .. nCities .. "|" .. totalPop '
        '      .. "|" .. string.format("%.1f", sci) .. "|" .. string.format("%.1f", cul) '
        '      .. "|" .. string.format("%.1f", gold) .. "|" .. mil .. "|" .. techs .. "|" .. civics '
        '      .. "|" .. string.format("%.1f", faith) .. "|" .. sciVP .. "|" .. diploVP .. "|" .. resStr) '
        "  end "
        "end "
        f'print("{SENTINEL}")'
    )


def parse_rival_snapshot_response(lines: list[str]) -> list[RivalSnapshot]:
    """Parse RIVAL| lines from build_rival_snapshot_query."""
    rivals = []
    for line in lines:
        if not line.startswith("RIVAL|"):
            continue
        p = line.split("|")
        if len(p) < 15:
            continue
        stockpiles = {}
        if len(p) > 15 and p[15]:
            for pair in p[15].split(","):
                if ":" in pair:
                    k, v = pair.split(":", 1)
                    try:
                        stockpiles[k] = int(v)
                    except ValueError:
                        pass
        rivals.append(
            RivalSnapshot(
                id=int(p[1]),
                name=p[2],
                score=int(float(p[3])),
                cities=int(float(p[4])),
                pop=int(float(p[5])),
                sci=round(float(p[6]), 1),
                cul=round(float(p[7]), 1),
                gold=round(float(p[8]), 1),
                mil=int(float(p[9])),
                techs=int(float(p[10])),
                civics=int(float(p[11])),
                faith=round(float(p[12]), 1),
                sci_vp=int(float(p[13])),
                diplo_vp=int(float(p[14])),
                stockpiles=stockpiles,
            )
        )
    return rivals


# ------------------------------------------------------------------
# Diary full snapshot — one row per player per turn + city detail
# ------------------------------------------------------------------


def build_diary_full_query() -> str:
    """Single InGame round-trip: full per-turn snapshot for diary JSONL.

    Emits per-player lines (all alive major civs, omniscient):
        PLAYER|pid|civ|leader|score|cities|pop|sci|cul|gold|goldPT|
              faith|faithPT|favor|favorPT|mil|techsN|civicsN|
              districts|wonders|greatWorks|territory|improvements|
              gov|tourism|stay|relCities|sciVP|diploVP|
              era|eraScore|age|curResearch|curCivic|pantheon|religion|
              explorePct
        PTECHS|pid|TECH1,TECH2,...
        PCIVICS|pid|CIVIC1,CIVIC2,...
        PPOLICIES|pid|POLICY1,POLICY2,...
        PBELIEFS|pid|BELIEF1,BELIEF2,...
        PLUXURIES|pid|TYPE:N,TYPE:N,...
        PSTOCKPILES|pid|TYPE:N,TYPE:N,...
        PUNITS|pid|total|mil|civ|sup|TYPE:N,TYPE:N,...
        PCITY|pid|cityId|name|pop|food|prod|gold|sci|cul|faith|
              housing|am|amNeed|districts|producing|loyalty|loyaltyPT

    Agent-only (local player):
        ADIPLO|rivalName|stateIdx|allianceType|allianceLevel|grievances
        ACS|suzerainties|envoysAvail|name:N,name:N,...
        AGOV|govType|city|established|promo1,promo2,...
        ATRADE|capacity|active|domestic|international
        AGPPTS|className:points,...
        ---END---
    """
    return (
        # --- Setup ---
        "local me = Game.GetLocalPlayer() "
        "local eraManager = Game.GetEras() "
        "local eraIdx = eraManager:GetCurrentEra() "
        "local eraEntry = GameInfo.Eras[eraIdx] "
        'local eraType = eraEntry and eraEntry.EraType or "UNKNOWN" '
        # Pre-compute territory, improvement, and exploration counts per player
        # (single map scan — also counts revealed land tiles per player)
        "local ownerTerritory = {} "
        "local ownerImprove = {} "
        "local ownerRevealed = {} "
        "local totalLand = 0 "
        # Build alive-major player list + visibility handles once
        "local aliveMajors = {} "
        "local aliveVis = {} "
        "for i = 0, 62 do "
        "  if Players[i] and Players[i]:IsMajor() and Players[i]:IsAlive() then "
        "    aliveMajors[#aliveMajors+1] = i "
        "    aliveVis[i] = PlayersVisibility[i] "
        "  end "
        "end "
        "for idx = 0, Map.GetPlotCount() - 1 do "
        "  local plot = Map.GetPlotByIndex(idx) "
        "  local owner = plot:GetOwner() "
        "  if owner >= 0 and owner < 63 then "
        "    ownerTerritory[owner] = (ownerTerritory[owner] or 0) + 1 "
        "    if plot:GetImprovementType() >= 0 then "
        "      ownerImprove[owner] = (ownerImprove[owner] or 0) + 1 "
        "    end "
        "  end "
        "  if not plot:IsWater() then "
        "    totalLand = totalLand + 1 "
        "    local px, py = plot:GetX(), plot:GetY() "
        "    for _, pid in ipairs(aliveMajors) do "
        "      if aliveVis[pid]:IsRevealed(px, py) then "
        "        ownerRevealed[pid] = (ownerRevealed[pid] or 0) + 1 "
        "      end "
        "    end "
        "  end "
        "end "
        # Hash name lookup for production
        "local hashName = {} "
        "for u in GameInfo.Units() do hashName[u.Hash] = u.UnitType end "
        "for b in GameInfo.Buildings() do hashName[b.Hash] = b.BuildingType end "
        "for d in GameInfo.Districts() do hashName[d.Hash] = d.DistrictType end "
        "for pr in GameInfo.Projects() do hashName[pr.Hash] = pr.ProjectType end "
        # === Player loop (omniscient — all alive major civs) ===
        "for i = 0, 62 do "
        "if Players[i] and Players[i]:IsMajor() and Players[i]:IsAlive() then "
        "  local p = Players[i] "
        "  local cfg = PlayerConfigurations[i] "
        "  local civName = Locale.Lookup(cfg:GetCivilizationShortDescription()) "
        "  local leaderName = Locale.Lookup(cfg:GetLeaderName()) "
        # Basic stats
        "  local sScore = p:GetScore() "
        "  local nCities, totalPop = 0, 0 "
        "  for _, c in p:GetCities():Members() do "
        "    nCities = nCities + 1; totalPop = totalPop + c:GetPopulation() "
        "  end "
        "  local sci = p:GetTechs():GetScienceYield() "
        "  local cul = p:GetCulture():GetCultureYield() "
        "  local tr = p:GetTreasury() "
        "  local goldBal = tr:GetGoldBalance() "
        "  local goldPT = tr:GetGoldYield() - tr:GetTotalMaintenance() "
        "  local faithBal = 0 "
        "  pcall(function() faithBal = p:GetReligion():GetFaithBalance() end) "
        "  local faithPT = 0 "
        "  pcall(function() faithPT = p:GetReligion():GetFaithYield() end) "
        "  local favor = 0 "
        "  pcall(function() favor = p:GetFavor() end) "
        "  local favorPT = 0 "
        # Military & victory stats
        "  local st = p:GetStats() "
        "  local mil = st:GetMilitaryStrength() "
        "  local techsN = st:GetNumTechsResearched() "
        "  local civicsN = st:GetNumCivicsCompleted() "
        "  local sciVP = st:GetScienceVictoryPoints() "
        "  local diploVP = st:GetDiplomaticVictoryPoints() "
        "  local tourism = st:GetTourism() "
        "  local relCities = st:GetNumCitiesFollowingReligion() "
        "  local stay = 0 "
        "  pcall(function() stay = p:GetCulture():GetStaycationers() end) "
        # Government
        "  local cu = p:GetCulture() "
        '  local govType = "NONE" '
        "  local govIdx = cu:GetCurrentGovernment() "
        "  if govIdx >= 0 then "
        "    local govRow = GameInfo.Governments[govIdx] "
        '    if govRow then govType = govRow.GovernmentType or "NONE" end '
        "  end "
        # Age (per player)
        '  local age = "NORMAL" '
        "  pcall(function() "
        '    if eraManager:HasHeroicAge(i) then age = "HEROIC" '
        '    elseif eraManager:HasGoldenAge(i) then age = "GOLDEN" '
        '    elseif eraManager:HasDarkAge(i) then age = "DARK" end '
        "  end) "
        # Era score (per player)
        "  local eraScore = 0 "
        "  pcall(function() eraScore = eraManager:GetPlayerCurrentScore(i) end) "
        # Current research/civic (type keys)
        '  local curResearch = "NONE" '
        "  local techIdx = p:GetTechs():GetResearchingTech() "
        "  if techIdx >= 0 then "
        "    local tRow = GameInfo.Technologies[techIdx] "
        "    if tRow then curResearch = tRow.TechnologyType end "
        "  end "
        '  local curCivic = "NONE" '
        "  local civicIdx = cu:GetProgressingCivic() "
        "  if civicIdx >= 0 then "
        "    local cRow = GameInfo.Civics[civicIdx] "
        "    if cRow then curCivic = cRow.CivicType end "
        "  end "
        # Pantheon / Religion (type keys)
        '  local pantheon = "NONE" '
        "  local panIdx = p:GetReligion():GetPantheon() "
        "  if panIdx >= 0 then "
        "    local bRow = GameInfo.Beliefs[panIdx] "
        "    if bRow then pantheon = bRow.BeliefType end "
        "  end "
        '  local religion = "NONE" '
        "  local relType = p:GetReligion():GetReligionTypeCreated() "
        "  if relType >= 0 then "
        "    local rRow = GameInfo.Religions[relType] "
        "    if rRow then religion = rRow.ReligionType end "
        "  end "
        # Infrastructure (iterate cities)
        "  local districtCount, wonderCount, greatWorkCount = 0, 0, 0 "
        "  for _, c in p:GetCities():Members() do "
        "    for _, d in c:GetDistricts():Members() do "
        "      local dInfo = GameInfo.Districts[d:GetType()] "
        '      if dInfo and dInfo.DistrictType ~= "DISTRICT_CITY_CENTER" then '
        "        districtCount = districtCount + 1 "
        "      end "
        "    end "
        "    local blds = c:GetBuildings() "
        "    for bldg in GameInfo.Buildings() do "
        "      if blds:HasBuilding(bldg.Index) then "
        "        if bldg.IsWonder then wonderCount = wonderCount + 1 end "
        "        local nSlots = blds:GetNumGreatWorkSlots(bldg.Index) "
        "        if nSlots and nSlots > 0 then "
        "          for s = 0, nSlots - 1 do "
        "            if blds:GetGreatWorkInSlot(bldg.Index, s) >= 0 then "
        "              greatWorkCount = greatWorkCount + 1 "
        "            end "
        "          end "
        "        end "
        "      end "
        "    end "
        "  end "
        # Territory + improvements from pre-computed map scan
        "  local territory = ownerTerritory[i] or 0 "
        "  local improvementCount = ownerImprove[i] or 0 "
        # Favor per turn (agent only — complex computation)
        "  if i == me then "
        "    local pDiplo = p:GetDiplomacy() "
        # Government tier (Tier is a string like "GOVERNMENT_TIER_1")
        "    if govIdx >= 0 then "
        "      local govRow = GameInfo.Governments[govIdx] "
        "      if govRow and govRow.Tier then "
        "        local n = tonumber(tostring(govRow.Tier):match('(%d+)$')) or 0 "
        "        favorPT = favorPT + math.max(1, n) "
        "      end "
        "    end "
        # Alliances (level-based, +1 per alliance level)
        "    for j = 0, 62 do "
        "      if j ~= i and Players[j] and Players[j]:IsAlive() "
        "        and Players[j]:IsMajor() and pDiplo:HasMet(j) then "
        "        local ok, ai = pcall(function() "
        "          return Players[j]:GetDiplomaticAI() end) "
        "        if ok and ai then "
        "          local ok2, si = pcall(function() "
        "            return ai:GetDiplomaticStateIndex(i) end) "
        "          if ok2 and si then "
        "            si = tonumber(si) or -1 "
        "            if si == 0 then "
        "              local ok3, aLvl = pcall(function() "
        "                return pDiplo:GetAllianceLevel(j) end) "
        "              favorPT = favorPT + (tonumber(ok3 and aLvl) or 1) "
        "            end "
        "          end "
        "        end "
        "      end "
        "    end "
        # Suzerainties (+1 each)
        "    for j = 0, 62 do "
        "      if Players[j] and Players[j]:IsAlive() then "
        "        local ok, canRecv = pcall(function() "
        "          return Players[j]:GetInfluence():CanReceiveInfluence() end) "
        "        if ok and canRecv then "
        "          local suzID = Players[j]:GetInfluence():GetSuzerain() "
        "          if suzID == i then favorPT = favorPT + 1 end "
        "        end "
        "      end "
        "    end "
        "  end "
        # --- PLAYER line ---
        "  local explorePct = totalLand > 0 "
        "    and math.floor(100 * (ownerRevealed[i] or 0) / totalLand) or 0 "
        '  print("PLAYER|" .. i '
        '    .. "|" .. civName .. "|" .. leaderName '
        '    .. "|" .. sScore .. "|" .. nCities .. "|" .. totalPop '
        '    .. "|" .. string.format("%.1f", sci) '
        '    .. "|" .. string.format("%.1f", cul) '
        '    .. "|" .. string.format("%.1f", goldBal) '
        '    .. "|" .. string.format("%.1f", goldPT) '
        '    .. "|" .. string.format("%.1f", faithBal) '
        '    .. "|" .. string.format("%.1f", faithPT) '
        '    .. "|" .. favor .. "|" .. favorPT '
        '    .. "|" .. mil .. "|" .. techsN .. "|" .. civicsN '
        '    .. "|" .. districtCount .. "|" .. wonderCount '
        '    .. "|" .. greatWorkCount '
        '    .. "|" .. territory .. "|" .. improvementCount '
        '    .. "|" .. govType .. "|" .. tourism '
        '    .. "|" .. stay .. "|" .. relCities '
        '    .. "|" .. sciVP .. "|" .. diploVP '
        '    .. "|" .. eraType .. "|" .. eraScore .. "|" .. age '
        '    .. "|" .. curResearch .. "|" .. curCivic '
        '    .. "|" .. pantheon .. "|" .. religion '
        '    .. "|" .. explorePct) '
        # --- PTECHS ---
        '  local techStr = "" '
        "  for row in GameInfo.Technologies() do "
        "    if p:GetTechs():HasTech(row.Index) then "
        '      techStr = techStr .. (techStr ~= "" and "," or "") '
        "        .. row.TechnologyType "
        "    end "
        "  end "
        '  print("PTECHS|" .. i .. "|" .. techStr) '
        # --- PCIVICS ---
        '  local civicStr = "" '
        "  for row in GameInfo.Civics() do "
        "    if cu:HasCivic(row.Index) then "
        '      civicStr = civicStr .. (civicStr ~= "" and "," or "") '
        "        .. row.CivicType "
        "    end "
        "  end "
        '  print("PCIVICS|" .. i .. "|" .. civicStr) '
        # --- PPOLICIES ---
        '  local polStr = "" '
        "  local nPSlots = cu:GetNumPolicySlots() "
        "  if nPSlots and nPSlots > 0 then "
        "    for s = 0, nPSlots - 1 do "
        "      local pIdx = cu:GetSlotPolicy(s) "
        "      if pIdx >= 0 then "
        "        local pRow = GameInfo.Policies[pIdx] "
        "        if pRow then "
        '          polStr = polStr .. (polStr ~= "" and "," or "") '
        "            .. pRow.PolicyType "
        "        end "
        "      end "
        "    end "
        "  end "
        '  print("PPOLICIES|" .. i .. "|" .. polStr) '
        # --- PBELIEFS ---
        '  local beliefStr = "" '
        "  if relType >= 0 then "
        "    for b = 0, 20 do "
        "      local bIdx = -1 "
        "      pcall(function() bIdx = p:GetReligion():GetBelief(b) end) "
        "      if bIdx and bIdx >= 0 then "
        "        local bRow = GameInfo.Beliefs[bIdx] "
        "        if bRow then "
        '          beliefStr = beliefStr .. (beliefStr ~= "" and "," or "") '
        "            .. bRow.BeliefType "
        "        end "
        "      end "
        "    end "
        "  end "
        '  print("PBELIEFS|" .. i .. "|" .. beliefStr) '
        # --- PLUXURIES ---
        '  local luxStr = "" '
        "  local pRes = p:GetResources() "
        "  for row in GameInfo.Resources() do "
        '    if row.ResourceClassType == "RESOURCECLASS_LUXURY" then '
        "      local amt = 0 "
        "      pcall(function() amt = pRes:GetResourceAmount(row.Index) end) "
        "      if amt and amt > 0 then "
        '        local rShort = string.gsub(row.ResourceType, "RESOURCE_", "") '
        '        luxStr = luxStr .. (luxStr ~= "" and "," or "") '
        '          .. rShort .. ":" .. amt '
        "      end "
        "    end "
        "  end "
        '  print("PLUXURIES|" .. i .. "|" .. luxStr) '
        # --- PSTOCKPILES ---
        '  local stockStr = "" '
        "  for row in GameInfo.Resources() do "
        '    if row.ResourceClassType == "RESOURCECLASS_STRATEGIC" then '
        "      local amt = 0 "
        "      pcall(function() amt = pRes:GetResourceAmount(row.Index) end) "
        "      if amt and amt > 0 then "
        '        local rShort = string.gsub(row.ResourceType, "RESOURCE_", "") '
        '        stockStr = stockStr .. (stockStr ~= "" and "," or "") '
        '          .. rShort .. ":" .. amt '
        "      end "
        "    end "
        "  end "
        '  print("PSTOCKPILES|" .. i .. "|" .. stockStr) '
        # --- PUNITS ---
        "  local nTotal, nMil, nCiv, nSup = 0, 0, 0, 0 "
        "  local comp = {} "
        "  for _, u in p:GetUnits():Members() do "
        "    if u:GetX() ~= -9999 then "
        "      local entry = GameInfo.Units[u:GetType()] "
        "      if entry then "
        '        local ut = string.gsub(entry.UnitType or "UNKNOWN", "UNIT_", "") '
        "        comp[ut] = (comp[ut] or 0) + 1 "
        "        nTotal = nTotal + 1 "
        '        local fc = entry.FormationClass or "" '
        '        if fc == "FORMATION_CLASS_LAND_COMBAT" '
        '          or fc == "FORMATION_CLASS_NAVAL" then '
        "          nMil = nMil + 1 "
        '        elseif fc == "FORMATION_CLASS_CIVILIAN" then '
        "          nCiv = nCiv + 1 "
        '        elseif fc == "FORMATION_CLASS_SUPPORT" then '
        "          nSup = nSup + 1 "
        "        else nMil = nMil + 1 end "
        "      end "
        "    end "
        "  end "
        '  local compStr = "" '
        "  for k, v in pairs(comp) do "
        '    compStr = compStr .. (compStr ~= "" and "," or "") '
        '      .. k .. ":" .. v '
        "  end "
        '  print("PUNITS|" .. i .. "|" .. nTotal .. "|" .. nMil '
        '    .. "|" .. nCiv .. "|" .. nSup .. "|" .. compStr) '
        # --- PCITY per city ---
        "  for _, c in p:GetCities():Members() do "
        "    local cID = c:GetID() "
        "    local cName = Locale.Lookup(c:GetName()) "
        "    local cPop = c:GetPopulation() "
        "    local g = c:GetGrowth() "
        # Production
        '    local producing = "NONE" '
        "    pcall(function() "
        "      local bq = c:GetBuildQueue() "
        "      if bq:GetSize() > 0 then "
        "        local h = bq:GetCurrentProductionTypeHash() "
        '        producing = hashName[h] or "UNKNOWN" '
        "      end "
        "    end) "
        # Districts in this city
        '    local dStr = "" '
        "    for _, d in c:GetDistricts():Members() do "
        "      local dInfo = GameInfo.Districts[d:GetType()] "
        "      if dInfo then "
        '        local short = string.gsub(dInfo.DistrictType, "DISTRICT_", "") '
        '        dStr = dStr .. (dStr ~= "" and "," or "") .. short '
        "      end "
        "    end "
        # Loyalty
        "    local loyalty, loyaltyPT = 100.0, 0.0 "
        "    pcall(function() "
        "      local ci = c:GetCulturalIdentity() "
        "      loyalty = ci:GetLoyalty() "
        "      loyaltyPT = ci:GetLoyaltyPerTurn() "
        "    end) "
        # Amenities needed
        "    local amNeed = 0 "
        "    pcall(function() amNeed = g:GetAmenitiesNeeded() end) "
        # Print PCITY
        '    print("PCITY|" .. i .. "|" .. cID '
        '      .. "|" .. cName .. "|" .. cPop '
        '      .. "|" .. string.format("%.1f", c:GetYield(0)) '
        '      .. "|" .. string.format("%.1f", c:GetYield(1)) '
        '      .. "|" .. string.format("%.1f", c:GetYield(2)) '
        '      .. "|" .. string.format("%.1f", c:GetYield(3)) '
        '      .. "|" .. string.format("%.1f", c:GetYield(4)) '
        '      .. "|" .. string.format("%.1f", c:GetYield(5)) '
        '      .. "|" .. string.format("%.1f", g:GetHousing()) '
        '      .. "|" .. g:GetAmenities() .. "|" .. amNeed '
        '      .. "|" .. dStr .. "|" .. producing '
        '      .. "|" .. string.format("%.1f", loyalty) '
        '      .. "|" .. string.format("%.1f", loyaltyPT)) '
        "  end "
        "end "
        "end "
        # === Agent-only section ===
        # Diplomacy per rival (met majors only)
        "local pDiplo = Players[me]:GetDiplomacy() "
        "for i = 0, 62 do "
        "  if i ~= me and Players[i] and Players[i]:IsAlive() "
        "    and Players[i]:IsMajor() and pDiplo:HasMet(i) then "
        "    local cfg = PlayerConfigurations[i] "
        "    local name = Locale.Lookup(cfg:GetCivilizationShortDescription()) "
        "    local stateIdx = -1 "
        "    pcall(function() "
        "      stateIdx = Players[i]:GetDiplomaticAI():GetDiplomaticStateIndex(me) "
        "    end) "
        "    local grievances = 0 "
        "    pcall(function() grievances = pDiplo:GetGrievancesAgainst(i) end) "
        '    local allianceType = "none" '
        "    local allianceLevel = 0 "
        "    if stateIdx == 0 then "
        "      pcall(function() allianceLevel = pDiplo:GetAllianceLevel(i) end) "
        "      pcall(function() "
        "        local aType = pDiplo:GetAllianceType(i) "
        "        if aType and aType >= 0 then "
        "          local aRow = GameInfo.Alliances[aType] "
        "          if aRow then allianceType = aRow.AllianceType end "
        "        end "
        "      end) "
        "    end "
        '    print("ADIPLO|" .. name .. "|" .. stateIdx '
        '      .. "|" .. allianceType .. "|" .. allianceLevel '
        '      .. "|" .. grievances) '
        "  end "
        "end "
        # City-state envoys
        "local suzCount = 0 "
        "local envoysAvail = 0 "
        "pcall(function() "
        "  envoysAvail = Players[me]:GetInfluence():GetTokensToGive() "
        "end) "
        'local envoyStr = "" '
        "for i = 0, 62 do "
        "  if i ~= me and Players[i] and Players[i]:IsAlive() "
        "    and not Players[i]:IsMajor() and not Players[i]:IsBarbarian() then "
        "    local csInf = Players[i]:GetInfluence() "
        "    local envoys = 0 "
        "    pcall(function() envoys = csInf:GetTokensReceived(me) end) "
        "    local suzID = -1 "
        "    pcall(function() suzID = csInf:GetSuzerain() end) "
        "    if suzID == me then suzCount = suzCount + 1 end "
        "    if envoys > 0 then "
        "      local csName = Locale.Lookup("
        "        PlayerConfigurations[i]:GetCivilizationShortDescription()) "
        "      local suffix = (suzID == me) and '*' or '' "
        '      envoyStr = envoyStr .. (envoyStr ~= "" and "," or "") '
        '        .. csName .. suffix .. ":" .. envoys '
        "    end "
        "  end "
        "end "
        'print("ACS|" .. suzCount .. "|" .. envoysAvail .. "|" .. envoyStr) '
        # Governors
        "local pGovs = Players[me]:GetGovernors() "
        "if pGovs then "
        "  for gRow in GameInfo.Governors() do "
        "    local ok, hasGov = pcall(function() "
        "      return pGovs:HasGovernor(gRow.Hash) end) "
        "    if ok and hasGov then "
        "      local gov = pGovs:GetGovernor(gRow.Hash) "
        '      local gType = string.gsub(gRow.GovernorType, "GOVERNOR_", "") '
        '      local cityName = "NONE" '
        "      local established = false "
        "      pcall(function() "
        "        local cObj = gov:GetAssignedCity() "
        "        if cObj then "
        "          cityName = Locale.Lookup(cObj:GetName()) "
        "          established = gov:IsEstablished() "
        "        end "
        "      end) "
        '      local promoStr = "" '
        "      for pRow in GameInfo.GovernorPromotions() do "
        "        pcall(function() "
        "          if gov:HasPromotion(pRow.Hash) then "
        "            local short = string.gsub("
        '              pRow.GovernorPromotionType, "GOVERNOR_PROMOTION_", "") '
        '            promoStr = promoStr .. (promoStr ~= "" and "," or "") '
        "              .. short "
        "          end "
        "        end) "
        "      end "
        '      print("AGOV|" .. gType .. "|" .. cityName '
        '        .. "|" .. tostring(established) .. "|" .. promoStr) '
        "    end "
        "  end "
        "end "
        # Trade routes — must iterate cities, player-level GetOutgoingRoutes() is nil
        "local trCap, trActive, trDom, trIntl = 0, 0, 0, 0 "
        "pcall(function() "
        "  trCap = Players[me]:GetTrade():GetOutgoingRouteCapacity() or 0 "
        "end) "
        "local trSeen = {} "
        "for _, city in Players[me]:GetCities():Members() do "
        "  pcall(function() "
        "    local routes = city:GetTrade():GetOutgoingRoutes() "
        "    if not routes then return end "
        "    for _, r in ipairs(routes) do "
        "      local key = r.TraderUnitID "
        "        .. '_' .. r.DestinationCityPlayer "
        "        .. '_' .. r.DestinationCityID "
        "      if not trSeen[key] then "
        "        trSeen[key] = true "
        "        trActive = trActive + 1 "
        "        if r.DestinationCityPlayer == me then "
        "          trDom = trDom + 1 "
        "        else trIntl = trIntl + 1 end "
        "      end "
        "    end "
        "  end) "
        "end "
        'print("ATRADE|" .. trCap .. "|" .. trActive '
        '  .. "|" .. trDom .. "|" .. trIntl) '
        # Great people points
        'local gpStr = "" '
        "local pGP = Players[me]:GetGreatPeoplePoints() "
        "if pGP then "
        "  for cls in GameInfo.GreatPersonClasses() do "
        "    local pts = 0 "
        "    pcall(function() pts = pGP:GetPointsTotal(cls.Index) end) "
        "    if pts and pts > 0 then "
        "      local cName = Locale.Lookup(cls.Name) "
        '      gpStr = gpStr .. (gpStr ~= "" and "," or "") '
        '        .. cName .. ":" .. pts '
        "    end "
        "  end "
        "end "
        'print("AGPPTS|" .. gpStr) '
        f'print("{SENTINEL}")'
    )


def _parse_kv_pairs(s: str) -> dict[str, int]:
    """Parse 'KEY:N,KEY:N,...' into {KEY: N, ...}."""
    result: dict[str, int] = {}
    if not s:
        return result
    for pair in s.split(","):
        if ":" in pair:
            k, v = pair.split(":", 1)
            try:
                result[k] = int(float(v))
            except ValueError:
                pass
    return result


def parse_diary_full_response(lines: list[str]) -> DiarySnapshot:
    """Parse tagged lines from build_diary_full_query into a DiarySnapshot."""
    players: list[PlayerRow] = []
    cities: list[CityRow] = []
    agent = AgentExtras()
    player_map: dict[int, PlayerRow] = {}

    for line in lines:
        if line.startswith("PLAYER|"):
            p = line.split("|")
            if len(p) < 36:
                continue
            pid = int(p[1])
            row = PlayerRow(
                pid=pid,
                civ=p[2],
                leader=p[3],
                is_agent=False,  # set by server.py based on local player
                score=int(float(p[4])),
                cities=int(float(p[5])),
                pop=int(float(p[6])),
                science=round(float(p[7]), 1),
                culture=round(float(p[8]), 1),
                gold=round(float(p[9]), 1),
                gold_per_turn=round(float(p[10]), 1),
                faith=round(float(p[11]), 1),
                faith_per_turn=round(float(p[12]), 1),
                favor=int(float(p[13])),
                favor_per_turn=int(float(p[14])),
                military=int(float(p[15])),
                techs_completed=int(float(p[16])),
                civics_completed=int(float(p[17])),
                districts=int(float(p[18])),
                wonders=int(float(p[19])),
                great_works=int(float(p[20])),
                territory=int(float(p[21])),
                improvements=int(float(p[22])),
                government=p[23],
                tourism=int(float(p[24])),
                staycationers=int(float(p[25])),
                religion_cities=int(float(p[26])),
                sci_vp=int(float(p[27])),
                diplo_vp=int(float(p[28])),
                era=p[29],
                era_score=int(float(p[30])),
                age=p[31],
                current_research=p[32],
                current_civic=p[33],
                pantheon=p[34],
                religion=p[35],
                exploration_pct=int(float(p[36])) if len(p) > 36 else 0,
            )
            players.append(row)
            player_map[pid] = row

        elif line.startswith("PTECHS|"):
            p = line.split("|", 3)
            if len(p) >= 3:
                pid = int(p[1])
                if pid in player_map:
                    techs = [t for t in p[2].split(",") if t]
                    player_map[pid].techs = techs
                    player_map[pid].techs_completed = len(techs)

        elif line.startswith("PCIVICS|"):
            p = line.split("|", 3)
            if len(p) >= 3:
                pid = int(p[1])
                if pid in player_map:
                    civics = [c for c in p[2].split(",") if c]
                    player_map[pid].civics = civics
                    player_map[pid].civics_completed = len(civics)

        elif line.startswith("PPOLICIES|"):
            p = line.split("|", 3)
            if len(p) >= 3:
                pid = int(p[1])
                if pid in player_map:
                    player_map[pid].policies = [pol for pol in p[2].split(",") if pol]

        elif line.startswith("PBELIEFS|"):
            p = line.split("|", 3)
            if len(p) >= 3:
                pid = int(p[1])
                if pid in player_map:
                    player_map[pid].religion_beliefs = [b for b in p[2].split(",") if b]

        elif line.startswith("PLUXURIES|"):
            p = line.split("|", 3)
            if len(p) >= 3:
                pid = int(p[1])
                if pid in player_map:
                    player_map[pid].luxuries = _parse_kv_pairs(p[2])

        elif line.startswith("PSTOCKPILES|"):
            p = line.split("|", 3)
            if len(p) >= 3:
                pid = int(p[1])
                if pid in player_map:
                    player_map[pid].stockpiles = _parse_kv_pairs(p[2])

        elif line.startswith("PUNITS|"):
            p = line.split("|")
            if len(p) >= 7:
                pid = int(p[1])
                if pid in player_map:
                    player_map[pid].units_total = int(float(p[2]))
                    player_map[pid].units_military = int(float(p[3]))
                    player_map[pid].units_civilian = int(float(p[4]))
                    player_map[pid].units_support = int(float(p[5]))
                    player_map[pid].unit_composition = _parse_kv_pairs(p[6])

        elif line.startswith("PCITY|"):
            p = line.split("|")
            if len(p) >= 18:
                cities.append(
                    CityRow(
                        pid=int(p[1]),
                        city_id=int(p[2]),
                        city=p[3],
                        pop=int(float(p[4])),
                        food=round(float(p[5]), 1),
                        production=round(float(p[6]), 1),
                        gold=round(float(p[7]), 1),
                        science=round(float(p[8]), 1),
                        culture=round(float(p[9]), 1),
                        faith=round(float(p[10]), 1),
                        housing=round(float(p[11]), 1),
                        amenities=int(float(p[12])),
                        amenities_needed=int(float(p[13])),
                        districts=p[14],
                        producing=p[15],
                        loyalty=round(float(p[16]), 1),
                        loyalty_per_turn=round(float(p[17]), 1),
                    )
                )

        # --- Agent-only lines ---
        elif line.startswith("ADIPLO|"):
            p = line.split("|")
            if len(p) >= 6:
                agent.diplo_states[p[1]] = {
                    "state": int(float(p[2])),
                    "alliance": p[3] if p[3] != "none" else None,
                    "alliance_level": int(float(p[4])),
                    "grievances": int(float(p[5])),
                }

        elif line.startswith("ACS|"):
            p = line.split("|")
            if len(p) >= 4:
                agent.suzerainties = int(float(p[1]))
                agent.envoys_available = int(float(p[2]))
                agent.envoys_sent = _parse_kv_pairs(p[3])

        elif line.startswith("AGOV|"):
            p = line.split("|")
            if len(p) >= 5:
                agent.governors.append(
                    {
                        "type": p[1],
                        "city": p[2],
                        "established": p[3] == "true",
                        "promotions": [pr for pr in p[4].split(",") if pr],
                    }
                )

        elif line.startswith("ATRADE|"):
            p = line.split("|")
            if len(p) >= 5:
                agent.trade_capacity = int(float(p[1]))
                agent.trade_active = int(float(p[2]))
                agent.trade_domestic = int(float(p[3]))
                agent.trade_international = int(float(p[4]))

        elif line.startswith("AGPPTS|"):
            agent.gp_points = _parse_kv_pairs(line[7:])

    return DiarySnapshot(players=players, cities=cities, agent=agent)
