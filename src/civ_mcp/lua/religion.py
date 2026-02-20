"""Religion domain — Lua builders and parsers."""

from __future__ import annotations

from civ_mcp.lua._helpers import SENTINEL, _bail, _bail_lua, _lua_get_unit
from civ_mcp.lua.models import BeliefInfo, CityReligionInfo, PantheonStatus, ReligionBeliefOption, ReligionFoundingStatus, ReligionStatus, ReligionSummary


def build_pantheon_status_query() -> str:
    """Get pantheon status and available beliefs (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pReligion = Players[me]:GetReligion()
local currentPantheon = pReligion:GetPantheon()
local faith = pReligion:GetFaithBalance()
local hasPantheon = currentPantheon >= 0
local beliefName = "None"
local beliefType = "None"
if hasPantheon then
    local entry = GameInfo.Beliefs[currentPantheon]
    if entry then
        beliefType = entry.BeliefType
        beliefName = Locale.Lookup(entry.Name)
    end
end
print("STATUS|" .. (hasPantheon and "1" or "0") .. "|" .. beliefType .. "|" .. beliefName:gsub("|","/") .. "|" .. string.format("%.1f", faith))
if not hasPantheon then
    local taken = {{}}
    for i = 0, 62 do
        if Players[i] and Players[i]:IsAlive() and i ~= me then
            local ok, pan = pcall(function() return Players[i]:GetReligion():GetPantheon() end)
            if ok and pan and pan >= 0 then taken[pan] = true end
        end
    end
    for belief in GameInfo.Beliefs() do
        if belief.BeliefClassType == "BELIEF_CLASS_PANTHEON" and not taken[belief.Index] then
            local name = Locale.Lookup(belief.Name):gsub("|","/")
            local desc = Locale.Lookup(belief.Description):gsub("|","/"):gsub("\\n", " ")
            print("BELIEF|" .. belief.BeliefType .. "|" .. name .. "|" .. desc)
        end
    end
end
print("{SENTINEL}")
"""


def build_choose_pantheon(belief_type: str) -> str:
    """Found a pantheon with the specified belief (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pReligion = Players[me]:GetReligion()
if pReligion:GetPantheon() >= 0 then {_bail("ERR:ALREADY_HAS_PANTHEON|You already have a pantheon")} end
local belief = GameInfo.Beliefs["{belief_type}"]
if belief == nil then {_bail(f"ERR:BELIEF_NOT_FOUND|{belief_type}")} end
local params = {{}}
params[PlayerOperations.PARAM_BELIEF_TYPE] = belief.Hash
UI.RequestPlayerOperation(me, PlayerOperations.FOUND_PANTHEON, params)
print("OK:PANTHEON_FOUNDED|" .. Locale.Lookup(belief.Name))
print("{SENTINEL}")
"""


def build_religion_beliefs_query() -> str:
    """Get religion founding status, available religions, and beliefs by class (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pRel = Players[me]:GetReligion()
local relCreated = pRel:GetReligionTypeCreated()
local faith = pRel:GetFaithBalance()
local pantheon = pRel:GetPantheon()

-- Current religion info
if relCreated >= 0 then
    local rRow = GameInfo.Religions[relCreated]
    if rRow then
        print("MYRELIGION|" .. rRow.ReligionType .. "|" .. Locale.Lookup(rRow.Name))
    end
end
print("STATUS|relCreated=" .. relCreated .. "|pantheon=" .. pantheon .. "|faith=" .. string.format("%.0f", faith))

-- Collect taken beliefs across all players
local takenBeliefs = {{}}
for i = 0, 62 do
    if Players[i] and Players[i]:IsAlive() then
        pcall(function()
            local pr = Players[i]:GetReligion()
            if pr then
                local pan = pr:GetPantheon()
                if pan >= 0 then takenBeliefs[pan] = true end
            end
        end)
    end
end

-- Collect taken religions
local takenReligions = {{}}
for i = 0, 62 do
    if Players[i] and Players[i]:IsAlive() then
        pcall(function()
            local pr = Players[i]:GetReligion()
            if pr then
                local rt = pr:GetReligionTypeCreated()
                if rt >= 0 then takenReligions[rt] = true end
            end
        end)
    end
end

-- Available religions (non-custom, not taken)
for row in GameInfo.Religions() do
    if row.ReligionType ~= "RELIGION_PANTHEON" and not row.ReligionType:find("CUSTOM") and not takenReligions[row.Index] then
        print("RELIGION|" .. row.ReligionType .. "|" .. Locale.Lookup(row.Name))
    end
end

-- Available beliefs by class (excluding pantheon and taken)
local classes = {{"BELIEF_CLASS_FOLLOWER", "BELIEF_CLASS_FOUNDER", "BELIEF_CLASS_ENHANCER", "BELIEF_CLASS_WORSHIP"}}
for _, cls in ipairs(classes) do
    for belief in GameInfo.Beliefs() do
        if belief.BeliefClassType == cls and not takenBeliefs[belief.Index] then
            local name = Locale.Lookup(belief.Name):gsub("|", "/")
            local desc = Locale.Lookup(belief.Description):gsub("|", "/"):gsub("\\n", " ")
            print("BELIEF|" .. cls .. "|" .. belief.BeliefType .. "|" .. name .. "|" .. desc)
        end
    end
end
print("{SENTINEL}")
"""


def parse_religion_beliefs_response(lines: list[str]) -> ReligionFoundingStatus:
    """Parse the output of build_religion_beliefs_query."""
    status = ReligionFoundingStatus(
        has_religion=False, religion_type=None, religion_name=None,
        pantheon_index=-1, faith_balance=0.0,
    )
    for line in lines:
        if line.startswith("MYRELIGION|"):
            parts = line.split("|", 2)
            status.has_religion = True
            status.religion_type = parts[1]
            status.religion_name = parts[2] if len(parts) > 2 else parts[1]
        elif line.startswith("STATUS|"):
            for kv in line[7:].split("|"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    if k == "relCreated":
                        status.has_religion = int(v) >= 0
                    elif k == "pantheon":
                        status.pantheon_index = int(v)
                    elif k == "faith":
                        status.faith_balance = float(v)
        elif line.startswith("RELIGION|"):
            parts = line.split("|", 2)
            if len(parts) >= 3:
                status.available_religions.append((parts[1], parts[2]))
        elif line.startswith("BELIEF|"):
            parts = line.split("|", 4)
            if len(parts) >= 5:
                cls = parts[1]
                opt = ReligionBeliefOption(
                    belief_class=cls,
                    belief_type=parts[2],
                    name=parts[3],
                    description=parts[4],
                )
                status.beliefs_by_class.setdefault(cls, []).append(opt)
    return status


def build_found_religion(religion_type: str, follower_belief: str, founder_belief: str) -> str:
    """Found a religion with chosen name and beliefs (InGame context).

    Requires Great Prophet already activated on Holy Site (UNITOPERATION_FOUND_RELIGION).
    """
    return f"""
local me = Game.GetLocalPlayer()
local pRel = Players[me]:GetReligion()
if pRel:GetReligionTypeCreated() >= 0 then
    {_bail("ERR:ALREADY_FOUNDED|You already have a religion")}
end
local relRow = GameInfo.Religions["{religion_type}"]
if not relRow then {_bail(f"ERR:RELIGION_NOT_FOUND|{religion_type}")} end
local follower = GameInfo.Beliefs["{follower_belief}"]
if not follower then {_bail(f"ERR:BELIEF_NOT_FOUND|{follower_belief}")} end
local founder = GameInfo.Beliefs["{founder_belief}"]
if not founder then {_bail(f"ERR:BELIEF_NOT_FOUND|{founder_belief}")} end

-- Step 1: Found religion with chosen type
local params = {{}}
params[PlayerOperations.PARAM_RELIGION_TYPE] = relRow.Hash
UI.RequestPlayerOperation(me, PlayerOperations.FOUND_RELIGION, params)

-- Step 2: Add follower belief
local p2 = {{}}
p2[PlayerOperations.PARAM_BELIEF_TYPE] = follower.Hash
UI.RequestPlayerOperation(me, PlayerOperations.ADD_BELIEF, p2)

-- Step 3: Add founder belief
local p3 = {{}}
p3[PlayerOperations.PARAM_BELIEF_TYPE] = founder.Hash
UI.RequestPlayerOperation(me, PlayerOperations.ADD_BELIEF, p3)

print("OK:RELIGION_FOUNDED|" .. Locale.Lookup(relRow.Name) .. "|" .. Locale.Lookup(follower.Name) .. "|" .. Locale.Lookup(founder.Name))
print("{SENTINEL}")
"""


def build_spread_religion(unit_index: int) -> str:
    """Spread religion at the current tile (InGame context).

    Works for Missionaries and Apostles. Consumes a spread charge.
    """
    return f"""
{_lua_get_unit(unit_index)}
local ux, uy = unit:GetX(), unit:GetY()
local uInfo = GameInfo.Units[unit:GetType()]
local uName = uInfo and uInfo.UnitType or "UNKNOWN"
local charges = unit:GetSpreadCharges()
if charges <= 0 then
    {_bail('ERR:NO_CHARGES|" .. uName .. " has no spread charges remaining')}
end
if unit:GetMovesRemaining() <= 0 then
    {_bail_lua('"ERR:NO_MOVES|" .. uName .. " has no moves remaining — wait until next turn"')}
end
local opRow = GameInfo.UnitOperations["UNITOPERATION_SPREAD_RELIGION"]
if not opRow then {_bail("ERR:CANNOT_SPREAD|UNITOPERATION_SPREAD_RELIGION not found in GameInfo")} end
local params = {{}}
params[UnitOperationTypes.PARAM_X] = ux
params[UnitOperationTypes.PARAM_Y] = uy
local canStart = UnitManager.CanStartOperation(unit, opRow.Hash, nil, params, true)
if not canStart then
    {_bail('ERR:CANNOT_SPREAD|Cannot spread religion here (" .. ux .. "," .. uy .. "). Must be in or adjacent to a city with a different majority religion.')}
end
UnitManager.RequestOperation(unit, opRow.Hash, params)
local newCharges = unit:GetSpreadCharges()
print("OK:RELIGION_SPREAD|" .. Locale.Lookup(unit:GetName()) .. " spread religion at " .. ux .. "," .. uy .. " (charges remaining: " .. newCharges .. ")")
print("{SENTINEL}")
"""


def parse_pantheon_status_response(lines: list[str]) -> PantheonStatus:
    """Parse STATUS| and BELIEF| lines from build_pantheon_status_query."""
    has_pantheon = False
    current_belief = None
    current_belief_name = None
    faith_balance = 0.0
    beliefs: list[BeliefInfo] = []

    for line in lines:
        if line.startswith("STATUS|"):
            parts = line.split("|")
            if len(parts) >= 5:
                has_pantheon = parts[1] == "1"
                current_belief = parts[2] if parts[2] != "None" else None
                current_belief_name = parts[3] if parts[3] != "None" else None
                faith_balance = float(parts[4])
        elif line.startswith("BELIEF|"):
            parts = line.split("|")
            if len(parts) >= 4:
                beliefs.append(BeliefInfo(
                    belief_type=parts[1],
                    name=parts[2],
                    description=parts[3],
                ))

    return PantheonStatus(
        has_pantheon=has_pantheon,
        current_belief=current_belief,
        current_belief_name=current_belief_name,
        faith_balance=faith_balance,
        available_beliefs=beliefs,
    )


def build_religion_status_query() -> str:
    """InGame: per-city religion status for all visible cities."""
    return f"""
local me = Game.GetLocalPlayer()
local pVis = PlayersVisibility[me]
local pDiplo = Players[me]:GetDiplomacy()
for pid = 0, 62 do
    local p = Players[pid]
    if p and p:IsMajor() and p:IsAlive() then
        if pid == me or pDiplo:HasMet(pid) then
            local cfg = PlayerConfigurations[pid]
            local civName = Locale.Lookup(cfg:GetCivilizationShortDescription())
            for _, c in p:GetCities():Members() do
                local cx, cy = c:GetX(), c:GetY()
                if pid == me or pVis:IsRevealed(cx, cy) then
                    local cityName = Locale.Lookup(c:GetName())
                    local cityRel = c:GetReligion()
                    local majRel = cityRel:GetMajorityReligion()
                    local relName = "none"
                    if majRel >= 0 then
                        local r = GameInfo.Religions[majRel]
                        if r then relName = Locale.Lookup(r.Name) end
                    end
                    local pop = c:GetPopulation()
                    local followers = ""
                    local rels = cityRel:GetReligionsInCity()
                    if rels then
                        local parts = {{}}
                        for _, r in ipairs(rels) do
                            if r.Religion >= 0 then
                                local rn = GameInfo.Religions[r.Religion]
                                local rName = rn and Locale.Lookup(rn.Name) or "Unknown"
                                table.insert(parts, rName .. ":" .. r.Followers)
                            end
                        end
                        followers = table.concat(parts, ",")
                    end
                    print("RCITY|" .. pid .. "|" .. civName .. "|" .. cityName .. "|" .. relName .. "|" .. pop .. "|" .. followers)
                end
            end
        end
    end
end
local relTotals = {{}}
local nMajors = 0
for i = 0, 62 do
    local p = Players[i]
    if p and p:IsMajor() and p:IsAlive() then
        nMajors = nMajors + 1
        local majRel = p:GetReligion():GetReligionInMajorityOfCities()
        if majRel >= 0 then
            local r = GameInfo.Religions[majRel]
            local rName = r and Locale.Lookup(r.Name) or "Unknown"
            relTotals[rName] = (relTotals[rName] or 0) + 1
        end
    end
end
for rName, count in pairs(relTotals) do
    print("RSUMMARY|" .. rName .. "|" .. count .. "|" .. nMajors)
end
print("{SENTINEL}")
"""


def parse_religion_status_response(lines: list[str]) -> ReligionStatus:
    cities: list[CityReligionInfo] = []
    summary: list[ReligionSummary] = []
    for line in lines:
        if line.startswith("RCITY|"):
            parts = line.split("|")
            if len(parts) >= 7:
                followers: dict[str, int] = {}
                if parts[6]:
                    for entry in parts[6].split(","):
                        name, _, count = entry.rpartition(":")
                        if name and count:
                            try:
                                followers[name] = int(count)
                            except ValueError:
                                pass
                cities.append(CityReligionInfo(
                    player_id=int(parts[1]),
                    civ_name=parts[2],
                    city_name=parts[3],
                    majority_religion=parts[4],
                    population=int(parts[5]),
                    followers=followers,
                ))
        elif line.startswith("RSUMMARY|"):
            parts = line.split("|")
            if len(parts) >= 4:
                summary.append(ReligionSummary(
                    religion_name=parts[1],
                    civs_with_majority=int(parts[2]),
                    total_majors=int(parts[3]),
                ))
    return ReligionStatus(cities=cities, summary=summary)
