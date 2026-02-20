"""Tech domain — Lua builders and parsers."""

from __future__ import annotations

from civ_mcp.lua._helpers import SENTINEL, _bail
from civ_mcp.lua.models import CivicOption, LockedCivic, TechCivicStatus, TechOption


def build_tech_civics_query() -> str:
    return f"""
local id = Game.GetLocalPlayer()
local te = Players[id]:GetTechs()
local cu = Players[id]:GetCulture()
local techIdx = te:GetResearchingTech()
local civicIdx = cu:GetProgressingCivic()
local techName = "None"
local techTurns = -1
if techIdx >= 0 then
    techName = Locale.Lookup(GameInfo.Technologies[techIdx].Name)
    techTurns = te:GetTurnsToResearch(techIdx)
end
local civicName = "None"
local civicTurns = -1
if civicIdx >= 0 then
    civicName = Locale.Lookup(GameInfo.Civics[civicIdx].Name)
    civicTurns = cu:GetTurnsLeftOnCurrentCivic()
end
print("CURRENT|" .. techName .. "|" .. techTurns .. "|" .. civicName .. "|" .. civicTurns)
-- Build boost lookup
local boostsByTech = {{}}
local boostsByCivic = {{}}
for b in GameInfo.Boosts() do
    if b.TechnologyType then boostsByTech[b.TechnologyType] = b end
    if b.CivicType then boostsByCivic[b.CivicType] = b end
end
for tech in GameInfo.Technologies() do
    if te:CanResearch(tech.Index) and not te:HasTech(tech.Index) then
        local cost = te:GetResearchCost(tech.Index)
        local progress = te:GetResearchProgress(tech.Index)
        local turns = te:GetTurnsToResearch(tech.Index)
        local pct = cost > 0 and math.floor(progress * 100 / cost) or 0
        local boosted = te:HasBoostBeenTriggered(tech.Index)
        local boostDesc = ""
        local b = boostsByTech[tech.TechnologyType]
        if b and b.TriggerDescription then
            boostDesc = Locale.Lookup(b.TriggerDescription):gsub("|", "/")
        end
        local unlocks = {{}}
        for u in GameInfo.Units() do if u.PrereqTech == tech.TechnologyType then table.insert(unlocks, Locale.Lookup(u.Name)) end end
        for bld in GameInfo.Buildings() do if bld.PrereqTech == tech.TechnologyType then table.insert(unlocks, Locale.Lookup(bld.Name)) end end
        for d in GameInfo.Districts() do if d.PrereqTech == tech.TechnologyType then table.insert(unlocks, Locale.Lookup(d.Name)) end end
        for imp in GameInfo.Improvements() do if imp.PrereqTech == tech.TechnologyType then table.insert(unlocks, Locale.Lookup(imp.Name)) end end
        for r in GameInfo.Resources() do
            if r.PrereqTech == tech.TechnologyType then table.insert(unlocks, "Reveals " .. Locale.Lookup(r.Name)) end
        end
        local unlockStr = table.concat(unlocks, ", "):gsub("|", "/")
        local boostTag = boosted and "BOOSTED" or "UNBOOSTED"
        print("TECH|" .. Locale.Lookup(tech.Name) .. "|" .. tech.TechnologyType .. "|" .. cost .. "|" .. pct .. "|" .. turns .. "|" .. boostTag .. "|" .. boostDesc .. "|" .. unlockStr)
    end
end
local completedTechs = 0
for tech in GameInfo.Technologies() do
    if te:HasTech(tech.Index) then completedTechs = completedTechs + 1 end
end
local completedCivics = 0
for civic in GameInfo.Civics() do
    if cu:HasCivic(civic.Index) then completedCivics = completedCivics + 1 end
end
print("COMPLETED|" .. completedTechs .. "|" .. completedCivics)
local curEra = Game.GetEras():GetCurrentEra()
local prereqs = {{}}
for row in GameInfo.CivicPrereqs() do
    if not prereqs[row.Civic] then prereqs[row.Civic] = {{}} end
    table.insert(prereqs[row.Civic], row.PrereqCivic)
end
local eraLookup = {{}}
for e in GameInfo.Eras() do eraLookup[e.EraType] = e.Index end
for civic in GameInfo.Civics() do
    if not cu:HasCivic(civic.Index) then
        local civicEra = eraLookup[civic.EraType] or 99
        if civicEra <= curEra + 2 then
            local canProgress = true
            if prereqs[civic.CivicType] then
                for _, pType in ipairs(prereqs[civic.CivicType]) do
                    local pEntry = GameInfo.Civics[pType]
                    if pEntry and not cu:HasCivic(pEntry.Index) then canProgress = false; break end
                end
            end
            if canProgress then
                local cost = cu:GetCultureCost(civic.Index)
                -- GameCore has no GetCulturalProgress/GetTurnsLeft per civic
                -- Estimate turns from cost and culture yield
                local cultureYield = Players[id]:GetCulture():GetCultureYield() or 1
                local turns2 = cultureYield > 0 and math.ceil(cost / cultureYield) or -1
                local boosted2 = cu:HasBoostBeenTriggered(civic.Index)
                local boostDesc2 = ""
                local b2 = boostsByCivic[civic.CivicType]
                if b2 and b2.TriggerDescription then
                    boostDesc2 = Locale.Lookup(b2.TriggerDescription):gsub("|", "/")
                end
                local boostTag2 = boosted2 and "BOOSTED" or "UNBOOSTED"
                print("CIVIC|" .. Locale.Lookup(civic.Name) .. "|" .. civic.CivicType .. "|" .. cost .. "|0|" .. turns2 .. "|" .. boostTag2 .. "|" .. boostDesc2)
            end
        end
    end
end
-- Locked civics: within era+1, have unmet prerequisites
for civic in GameInfo.Civics() do
    if not cu:HasCivic(civic.Index) then
        local civicEra = eraLookup[civic.EraType] or 99
        if civicEra <= curEra + 1 then
            local missing = {{}}
            if prereqs[civic.CivicType] then
                for _, pType in ipairs(prereqs[civic.CivicType]) do
                    local pEntry = GameInfo.Civics[pType]
                    if pEntry and not cu:HasCivic(pEntry.Index) then
                        table.insert(missing, (Locale.Lookup(pEntry.Name):gsub("|", "/")))
                    end
                end
            end
            if #missing > 0 then
                print("LOCKED_CIVIC|" .. Locale.Lookup(civic.Name):gsub("|", "/") .. "|" .. civic.CivicType .. "|" .. table.concat(missing, ","))
            end
        end
    end
end
print("{SENTINEL}")
"""


def build_set_research(tech_name: str) -> str:
    return f"""
local id = Game.GetLocalPlayer()
local idx = nil
for row in GameInfo.Technologies() do
    if row.TechnologyType == "{tech_name}" then idx = row.Index; break end
end
if idx == nil then {_bail(f"ERR:TECH_NOT_FOUND|{tech_name}")} end
local params = {{}}
params[PlayerOperations.PARAM_TECH_TYPE] = idx
UI.RequestPlayerOperation(id, PlayerOperations.RESEARCH, params)
local list = NotificationManager.GetList(id)
if list then
    for _, nid in ipairs(list) do
        local e = NotificationManager.Find(id, nid)
        if e and not e:IsDismissed() then
            local bt = e:GetEndTurnBlocking()
            if bt and bt == EndTurnBlockingTypes.ENDTURN_BLOCKING_RESEARCH then
                pcall(function() NotificationManager.SendActivated(id, nid) end)
                pcall(function() NotificationManager.Dismiss(id, nid) end)
            end
        end
    end
end
print("OK:RESEARCHING|{tech_name}")
print("{SENTINEL}")
"""


def build_set_civic(civic_name: str) -> str:
    return f"""
local id = Game.GetLocalPlayer()
local idx = nil
for row in GameInfo.Civics() do
    if row.CivicType == "{civic_name}" then idx = row.Index; break end
end
if idx == nil then {_bail(f"ERR:CIVIC_NOT_FOUND|{civic_name}")} end
local params = {{}}
params[PlayerOperations.PARAM_CIVIC_TYPE] = idx
UI.RequestPlayerOperation(id, PlayerOperations.PROGRESS_CIVIC, params)
local list = NotificationManager.GetList(id)
if list then
    for _, nid in ipairs(list) do
        local e = NotificationManager.Find(id, nid)
        if e and not e:IsDismissed() then
            local bt = e:GetEndTurnBlocking()
            if bt and bt == EndTurnBlockingTypes.ENDTURN_BLOCKING_CIVIC then
                pcall(function() NotificationManager.SendActivated(id, nid) end)
                pcall(function() NotificationManager.Dismiss(id, nid) end)
            end
        end
    end
end
print("OK:PROGRESSING|{civic_name}")
print("{SENTINEL}")
"""


def build_set_research_gamecore(tech_name: str) -> str:
    """Set tech via GameCore — fallback when InGame RequestPlayerOperation silently fails."""
    return f"""
local id = Game.GetLocalPlayer()
local idx = nil
for row in GameInfo.Technologies() do
    if row.TechnologyType == "{tech_name}" then idx = row.Index; break end
end
if idx == nil then {_bail(f"ERR:TECH_NOT_FOUND|{tech_name}")} end
Players[id]:GetTechs():SetResearchingTech(idx)
local now = Players[id]:GetTechs():GetResearchingTech()
if now == idx then
    print("OK:RESEARCHING_GAMECORE|{tech_name}")
else
    {_bail(f"ERR:RESEARCH_FAILED|GameCore also failed to set {tech_name}")}
end
print("{SENTINEL}")
"""


def build_set_civic_gamecore(civic_name: str) -> str:
    """Set civic via GameCore — fallback when InGame RequestPlayerOperation silently fails."""
    return f"""
local id = Game.GetLocalPlayer()
local idx = nil
for row in GameInfo.Civics() do
    if row.CivicType == "{civic_name}" then idx = row.Index; break end
end
if idx == nil then {_bail(f"ERR:CIVIC_NOT_FOUND|{civic_name}")} end
Players[id]:GetCulture():SetProgressingCivic(idx)
print("OK:PROGRESSING_GC|{civic_name}")
print("{SENTINEL}")
"""


def parse_tech_civics_response(lines: list[str]) -> TechCivicStatus:
    current_research = "None"
    current_research_turns = -1
    current_civic = "None"
    current_civic_turns = -1
    available_techs: list[TechOption] = []
    available_civics: list[CivicOption] = []
    completed_tech_count = 0
    completed_civic_count = 0

    locked_civics: list[LockedCivic] = []

    for line in lines:
        if line.startswith("COMPLETED|"):
            parts = line.split("|")
            completed_tech_count = int(parts[1]) if len(parts) > 1 else 0
            completed_civic_count = int(parts[2]) if len(parts) > 2 else 0
        elif line.startswith("CURRENT|"):
            parts = line.split("|")
            current_research = parts[1]
            current_research_turns = int(parts[2])
            current_civic = parts[3]
            current_civic_turns = int(parts[4])
        elif line.startswith("TECH|"):
            parts = line.split("|")
            if len(parts) >= 9:
                available_techs.append(TechOption(
                    name=parts[1],
                    tech_type=parts[2],
                    cost=int(parts[3]),
                    progress_pct=int(parts[4]),
                    turns=int(parts[5]),
                    boosted=parts[6] == "BOOSTED",
                    boost_desc=parts[7],
                    unlocks=parts[8],
                ))
            elif len(parts) >= 3:
                available_techs.append(TechOption(
                    name=parts[1], tech_type=parts[2],
                    cost=0, progress_pct=0, turns=0,
                    boosted=False, boost_desc="", unlocks="",
                ))
        elif line.startswith("CIVIC|"):
            parts = line.split("|")
            if len(parts) >= 8:
                available_civics.append(CivicOption(
                    name=parts[1],
                    civic_type=parts[2],
                    cost=int(parts[3]),
                    progress_pct=int(parts[4]),
                    turns=int(parts[5]),
                    boosted=parts[6] == "BOOSTED",
                    boost_desc=parts[7],
                ))
            elif len(parts) >= 3:
                available_civics.append(CivicOption(
                    name=parts[1], civic_type=parts[2],
                    cost=0, progress_pct=0, turns=0,
                    boosted=False, boost_desc="",
                ))
        elif line.startswith("LOCKED_CIVIC|"):
            parts = line.split("|")
            if len(parts) >= 4:
                locked_civics.append(LockedCivic(
                    name=parts[1],
                    civic_type=parts[2],
                    missing_prereqs=parts[3].split(","),
                ))

    return TechCivicStatus(
        current_research=current_research,
        current_research_turns=current_research_turns,
        current_civic=current_civic,
        current_civic_turns=current_civic_turns,
        available_techs=available_techs,
        available_civics=available_civics,
        completed_tech_count=completed_tech_count,
        completed_civic_count=completed_civic_count,
        locked_civics=locked_civics or None,
    )
