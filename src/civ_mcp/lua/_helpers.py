"""Internal helpers — reduce boilerplate in Lua query/action builders."""

from __future__ import annotations

SENTINEL = "---END---"

# Item type → GameInfo table name (shared by produce + purchase builders)
_ITEM_TABLE_MAP: dict[str, str] = {
    "UNIT": "Units",
    "BUILDING": "Buildings",
    "DISTRICT": "Districts",
    "PROJECT": "Projects",
}

# Item type → CityOperationTypes param key (shared by produce + purchase builders)
_ITEM_PARAM_MAP: dict[str, str] = {
    "UNIT": "PARAM_UNIT_TYPE",
    "BUILDING": "PARAM_BUILDING_TYPE",
    "DISTRICT": "PARAM_DISTRICT_TYPE",
    "PROJECT": "PARAM_PROJECT_TYPE",
}


def _bail(msg: str) -> str:
    """Python-side helper that expands to the Lua bail pattern.

    Usage in f-strings: ``if cond then {_bail("ERR:REASON")} end``
    Generates: ``print("ERR:REASON"); print("---END---"); return``
    """
    return f'print("{msg}"); print("{SENTINEL}"); return'


def _bail_lua(lua_expr: str) -> str:
    """Like _bail but the argument is a raw Lua expression (for string concatenation).

    Usage in f-strings: ``if cond then {_bail_lua('"ERR:REASON|" .. luaVar')} end``
    Generates: ``print("ERR:REASON|" .. luaVar); print("---END---"); return``
    """
    return f'print({lua_expr}); print("{SENTINEL}"); return'


def _lua_close_diplo_session() -> str:
    """Lua snippet: close any open diplomacy session with ``target``, restore UI.

    Expects ``me`` and ``target`` to be defined in scope.
    """
    return (
        "for r = 1, 5 do "
        "sid = DiplomacyManager.FindOpenSessionID(me, target) "
        "if not sid or sid < 0 then break end "
        'DiplomacyManager.AddResponse(sid, me, "NEGATIVE") '
        "sid = DiplomacyManager.FindOpenSessionID(me, target) "
        "if not sid or sid < 0 then break end "
        "DiplomacyManager.CloseSession(sid) "
        "end "
        "LuaEvents.DiplomacyActionView_ShowIngameUI() "
        "pcall(function() Events.HideLeaderScreen() end)"
    )


def _lua_get_unit(unit_index: int) -> str:
    """Lua snippet: look up a unit in InGame context or bail."""
    return (
        f"local me = Game.GetLocalPlayer() "
        f"local unit = UnitManager.GetUnit(me, {unit_index}) "
        f"if unit == nil then {_bail('ERR:UNIT_NOT_FOUND')} end"
    )


def _lua_get_unit_gamecore(unit_index: int) -> str:
    """Lua snippet: look up a unit in GameCore context or bail."""
    return (
        f"local me = Game.GetLocalPlayer() "
        f"local unit = Players[me]:GetUnits():FindID({unit_index}) "
        f"if unit == nil then {_bail('ERR:UNIT_NOT_FOUND')} end"
    )


def _lua_get_city(city_id: int) -> str:
    """Lua snippet: look up a city in InGame context or bail."""
    return (
        f"local me = Game.GetLocalPlayer() "
        f"local pCity = CityManager.GetCity(me, {city_id} % 65536) "
        f"if pCity == nil then {_bail('ERR:CITY_NOT_FOUND')} end"
    )
