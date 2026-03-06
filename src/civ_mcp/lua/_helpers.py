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


# ---------------------------------------------------------------------------
# Parser helpers — reduce noise in pipe-delimited response parsers
# ---------------------------------------------------------------------------


def _int(s: str) -> int:
    """Parse a string that may be a float representation to int.

    Lua prints integers as floats (e.g. ``3.0``).  This avoids the
    ``int(float(x))`` pattern repeated across every parser.
    """
    return int(float(s))


# ---------------------------------------------------------------------------
# Shared Lua snippet constants — compose into builders via string concat.
# These are plain strings (NOT f-strings), so Lua braces are unescaped.
# Interpolate into f-string builders with {_LUA_RES_VISIBLE} etc.
# ---------------------------------------------------------------------------

# Resource visibility check — expects ``pTech`` in scope.
_LUA_RES_VISIBLE = """\
local function resVisible(resEntry)
    if not resEntry.PrereqTech then return true end
    local t = GameInfo.Technologies[resEntry.PrereqTech]
    return t and pTech:HasTech(t.Index)
end"""

# Victory-enabled check — prints VENABLED| lines for each enabled victory type.
# Yield label table + formatters for trade route yield display.
# fmtY: format array of {YieldIndex, Amount} objects (from GetOutgoingRoutes).
# fmtFlat/sumFlat: format/sum flat 6-element arrays (from Calculate* APIs).
# Both share the yN label table.
_LUA_YIELD_LABELS = 'local yN = {"F","P","G","S","C","A"}'

_LUA_FMT_Y = """\
local function fmtY(tbl)
    if not tbl then return "" end
    local s = ""
    for _, e in ipairs(tbl) do
        if e.Amount and e.Amount > 0 then
            local idx = e.YieldIndex + 1
            if idx >= 1 and idx <= 6 then
                local amt = e.Amount
                if amt == math.floor(amt) then amt = math.floor(amt) end
                s = s .. yN[idx] .. amt
            end
        end
    end
    return s
end"""

_LUA_FMT_FLAT = """\
local function sumFlat(...)
    local s = {0,0,0,0,0,0}
    for _, t in ipairs({...}) do
        if t then for j = 1, 6 do s[j] = s[j] + (t[j] or 0) end end
    end
    return s
end
local function fmtFlat(arr)
    if not arr then return "" end
    local s = ""
    for j = 1, 6 do
        local v = arr[j]
        if v and v > 0 then
            if v == math.floor(v) then v = math.floor(v) end
            s = s .. yN[j] .. v
        end
    end
    return s
end"""

# XP threshold calculation for unit promotions.
# Expects ``exp`` (unit:GetExperience()), ``promClass`` (PromotionClass string) in scope.
# Produces: xpPromoCount, t1, xp, xpNeeded.
_LUA_XP_THRESHOLD = """\
local xpPromoCount = 0
if promClass ~= "" then
    for p in GameInfo.UnitPromotions() do
        if p.PromotionClass == promClass and exp:HasPromotion(p.Index) then
            xpPromoCount = xpPromoCount + 1
        end
    end
end
local t1 = exp:GetExperienceForNextLevel()
local xp = exp:GetExperiencePoints()
local xpNeeded = t1 * (xpPromoCount + 1) * (xpPromoCount + 2) / 2"""

_LUA_VICTORY_ENABLED = """\
local _vtypes = {"VICTORY_TECHNOLOGY","VICTORY_CULTURE","VICTORY_RELIGIOUS","VICTORY_DIPLOMATIC","VICTORY_CONQUEST"}
for _, vt in ipairs(_vtypes) do
    local row = GameInfo.Victories[vt]
    if row then
        local ok, en = pcall(function() return Game.IsVictoryEnabled(row.Index) end)
        if ok and en then print("VENABLED|" .. vt) end
    end
end"""
