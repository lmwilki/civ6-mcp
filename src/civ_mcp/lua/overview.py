"""Overview domain — Lua builders and parsers."""

from __future__ import annotations

from civ_mcp.lua._helpers import SENTINEL
from civ_mcp.lua.models import GameOverStatus, GameOverview, ReligionInfo, RivalSnapshot, ScoreEntry


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
-- GetFavorPerTurn() returns 0 (broken API) — compute manually
local pDiplo = p:GetDiplomacy()
-- 1. Government tier bonus
local govIdx = cu:GetCurrentGovernment()
if govIdx >= 0 then
    local govRow = GameInfo.Governments[govIdx]
    if govRow then
        local ok, tier = pcall(function() return govRow.Tier end)
        if ok and tier then favorPerTurn = favorPerTurn + (tonumber(tier) or 0) end
    end
end
-- 2. Friendships (+1 each) and Alliances (level-based)
for i = 0, 62 do
    if i ~= id and Players[i] and Players[i]:IsAlive() and Players[i]:IsMajor() and pDiplo:HasMet(i) then
        local ok, ai = pcall(function() return Players[i]:GetDiplomaticAI() end)
        if ok and ai then
            local ok2, stateIdx = pcall(function() return ai:GetDiplomaticStateIndex(id) end)
            if ok2 and stateIdx then
                local si = tonumber(stateIdx) or -1
                if si == 1 then favorPerTurn = favorPerTurn + 1 end
                if si == 0 then
                    local ok3, aLvl = pcall(function() return pDiplo:GetAllianceLevel(i) end)
                    favorPerTurn = favorPerTurn + (tonumber(ok3 and aLvl) or 1)
                end
            end
        end
    end
end
-- 3. Suzerainties (+2 each)
for i = 0, 62 do
    if Players[i] and Players[i]:IsAlive() then
        local ok, canRecv = pcall(function() return Players[i]:GetInfluence():CanReceiveInfluence() end)
        if ok and canRecv then
            local suzID = Players[i]:GetInfluence():GetSuzerain()
            if suzID == id then favorPerTurn = favorPerTurn + 2 end
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
local victoryType = "Unknown"
if winTeam >= 0 then
    for i = 0, 62 do
        local p = Players[i]
        if p and p:IsMajor() and p:IsAlive() and p:GetTeam() == winTeam then
            winnerId = i
            local cfg = PlayerConfigurations[i]
            winnerName = Locale.Lookup(cfg:GetCivilizationShortDescription())
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
print("GAME_OVER|" .. result .. "|" .. winnerName .. "|" .. victoryType .. "|" .. (meAlive and "alive" or "dead"))
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
                victory_type=parts[3] if len(parts) > 3 else "Unknown",
                player_alive=parts[4] == "alive" if len(parts) > 4 else True,
            )
    return None


def parse_overview_response(lines: list[str]) -> GameOverview:
    if not lines:
        raise ValueError("Empty overview response")
    parts = lines[0].split("|")
    if len(parts) < 13:
        raise ValueError(f"Overview response has {len(parts)} fields, expected 13: {lines[0]}")
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
    player_id_parsed = int(parts[1])
    for line in lines[1:]:
        if line.startswith("RANK|"):
            rp = line.split("|")
            if len(rp) >= 4:
                rankings.append(ScoreEntry(
                    player_id=int(rp[1]),
                    civ_name=rp[2],
                    score=int(rp[3]),
                ))
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
    )


def build_rival_snapshot_query() -> str:
    """Lightweight per-rival stats for diary power curves. InGame context.

    Output: one RIVAL| line per met major civ (excluding self).
    Format: RIVAL|pid|name|score|cities|pop|sci|cul|gold|mil|techs|civics|faith|sciVP|diploVP
    """
    return (
        'local me = Game.GetLocalPlayer() '
        'local pDiplo = Players[me]:GetDiplomacy() '
        'for i = 0, 62 do '
        '  if i ~= me and Players[i] and Players[i]:IsMajor() and Players[i]:IsAlive() and pDiplo:HasMet(i) then '
        '    local cfg = PlayerConfigurations[i] '
        '    local name = Locale.Lookup(cfg:GetCivilizationShortDescription()) '
        '    local p = Players[i] '
        '    local score = p:GetScore() '
        '    local nCities, totalPop = 0, 0 '
        '    for _, c in p:GetCities():Members() do nCities = nCities + 1; totalPop = totalPop + c:GetPopulation() end '
        '    local sci = p:GetTechs():GetScienceYield() '
        '    local cul = p:GetCulture():GetCultureYield() '
        '    local gold = p:GetTreasury():GetGoldYield() - p:GetTreasury():GetTotalMaintenance() '
        '    local st = p:GetStats() '
        '    local mil = st:GetMilitaryStrength() '
        '    local techs = st:GetNumTechsResearched() '
        '    local civics = st:GetNumCivicsCompleted() '
        '    local sciVP = st:GetScienceVictoryPoints() '
        '    local diploVP = st:GetDiplomaticVictoryPoints() '
        '    local faith = 0 '
        '    pcall(function() faith = p:GetReligion():GetFaithBalance() end) '
        '    print("RIVAL|" .. i .. "|" .. name .. "|" .. score .. "|" .. nCities .. "|" .. totalPop '
        '      .. "|" .. string.format("%.1f", sci) .. "|" .. string.format("%.1f", cul) '
        '      .. "|" .. string.format("%.1f", gold) .. "|" .. mil .. "|" .. techs .. "|" .. civics '
        '      .. "|" .. string.format("%.1f", faith) .. "|" .. sciVP .. "|" .. diploVP) '
        '  end '
        'end '
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
        rivals.append(RivalSnapshot(
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
        ))
    return rivals
