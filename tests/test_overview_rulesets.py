"""Execute overview Lua with ruleset-specific game API stubs (issue 22).

Run with: uv run --frozen --with pytest --with lupa python -m pytest tests/test_overview_rulesets.py

The optional Lua runtime keeps game/API stubs offline; it is not a server dependency.
"""
import pytest

lua51 = pytest.importorskip("lupa.lua51")

from civ_mcp.lua._helpers import SENTINEL
from civ_mcp.lua.overview import build_overview_query, parse_overview_response

GAME_STUB = """
local treasury = {
    GetGoldBalance = function() return 500 end,
    GetGoldYield = function() return 35 end,
    GetTotalMaintenance = function() return 5 end,
}
local techs = {
    GetResearchingTech = function() return 0 end,
    GetScienceYield = function() return 25 end,
}
local culture = {
    GetProgressingCivic = function() return 0 end,
    GetCultureYield = function() return 18 end,
    GetCurrentGovernment = function() return 0 end,
}
local religion = {
    GetFaithBalance = function() return 12 end,
    GetReligionTypeCreated = function() return -1 end,
}
local diplomacy = {HasMet = function() return false end}
local city = {GetPopulation = function() return 3 end}
local unit = {GetType = function() return 0 end}
local player = {
    GetTreasury = function() return treasury end,
    GetTechs = function() return techs end,
    GetCulture = function() return culture end,
    GetReligion = function() return religion end,
    GetDiplomacy = function() return diplomacy end,
    GetScore = function() return 120 end,
    GetCities = function() return {Members = function() return ipairs({city}) end} end,
    GetUnits = function() return {Members = function() return ipairs({unit}) end} end,
    IsAlive = function() return true end,
    IsMajor = function() return true end,
    GetInfluence = function()
        return {CanReceiveInfluence = function() return false end}
    end,
}
Players = {[0] = player}
PlayerConfigurations = {[0] = {
    GetCivilizationShortDescription = function() return "Rome" end,
    GetLeaderName = function() return "Trajan" end,
    GetHandicapTypeID = function() return 123 end,
}}
PlayersVisibility = {[0] = {IsRevealed = function() return true end}}
Game = {
    GetLocalPlayer = function() return 0 end,
    GetCurrentGameTurn = function() return 42 end,
    GetGameSpeedType = function() return 0 end,
    IsVictoryEnabled = function() return true end,
}
GameInfo = {
    Technologies = {[0] = {Name = "Pottery"}},
    Civics = {[0] = {Name = "Code of Laws"}},
    Units = {[0] = {Name = "Warrior", Maintenance = 1}},
    Governments = {[0] = {Tier = "GOVERNMENT_TIER_2"}},
    Religions = {},
    Eras = {[0] = {Name = "Ancient"}},
    GameSpeeds = {[0] = {
        Name = "Standard", GameSpeedType = "GAMESPEED_STANDARD", CostMultiplier = 100,
    }},
    Victories = {},
    Difficulties = function()
        local done = false
        return function()
            if not done then
                done = true
                return {DifficultyType = "DIFFICULTY_PRINCE", Name = "Prince"}
            end
        end
    end,
}
GameConfiguration = {
    GetValue = function() return 500 end,
    MakeHash = function() return 123 end,
}
Locale = {Lookup = function(value) return value end}
Map = {
    GetPlotCount = function() return 1 end,
    GetPlotByIndex = function()
        return {
            IsWater = function() return false end,
            GetX = function() return 0 end,
            GetY = function() return 0 end,
        }
    end,
}
"""

ERA_STUB = """
Game.GetEras = function()
    return {
        GetCurrentEra = function() return 0 end,
        GetPlayerCurrentScore = function() return 12 end,
        GetPlayerDarkAgeThreshold = function() return 10 end,
        GetPlayerGoldenAgeThreshold = function() return 20 end,
    }
end
"""


@pytest.mark.parametrize(
    "favor_stub,has_eras,expected_favor,expected_rate",
    [
        pytest.param("", False, 0, 0, id="standard"),
        pytest.param("", True, 0, 0, id="rise-and-fall"),
        pytest.param(
            "Players[0].GetFavor = function() return 0 end", True, 0, 2,
            id="gathering-storm-zero-balance",
        ),
        pytest.param(
            "Players[0].GetFavor = function() return 45 end", True, 45, 2,
            id="gathering-storm",
        ),
    ],
)
def test_overview_query_across_rulesets(
    favor_stub, has_eras, expected_favor, expected_rate,
):
    lua = lua51.LuaRuntime()
    lines = []
    lua.globals().print = lambda value: lines.append(str(value))
    lua.execute(GAME_STUB)
    lua.execute(favor_stub)
    if has_eras:
        lua.execute(ERA_STUB)

    lua.execute(build_overview_query())

    assert lines[-1] == SENTINEL
    assert len(lines[0].split("|")) == 19
    assert any(line.startswith("ERA|") for line in lines) == has_eras
    result = parse_overview_response(lines[:-1])
    assert result.turn == 42
    assert result.civ_name == "Rome"
    assert result.num_cities == 1
    assert result.num_units == 1
    assert result.total_population == 3
    assert result.gold == 500
    assert result.gold_per_turn == 30
    assert result.unit_maintenance == 1
    assert result.current_research == "Pottery"
    assert result.current_civic == "Code of Laws"
    assert result.science_yield == 25
    assert result.culture_yield == 18
    assert result.diplomatic_favor == expected_favor
    assert result.favor_per_turn == expected_rate
    assert result.era_name == ("Ancient" if has_eras else "")
    assert result.era_score == (12 if has_eras else 0)
    assert result.era_dark_threshold == (10 if has_eras else 0)
    assert result.era_golden_threshold == (20 if has_eras else 0)
    # These records follow ERA; an optional API must not truncate output.
    assert result.max_turns == 500
    assert result.difficulty == "Prince"
    assert result.unit_breakdown == {"Warrior": 1}
    assert result.game_speed == "GAMESPEED_STANDARD"
