"""Espionage domain — Lua builders and parsers for spy operations."""

from __future__ import annotations

from civ_mcp.lua._helpers import SENTINEL, _bail, _bail_lua, _lua_get_unit
from civ_mcp.lua.models import SpyInfo

# Spy operation hashes — GameInfo.UnitOperations() returns 0 rows so we hardcode these.
# Verified live via UnitOperationTypes enum in InGame Lua context.
_SPY_OP_HASHES: dict[str, int] = {
    "TRAVEL": -1295211657,
    "COUNTERSPY": -2005926703,
    "GAIN_SOURCES": -311249027,
    "SIPHON_FUNDS": 574548564,
    "STEAL_TECH_BOOST": -664243095,
    "SABOTAGE_PRODUCTION": 163704001,
    "GREAT_WORK_HEIST": 485545794,
    "RECRUIT_PARTISANS": -713713573,
    "NEUTRALIZE_GOVERNOR": -1064658215,
    "FABRICATE_SCANDAL": -1766334630,
}

_RANK_NAMES = {1: "Recruit", 2: "Agent", 3: "Special Agent", 4: "Senior Agent"}


def build_get_spies_query() -> str:
    """InGame context: list all spy units with rank, position, city, and available ops."""
    # Build the op table literal for Lua (key=name, value=hash)
    op_entries = ", ".join(f'{name}={hash_val}' for name, hash_val in _SPY_OP_HASHES.items())
    sentinel = SENTINEL
    return f"""
local me = Game.GetLocalPlayer()
local SPY_OPS = {{{op_entries}}}
for i, u in Players[me]:GetUnits():Members() do
    local entry = GameInfo.Units[u:GetType()]
    if entry and entry.UnitType == "UNIT_SPY" then
        local x, y = u:GetX(), u:GetY()
        if x ~= -9999 then
            local name = Locale.Lookup(u:GetName())
            local uid = u:GetID() + me * 65536
            local rank = 1
            local xp = 0
            local exp = u:GetExperience()
            if exp then
                local ok_r, lv = pcall(function() return exp:GetLevel() end)
                if ok_r and lv then rank = lv end
                local ok_x, ep = pcall(function() return exp:GetExperiencePoints() end)
                if ok_x and ep then xp = ep end
            end
            local moves = u:GetMovesRemaining()
            local cityName = "none"
            local cityOwner = -1
            local pCity = CityManager.GetCityAt(x, y)
            if pCity then
                cityName = Locale.Lookup(pCity:GetName())
                cityOwner = pCity:GetOwner()
            end
            local params = {{[UnitOperationTypes.PARAM_X0]=x, [UnitOperationTypes.PARAM_Y0]=y}}
            local availOps = {{}}
            for opName, opHash in pairs(SPY_OPS) do
                if UnitManager.CanStartOperation(u, opHash, nil, params) then
                    table.insert(availOps, opName)
                end
            end
            local opStr = table.concat(availOps, ",")
            print(uid.."|"..name.."|"..x.."|"..y.."|"..rank.."|"..xp.."|"..moves.."|"..cityName.."|"..cityOwner.."|"..opStr)
        end
    end
end
print("{sentinel}")
"""


def parse_spies_response(lines: list[str]) -> list[SpyInfo]:
    """Parse pipe-delimited spy rows into SpyInfo list."""
    spies = []
    for line in lines:
        if not line or line == SENTINEL:
            continue
        parts = line.split("|")
        if len(parts) < 10:
            continue
        try:
            uid = int(parts[0])
            name = parts[1]
            x = int(parts[2])
            y = int(parts[3])
            rank = int(parts[4])
            xp = int(parts[5])
            moves = int(parts[6])
            city_name = parts[7]
            city_owner = int(parts[8])
            ops_str = parts[9].strip()
            available_ops = [op for op in ops_str.split(",") if op]
            spies.append(SpyInfo(
                unit_id=uid,
                unit_index=uid % 65536,
                name=name,
                x=x,
                y=y,
                rank=rank,
                xp=xp,
                moves=moves,
                city_name=city_name,
                city_owner=city_owner,
                available_ops=available_ops,
            ))
        except (ValueError, IndexError):
            continue
    return spies


def build_spy_travel(unit_index: int, target_x: int, target_y: int) -> str:
    """InGame context: send spy to a target city tile.

    Valid targets: own cities and city-states. Allied civ cities return ERR:CANNOT_TRAVEL.
    Travel is queued end-of-turn — spy does not immediately appear at destination.
    """
    travel_hash = _SPY_OP_HASHES["TRAVEL"]
    sentinel = SENTINEL
    # Build the Lua error message expression without backslash escapes in f-strings
    err_lua = (
        '"ERR:CANNOT_TRAVEL|Cannot send spy to (" .. '
        f"{target_x} .. ',' .. {target_y} .. "
        '"). Allied civ cities are not valid; only own cities and city-states."'
    )
    return " ".join([
        _lua_get_unit(unit_index),
        "local entry = GameInfo.Units[unit:GetType()]",
        f'if not entry or entry.UnitType ~= "UNIT_SPY" then {_bail("ERR:NOT_A_SPY")} end',
        f"local params = {{[UnitOperationTypes.PARAM_X0]={target_x}, [UnitOperationTypes.PARAM_Y0]={target_y}}}",
        f"if not UnitManager.CanStartOperation(unit, {travel_hash}, nil, params) then",
        f"  {_bail_lua(err_lua)}",
        "end",
        f"UnitManager.RequestOperation(unit, {travel_hash}, params)",
        f'print("OK:SPY_TRAVEL|Spy en route to ({target_x},{target_y}). Travel completes at end of turn.")',
        f'print("{sentinel}")',
    ])


def build_spy_mission(
    unit_index: int, mission_type: str, target_x: int, target_y: int
) -> str:
    """InGame context: launch a spy mission at a target city tile.

    Offensive missions (anything except COUNTERSPY) require the spy to be physically
    IN the target city. CanStartOperation will return false until arrival.
    """
    op_hash = _SPY_OP_HASHES.get(mission_type.upper())
    sentinel = SENTINEL
    if op_hash is None:
        valid = ", ".join(k for k in _SPY_OP_HASHES if k != "TRAVEL")
        # Escape the mission_type for Lua string embedding
        safe_mission = mission_type.replace('"', '\\"')
        return " ".join([
            f'print("ERR:UNKNOWN_MISSION|Unknown mission type {safe_mission}. Valid missions: {valid}")',
            f'print("{sentinel}")',
        ])
    err_lua = (
        f'"ERR:CANNOT_MISSION|{mission_type} not available at (" .. '
        f"{target_x} .. ',' .. {target_y} .. "
        '"). Spy must be in the target city first (use spy_action travel)."'
    )
    return " ".join([
        _lua_get_unit(unit_index),
        "local entry = GameInfo.Units[unit:GetType()]",
        f'if not entry or entry.UnitType ~= "UNIT_SPY" then {_bail("ERR:NOT_A_SPY")} end',
        f"local params = {{[UnitOperationTypes.PARAM_X0]={target_x}, [UnitOperationTypes.PARAM_Y0]={target_y}}}",
        f"if not UnitManager.CanStartOperation(unit, {op_hash}, nil, params) then",
        f"  {_bail_lua(err_lua)}",
        "end",
        f"UnitManager.RequestOperation(unit, {op_hash}, params)",
        f'print("OK:SPY_MISSION|{mission_type} mission launched at ({target_x},{target_y}).")',
        f'print("{sentinel}")',
    ])
