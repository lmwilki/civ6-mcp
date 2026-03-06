"""World Congress domain — Lua builders and parsers."""

from __future__ import annotations

from civ_mcp.lua._helpers import SENTINEL, _bail
from civ_mcp.lua.models import CongressProposal, CongressResolution, WorldCongressStatus


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
    return """
local me = Game.GetLocalPlayer()
local intro = ContextPtr:LookUpControl("/InGame/WorldCongressIntro")
if intro then intro:SetHide(true) end
local popup = ContextPtr:LookUpControl("/InGame/WorldCongressPopup")
if popup then popup:SetHide(true) end
UI.RequestPlayerOperation(me, PlayerOperations.WORLD_CONGRESS_SUBMIT_TURN, {})
UI.RequestAction(ActionTypes.ACTION_ENDTURN)
print("OK:CONGRESS_SUBMITTED")
print("{SENTINEL}")
""".replace("{SENTINEL}", SENTINEL)


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
    if not ress or #ress == 0 then
        UI.RequestPlayerOperation(me, PlayerOperations.WORLD_CONGRESS_SUBMIT_TURN, {{}})
        __civmcp_wc_votes = nil
        pcall(function() Events.WorldCongressStage1.Remove(__civmcp_wc_handler) end)
        __civmcp_wc_handler = nil
        return
    end

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
