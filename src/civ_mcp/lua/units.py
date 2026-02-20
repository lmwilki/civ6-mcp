"""Units domain — Lua builders and parsers."""

from __future__ import annotations

from civ_mcp.lua._helpers import SENTINEL, _bail, _bail_lua, _lua_get_unit, _lua_get_unit_gamecore
from civ_mcp.lua.models import CombatEstimate, ThreatInfo, UnitInfo


def build_units_query() -> str:
    """InGame context: lists all units with upgrade and builder improvement info."""
    return f"""
local id = Game.GetLocalPlayer()
for i, u in Players[id]:GetUnits():Members() do
    local x, y = u:GetX(), u:GetY()
    if x ~= -9999 then
        local uid = u:GetID()
        local entry = GameInfo.Units[u:GetType()]
        local ut = entry and entry.UnitType or "UNKNOWN"
        local nm = Locale.Lookup(u:GetName())
        local cs = entry and entry.Combat or 0
        local rs = entry and entry.RangedCombat or 0
        local charges = u:GetBuildCharges() or 0
        local gp = u:GetGreatPerson()
        if gp then
            local ok_gp, gp_charges = pcall(function() return gp:GetActionCharges() end)
            if ok_gp and gp_charges and gp_charges > 0 then charges = gp_charges end
        end
        if charges == 0 then
            local ok_sp, sp = pcall(function() return u:GetSpreadCharges() end)
            if ok_sp and sp and sp > 0 then charges = sp end
        end
        local relName = ""
        local ok_r, rIdx = pcall(function() return u:GetReligionType() end)
        if ok_r and rIdx and rIdx >= 0 then
            for row in GameInfo.Religions() do
                if row.Index == rIdx then relName = row.ReligionType; break end
            end
        end
        -- Scan for attackable enemies if unit has moves
        local targets = ""
        if u:GetMovesRemaining() > 0 and (cs > 0 or rs > 0) then
            local rng = (rs > 0) and (entry and entry.Range or 1) or 1
            local tgtList = {{}}
            for dy = -rng, rng do
                for dx = -rng, rng do
                    local tx, ty = x + dx, y + dy
                    local d = Map.GetPlotDistance(x, y, tx, ty)
                    if d >= 1 and d <= rng then
                        local plotUnits = Map.GetUnitsAt(tx, ty)
                        if plotUnits then
                            for other in plotUnits:Units() do
                                local otherOwner = other:GetOwner()
                                if otherOwner ~= id and (otherOwner == 63 or Players[id]:GetDiplomacy():IsAtWarWith(otherOwner)) then
                                    local eInfo = GameInfo.Units[other:GetType()]
                                    local eName = eInfo and eInfo.UnitType or "UNKNOWN"
                                    local eHP = other:GetMaxDamage() - other:GetDamage()
                                    table.insert(tgtList, eName .. "@" .. tx .. "," .. ty .. "(" .. eHP .. "hp)")
                                end
                            end
                        end
                    end
                end
            end
            if #tgtList > 0 then targets = table.concat(tgtList, ";") end
        end
        local promo = "0"
        local exp = u:GetExperience()
        if exp then
            local xp = exp:GetExperiencePoints()
            local threshold = exp:GetExperienceForNextLevel()
            if xp >= threshold then
                local promoCount = 0
                local ok_p, promoList = pcall(function() return exp:GetPromotions() end)
                if ok_p and promoList then promoCount = #promoList end
                local lvl = 1
                local ok_l, l = pcall(function() return exp:GetLevel() end)
                if ok_l and l then lvl = l end
                if promoCount < lvl then promo = "1" end
            end
        end
        -- Upgrade info (InGame only: CanStartCommand)
        local canUp, upName, upCost = "0", "", "0"
        local ok1, _ = pcall(function()
            if UnitManager.CanStartCommand(u, UnitCommandTypes.UPGRADE, nil, true) then
                canUp = "1"
                local c2 = u:GetUpgradeCost()
                if c2 then upCost = tostring(c2) end
                if entry and entry.UpgradeUnitCollection then
                    for _, row in ipairs(entry.UpgradeUnitCollection) do
                        if row.UpgradeUnit then upName = row.UpgradeUnit end
                        break
                    end
                end
            end
        end)
        -- Builder improvement advisor (InGame only: CanStartOperation)
        local validImps = ""
        if ut == "UNIT_BUILDER" and u:GetMovesRemaining() > 0 then
            local plot = Map.GetPlot(x, y)
            if plot and plot:GetOwner() == id then
                local impList = {{}}
                for imp in GameInfo.Improvements() do
                    if imp.Buildable and not imp.TraitType then
                        local bParams = {{}}
                        bParams[UnitOperationTypes.PARAM_X] = x
                        bParams[UnitOperationTypes.PARAM_Y] = y
                        bParams[UnitOperationTypes.PARAM_IMPROVEMENT_TYPE] = imp.Hash
                        local ok2, _ = pcall(function()
                            if UnitManager.CanStartOperation(u, UnitOperationTypes.BUILD_IMPROVEMENT, nil, bParams) then
                                table.insert(impList, imp.ImprovementType)
                            end
                        end)
                    end
                end
                if #impList > 0 then validImps = table.concat(impList, ";") end
            end
        end
        print(uid .. "|" .. (uid % 65536) .. "|" .. nm .. "|" .. ut .. "|" .. x .. "," .. y .. "|" .. u:GetMovesRemaining() .. "/" .. u:GetMaxMoves() .. "|" .. (u:GetMaxDamage() - u:GetDamage()) .. "/" .. u:GetMaxDamage() .. "|" .. cs .. "|" .. rs .. "|" .. charges .. "|" .. targets .. "|" .. promo .. "|" .. canUp .. "|" .. upName .. "|" .. upCost .. "|" .. validImps .. "|" .. relName)
    end
end
print("{SENTINEL}")
"""


def build_move_unit(unit_index: int, target_x: int, target_y: int) -> str:
    return f"""
{_lua_get_unit(unit_index)}
if not UnitManager.CanStartOperation(unit, UnitOperationTypes.MOVE_TO, nil, true) then
    {_bail("ERR:CANNOT_MOVE|Unit cannot move (no movement points or invalid state)")}
end
-- Pre-check: stacking conflict at target tile
local unitInfo = GameInfo.Units[unit:GetType()]
local isCivilian = (unitInfo and unitInfo.FormationClass == "FORMATION_CLASS_CIVILIAN")
local tgtUnits = Map.GetUnitsAt({target_x}, {target_y})
if tgtUnits then
    for other in tgtUnits:Units() do
        if other:GetOwner() == me then
            local otherInfo = GameInfo.Units[other:GetType()]
            local otherCivilian = (otherInfo and otherInfo.FormationClass == "FORMATION_CLASS_CIVILIAN")
            if isCivilian == otherCivilian then
                local otherName = otherInfo and otherInfo.UnitType or "unit"
                {_bail_lua(f'"ERR:STACKING_CONFLICT|Friendly " .. otherName .. " already on ({target_x},{target_y}). Cannot stack same formation class."')}
            end
        end
    end
end
local fromX, fromY = unit:GetX(), unit:GetY()
local params = {{}}
params[UnitOperationTypes.PARAM_X] = {target_x}
params[UnitOperationTypes.PARAM_Y] = {target_y}
-- Add ATTACK modifier if hostile unit on target tile (needed for civilian capture)
local hasHostile = false
if tgtUnits then
    for other in tgtUnits:Units() do
        if other:GetOwner() ~= me then hasHostile = true end
    end
end
if hasHostile then
    params[UnitOperationTypes.PARAM_MODIFIERS] = UnitOperationMoveModifiers.ATTACK
end
UnitManager.RequestOperation(unit, UnitOperationTypes.MOVE_TO, params)
local tag = hasHostile and "OK:CAPTURE_MOVE|" or "OK:MOVING_TO|"
print(tag .. {target_x} .. "," .. {target_y} .. "|from:" .. fromX .. "," .. fromY)
print("{SENTINEL}")
"""


def build_unit_position_query(unit_index: int) -> str:
    """GameCore: read a unit's current position."""
    return f"""
local u = Players[Game.GetLocalPlayer()]:GetUnits():FindID({unit_index})
if u then print("POS|" .. u:GetX() .. "|" .. u:GetY()) else print("POS|GONE") end
print("{SENTINEL}")
"""


def build_attack_unit(unit_index: int, target_x: int, target_y: int) -> str:
    return f"""
{_lua_get_unit(unit_index)}
local ux, uy = unit:GetX(), unit:GetY()
local dist = Map.GetPlotDistance(ux, uy, {target_x}, {target_y})
-- Find hostile unit on target tile (prefer military over civilian)
local enemy = nil
local enemyName = "unknown"
local tgtUnits = Map.GetUnitsAt({target_x}, {target_y})
if tgtUnits then
    local fallback = nil
    local fallbackName = "unknown"
    for other in tgtUnits:Units() do
        if other:GetOwner() ~= me then
            local eInfo = GameInfo.Units[other:GetType()]
            local eName = eInfo and eInfo.UnitType or "UNKNOWN"
            local eCombat = eInfo and eInfo.Combat or 0
            if eCombat > 0 then
                enemy = other
                enemyName = eName
                break
            elseif fallback == nil then
                fallback = other
                fallbackName = eName
            end
        end
    end
    if enemy == nil and fallback then enemy = fallback; enemyName = fallbackName end
end
if enemy == nil then
    {_bail(f"ERR:NO_ENEMY|No hostile unit at ({target_x},{target_y})")}
end
local enemyHP = enemy:GetMaxDamage() - enemy:GetDamage()
local enemyMaxHP = enemy:GetMaxDamage()
local myHP = unit:GetMaxDamage() - unit:GetDamage()
local params = {{}}
params[UnitOperationTypes.PARAM_X] = {target_x}
params[UnitOperationTypes.PARAM_Y] = {target_y}
-- Determine attack type
local unitInfo = GameInfo.Units[unit:GetType()]
local isRanged = UnitManager.CanStartOperation(unit, UnitOperationTypes.RANGE_ATTACK, nil, true)
if isRanged then
    local rng = unitInfo and unitInfo.Range or 1
    if dist > rng then
        {_bail_lua('"ERR:OUT_OF_RANGE|Target at distance " .. dist .. " but range is " .. rng .. ". Move closer first."')}
    end
    -- LOS check: CanStartOperation with target params is authoritative;
    -- GetOperationTargets returns empty for some valid targets (naval units, etc.)
    local losParams = {{}}
    losParams[UnitOperationTypes.PARAM_X] = {target_x}
    losParams[UnitOperationTypes.PARAM_Y] = {target_y}
    if not UnitManager.CanStartOperation(unit, UnitOperationTypes.RANGE_ATTACK, nil, losParams) then
        {_bail_lua(f'"ERR:NO_LOS|Cannot attack target at ({target_x},{target_y}) from (" .. ux .. "," .. uy .. "). Check line of sight or target validity."')}
    end
    UnitManager.RequestOperation(unit, UnitOperationTypes.RANGE_ATTACK, params)
    print("OK:RANGE_ATTACK|target:" .. enemyName .. " at ({target_x},{target_y})|pre_hp:" .. enemyHP .. "/" .. enemyMaxHP .. "|your HP:" .. myHP .. "|range:" .. rng .. " dist:" .. dist)
else
    -- Melee: must be adjacent (dist == 1)
    if dist > 1 then
        {_bail_lua('"ERR:NOT_ADJACENT|Melee attack needs adjacency (dist=1) but target is " .. dist .. " tiles away. Move adjacent first, then attack."')}
    end
    local myCS = unitInfo and unitInfo.Combat or 0
    params[UnitOperationTypes.PARAM_MODIFIERS] = UnitOperationMoveModifiers.ATTACK
    if not UnitManager.CanStartOperation(unit, UnitOperationTypes.MOVE_TO, nil, params) then
        {_bail_lua(f'"ERR:ATTACK_BLOCKED|Cannot attack " .. enemyName .. " at ({target_x},{target_y}). Check for popups or diplomacy blocking operations."')}
    end
    UnitManager.RequestOperation(unit, UnitOperationTypes.MOVE_TO, params)
    -- Try to read post-combat state (may fail if units moved/died)
    local myAfterHP = myHP
    local ok1, _ = pcall(function() myAfterHP = unit:GetMaxDamage() - unit:GetDamage() end)
    local enemyAfterHP = 0
    local enemyAlive = false
    local ok2, _ = pcall(function()
        local d = enemy:GetDamage()
        if d ~= nil then enemyAfterHP = enemy:GetMaxDamage() - d; enemyAlive = true end
    end)
    local report = "OK:MELEE_ATTACK|target:" .. enemyName .. " at ({target_x},{target_y})"
    if enemyAlive then
        report = report .. "|enemy HP:" .. enemyHP .. " -> " .. enemyAfterHP .. "/" .. enemyMaxHP
    else
        report = report .. "|enemy HP:" .. enemyHP .. " -> KILLED"
    end
    report = report .. "|your HP:" .. myHP .. " -> " .. myAfterHP .. " CS:" .. myCS
    print(report)
end
print("{SENTINEL}")
"""


def build_attack_followup_query(target_x: int, target_y: int) -> str:
    """GameCore read: get actual HP of units at target tile after combat."""
    return f"""
local found = false
for i = 0, 63 do
    if Players[i] and Players[i]:IsAlive() then
        for _, u in Players[i]:GetUnits():Members() do
            if u:GetX() == {target_x} and u:GetY() == {target_y} then
                local hp = u:GetMaxDamage() - u:GetDamage()
                local entry = GameInfo.Units[u:GetType()]
                local name = entry and entry.UnitType or "UNKNOWN"
                print("UNIT|" .. name .. "|" .. hp .. "/" .. u:GetMaxDamage() .. "|owner:" .. i)
                found = true
            end
        end
    end
end
if not found then print("EMPTY") end
print("{SENTINEL}")
"""


def build_combat_estimate_query(unit_index: int, target_x: int, target_y: int) -> str:
    """InGame context: gather combat stats for damage estimation (no attack executed)."""
    return f"""
{_lua_get_unit(unit_index)}
local ux, uy = unit:GetX(), unit:GetY()
local dist = Map.GetPlotDistance(ux, uy, {target_x}, {target_y})
local unitInfo = GameInfo.Units[unit:GetType()]
local attType = unitInfo and unitInfo.UnitType or "UNKNOWN"
local attCS = unitInfo and unitInfo.Combat or 0
local attRS = unitInfo and unitInfo.RangedCombat or 0
local isRanged = attRS > 0 and dist > 1
local effAttCS = isRanged and attRS or attCS
-- Find defender
local enemy = nil
local tgtUnits = Map.GetUnitsAt({target_x}, {target_y})
if tgtUnits then
    for other in tgtUnits:Units() do
        if other:GetOwner() ~= me then
            local eInfo = GameInfo.Units[other:GetType()]
            local eCombat = eInfo and eInfo.Combat or 0
            if eCombat > 0 or enemy == nil then enemy = other end
            if eCombat > 0 then break end
        end
    end
end
if enemy == nil then {_bail(f"ERR:NO_ENEMY|No hostile unit at ({target_x},{target_y})")} end
local eInfo = GameInfo.Units[enemy:GetType()]
local defType = eInfo and eInfo.UnitType or "UNKNOWN"
local defCS = eInfo and eInfo.Combat or 0
local enemyHP = enemy:GetMaxDamage() - enemy:GetDamage()
local myHP = unit:GetMaxDamage() - unit:GetDamage()
-- Gather modifiers
local mods = {{}}
local modTotal = 0
-- Defender fortified?
local ok1, ft = pcall(function() return enemy:GetFortifyTurns() end)
if ok1 and ft and ft > 0 then
    local bonus = math.min(ft * 3, 6)
    table.insert(mods, "fortified +" .. bonus)
    modTotal = modTotal + bonus
end
-- Defender on hills?
local tgtPlot = Map.GetPlot({target_x}, {target_y})
if tgtPlot and tgtPlot:IsHills() then
    table.insert(mods, "hills +3")
    modTotal = modTotal + 3
end
-- River crossing penalty (attacker crosses river for melee)
if not isRanged and tgtPlot then
    local attPlot = Map.GetPlot(ux, uy)
    if attPlot and tgtPlot:IsRiverCrossingToPlot(attPlot) then
        table.insert(mods, "river -2")
        modTotal = modTotal - 2
    end
end
local effDefCS = defCS + modTotal
print("ESTIMATE|" .. attType .. "|" .. defType .. "|" .. effAttCS .. "|" .. effDefCS .. "|" .. (isRanged and "1" or "0") .. "|" .. table.concat(mods, ";") .. "|" .. myHP .. "|" .. enemyHP)
print("{SENTINEL}")
"""


def parse_combat_estimate(lines: list[str], att_cs: int, def_cs: int) -> CombatEstimate | None:
    """Parse ESTIMATE line and compute damage using Civ 6 formula."""
    for line in lines:
        if line.startswith("ESTIMATE|"):
            p = line.split("|")
            if len(p) < 9:
                return None
            eff_att = int(p[3])
            eff_def = int(p[4])
            is_ranged = p[5] == "1"
            mods = [m for m in p[6].split(";") if m]
            my_hp = int(p[7])
            enemy_hp = int(p[8])
            # Civ 6 damage formula: BASE * 10^((att-def)/30)
            import math
            base_damage = 24
            if eff_att > 0 and eff_def > 0:
                dmg_to_def = base_damage * (10 ** ((eff_att - eff_def) / 30))
                dmg_to_att = base_damage * (10 ** ((eff_def - eff_att) / 30)) if not is_ranged else 0
            else:
                dmg_to_def = 0
                dmg_to_att = 0
            return CombatEstimate(
                attacker_type=p[1],
                defender_type=p[2],
                attacker_cs=eff_att,
                defender_cs=eff_def,
                is_ranged=is_ranged,
                modifiers=mods,
                est_damage_to_defender=int(round(dmg_to_def)),
                est_damage_to_attacker=int(round(dmg_to_att)),
                defender_hp=enemy_hp,
                attacker_hp=my_hp,
            )
    return None


def build_threat_scan_query() -> str:
    """GameCore: scan for foreign military units visible to the player.

    Scans all players (not just barbarians) but only reports units on tiles
    the player can currently see (PlayersVisibility:IsVisible). No arbitrary
    distance limits — fog of war is the natural filter.

    Uses GameCore context but filters by fog of war — only reports units
    on tiles the player can currently see (PlayersVisibility:IsVisible).
    Reports owner, HP, combat strength, and distance from nearest friendly position.
    """
    return f"""
local me = Game.GetLocalPlayer()
local pDiplo = Players[me]:GetDiplomacy()
local pVis = PlayersVisibility[me]
local myPos = {{}}
for _, c in Players[me]:GetCities():Members() do
    table.insert(myPos, {{c:GetX(), c:GetY()}})
end
for _, u in Players[me]:GetUnits():Members() do
    local ux, uy = u:GetX(), u:GetY()
    if ux ~= -9999 then table.insert(myPos, {{ux, uy}}) end
end
local found = false
for pid = 0, 63 do
    if pid ~= me and Players[pid] and Players[pid]:IsAlive() then
        local ownerName = "Barbarian"
        if pid ~= 63 then
            local cfg = PlayerConfigurations[pid]
            if cfg then ownerName = Locale.Lookup(cfg:GetCivilizationShortDescription()) end
        end
        for _, bu in Players[pid]:GetUnits():Members() do
            local bx, by = bu:GetX(), bu:GetY()
            if bx ~= -9999 and pVis:IsVisible(bx, by) then
                local uType = bu:GetType()
                if uType then
                    local entry = GameInfo.Units[uType]
                    local bcs = entry and entry.Combat or 0
                    if bcs > 0 or (entry and entry.RangedCombat and entry.RangedCombat > 0) then
                        local minDist = 999
                        for _, pos in ipairs(myPos) do
                            local d = Map.GetPlotDistance(pos[1], pos[2], bx, by)
                            if d < minDist then minDist = d end
                        end
                        local name = entry and entry.UnitType or "UNKNOWN"
                        local hp = bu:GetMaxDamage() - bu:GetDamage()
                        local brs = entry and entry.RangedCombat or 0
                        print("THREAT|" .. pid .. "|" .. ownerName:gsub("|","/") .. "|" .. name .. "|" .. bx .. "," .. by .. "|" .. hp .. "/" .. bu:GetMaxDamage() .. "|CS:" .. bcs .. "|RS:" .. brs .. "|dist:" .. minDist)
                        found = true
                    end
                end
            end
        end
    end
end
if not found then print("NO_THREATS") end
print("{SENTINEL}")
"""


def build_fortify_unit(unit_index: int) -> str:
    return f"""
{_lua_get_unit(unit_index)}
if unit:GetFortifyTurns() > 0 then
    print("OK:ALREADY_FORTIFIED|Fortify turns: " .. unit:GetFortifyTurns())
    print("{SENTINEL}"); return
end
if UnitManager.CanStartOperation(unit, UnitOperationTypes.FORTIFY, nil, true) then
    UnitManager.RequestOperation(unit, UnitOperationTypes.FORTIFY)
    print("OK:FORTIFIED")
else
    local sleepOp = GameInfo.UnitOperations["UNITOPERATION_SLEEP"]
    if sleepOp and UnitManager.CanStartOperation(unit, sleepOp.Hash, nil, true) then
        UnitManager.RequestOperation(unit, sleepOp.Hash)
        print("OK:SLEEPING")
    else
        {_bail("ERR:CANNOT_FORTIFY|Unit cannot fortify or sleep")}
    end
end
print("{SENTINEL}")
"""


def build_skip_unit(unit_index: int) -> str:
    """Skip a unit's turn (GameCore context — uses FinishMoves)."""
    return f"""
{_lua_get_unit_gamecore(unit_index)}
UnitManager.FinishMoves(unit)
print("OK:SKIPPED")
print("{SENTINEL}")
"""


def build_fortify_remaining_units() -> str:
    """Fortify/heal combat units with remaining moves (InGame context).

    Tries to fortify (or heal if damaged) combat units. Non-combat units
    and units that can't fortify are left for skip_remaining_units to handle.
    """
    return f"""
local me = Game.GetLocalPlayer()
local fortified = 0
local healed = 0
local healHash = GameInfo.UnitOperations["UNITOPERATION_HEAL"] and GameInfo.UnitOperations["UNITOPERATION_HEAL"].Hash
for _, unit in Players[me]:GetUnits():Members() do
    local x = unit:GetX()
    if x ~= -9999 and unit:GetMovesRemaining() > 0 then
        local info = GameInfo.Units[unit:GetType()]
        local isCombat = info and info.Combat > 0
        if isCombat then
            if unit:GetDamage() > 0 and healHash then
                local ok = pcall(function()
                    if UnitManager.CanStartOperation(unit, healHash, nil, true) then
                        UnitManager.RequestOperation(unit, healHash)
                        healed = healed + 1
                    end
                end)
            else
                local ok = pcall(function()
                    if UnitManager.CanStartOperation(unit, UnitOperationTypes.FORTIFY, nil, true) then
                        UnitManager.RequestOperation(unit, UnitOperationTypes.FORTIFY)
                        fortified = fortified + 1
                    end
                end)
            end
        end
    end
end
print("OK:FORTIFIED|" .. fortified .. " fortified, " .. healed .. " healing")
print("{SENTINEL}")
"""


def build_skip_remaining_units() -> str:
    """Skip all units with moves remaining (GameCore context — FinishMoves for each)."""
    return f"""
local me = Game.GetLocalPlayer()
local count = 0
for _, unit in Players[me]:GetUnits():Members() do
    local x = unit:GetX()
    if x ~= -9999 and unit:GetMovesRemaining() > 0 then
        UnitManager.FinishMoves(unit)
        count = count + 1
    end
end
print("OK:SKIPPED|" .. count .. " units")
print("{SENTINEL}")
"""


def build_automate_explore(unit_index: int) -> str:
    """Automate a unit's exploration (InGame context)."""
    return f"""
{_lua_get_unit(unit_index)}
local hash = GameInfo.UnitOperations["UNITOPERATION_AUTOMATE_EXPLORE"].Hash
if not UnitManager.CanStartOperation(unit, hash, nil, nil) then
    {_bail("ERR:CANNOT_AUTOMATE|Unit cannot auto-explore")}
end
UnitManager.RequestOperation(unit, hash, {{}})
print("OK:AUTOMATED|" .. unit:GetX() .. "," .. unit:GetY())
print("{SENTINEL}")
"""


def build_heal_unit(unit_index: int) -> str:
    """Fortify until healed (InGame context). Distinct from plain fortify."""
    return f"""
{_lua_get_unit(unit_index)}
local hp = unit:GetMaxDamage() - unit:GetDamage()
local maxHP = unit:GetMaxDamage()
if hp >= maxHP then {_bail_lua('"ERR:FULL_HP|Unit already at full health (" .. hp .. "/" .. maxHP .. ")"')} end
local healHash = GameInfo.UnitOperations["UNITOPERATION_HEAL"].Hash
if UnitManager.CanStartOperation(unit, healHash, nil, nil) then
    UnitManager.RequestOperation(unit, healHash, {{}})
    print("OK:HEALING|HP:" .. hp .. "/" .. maxHP)
else
    {_bail("ERR:CANNOT_HEAL|Unit cannot fortify-until-healed")}
end
print("{SENTINEL}")
"""


def build_alert_unit(unit_index: int) -> str:
    """Put unit on alert — sleeps but auto-wakes when enemy enters sight (InGame context)."""
    return f"""
{_lua_get_unit(unit_index)}
if UnitManager.CanStartOperation(unit, UnitOperationTypes.ALERT, nil, nil) then
    UnitManager.RequestOperation(unit, UnitOperationTypes.ALERT, {{}})
    print("OK:ALERT|" .. unit:GetX() .. "," .. unit:GetY())
else
    {_bail("ERR:CANNOT_ALERT|Unit cannot be put on alert")}
end
print("{SENTINEL}")
"""


def build_sleep_unit(unit_index: int) -> str:
    """Put unit to sleep — stays until manually woken (InGame context)."""
    return f"""
{_lua_get_unit(unit_index)}
local sleepHash = GameInfo.UnitOperations["UNITOPERATION_SLEEP"].Hash
if UnitManager.CanStartOperation(unit, sleepHash, nil, nil) then
    UnitManager.RequestOperation(unit, sleepHash, {{}})
    print("OK:SLEEPING|" .. unit:GetX() .. "," .. unit:GetY())
else
    {_bail("ERR:CANNOT_SLEEP|Unit cannot sleep")}
end
print("{SENTINEL}")
"""


def build_delete_unit(unit_index: int) -> str:
    """Delete (disband) a unit (InGame context)."""
    return f"""
{_lua_get_unit(unit_index)}
local unitInfo = GameInfo.Units[unit:GetType()]
local uName = unitInfo and unitInfo.UnitType or "UNKNOWN"
if UnitManager.CanStartCommand(unit, UnitCommandTypes.DELETE, true) then
    UnitManager.RequestCommand(unit, UnitCommandTypes.DELETE)
    print("OK:DELETED|" .. uName .. " at " .. unit:GetX() .. "," .. unit:GetY())
else
    {_bail("ERR:CANNOT_DELETE|Unit cannot be deleted")}
end
print("{SENTINEL}")
"""


def build_improve_tile(unit_index: int, improvement_name: str) -> str:
    """Build an improvement with a builder unit (InGame context).

    improvement_name is e.g. IMPROVEMENT_FARM, IMPROVEMENT_MINE, etc.
    """
    return f"""
{_lua_get_unit(unit_index)}
local imp = GameInfo.Improvements["{improvement_name}"]
if imp == nil then {_bail(f"ERR:IMPROVEMENT_NOT_FOUND|{improvement_name}")} end
local plot = Map.GetPlot(unit:GetX(), unit:GetY())
if plot:GetOwner() ~= me then {_bail_lua('"ERR:NOT_YOUR_TERRITORY|Tile at " .. unit:GetX() .. "," .. unit:GetY() .. " is not in your territory"')} end
local params = {{}}
params[UnitOperationTypes.PARAM_X] = unit:GetX()
params[UnitOperationTypes.PARAM_Y] = unit:GetY()
params[UnitOperationTypes.PARAM_IMPROVEMENT_TYPE] = imp.Hash
if plot:IsImprovementPillaged() then
    local repairHash = GameInfo.UnitOperations["UNITOPERATION_REPAIR"] and GameInfo.UnitOperations["UNITOPERATION_REPAIR"].Hash
    if repairHash then
        local rParams = {{}}
        rParams[UnitOperationTypes.PARAM_X] = unit:GetX()
        rParams[UnitOperationTypes.PARAM_Y] = unit:GetY()
        if UnitManager.CanStartOperation(unit, repairHash, nil, rParams) then
            UnitManager.RequestOperation(unit, repairHash, rParams)
            print("OK:REPAIRING|{improvement_name}|" .. unit:GetX() .. "," .. unit:GetY())
            print("{SENTINEL}"); return
        end
    end
end
if not UnitManager.CanStartOperation(unit, UnitOperationTypes.BUILD_IMPROVEMENT, nil, params) then
    local featIdx = plot:GetFeatureType()
    if featIdx >= 0 then
        local feat = GameInfo.Features[featIdx]
        local featName = feat and Locale.Lookup(feat.Name) or ("feature " .. featIdx)
        {_bail_lua(f'"ERR:CANNOT_IMPROVE|Cannot build {improvement_name} here — " .. featName .. " on tile may need tech to remove"')}
    else
        {_bail(f"ERR:CANNOT_IMPROVE|Builder cannot build {improvement_name} here (check tech requirements or tile type)")}
    end
end
UnitManager.RequestOperation(unit, UnitOperationTypes.BUILD_IMPROVEMENT, params)
print("OK:IMPROVING|{improvement_name}|" .. unit:GetX() .. "," .. unit:GetY())
print("{SENTINEL}")
"""


def parse_units_response(lines: list[str]) -> list[UnitInfo]:
    units = []
    for line in lines:
        parts = line.split("|")
        if len(parts) < 7:
            continue
        x_str, y_str = parts[4].split(",")
        moves_cur, moves_max = parts[5].split("/")
        hp_cur, hp_max = parts[6].split("/")
        cs = int(parts[7]) if len(parts) > 7 else 0
        rs = int(parts[8]) if len(parts) > 8 else 0
        charges = int(parts[9]) if len(parts) > 9 else 0
        targets_raw = parts[10] if len(parts) > 10 else ""
        targets = [t for t in targets_raw.split(";") if t] if targets_raw else []
        needs_promo = parts[11] == "1" if len(parts) > 11 else False
        can_upgrade = parts[12] == "1" if len(parts) > 12 else False
        upgrade_target = parts[13] if len(parts) > 13 else ""
        upgrade_cost = int(parts[14]) if len(parts) > 14 and parts[14].isdigit() else 0
        valid_imps_raw = parts[15] if len(parts) > 15 else ""
        valid_imps = [v for v in valid_imps_raw.split(";") if v] if valid_imps_raw else []
        religion = parts[16] if len(parts) > 16 else ""
        units.append(UnitInfo(
            unit_id=int(parts[0]),
            unit_index=int(parts[1]),
            name=parts[2],
            unit_type=parts[3],
            x=int(x_str),
            y=int(y_str),
            moves_remaining=float(moves_cur),
            max_moves=float(moves_max),
            health=int(hp_cur),
            max_health=int(hp_max),
            combat_strength=cs,
            ranged_strength=rs,
            build_charges=charges,
            targets=targets,
            needs_promotion=needs_promo,
            can_upgrade=can_upgrade,
            upgrade_target=upgrade_target,
            upgrade_cost=upgrade_cost,
            valid_improvements=valid_imps,
            religion=religion,
        ))
    return units


def parse_threat_scan_response(lines: list[str]) -> list[ThreatInfo]:
    threats: list[ThreatInfo] = []
    for line in lines:
        if not line.startswith("THREAT|"):
            continue
        parts = line.split("|")
        # New format: THREAT|owner_id|owner_name|unit_type|x,y|hp/max|CS:n|RS:n|dist:n
        if len(parts) >= 9:
            x_str, y_str = parts[4].split(",")
            hp_str, max_str = parts[5].split("/")
            cs = int(parts[6].replace("CS:", "")) if parts[6].startswith("CS:") else 0
            rs = int(parts[7].replace("RS:", "")) if parts[7].startswith("RS:") else 0
            dist = int(parts[8].replace("dist:", "")) if parts[8].startswith("dist:") else 0
            threats.append(ThreatInfo(
                unit_type=parts[3],
                x=int(x_str),
                y=int(y_str),
                hp=int(hp_str),
                max_hp=int(max_str),
                combat_strength=cs,
                ranged_strength=rs,
                distance=dist,
                owner_id=int(parts[1]),
                owner_name=parts[2],
            ))
        elif len(parts) >= 7:
            # Legacy format fallback: THREAT|unit_type|x,y|hp/max|CS:n|RS:n|dist:n
            x_str, y_str = parts[2].split(",")
            hp_str, max_str = parts[3].split("/")
            cs = int(parts[4].replace("CS:", "")) if parts[4].startswith("CS:") else 0
            rs = int(parts[5].replace("RS:", "")) if parts[5].startswith("RS:") else 0
            dist = int(parts[6].replace("dist:", "")) if parts[6].startswith("dist:") else 0
            threats.append(ThreatInfo(
                unit_type=parts[1],
                x=int(x_str),
                y=int(y_str),
                hp=int(hp_str),
                max_hp=int(max_str),
                combat_strength=cs,
                ranged_strength=rs,
                distance=dist,
            ))
    return threats
