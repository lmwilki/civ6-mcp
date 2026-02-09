"""Lua code builders and response parsers for Civ 6 game state.

Each domain has:
- build_*_query() -> str: returns Lua code to execute via FireTuner
- parse_*_response() -> dataclass: parses pipe-delimited output lines

All queries use print() for output (not return) and terminate with ---END---.
Output format: pipe-delimited fields, one entity per line.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SENTINEL = "---END---"

# ---------------------------------------------------------------------------
# Internal helpers — reduce boilerplate in Lua query/action builders
# ---------------------------------------------------------------------------

# Item type → GameInfo table name (shared by produce + purchase builders)
_ITEM_TABLE_MAP: dict[str, str] = {
    "UNIT": "Units",
    "BUILDING": "Buildings",
    "DISTRICT": "Districts",
}

# Item type → CityOperationTypes param key (shared by produce + purchase builders)
_ITEM_PARAM_MAP: dict[str, str] = {
    "UNIT": "PARAM_UNIT_TYPE",
    "BUILDING": "PARAM_BUILDING_TYPE",
    "DISTRICT": "PARAM_DISTRICT_TYPE",
}


def _bail(msg: str) -> str:
    """Python-side helper that expands to the Lua bail pattern.

    Usage in f-strings: ``if cond then {_bail("ERR:REASON")} end``
    Generates: ``print("ERR:REASON"); print("---END---"); return``
    """
    return f'print("{msg}"); print("{SENTINEL}"); return'


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
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ScoreEntry:
    player_id: int
    civ_name: str
    score: int


@dataclass
class GameOverview:
    turn: int
    player_id: int
    civ_name: str
    leader_name: str
    gold: float
    gold_per_turn: float
    science_yield: float
    culture_yield: float
    faith: float
    current_research: str
    current_civic: str
    num_cities: int
    num_units: int
    score: int = 0
    rankings: list[ScoreEntry] | None = None


@dataclass
class UnitInfo:
    unit_id: int
    unit_index: int
    name: str
    unit_type: str
    x: int
    y: int
    moves_remaining: int
    max_moves: int
    health: int
    max_health: int
    combat_strength: int = 0
    ranged_strength: int = 0
    build_charges: int = 0
    targets: list[str] = field(default_factory=list)
    needs_promotion: bool = False


@dataclass
class CityInfo:
    city_id: int
    name: str
    x: int
    y: int
    population: int
    food: float
    production: float
    gold: float
    science: float
    culture: float
    faith: float
    housing: float
    amenities: int
    turns_to_grow: int
    currently_building: str
    production_turns_left: int = 0


@dataclass
class ProductionOption:
    category: str       # "UNIT", "BUILDING", "DISTRICT"
    item_name: str      # "UNIT_WARRIOR", "BUILDING_MONUMENT"
    cost: int           # production cost
    turns: int = 0      # estimated turns to produce
    gold_cost: int = -1 # gold purchase cost (-1 = not purchasable)


@dataclass
class TileInfo:
    x: int
    y: int
    terrain: str
    feature: str | None
    resource: str | None
    is_hills: bool
    is_river: bool
    is_coastal: bool
    improvement: str | None
    owner_id: int
    visibility: str = "visible"     # "visible", "revealed", or "unexplored"
    is_fresh_water: bool = False
    yields: tuple[int, ...] | None = None  # (food, prod, gold, science, culture, faith)
    units: list[str] | None = None  # visible foreign units, e.g. ["Barbarian WARRIOR"]
    resource_class: str | None = None  # "strategic", "luxury", "bonus"


@dataclass
class DiplomacyModifier:
    score: int
    text: str


@dataclass
class CivInfo:
    player_id: int
    civ_name: str
    leader_name: str
    has_met: bool
    is_at_war: bool
    diplomatic_state: str = "UNKNOWN"    # FRIENDLY, NEUTRAL, UNFRIENDLY, etc.
    relationship_score: int = 0
    modifiers: list[DiplomacyModifier] | None = None
    grievances: int = 0
    access_level: int = 0                # 0=None, higher=more visibility
    has_delegation: bool = False
    has_embassy: bool = False
    they_have_delegation: bool = False
    they_have_embassy: bool = False
    available_actions: list[str] | None = None  # actions we can take


@dataclass
class TechCivicStatus:
    current_research: str
    current_research_turns: int
    current_civic: str
    current_civic_turns: int
    available_techs: list[str]
    available_civics: list[str]


@dataclass
class DiplomacyChoice:
    key: str       # e.g. "CHOICE_POSITIVE", "CHOICE_EXIT"
    text: str      # localized display text


@dataclass
class DiplomacySession:
    session_id: int
    other_player_id: int
    other_civ_name: str
    other_leader_name: str
    choices: list[DiplomacyChoice]


@dataclass
class CitySnapshot:
    """Minimal city state for diffing between turns."""
    city_id: int
    name: str
    population: int
    currently_building: str


@dataclass
class TurnSnapshot:
    """Full game state snapshot taken before/after end_turn."""
    turn: int
    units: dict[int, UnitInfo]         # keyed by unit_id
    cities: dict[int, CitySnapshot]    # keyed by city_id
    current_research: str
    current_civic: str


@dataclass
class TurnEvent:
    """An event detected by diffing two snapshots."""
    priority: int       # 1=critical, 2=important, 3=info
    category: str       # "unit", "city", "research", "civic"
    message: str


@dataclass
class GameNotification:
    """An active notification from NotificationManager."""
    type_name: str
    message: str
    turn: int
    x: int
    y: int
    is_action_required: bool = False
    resolution_hint: str | None = None


@dataclass
class SettleCandidate:
    """A candidate location for founding a city."""
    x: int
    y: int
    score: float
    total_food: int
    total_prod: int
    water_type: str      # "fresh", "coast", "none"
    resources: list[str]  # classified: ["S:IRON", "L:DIAMONDS", "B:WHEAT"]
    defense_score: int = 0
    luxury_count: int = 0
    strategic_count: int = 0


@dataclass
class ResourceStockpile:
    """Strategic resource stockpile info."""
    name: str
    amount: int
    cap: int
    per_turn: int       # accumulation per turn
    demand: int         # unit upkeep demand per turn
    imported: int       # from trade deals


@dataclass
class OwnedResource:
    """A resource on a tile owned by the player."""
    name: str
    resource_class: str  # "strategic", "luxury", "bonus"
    improved: bool
    x: int
    y: int


@dataclass
class NearbyResource:
    """An unclaimed resource near one of the player's cities."""
    name: str
    resource_class: str
    x: int
    y: int
    nearest_city: str
    distance: int


@dataclass
class ThreatInfo:
    """A hostile military unit spotted near one of our cities."""
    city_name: str
    unit_desc: str
    x: int
    y: int
    distance: int


@dataclass
class DealItem:
    """A single item in a trade deal."""
    from_player_id: int
    from_player_name: str
    item_type: str            # "GOLD", "RESOURCE", "AGREEMENT", "FAVOR", "CITY", "GREAT_WORK"
    name: str                 # human-readable: "Gold", "Tobacco", "Open Borders"
    amount: int
    duration: int             # 0 = lump sum, >0 = per-turn
    is_from_us: bool


@dataclass
class PendingDeal:
    """A trade deal offered by another civilization."""
    other_player_id: int
    other_player_name: str
    other_leader_name: str
    items_from_them: list[DealItem] = field(default_factory=list)
    items_from_us: list[DealItem] = field(default_factory=list)


@dataclass
class PolicySlot:
    """A government policy slot with its current policy."""
    slot_index: int
    slot_type: str            # "SLOT_MILITARY", "SLOT_ECONOMIC", "SLOT_DIPLOMATIC", "SLOT_WILDCARD"
    current_policy: str | None
    current_policy_name: str | None


@dataclass
class PolicyInfo:
    """An available (unlocked) policy."""
    policy_type: str          # e.g. "POLICY_AGOGE"
    name: str
    description: str
    slot_type: str            # compatible slot type


@dataclass
class GovernmentStatus:
    """Current government and policy configuration."""
    government_name: str
    government_type: str
    slots: list[PolicySlot] = field(default_factory=list)
    available_policies: list[PolicyInfo] = field(default_factory=list)


@dataclass
class GovernorInfo:
    """An available governor type."""
    governor_type: str
    name: str
    title: str


@dataclass
class AppointedGovernor:
    """A governor the player has appointed."""
    governor_type: str
    name: str
    assigned_city_id: int       # -1 = unassigned
    assigned_city_name: str     # "Unassigned" if not placed
    is_established: bool
    turns_to_establish: int = 0


@dataclass
class GovernorStatus:
    """Full governor status for the player."""
    points_available: int
    points_spent: int
    can_appoint: bool
    appointed: list[AppointedGovernor] = field(default_factory=list)
    available_to_appoint: list[GovernorInfo] = field(default_factory=list)


@dataclass
class PromotionOption:
    """A promotion available for a unit."""
    promotion_type: str
    name: str
    description: str


@dataclass
class UnitPromotionStatus:
    """Promotions available for a specific unit."""
    unit_id: int
    unit_index: int
    unit_type: str
    promotions: list[PromotionOption] = field(default_factory=list)


@dataclass
class CityStateInfo:
    """A known city-state with envoy info."""
    player_id: int
    name: str
    city_state_type: str   # "Scientific", "Industrial", "Trade", etc.
    envoys_sent: int       # envoys we've sent
    suzerain_id: int       # player ID of suzerain (-1 = none)
    suzerain_name: str     # "None" or civ name
    can_send_envoy: bool


@dataclass
class EnvoyStatus:
    """Full envoy status for the player."""
    tokens_available: int
    city_states: list[CityStateInfo] = field(default_factory=list)


@dataclass
class BeliefInfo:
    """A pantheon belief available for selection."""
    belief_type: str       # e.g. "BELIEF_DANCE_OF_THE_AURORA"
    name: str
    description: str


@dataclass
class PantheonStatus:
    """Current pantheon status and available beliefs."""
    has_pantheon: bool
    current_belief: str | None     # belief type if has pantheon
    current_belief_name: str | None
    faith_balance: float
    available_beliefs: list[BeliefInfo] = field(default_factory=list)


@dataclass
class UnitUpgradeInfo:
    """Info about a unit's upgrade path."""
    unit_id: int
    current_type: str
    upgrade_type: str      # e.g. "UNIT_ARCHER"
    upgrade_name: str
    gold_cost: int
    can_upgrade: bool
    reason: str = ""       # failure reason if can't upgrade


@dataclass
class DedicationChoice:
    """A dedication/commemoration available for selection."""
    index: int
    name: str              # e.g. "COMMEMORATION_SCIENTIFIC"
    normal_desc: str       # bonus in Normal age
    golden_desc: str       # bonus in Golden/Heroic age
    dark_desc: str         # bonus in Dark age


@dataclass
class DedicationStatus:
    """Current dedication/commemoration state."""
    age_type: str          # "Normal", "Golden", "Dark", "Heroic"
    era: int
    era_score: int
    dark_threshold: int
    golden_threshold: int
    selections_allowed: int
    active: list[str] = field(default_factory=list)
    choices: list[DedicationChoice] = field(default_factory=list)


# Map notification types to the MCP tool that resolves them
NOTIFICATION_TOOL_MAP: dict[str, str] = {
    "NOTIFICATION_CHOOSE_TECH": "set_research(tech_or_civic=..., category='tech')",
    "NOTIFICATION_CHOOSE_CIVIC": "set_research(tech_or_civic=..., category='civic')",
    "NOTIFICATION_CHOOSE_CITY_PRODUCTION": "set_city_production(city_id=..., item_type=..., item_name=...)",
    "NOTIFICATION_FILL_CIVIC_SLOT": "get_policies() then set_policies(assignments='...')",
    "NOTIFICATION_CONSIDER_GOVERNMENT_CHANGE": "get_policies() then set_policies()",
    "NOTIFICATION_CHOOSE_PANTHEON": "get_available_beliefs() then choose_pantheon(belief_type=...)",
    "NOTIFICATION_CHOOSE_RELIGION": "execute_lua (religion — no dedicated tool yet)",
    "NOTIFICATION_CHOOSE_BELIEF": "execute_lua (belief — no dedicated tool yet)",
    "NOTIFICATION_DIPLOMACY_SESSION": "get_pending_diplomacy() then diplomacy_respond()",
    "NOTIFICATION_UNIT_PROMOTION_AVAILABLE": "get_unit_promotions(unit_id=...) then promote_unit()",
    "NOTIFICATION_CLAIM_GREAT_PERSON": "execute_lua (great people — no dedicated tool yet)",
    "NOTIFICATION_GIVE_INFLUENCE_TOKEN": "get_city_states() then send_envoy(city_state_player_id=...)",
    "NOTIFICATION_GOVERNOR_APPOINTMENT_AVAILABLE": "get_governors() then appoint_governor()",
    "NOTIFICATION_GOVERNOR_PROMOTION_AVAILABLE": "get_governors() then appoint_governor()",
    "NOTIFICATION_COMMEMORATION_AVAILABLE": "get_dedications() then choose_dedication(dedication_index=...)",
}

_ACTION_KEYWORDS = ("CHOOSE", "FILL", "CONSIDER", "GOVERNOR", "PANTHEON", "PROMOTION", "CLAIM", "INFLUENCE_TOKEN", "COMMEMORATION")

# Map EndTurnBlockingTypes to resolution hints
BLOCKING_TOOL_MAP: dict[str, str] = {
    "ENDTURN_BLOCKING_GOVERNOR_APPOINTMENT": "Use get_governors() then appoint_governor()",
    "ENDTURN_BLOCKING_UNIT_PROMOTION": "Use get_unit_promotions(unit_id=...) then promote_unit()",
    "ENDTURN_BLOCKING_FILL_CIVIC_SLOT": "Use get_policies() then set_policies()",
    "ENDTURN_BLOCKING_PRODUCTION": "Use set_city_production()",
    "ENDTURN_BLOCKING_RESEARCH": "Use set_research()",
    "ENDTURN_BLOCKING_CIVIC": "Use set_research(category='civic')",
    "ENDTURN_BLOCKING_UNITS": "Move or skip remaining units",
    "ENDTURN_BLOCKING_PANTHEON": "Use get_available_beliefs() then choose_pantheon(belief_type=...)",
    "ENDTURN_BLOCKING_STACKED_UNITS": "Move units — cannot stack military units",
    "ENDTURN_BLOCKING_CONSIDER_GOVERNMENT_CHANGE": "Consider Changing Governments",
    "ENDTURN_BLOCKING_COMMEMORATION_AVAILABLE": "Use get_dedications() then choose_dedication(dedication_index=...)",
}


# ---------------------------------------------------------------------------
# Query builders
# ---------------------------------------------------------------------------


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
local nCities = 0; for _ in p:GetCities():Members() do nCities = nCities + 1 end
local nUnits = 0; for _ in p:GetUnits():Members() do nUnits = nUnits + 1 end
local myScore = p:GetScore()
print(Game.GetCurrentGameTurn() .. "|" .. id .. "|" .. Locale.Lookup(cfg:GetCivilizationShortDescription()) .. "|" .. Locale.Lookup(cfg:GetLeaderName()) .. "|" .. string.format("%.1f", tr:GetGoldBalance()) .. "|" .. string.format("%.1f", tr:GetGoldYield() - tr:GetTotalMaintenance()) .. "|" .. string.format("%.1f", te:GetScienceYield()) .. "|" .. string.format("%.1f", cu:GetCultureYield()) .. "|" .. string.format("%.1f", re:GetFaithBalance()) .. "|" .. techName .. "|" .. civicName .. "|" .. nCities .. "|" .. nUnits .. "|" .. myScore)
local pDiplo = p:GetDiplomacy()
for i = 0, 62 do
    if i ~= id and Players[i] and Players[i]:IsAlive() and Players[i]:IsMajor() and pDiplo:HasMet(i) then
        local oCfg = PlayerConfigurations[i]
        print("RANK|" .. i .. "|" .. Locale.Lookup(oCfg:GetCivilizationShortDescription()) .. "|" .. Players[i]:GetScore())
    end
end
print("{SENTINEL}")
"""


def build_units_query() -> str:
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
                                if other:GetOwner() ~= id then
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
        if exp and exp:GetExperiencePoints() >= exp:GetExperienceForNextLevel() then promo = "1" end
        print(uid .. "|" .. (uid % 65536) .. "|" .. nm .. "|" .. ut .. "|" .. x .. "," .. y .. "|" .. u:GetMovesRemaining() .. "/" .. u:GetMaxMoves() .. "|" .. (u:GetMaxDamage() - u:GetDamage()) .. "/" .. u:GetMaxDamage() .. "|" .. cs .. "|" .. rs .. "|" .. charges .. "|" .. targets .. "|" .. promo)
    end
end
print("{SENTINEL}")
"""


def build_cities_query() -> str:
    return f"""
local me = Game.GetLocalPlayer()
local hashName = {{}}
for u in GameInfo.Units() do hashName[u.Hash] = u.UnitType end
for b in GameInfo.Buildings() do hashName[b.Hash] = b.BuildingType end
for d in GameInfo.Districts() do hashName[d.Hash] = d.DistrictType end
for p in GameInfo.Projects() do hashName[p.Hash] = p.ProjectType end
for i, c in Players[me]:GetCities():Members() do
    local nm = Locale.Lookup(c:GetName())
    local bq = c:GetBuildQueue()
    local producing = "nothing"
    local turnsLeft = 0
    if bq:GetSize() > 0 then
        local h = bq:GetCurrentProductionTypeHash()
        producing = hashName[h] or "UNKNOWN"
        turnsLeft = bq:GetTurnsLeft()
    end
    local g = c:GetGrowth()
    print(c:GetID() .. "|" .. nm .. "|" .. c:GetX() .. "," .. c:GetY() .. "|" .. c:GetPopulation() .. "|" .. string.format("%.1f|%.1f|%.1f|%.1f|%.1f|%.1f", c:GetYield(0), c:GetYield(1), c:GetYield(2), c:GetYield(3), c:GetYield(4), c:GetYield(5)) .. "|" .. string.format("%.1f", g:GetHousing()) .. "|" .. g:GetAmenities() .. "|" .. g:GetTurnsUntilGrowth() .. "|" .. producing .. "|" .. turnsLeft)
end
print("{SENTINEL}")
"""


def build_map_area_query(center_x: int, center_y: int, radius: int = 2) -> str:
    return f"""
local cx, cy, r = {center_x}, {center_y}, {radius}
local me = Game.GetLocalPlayer()
local vis = PlayersVisibility[me]
local pTech = Players[me]:GetTechs()
local function resVisible(resEntry)
    if not resEntry.PrereqTech then return true end
    local t = GameInfo.Technologies[resEntry.PrereqTech]
    return t and pTech:HasTech(t.Index)
end
for dy = -r, r do
    for dx = -r, r do
        local x, y = cx + dx, cy + dy
        local plot = Map.GetPlot(x, y)
        if plot then
            local plotIdx = plot:GetIndex()
            local revealed = vis:IsRevealed(plotIdx)
            local visible = vis:IsVisible(plotIdx)
            if revealed then
                local terrain = GameInfo.Terrains[plot:GetTerrainType()].TerrainType
                local hills = plot:IsHills() and "1" or "0"
                local river = plot:IsRiver() and "1" or "0"
                local coastal = plot:IsCoastalLand() and "1" or "0"
                local owner = plot:GetOwner()
                local featureIdx = plot:GetFeatureType()
                local feature = "none"
                if featureIdx >= 0 then feature = GameInfo.Features[featureIdx].FeatureType end
                local resource = "none"
                local resIdx = plot:GetResourceType()
                if resIdx >= 0 then
                    local resEntry = GameInfo.Resources[resIdx]
                    if resVisible(resEntry) then
                        resource = resEntry.ResourceType .. ":" .. (resEntry.ResourceClassType or "")
                    end
                end
                local imp = "none"
                local freshWater = "0"
                local yields = "0,0,0,0,0,0"
                local unitStr = "none"
                local visTag = "revealed"
                if visible then
                    visTag = "visible"
                    local impIdx = plot:GetImprovementType()
                    if impIdx >= 0 then imp = GameInfo.Improvements[impIdx].ImprovementType end
                    freshWater = plot:IsFreshWater() and "1" or "0"
                    yields = plot:GetYield(0) .. "," .. plot:GetYield(1) .. "," .. plot:GetYield(2) .. "," .. plot:GetYield(3) .. "," .. plot:GetYield(4) .. "," .. plot:GetYield(5)
                    local uParts = {{}}
                    for i = 0, 63 do
                        if i ~= me and Players[i] and Players[i]:IsAlive() then
                            local units = Players[i]:GetUnits()
                            if units then
                                for _, u in units:Members() do
                                    if u:GetX() == x and u:GetY() == y then
                                        local entry = GameInfo.Units[u:GetType()]
                                        local ut = entry and entry.UnitType or "UNKNOWN"
                                        local label = ""
                                        if i == 63 then label = "Barbarian"
                                        else
                                            local oCfg = PlayerConfigurations[i]
                                            label = Locale.Lookup(oCfg:GetCivilizationShortDescription())
                                        end
                                        table.insert(uParts, label .. " " .. ut:gsub("UNIT_", ""))
                                    end
                                end
                            end
                        end
                    end
                    if #uParts > 0 then unitStr = table.concat(uParts, ";") end
                end
                print(x .. "," .. y .. "|" .. terrain .. "|" .. feature .. "|" .. resource .. "|" .. hills .. "|" .. river .. "|" .. coastal .. "|" .. imp .. "|" .. owner .. "|" .. unitStr .. "|" .. visTag .. "|" .. freshWater .. "|" .. yields)
            end
        end
    end
end
print("{SENTINEL}")
"""


def build_diplomacy_query() -> str:
    """Rich diplomacy query — runs in InGame context for GetDiplomaticAI access."""
    return f"""
local me = Game.GetLocalPlayer()
local pDiplo = Players[me]:GetDiplomacy()
local states = {{"ALLIED","DECLARED_FRIEND","FRIENDLY","NEUTRAL","UNFRIENDLY","DENOUNCED","WAR"}}
local checkActions = {{"DIPLOACTION_DIPLOMATIC_DELEGATION","DIPLOACTION_DECLARE_FRIENDSHIP","DIPLOACTION_DENOUNCE","DIPLOACTION_RESIDENT_EMBASSY","DIPLOACTION_OPEN_BORDERS"}}
for i = 0, 62 do
    if i ~= me and Players[i] and Players[i]:IsAlive() and Players[i]:IsMajor() then
        local cfg = PlayerConfigurations[i]
        local civName = Locale.Lookup(cfg:GetCivilizationShortDescription())
        local leaderName = Locale.Lookup(cfg:GetLeaderName())
        local met = pDiplo:HasMet(i) and "1" or "0"
        local war = pDiplo:IsAtWarWith(i) and "1" or "0"
        if pDiplo:HasMet(i) then
            local ai = Players[i]:GetDiplomaticAI()
            local stateIdx = ai:GetDiplomaticStateIndex(me)
            local stateName = states[stateIdx + 1] or tostring(stateIdx)
            local grievances = pDiplo:GetGrievancesAgainst(i)
            local vis = pDiplo:GetVisibilityOn(i)
            local hasDel = pDiplo:HasDelegationAt(i) and "1" or "0"
            local hasEmb = pDiplo:HasEmbassyAt(i) and "1" or "0"
            local theyDel = Players[i]:GetDiplomacy():HasDelegationAt(me) and "1" or "0"
            local theyEmb = Players[i]:GetDiplomacy():HasEmbassyAt(me) and "1" or "0"
            print("CIV|" .. i .. "|" .. civName .. "|" .. leaderName .. "|" .. met .. "|" .. war .. "|" .. stateName .. "|" .. grievances .. "|" .. vis .. "|" .. hasDel .. "|" .. hasEmb .. "|" .. theyDel .. "|" .. theyEmb)
            local mods = ai:GetDiplomaticModifiers(me)
            if mods then
                for _, mod in ipairs(mods) do
                    local txt = tostring(mod.Text):gsub("|", "/")
                    print("MOD|" .. i .. "|" .. mod.Score .. "|" .. txt)
                end
            end
            local avail = {{}}
            for _, aName in ipairs(checkActions) do
                local ok2, valid = pcall(function() return pDiplo:IsDiplomaticActionValid(aName, i, false) end)
                if ok2 and valid then table.insert(avail, (aName:gsub("DIPLOACTION_", ""))) end
            end
            if #avail > 0 then print("ACTIONS|" .. i .. "|" .. table.concat(avail, ",")) end
        else
            print("CIV|" .. i .. "|" .. civName .. "|" .. leaderName .. "|" .. met .. "|" .. war .. "|UNKNOWN|0|0|0|0|0|0")
        end
    end
end
print("{SENTINEL}")
"""


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
for tech in GameInfo.Technologies() do
    if te:CanResearch(tech.Index) and not te:HasTech(tech.Index) then
        print("TECH|" .. Locale.Lookup(tech.Name) .. "|" .. tech.TechnologyType)
    end
end
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
                print("CIVIC|" .. Locale.Lookup(civic.Name) .. "|" .. civic.CivicType)
            end
        end
    end
end
print("{SENTINEL}")
"""


# ---------------------------------------------------------------------------
# Action builders
# ---------------------------------------------------------------------------


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
                print("ERR:STACKING_CONFLICT|Friendly " .. otherName .. " already on ({target_x},{target_y}). Cannot stack same formation class.")
                print("{SENTINEL}"); return
            end
        end
    end
end
local fromX, fromY = unit:GetX(), unit:GetY()
local params = {{}}
params[UnitOperationTypes.PARAM_X] = {target_x}
params[UnitOperationTypes.PARAM_Y] = {target_y}
UnitManager.RequestOperation(unit, UnitOperationTypes.MOVE_TO, params)
print("OK:MOVING_TO|" .. {target_x} .. "," .. {target_y} .. "|from:" .. fromX .. "," .. fromY)
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
        print("ERR:OUT_OF_RANGE|Target at distance " .. dist .. " but range is " .. rng .. ". Move closer first.")
        print("{SENTINEL}"); return
    end
    UnitManager.RequestOperation(unit, UnitOperationTypes.RANGE_ATTACK, params)
    print("OK:RANGE_ATTACK|target:" .. enemyName .. " at ({target_x},{target_y})|enemy HP before:" .. enemyHP .. "/" .. enemyMaxHP .. "|your HP:" .. myHP .. "|range:" .. rng .. " dist:" .. dist)
else
    -- Melee: must be adjacent (dist == 1)
    if dist > 1 then
        print("ERR:NOT_ADJACENT|Melee attack needs adjacency (dist=1) but target is " .. dist .. " tiles away. Move adjacent first, then attack.")
        print("{SENTINEL}"); return
    end
    local myCS = unitInfo and unitInfo.Combat or 0
    params[UnitOperationTypes.PARAM_MODIFIERS] = UnitOperationMoveModifiers.ATTACK
    if not UnitManager.CanStartOperation(unit, UnitOperationTypes.MOVE_TO, nil, params) then
        print("ERR:ATTACK_BLOCKED|Cannot attack " .. enemyName .. " at ({target_x},{target_y}). Check for popups or diplomacy blocking operations.")
        print("{SENTINEL}"); return
    end
    UnitManager.RequestOperation(unit, UnitOperationTypes.MOVE_TO, params)
    print("OK:MELEE_ATTACK|target:" .. enemyName .. " at ({target_x},{target_y})|enemy HP before:" .. enemyHP .. "/" .. enemyMaxHP .. "|your HP:" .. myHP .. " CS:" .. myCS .. "|unit moves onto target tile if enemy dies")
end
print("{SENTINEL}")
"""


def build_found_city(unit_index: int) -> str:
    return f"""
{_lua_get_unit(unit_index)}
if not UnitManager.CanStartOperation(unit, UnitOperationTypes.FOUND_CITY, nil, true) then
    {_bail("ERR:CANNOT_FOUND|Unit cannot found cities (not a settler or no moves)")}
end
local x, y = unit:GetX(), unit:GetY()
local plot = Map.GetPlot(x, y)
if plot:IsWater() then {_bail("ERR:CANNOT_FOUND|Cannot found city on water")} end
if plot:IsMountain() then {_bail("ERR:CANNOT_FOUND|Cannot found city on mountain")} end
for i = 0, 62 do
    if Players[i] and Players[i]:IsAlive() then
        local cities = Players[i]:GetCities()
        if cities then
            for _, c in cities:Members() do
                local dist = Map.GetPlotDistance(x, y, c:GetX(), c:GetY())
                if dist <= 3 then
                    print("ERR:CANNOT_FOUND|Too close to " .. Locale.Lookup(c:GetName()) .. " (settler at " .. x .. "," .. y .. ", distance " .. dist .. ", need > 3)")
                    print("{SENTINEL}"); return
                end
            end
        end
    end
end
local params = {{}}
params[UnitOperationTypes.PARAM_X] = x
params[UnitOperationTypes.PARAM_Y] = y
UnitManager.RequestOperation(unit, UnitOperationTypes.FOUND_CITY, params)
print("OK:FOUNDED|" .. x .. "," .. y)
print("{SENTINEL}")
"""


def build_settle_advisor_query(unit_index: int) -> str:
    """Scan radius 5 around settler for valid + scored settle candidates.

    Scores by weighted yields, water bonus, defense, and resource value.
    Resources are classified (S=strategic, L=luxury, B=bonus).
    Returns top 5 candidates sorted by score.
    """
    return f"""
local me = Game.GetLocalPlayer()
local unit = UnitManager.GetUnit(me, {unit_index})
if unit == nil then print("NONE"); print("{SENTINEL}"); return end
local sx, sy = unit:GetX(), unit:GetY()
local vis = PlayersVisibility[me]
local allCities = {{}}
for i = 0, 62 do
    if Players[i] and Players[i]:IsAlive() then
        local cities = Players[i]:GetCities()
        if cities then
            for _, c in cities:Members() do
                table.insert(allCities, {{x=c:GetX(), y=c:GetY()}})
            end
        end
    end
end
local classPrefix = {{RESOURCECLASS_STRATEGIC="S", RESOURCECLASS_LUXURY="L", RESOURCECLASS_BONUS="B"}}
local pTech = Players[me]:GetTechs()
local function resVisible(resEntry)
    if not resEntry.PrereqTech then return true end
    local t = GameInfo.Technologies[resEntry.PrereqTech]
    return t and pTech:HasTech(t.Index)
end
local candidates = {{}}
for dy = -5, 5 do
    for dx = -5, 5 do
        local cx, cy = sx + dx, sy + dy
        local cPlot = Map.GetPlot(cx, cy)
        if cPlot then
            local cIdx = cPlot:GetIndex()
            if vis:IsVisible(cIdx) and not cPlot:IsWater() and not cPlot:IsMountain() then
                local tooClose = false
                for _, city in ipairs(allCities) do
                    if Map.GetPlotDistance(cx, cy, city.x, city.y) <= 3 then tooClose = true; break end
                end
                if not tooClose then
                    local totalF, totalP, totalG = 0, 0, 0
                    local resList = {{}}
                    local luxCount, stratCount = 0, 0
                    for ry = -3, 3 do
                        for rx = -3, 3 do
                            local tx, ty = cx + rx, cy + ry
                            local tPlot = Map.GetPlot(tx, ty)
                            if tPlot and Map.GetPlotDistance(cx, cy, tx, ty) <= 3 then
                                totalF = totalF + tPlot:GetYield(0)
                                totalP = totalP + tPlot:GetYield(1)
                                totalG = totalG + tPlot:GetYield(2)
                                local rIdx = tPlot:GetResourceType()
                                if rIdx >= 0 then
                                    local resEntry = GameInfo.Resources[rIdx]
                                    if resVisible(resEntry) then
                                        local rName = resEntry.ResourceType:gsub("RESOURCE_", "")
                                        local prefix = classPrefix[resEntry.ResourceClassType] or "B"
                                        table.insert(resList, prefix .. ":" .. rName)
                                        if prefix == "L" then luxCount = luxCount + 1
                                        elseif prefix == "S" then stratCount = stratCount + 1 end
                                    end
                                end
                            end
                        end
                    end
                    local waterType = "none"
                    if cPlot:IsFreshWater() then waterType = "fresh"
                    elseif cPlot:IsCoastalLand() then waterType = "coast" end
                    local defScore = 0
                    if cPlot:IsHills() then defScore = defScore + 2 end
                    if cPlot:IsRiver() then defScore = defScore + 1 end
                    for ady = -1, 1 do
                        for adx = -1, 1 do
                            if adx ~= 0 or ady ~= 0 then
                                local ap = Map.GetPlot(cx + adx, cy + ady)
                                if ap and ap:IsHills() and Map.GetPlotDistance(cx, cy, cx+adx, cy+ady) == 1 then defScore = defScore + 1 end
                            end
                        end
                    end
                    local score = totalF * 2 + totalP * 2 + totalG + luxCount * 4 + stratCount * 3 + defScore
                    if waterType == "fresh" then score = score + 5
                    elseif waterType == "coast" then score = score + 3 end
                    table.insert(candidates, {{x=cx, y=cy, score=score, f=totalF, p=totalP, water=waterType, def=defScore, res=table.concat(resList, ",")}})
                end
            end
        end
    end
end
table.sort(candidates, function(a, b) return a.score > b.score end)
for i = 1, math.min(5, #candidates) do
    local c = candidates[i]
    print("SETTLE|" .. c.x .. "," .. c.y .. "|" .. c.score .. "|" .. c.f .. "|" .. c.p .. "|" .. c.water .. "|" .. c.def .. "|" .. c.res)
end
if #candidates == 0 then print("NONE") end
print("{SENTINEL}")
"""


def build_empire_resources_query() -> str:
    """Scan owned tiles for resources, stockpile counts, and nearby unclaimed.

    Returns STOCKPILE lines for strategic resource amounts/caps,
    OWNED lines for resources on player-owned tiles, and
    NEARBY lines for unclaimed resources within 5 tiles of cities.
    Runs in InGame context for GetResourceStockpileCap/GetResourceAccumulationPerTurn.
    """
    return f"""
local me = Game.GetLocalPlayer()
local vis = PlayersVisibility[me]
local pRes = Players[me]:GetResources()
local classMap = {{RESOURCECLASS_STRATEGIC="strategic", RESOURCECLASS_LUXURY="luxury", RESOURCECLASS_BONUS="bonus"}}
-- Stockpile info for strategic and luxury resources
for row in GameInfo.Resources() do
    if pRes:IsResourceVisible(row.Index) then
        local cls = classMap[row.ResourceClassType]
        if cls == "strategic" then
            local amt = pRes:GetResourceAmount(row.Index)
            local cap = pRes:GetResourceStockpileCap(row.Index)
            local accum = pRes:GetResourceAccumulationPerTurn(row.Index)
            local demand = pRes:GetUnitResourceDemandPerTurn(row.Index)
            local imported = pRes:GetResourceImportPerTurn(row.Index)
            local rName = row.ResourceType:gsub("RESOURCE_", "")
            print("STOCKPILE|" .. rName .. "|" .. amt .. "|" .. cap .. "|" .. accum .. "|" .. demand .. "|" .. imported)
        elseif cls == "luxury" then
            local amt = pRes:GetResourceAmount(row.Index)
            if amt > 0 then
                local rName = row.ResourceType:gsub("RESOURCE_", "")
                print("LUXURY_OWNED|" .. rName .. "|" .. amt)
            end
        end
    end
end
local myCities = {{}}
local seen = {{}}
for _, c in Players[me]:GetCities():Members() do
    table.insert(myCities, {{name=Locale.Lookup(c:GetName()), x=c:GetX(), y=c:GetY()}})
end
-- Scan all owned tiles
local mapW, mapH = Map.GetGridSize()
for x = 0, mapW - 1 do
    for y = 0, mapH - 1 do
        local plot = Map.GetPlot(x, y)
        if plot and plot:GetOwner() == me then
            local rIdx = plot:GetResourceType()
            if rIdx >= 0 and pRes:IsResourceVisible(rIdx) then
                local resEntry = GameInfo.Resources[rIdx]
                local rName = resEntry.ResourceType:gsub("RESOURCE_", "")
                local rClass = classMap[resEntry.ResourceClassType] or "bonus"
                local impIdx = plot:GetImprovementType()
                local improved = "0"
                if impIdx >= 0 then improved = "1" end
                print("OWNED|" .. rName .. "|" .. rClass .. "|" .. improved .. "|" .. x .. "," .. y)
                seen[x .. "," .. y] = true
            end
        end
    end
end
-- Scan radius 5 around each city for unowned visible resources
for _, city in ipairs(myCities) do
    for dy = -5, 5 do
        for dx = -5, 5 do
            local tx, ty = city.x + dx, city.y + dy
            local key = tx .. "," .. ty
            if not seen[key] then
                local tPlot = Map.GetPlot(tx, ty)
                if tPlot and vis:IsRevealed(tPlot:GetIndex()) and tPlot:GetOwner() ~= me then
                    local rIdx = tPlot:GetResourceType()
                    if rIdx >= 0 and pRes:IsResourceVisible(rIdx) then
                        local resEntry = GameInfo.Resources[rIdx]
                        local rName = resEntry.ResourceType:gsub("RESOURCE_", "")
                        local rClass = classMap[resEntry.ResourceClassType] or "bonus"
                        local dist = Map.GetPlotDistance(city.x, city.y, tx, ty)
                        print("NEARBY|" .. rName .. "|" .. rClass .. "|" .. tx .. "," .. ty .. "|" .. city.name .. "|" .. dist)
                        seen[key] = true
                    end
                end
            end
        end
    end
end
print("{SENTINEL}")
"""


def build_threat_scan_query() -> str:
    """Scan visible tiles around each city for hostile military units.

    Only checks tiles the player can currently see (vis:IsVisible).
    Returns THREAT lines for each hostile military unit found.
    """
    return f"""
local me = Game.GetLocalPlayer()
local vis = PlayersVisibility[me]
local cities = {{}}
for _, c in Players[me]:GetCities():Members() do
    table.insert(cities, {{x=c:GetX(), y=c:GetY(), name=Locale.Lookup(c:GetName())}})
end
local seen = {{}}
for _, city in ipairs(cities) do
    for dy = -4, 4 do
        for dx = -4, 4 do
            local x, y = city.x + dx, city.y + dy
            local dist = Map.GetPlotDistance(city.x, city.y, x, y)
            if dist > 0 and dist <= 4 then
                local plot = Map.GetPlot(x, y)
                if plot and vis:IsVisible(plot:GetIndex()) then
                    local key = x .. "," .. y
                    if not seen[key] then
                        seen[key] = true
                        for i = 0, 63 do
                            if i ~= me and Players[i] and Players[i]:IsAlive() then
                                for _, u in Players[i]:GetUnits():Members() do
                                    if u:GetX() == x and u:GetY() == y then
                                        local entry = GameInfo.Units[u:GetType()]
                                        local cs = entry and entry.Combat or 0
                                        if cs > 0 then
                                            local label = i == 63 and "Barbarian" or Locale.Lookup(PlayerConfigurations[i]:GetCivilizationShortDescription())
                                            print("THREAT|" .. city.name .. "|" .. label .. " " .. entry.UnitType:gsub("UNIT_","") .. " (CS:" .. cs .. ")" .. "|" .. x .. "," .. y .. "|" .. dist)
                                        end
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
    end
end
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
        print("ERR:CANNOT_FORTIFY|Unit cannot fortify or sleep")
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
if hp >= maxHP then
    print("ERR:FULL_HP|Unit already at full health (" .. hp .. "/" .. maxHP .. ")")
    print("{SENTINEL}"); return
end
local healHash = GameInfo.UnitOperations["UNITOPERATION_HEAL"].Hash
if UnitManager.CanStartOperation(unit, healHash, nil, nil) then
    UnitManager.RequestOperation(unit, healHash, {{}})
    print("OK:HEALING|HP:" .. hp .. "/" .. maxHP)
else
    print("ERR:CANNOT_HEAL|Unit cannot fortify-until-healed")
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
    print("ERR:CANNOT_ALERT|Unit cannot be put on alert")
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
    print("ERR:CANNOT_SLEEP|Unit cannot sleep")
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
    print("ERR:CANNOT_DELETE|Unit cannot be deleted")
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
if plot:GetOwner() ~= me then
    print("ERR:NOT_YOUR_TERRITORY|Tile at " .. unit:GetX() .. "," .. unit:GetY() .. " is not in your territory")
    print("{SENTINEL}"); return
end
local params = {{}}
params[UnitOperationTypes.PARAM_X] = unit:GetX()
params[UnitOperationTypes.PARAM_Y] = unit:GetY()
params[UnitOperationTypes.PARAM_IMPROVEMENT_TYPE] = imp.Hash
if not UnitManager.CanStartOperation(unit, UnitOperationTypes.BUILD_IMPROVEMENT, nil, params) then
    local featIdx = plot:GetFeatureType()
    if featIdx >= 0 then
        local feat = GameInfo.Features[featIdx]
        local featName = feat and Locale.Lookup(feat.Name) or ("feature " .. featIdx)
        print("ERR:CANNOT_IMPROVE|Cannot build {improvement_name} here — " .. featName .. " on tile may need tech to remove")
    else
        print("ERR:CANNOT_IMPROVE|Builder cannot build {improvement_name} here (check tech requirements or tile type)")
    end
    print("{SENTINEL}"); return
end
UnitManager.RequestOperation(unit, UnitOperationTypes.BUILD_IMPROVEMENT, params)
print("OK:IMPROVING|{improvement_name}|" .. unit:GetX() .. "," .. unit:GetY())
print("{SENTINEL}")
"""


def build_city_production_query(city_id: int) -> str:
    """Returns Lua that lists what the city can produce. Actual production setting
    needs the item type, so this is a two-step process: list, then set."""
    return f"""
local me = Game.GetLocalPlayer()
local pCity = Players[me]:GetCities():FindID({city_id})
if pCity == nil then {_bail("ERR:CITY_NOT_FOUND")} end
local bq = pCity:GetBuildQueue()
local goldIdx = GameInfo.Yields["YIELD_GOLD"].Index
local cityGold = pCity:GetGold()
local function getGoldCost(hash, isUnit)
    local ok, cost = pcall(function()
        if isUnit then
            return cityGold:GetPurchaseCost(goldIdx, hash, MilitaryFormationTypes.STANDARD_MILITARY_FORMATION)
        else
            return cityGold:GetPurchaseCost(goldIdx, hash, -1)
        end
    end)
    if ok and cost and cost > 0 then return math.floor(cost) end
    return -1
end
print("UNITS:")
for unit in GameInfo.Units() do
    if bq:CanProduce(unit.Hash, true) then
        local t = bq:GetTurnsLeft(unit.Hash)
        local gc = getGoldCost(unit.Hash, true)
        print("UNIT|" .. unit.UnitType .. "|" .. unit.Cost .. "|" .. t .. "|" .. gc)
    end
end
print("BUILDINGS:")
for bldg in GameInfo.Buildings() do
    if bq:CanProduce(bldg.Hash, true) then
        local t = bq:GetTurnsLeft(bldg.Hash)
        local gc = getGoldCost(bldg.Hash, false)
        print("BUILDING|" .. bldg.BuildingType .. "|" .. bldg.Cost .. "|" .. t .. "|" .. gc)
    end
end
print("DISTRICTS:")
for dist in GameInfo.Districts() do
    if bq:CanProduce(dist.Hash, true) then
        local t = bq:GetTurnsLeft(dist.Hash)
        print("DISTRICT|" .. dist.DistrictType .. "|" .. dist.Cost .. "|" .. t .. "|-1")
    end
end
print("{SENTINEL}")
"""


def build_produce_item(city_id: int, item_type: str, item_name: str) -> str:
    """Set production for a city via CityManager.RequestOperation (InGame context).

    item_type is UNIT/BUILDING/DISTRICT, item_name is e.g. UNIT_WARRIOR.
    Uses .Hash for item refs and VALUE_REPLACE_AT position 0 to replace current production.
    """
    table_name = _ITEM_TABLE_MAP.get(item_type.upper(), "Units")
    param_key = _ITEM_PARAM_MAP.get(item_type.upper(), "PARAM_UNIT_TYPE")
    return f"""
{_lua_get_city(city_id)}
local item = GameInfo.{table_name}["{item_name}"]
if item == nil then {_bail(f"ERR:ITEM_NOT_FOUND|{item_name}")} end
local bq = pCity:GetBuildQueue()
if not bq:CanProduce(item.Hash, true) then
    {_bail(f"ERR:CANNOT_PRODUCE|{item_name} cannot be produced in this city")}
end
local tParams = {{}}
tParams[CityOperationTypes.{param_key}] = item.Hash
tParams[CityOperationTypes.PARAM_INSERT_MODE] = CityOperationTypes.VALUE_REPLACE_AT
tParams[CityOperationTypes.PARAM_QUEUE_DESTINATION_LOCATION] = 0
CityManager.RequestOperation(pCity, CityOperationTypes.BUILD, tParams)
local turnsLeft = bq:GetTurnsLeft(item.Hash)
print("OK:PRODUCING|{item_name}|" .. turnsLeft .. " turns")
print("{SENTINEL}")
"""


def build_purchase_item(city_id: int, item_type: str, item_name: str, yield_type: str = "YIELD_GOLD") -> str:
    """Purchase a unit or building with gold/faith via CityManager.RequestCommand (InGame context)."""
    itype = item_type.upper()
    table_name = _ITEM_TABLE_MAP.get(itype)
    param_key = _ITEM_PARAM_MAP.get(itype)
    if table_name is None or param_key is None:
        return f'print("ERR:INVALID_TYPE|Can only purchase UNIT or BUILDING, got {item_type}"); print("{SENTINEL}")'
    return f"""
{_lua_get_city(city_id)}
local item = GameInfo.{table_name}["{item_name}"]
if item == nil then {_bail(f"ERR:ITEM_NOT_FOUND|{item_name}")} end
local yieldRow = GameInfo.Yields["{yield_type}"]
if yieldRow == nil then {_bail(f"ERR:YIELD_NOT_FOUND|{yield_type}")} end
local tParams = {{}}
tParams[CityCommandTypes.{param_key}] = item.Hash
tParams[CityCommandTypes.PARAM_YIELD_TYPE] = yieldRow.Index
if "{itype}" == "UNIT" then
    tParams[CityCommandTypes.PARAM_MILITARY_FORMATION_TYPE] = MilitaryFormationTypes.STANDARD_MILITARY_FORMATION
    local cx, cy = pCity:GetX(), pCity:GetY()
    local targetClass = item.FormationClass
    local existing = Map.GetUnitsAt(cx, cy)
    if existing and existing:GetCount() > 0 then
        for u in existing:Units() do
            if u:GetOwner() == me then
                local uDef = GameInfo.Units[u:GetType()]
                if uDef and uDef.FormationClass == targetClass then
                    print("ERR:STACKING_CONFLICT|Cannot purchase {item_name} — " .. uDef.UnitType .. " already on city tile. Move it first.")
                    print("{SENTINEL}"); return
                end
            end
        end
    end
end
local cost = pCity:GetGold():GetPurchaseCost(yieldRow.Index, item.Hash, MilitaryFormationTypes.STANDARD_MILITARY_FORMATION)
local balance = Players[me]:GetTreasury():GetGoldBalance()
local canBuy, results = CityManager.CanStartCommand(pCity, CityCommandTypes.PURCHASE, false, tParams, true)
if not canBuy then
    local reasons = {{}}
    if results then
        for _,v in pairs(results) do
            if type(v) == "table" then
                for _,msg in pairs(v) do if type(msg) == "string" then table.insert(reasons, msg) end end
            elseif type(v) == "string" then table.insert(reasons, v)
            end
        end
    end
    if cost > balance then
        table.insert(reasons, 1, "costs " .. math.floor(cost) .. "g but you only have " .. math.floor(balance) .. "g")
    end
    local reason = #reasons > 0 and table.concat(reasons, "; ") or "unknown"
    print("ERR:CANNOT_PURCHASE|" .. reason)
    print("{SENTINEL}"); return
end
CityManager.RequestCommand(pCity, CityCommandTypes.PURCHASE, tParams)
print("OK:PURCHASED|{item_name}|cost=" .. math.floor(cost) .. "g (had " .. math.floor(balance) .. "g)")
print("{SENTINEL}")
"""


def build_set_research(tech_name: str) -> str:
    return f"""
local id = Game.GetLocalPlayer()
local idx = nil
for row in GameInfo.Technologies() do
    if row.TechnologyType == "{tech_name}" then idx = row.Index; break end
end
if idx == nil then print("ERR:TECH_NOT_FOUND|{tech_name}"); print("{SENTINEL}"); return end
local params = {{}}
params[PlayerOperations.PARAM_TECH_TYPE] = idx
UI.RequestPlayerOperation(id, PlayerOperations.RESEARCH, params)
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
if idx == nil then print("ERR:CIVIC_NOT_FOUND|{civic_name}"); print("{SENTINEL}"); return end
local params = {{}}
params[PlayerOperations.PARAM_CIVIC_TYPE] = idx
UI.RequestPlayerOperation(id, PlayerOperations.PROGRESS_CIVIC, params)
print("OK:PROGRESSING|{civic_name}")
print("{SENTINEL}")
"""


def build_diplomacy_session_query() -> str:
    """Check for open diplomacy sessions and return choices (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local found = false
for i = 0, 62 do
    if i ~= me and Players[i] and Players[i]:IsAlive() then
        local sid = DiplomacyManager.FindOpenSessionID(me, i)
        if sid and sid >= 0 then
            local cfg = PlayerConfigurations[i]
            local civName = Locale.Lookup(cfg:GetCivilizationShortDescription())
            local leaderName = Locale.Lookup(cfg:GetLeaderName())
            print("SESSION|" .. sid .. "|" .. i .. "|" .. civName .. "|" .. leaderName)
            found = true
        end
    end
end
if not found then print("NONE") end
print("{SENTINEL}")
"""


def build_diplomacy_choices_query(other_player_id: int) -> str:
    """Get available dialogue choices for an open session with a specific player."""
    return f"""
local me = Game.GetLocalPlayer()
local sid = DiplomacyManager.FindOpenSessionID(me, {other_player_id})
if sid == nil or sid < 0 then print("ERR:NO_SESSION"); print("{SENTINEL}"); return end
print("SESSION|" .. sid)
local ctrl = ContextPtr:LookUpControl("/InGame/DiplomacyActionView")
local isVisible = ctrl and not ctrl:IsHidden() or false
print("VISIBLE|" .. tostring(isVisible))
for row in GameInfo.DiplomacySelections() do
    if string.find(row.Type, "FIRST_MEET") or string.find(row.Type, "GREETING") or string.find(row.Type, "DECLARE_FRIEND") or string.find(row.Type, "DENOUNCE") then
        local text = Locale.Lookup(row.Text)
        print("CHOICE|" .. row.Type .. "|" .. row.Key .. "|" .. text)
    end
end
print("{SENTINEL}")
"""


def build_diplomacy_respond(other_player_id: int, response: str) -> str:
    """Respond to a diplomacy session.

    response is 'POSITIVE', 'NEGATIVE', or 'EXIT'.
    EXIT closes the session directly (for the goodbye phase).
    POSITIVE/NEGATIVE sends AddResponse, then auto-closes if the session
    persists (indicating the goodbye phase was reached).
    """
    return f"""
local me = Game.GetLocalPlayer()
local sid = DiplomacyManager.FindOpenSessionID(me, {other_player_id})
if sid == nil or sid < 0 then print("ERR:NO_SESSION"); print("{SENTINEL}"); return end
if "{response}" == "EXIT" then
    DiplomacyManager.CloseSession(sid)
    print("OK:SESSION_CLOSED")
    print("{SENTINEL}"); return
end
DiplomacyManager.AddResponse(sid, me, "{response}")
local stillOpen = DiplomacyManager.FindOpenSessionID(me, {other_player_id})
if stillOpen and stillOpen >= 0 then
    DiplomacyManager.CloseSession(stillOpen)
    local final = DiplomacyManager.FindOpenSessionID(me, {other_player_id})
    if final and final >= 0 then
        print("OK:RESPONDED|{response}|SESSION_CONTINUES")
    else
        print("OK:RESPONDED|{response}|SESSION_CLOSED_GOODBYE")
    end
else
    print("OK:RESPONDED|{response}|SESSION_CLOSED")
end
print("{SENTINEL}")
"""


def build_send_diplo_action(other_player_id: int, action_name: str) -> str:
    """Send a proactive diplomatic action and detect acceptance/rejection.

    action_name is e.g. DIPLOMATIC_DELEGATION, DECLARE_FRIENDSHIP, DENOUNCE.
    Checks pre-state, sends via RequestSession, then checks post-state.
    """
    # Map action names to the state checks
    return f"""
local me = Game.GetLocalPlayer()
local pDiplo = Players[me]:GetDiplomacy()
local target = {other_player_id}
local action = "{action_name}"
local fullAction = "DIPLOACTION_" .. action
-- Validate first
local valid, results = pDiplo:IsDiplomaticActionValid(fullAction, target, true)
if not valid then
    local reasons = "unknown"
    if results and results.FailureReasons then
        local parts = {{}}
        for _, r in ipairs(results.FailureReasons) do
            table.insert(parts, Locale.Lookup(r))
        end
        reasons = table.concat(parts, "; ")
    end
    print("ERR:INVALID|" .. reasons)
    print("{SENTINEL}"); return
end
-- Capture pre-state
local preDel = pDiplo:HasDelegationAt(target)
local preEmb = pDiplo:HasEmbassyAt(target)
local preGold = Players[me]:GetTreasury():GetGoldBalance()
-- Send via RequestSession
DiplomacyManager.RequestSession(me, target, action)
-- Check if a session opened (AI may respond with dialogue)
local sid = DiplomacyManager.FindOpenSessionID(me, target)
if sid and sid >= 0 then
    -- Auto-respond POSITIVE to complete the action dialogue
    for round = 1, 5 do
        DiplomacyManager.AddResponse(sid, me, "POSITIVE")
        sid = DiplomacyManager.FindOpenSessionID(me, target)
        if not sid or sid < 0 then break end
        DiplomacyManager.CloseSession(sid)
        sid = DiplomacyManager.FindOpenSessionID(me, target)
        if not sid or sid < 0 then break end
    end
end
-- Check post-state to detect acceptance/rejection
local postDel = pDiplo:HasDelegationAt(target)
local postEmb = pDiplo:HasEmbassyAt(target)
local postGold = Players[me]:GetTreasury():GetGoldBalance()
local name = Locale.Lookup(PlayerConfigurations[target]:GetCivilizationShortDescription())
if action == "DIPLOMATIC_DELEGATION" then
    if postDel and not preDel then
        print("OK:ACCEPTED|" .. name .. " accepted your delegation (cost " .. string.format("%.0f", preGold - postGold) .. " gold)")
    else
        print("OK:REJECTED|" .. name .. " rejected your delegation")
    end
elseif action == "RESIDENT_EMBASSY" then
    if postEmb and not preEmb then
        print("OK:ACCEPTED|" .. name .. " accepted your embassy")
    else
        print("OK:REJECTED|" .. name .. " rejected your embassy")
    end
elseif action == "DECLARE_FRIENDSHIP" then
    print("OK:SENT|Friendship declaration sent to " .. name)
elseif action == "DENOUNCE" then
    print("OK:SENT|Denounced " .. name)
else
    print("OK:SENT|" .. action .. " sent to " .. name)
end
print("{SENTINEL}")
"""


def build_end_turn_blocking_query() -> str:
    """Check for EndTurnBlocking notifications (InGame context).

    GetFirstEndTurnBlocking returns the blocking TYPE VALUE (not a notification ID).
    Match it against EndTurnBlockingTypes enum values to get the type name.
    """
    return f"""
local me = Game.GetLocalPlayer()
local blockVal = NotificationManager.GetFirstEndTurnBlocking(me)
if blockVal == nil or blockVal == 0 then
    print("NONE")
else
    local typeName = "UNKNOWN"
    for k, v in pairs(EndTurnBlockingTypes) do
        if v == blockVal then typeName = k; break end
    end
    local msg = ""
    local list = NotificationManager.GetList(me)
    if list then
        for _, nid in ipairs(list) do
            local entry = NotificationManager.Find(me, nid)
            if entry and not entry:IsDismissed() then
                local bt = entry:GetEndTurnBlocking()
                if bt and bt == blockVal then
                    msg = (entry:GetMessage() or ""):gsub("|", "/")
                    break
                end
            end
        end
    end
    print("BLOCKING|" .. typeName .. "|" .. msg)
end
print("{SENTINEL}")
"""


def build_end_turn() -> str:
    return f"""
UI.RequestAction(ActionTypes.ACTION_ENDTURN)
print("OK:TURN_ENDED")
print("{SENTINEL}")
"""


def build_notifications_query() -> str:
    """Query NotificationManager for active notifications (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local nm = NotificationManager
local list = nm.GetList(me)
if list then
    for _, nID in ipairs(list) do
        local entry = nm.Find(me, nID)
        if entry and not entry:IsDismissed() then
            local typeName = entry:GetTypeName() or "UNKNOWN"
            local msg = entry:GetMessage() or ""
            msg = msg:gsub("|", "/")
            local turn = entry:GetAddedTurn() or -1
            local x, y = -1, -1
            pcall(function() x, y = entry:GetLocation() end)
            if x == nil then x = -1 end
            if y == nil then y = -1 end
            print("NOTIF|" .. typeName .. "|" .. msg .. "|" .. turn .. "|" .. x .. "," .. y)
        end
    end
end
print("{SENTINEL}")
"""



# ---------------------------------------------------------------------------
# Trade deal queries (InGame context)
# ---------------------------------------------------------------------------


def build_pending_deals_query() -> str:
    """Scan all met players for incoming trade deal offers (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pDiplo = Players[me]:GetDiplomacy()
for i = 0, 62 do
    if i ~= me and Players[i] and Players[i]:IsAlive() and Players[i]:IsMajor() and pDiplo:HasMet(i) then
        local sid = DiplomacyManager.FindOpenSessionID(me, i)
        if sid and sid >= 0 then
        local ok, deal = pcall(function() return DealManager.GetWorkingDeal(DealDirection.INCOMING, me, i) end)
        if ok and deal then
            local count = deal:GetItemCount()
            if count and count > 0 then
                local cfg = PlayerConfigurations[i]
                local civName = Locale.Lookup(cfg:GetCivilizationShortDescription())
                local leaderName = Locale.Lookup(cfg:GetLeaderName())
                print("DEAL|" .. i .. "|" .. civName:gsub("|","/") .. "|" .. leaderName:gsub("|","/"))
                for item in deal:Items() do
                    local fromID = item:GetFromPlayerID()
                    local iType = item:GetType()
                    local subType = item:GetSubType()
                    local amount = item:GetAmount() or 0
                    local duration = item:GetDuration() or 0
                    local valueType = item:GetValueType() or -1
                    local typeName = "UNKNOWN"
                    local itemName = "Unknown"
                    if iType == DealItemTypes.GOLD then
                        typeName = "GOLD"
                        if duration > 0 then itemName = "Gold per turn" else itemName = "Gold (lump sum)" end
                    elseif iType == DealItemTypes.RESOURCES then
                        typeName = "RESOURCE"
                        local res = GameInfo.Resources[valueType]
                        if res then itemName = Locale.Lookup(res.Name) else itemName = "Resource#" .. tostring(valueType) end
                    elseif iType == DealItemTypes.AGREEMENTS then
                        typeName = "AGREEMENT"
                        if subType == DealAgreementTypes.OPEN_BORDERS then itemName = "Open Borders"
                        elseif subType == DealAgreementTypes.JOINT_WAR then itemName = "Joint War"
                        elseif subType == DealAgreementTypes.ALLIANCE then itemName = "Alliance"
                        else itemName = "Agreement#" .. tostring(subType) end
                    elseif iType == DealItemTypes.FAVOR then
                        typeName = "FAVOR"
                        itemName = "Diplomatic Favor"
                    elseif iType == DealItemTypes.CITIES then
                        typeName = "CITY"
                        itemName = "City"
                    elseif iType == DealItemTypes.GREATWORK then
                        typeName = "GREAT_WORK"
                        itemName = "Great Work"
                    end
                    local fromTag = "THEM"
                    if fromID == me then fromTag = "US" end
                    print("ITEM|" .. i .. "|" .. fromTag .. "|" .. typeName .. "|" .. itemName:gsub("|","/") .. "|" .. amount .. "|" .. duration)
                end
            end
        end
        end
    end
end
print("{SENTINEL}")
"""


def build_respond_to_deal(other_player_id: int, accept: bool) -> str:
    """Accept or reject a pending trade deal (InGame context)."""
    action = "DealProposalAction.ACCEPTED" if accept else "DealProposalAction.REJECTED"
    verb = "ACCEPTED" if accept else "REJECTED"
    return f"""
local me = Game.GetLocalPlayer()
local target = {other_player_id}
local sid = DiplomacyManager.FindOpenSessionID(me, target)
if not sid or sid < 0 then
    print("ERR:NO_DEAL|No active deal session with player {other_player_id}")
    print("{SENTINEL}"); return
end
DealManager.SendWorkingDeal({action}, me, target)
for r = 1, 5 do
    sid = DiplomacyManager.FindOpenSessionID(me, target)
    if not sid or sid < 0 then break end
    DiplomacyManager.AddResponse(sid, me, "NEGATIVE")
    sid = DiplomacyManager.FindOpenSessionID(me, target)
    if not sid or sid < 0 then break end
    DiplomacyManager.CloseSession(sid)
end
local name = Locale.Lookup(PlayerConfigurations[target]:GetCivilizationShortDescription())
print("OK:DEAL_{verb}|" .. name)
print("{SENTINEL}")
"""


# ---------------------------------------------------------------------------
# Policy queries (InGame context)
# ---------------------------------------------------------------------------


def build_policies_query() -> str:
    """Read current government, policy slots, and available policies (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pCulture = Players[me]:GetCulture()
local govIdx = pCulture:GetCurrentGovernment()
local govName = "None"
local govType = "NONE"
if govIdx and govIdx >= 0 then
    local govEntry = GameInfo.Governments[govIdx]
    if govEntry then
        govName = Locale.Lookup(govEntry.Name)
        govType = govEntry.GovernmentType
    end
end
local numSlots = pCulture:GetNumPolicySlots()
print("GOV|" .. govType .. "|" .. govName:gsub("|","/") .. "|" .. numSlots)
local slotNames = {{[0]="SLOT_ECONOMIC", [1]="SLOT_MILITARY", [2]="SLOT_DIPLOMATIC", [3]="SLOT_WILDCARD", [4]="SLOT_WILDCARD"}}
for s = 0, numSlots - 1 do
    local slotType = slotNames[pCulture:GetSlotType(s)] or ("SLOT_" .. pCulture:GetSlotType(s))
    local policyIdx = pCulture:GetSlotPolicy(s)
    local policyType = "NONE"
    local policyName = "Empty"
    if policyIdx >= 0 then
        local pe = GameInfo.Policies[policyIdx]
        if pe then
            policyType = pe.PolicyType
            policyName = Locale.Lookup(pe.Name)
        end
    end
    print("SLOT|" .. s .. "|" .. slotType .. "|" .. policyType .. "|" .. policyName:gsub("|","/"))
end
for policy in GameInfo.Policies() do
    if pCulture:IsPolicyUnlocked(policy.Index) then
        local slotType = "SLOT_WILDCARD"
        if policy.GovernmentSlotType then slotType = policy.GovernmentSlotType end
        local name = Locale.Lookup(policy.Name)
        local desc = Locale.Lookup(policy.Description):gsub("|", "/"):gsub("\\n", " ")
        print("AVAIL|" .. policy.PolicyType .. "|" .. name:gsub("|","/") .. "|" .. desc .. "|" .. slotType)
    end
end
print("{SENTINEL}")
"""


def build_set_policies(assignments: dict[int, str]) -> str:
    """Set policy cards in government slots (InGame context).

    assignments maps slot_index -> policy_type string.
    Two-step: UNLOCK_POLICIES first, then RequestPolicyChanges.
    """
    add_entries = []
    for slot_idx, policy_type in assignments.items():
        add_entries.append(
            f'local pe_{slot_idx} = GameInfo.Policies["{policy_type}"]; '
            f'if pe_{slot_idx} == nil then {_bail(f"ERR:POLICY_NOT_FOUND|{policy_type}")} end; '
            f'local sType_{slot_idx} = pCulture:GetSlotType({slot_idx}); '
            f'local pSlot_{slot_idx} = slotTypeMap[pe_{slot_idx}.GovernmentSlotType] or -1; '
            f'if sType_{slot_idx} < 2 and pSlot_{slot_idx} ~= sType_{slot_idx} then '
            f'local sName = slotNames[sType_{slot_idx}] or "unknown"; '
            f'local pType = pe_{slot_idx}.GovernmentSlotType or "unknown"; '
            f'print("ERR:SLOT_MISMATCH|{policy_type} (" .. pType .. ") cannot go in slot {slot_idx} (" .. sName .. ")"); '
            f'print("{SENTINEL}"); return end; '
            f'addList[{slot_idx}] = pe_{slot_idx}.Hash'
        )
    add_lua = " ".join(add_entries)

    return f"""
local me = Game.GetLocalPlayer()
local pCulture = Players[me]:GetCulture()
local numSlots = pCulture:GetNumPolicySlots()
if numSlots <= 0 then
    print("ERR:NO_GOVERNMENT|No government selected")
    print("{SENTINEL}"); return
end
local slotNames = {{[0]="Economic", [1]="Military", [2]="Diplomatic", [3]="Wildcard", [4]="Wildcard"}}
local slotTypeMap = {{SLOT_ECONOMIC=0, SLOT_MILITARY=1, SLOT_DIPLOMATIC=2, SLOT_WILDCARD=3, SLOT_GREAT_PERSON=4}}
UI.RequestPlayerOperation(me, PlayerOperations.UNLOCK_POLICIES, {{}})
local clearList = {{}}
for s = 0, numSlots - 1 do table.insert(clearList, s) end
local addList = {{}}
{add_lua}
pCulture:RequestPolicyChanges(clearList, addList)
print("OK:POLICIES_SET|Policies updated. Use get_policies to verify.")
print("{SENTINEL}")
"""


# ---------------------------------------------------------------------------
# Governor queries (InGame context)
# ---------------------------------------------------------------------------


def build_governors_query() -> str:
    """Read governor status, appointed governors, and available types (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pGovs = Players[me]:GetGovernors()
local pts = pGovs:GetGovernorPoints()
local spent = pGovs:GetGovernorPointsSpent()
local canAppoint = pGovs:CanAppoint() and "1" or "0"
print("STATUS|" .. pts .. "|" .. spent .. "|" .. canAppoint)
local appointedTypes = {{}}
for row in GameInfo.Governors() do
    if row.TransitionStrength and row.TransitionStrength > 0 and pGovs:HasGovernor(row.Hash) then
        appointedTypes[row.GovernorType] = true
        local gov = pGovs:GetGovernor(row.Hash)
        local gName = Locale.Lookup(row.Name)
        local gTitle = Locale.Lookup(row.Title)
        local cityID = -1
        local cityName = "Unassigned"
        local established = "0"
        local turnsLeft = 0
        local assignedCity = gov:GetAssignedCity()
        if assignedCity then
            cityID = assignedCity:GetID()
            cityName = Locale.Lookup(assignedCity:GetName())
            established = gov:IsEstablished() and "1" or "0"
            if not gov:IsEstablished() then turnsLeft = gov:GetTurnsToEstablish() end
        end
        print("APPOINTED|" .. row.GovernorType .. "|" .. gName:gsub("|","/") .. "|" .. gTitle:gsub("|","/") .. "|" .. cityID .. "|" .. cityName:gsub("|","/") .. "|" .. established .. "|" .. turnsLeft)
    end
end
for gov in GameInfo.Governors() do
    if gov.TransitionStrength and gov.TransitionStrength > 0 and not appointedTypes[gov.GovernorType] then
        local gName = Locale.Lookup(gov.Name)
        local gTitle = Locale.Lookup(gov.Title)
        print("AVAILABLE|" .. gov.GovernorType .. "|" .. gName:gsub("|","/") .. "|" .. gTitle:gsub("|","/"))
    end
end
print("{SENTINEL}")
"""


def build_appoint_governor(governor_type: str) -> str:
    """Appoint a new governor (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pGovs = Players[me]:GetGovernors()
if not pGovs:CanAppoint() then {_bail("ERR:CANNOT_APPOINT|No governor points available")} end
local gov = GameInfo.Governors["{governor_type}"]
if gov == nil then {_bail(f"ERR:GOVERNOR_NOT_FOUND|{governor_type}")} end
if PlayerOperations.APPOINT_GOVERNOR == nil then {_bail("ERR:API_MISSING|PlayerOperations.APPOINT_GOVERNOR is nil")} end
if PlayerOperations.PARAM_GOVERNOR_TYPE == nil then {_bail("ERR:API_MISSING|PlayerOperations.PARAM_GOVERNOR_TYPE is nil")} end
local prePts = pGovs:GetGovernorPointsSpent()
local params = {{}}
params[PlayerOperations.PARAM_GOVERNOR_TYPE] = gov.Index
UI.RequestPlayerOperation(me, PlayerOperations.APPOINT_GOVERNOR, params)
local postPts = pGovs:GetGovernorPointsSpent()
if postPts > prePts then
    print("OK:APPOINTED|" .. Locale.Lookup(gov.Name) .. " (" .. Locale.Lookup(gov.Title) .. ")")
else
    print("OK:APPOINT_REQUESTED|" .. Locale.Lookup(gov.Name) .. " — verify with get_governors()")
end
print("{SENTINEL}")
"""


def build_assign_governor(governor_type: str, city_id: int) -> str:
    """Assign a governor to a city (InGame context)."""
    return f"""
{_lua_get_city(city_id)}
local gov = GameInfo.Governors["{governor_type}"]
if gov == nil then {_bail(f"ERR:GOVERNOR_NOT_FOUND|{governor_type}")} end
if PlayerOperations.ASSIGN_GOVERNOR == nil then {_bail("ERR:API_MISSING|PlayerOperations.ASSIGN_GOVERNOR is nil")} end
local params = {{}}
params[PlayerOperations.PARAM_GOVERNOR_TYPE] = gov.Index
params[PlayerOperations.PARAM_CITY_DEST] = pCity:GetID()
params[PlayerOperations.PARAM_PLAYER_ONE] = me
UI.RequestPlayerOperation(me, PlayerOperations.ASSIGN_GOVERNOR, params)
print("OK:ASSIGNED|" .. Locale.Lookup(gov.Name) .. " to " .. Locale.Lookup(pCity:GetName()))
print("{SENTINEL}")
"""


# ---------------------------------------------------------------------------
# Promotion queries (GameCore + InGame)
# ---------------------------------------------------------------------------


def build_unit_promotions_query(unit_index: int) -> str:
    """List available promotions for a unit (GameCore context)."""
    return f"""
{_lua_get_unit_gamecore(unit_index)}
local x, y = unit:GetX(), unit:GetY()
if x == -9999 then {_bail("ERR:UNIT_CONSUMED")} end
local typeIdx = unit:GetType()
if typeIdx == nil then {_bail("ERR:UNIT_NO_TYPE")} end
local info = GameInfo.Units[typeIdx]
local ut = info and info.UnitType or "UNKNOWN"
local promClass = info and info.PromotionClass or ""
print("UNIT|" .. {unit_index} .. "|" .. (unit:GetID() % 65536) .. "|" .. ut)
local exp = unit:GetExperience()
for promo in GameInfo.UnitPromotions() do
    if promo.PromotionClass == promClass then
        local canPromote = false
        pcall(function() canPromote = exp:CanPromote(promo.Index) end)
        if canPromote then
            local name = Locale.Lookup(promo.Name)
            local desc = Locale.Lookup(promo.Description):gsub("|","/"):gsub("\\n"," ")
            print("PROMO|" .. promo.UnitPromotionType .. "|" .. name:gsub("|","/") .. "|" .. desc)
        end
    end
end
print("{SENTINEL}")
"""


def build_promote_unit(unit_index: int, promotion_type: str) -> str:
    """Apply a promotion to a unit (InGame context)."""
    return f"""
{_lua_get_unit(unit_index)}
local promo = GameInfo.UnitPromotions["{promotion_type}"]
if promo == nil then {_bail(f"ERR:PROMOTION_NOT_FOUND|{promotion_type}")} end
local params = {{}}
params[UnitCommandTypes.PARAM_PROMOTION_TYPE] = promo.Hash
if not UnitManager.CanStartCommand(unit, UnitCommandTypes.PROMOTE, params, true) then
    {_bail("ERR:CANNOT_PROMOTE|Unit cannot be promoted right now")}
end
UnitManager.RequestCommand(unit, UnitCommandTypes.PROMOTE, params)
print("OK:PROMOTED|" .. Locale.Lookup(promo.Name))
print("{SENTINEL}")
"""


# ---------------------------------------------------------------------------
# City-state / Envoy queries (InGame context)
# ---------------------------------------------------------------------------


def build_city_states_query() -> str:
    """List known city-states with envoy info (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pInfluence = Players[me]:GetInfluence()
local pDiplo = Players[me]:GetDiplomacy()
print("TOKENS|" .. pInfluence:GetTokensToGive())
local csTypeMap = {{}}
csTypeMap["LEADER_MINOR_CIV_SCIENTIFIC"] = "Scientific"
csTypeMap["LEADER_MINOR_CIV_CULTURAL"] = "Cultural"
csTypeMap["LEADER_MINOR_CIV_MILITARISTIC"] = "Militaristic"
csTypeMap["LEADER_MINOR_CIV_RELIGIOUS"] = "Religious"
csTypeMap["LEADER_MINOR_CIV_TRADE"] = "Trade"
csTypeMap["LEADER_MINOR_CIV_INDUSTRIAL"] = "Industrial"
for i = 0, 62 do
    if Players[i] and Players[i]:IsAlive() and Players[i]:IsMajor() == false and Players[i]:IsBarbarian() == false and pDiplo:HasMet(i) then
        local cfg = PlayerConfigurations[i]
        local name = Locale.Lookup(cfg:GetPlayerName())
        local leaderType = cfg:GetLeaderTypeName() or ""
        local csType = "Unknown"
        local leader = GameInfo.Leaders[leaderType]
        if leader and leader.InheritFrom then
            csType = csTypeMap[leader.InheritFrom] or leader.InheritFrom
        end
        local csInfluence = Players[i]:GetInfluence()
        local envoys = csInfluence:GetTokensReceived(me)
        local suzID = csInfluence:GetSuzerain() or -1
        local suzName = "None"
        if suzID >= 0 and suzID ~= 63 then
            local sCfg = PlayerConfigurations[suzID]
            if sCfg then suzName = Locale.Lookup(sCfg:GetCivilizationShortDescription()) end
        end
        local canSend = pInfluence:CanGiveTokensToPlayer(i) and "1" or "0"
        print("CS|" .. i .. "|" .. name:gsub("|","/") .. "|" .. csType .. "|" .. envoys .. "|" .. suzID .. "|" .. suzName:gsub("|","/") .. "|" .. canSend)
    end
end
print("{SENTINEL}")
"""


def build_send_envoy(city_state_player_id: int) -> str:
    """Send an envoy to a city-state (InGame context)."""
    return f"""
local me = Game.GetLocalPlayer()
local pInfluence = Players[me]:GetInfluence()
if pInfluence:GetTokensToGive() <= 0 then {_bail("ERR:NO_ENVOYS|No envoy tokens available")} end
if not pInfluence:CanGiveTokensToPlayer({city_state_player_id}) then
    {_bail(f"ERR:CANNOT_SEND|Cannot send envoy to player {city_state_player_id}")}
end
local params = {{}}
params[PlayerOperations.PARAM_PLAYER_ONE] = {city_state_player_id}
params[PlayerOperations.PARAM_FLAGS] = 0
UI.RequestPlayerOperation(me, PlayerOperations.GIVE_INFLUENCE_TOKEN, params)
local remaining = pInfluence:GetTokensToGive()
local cfg = PlayerConfigurations[{city_state_player_id}]
local name = cfg and Locale.Lookup(cfg:GetPlayerName()) or "Unknown"
print("OK:ENVOY_SENT|" .. name .. "|remaining=" .. remaining)
print("{SENTINEL}")
"""


# ---------------------------------------------------------------------------
# Pantheon queries (InGame context)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Unit upgrade queries (InGame context)
# ---------------------------------------------------------------------------


def build_unit_upgrade_query(unit_index: int) -> str:
    """Check if a unit can upgrade and get cost/target info (InGame context)."""
    return f"""
{_lua_get_unit(unit_index)}
local info = GameInfo.Units[unit:GetType()]
local ut = info and info.UnitType or "UNKNOWN"
local params = {{}}
local canUpgrade = UnitManager.CanStartCommand(unit, UnitCommandTypes.UPGRADE, params, true)
local upgCol = info.UpgradeUnitCollection
local upgradeType = ""
if upgCol and #upgCol > 0 then upgradeType = upgCol[1].UpgradeUnit or "" end
if not canUpgrade then
    print("ERR:CANNOT_UPGRADE|" .. ut .. (upgradeType ~= "" and (" -> " .. upgradeType) or "") .. " cannot be upgraded right now (missing tech, resources, gold, or no upgrade path)")
    print("{SENTINEL}"); return
end
if upgradeType == "" then
    print("ERR:NO_UPGRADE_PATH|" .. ut .. " has no upgrade")
    print("{SENTINEL}"); return
end
local upInfo = GameInfo.Units[upgradeType]
local upName = upInfo and Locale.Lookup(upInfo.Name) or upgradeType
local gold = Players[me]:GetTreasury():GetGoldBalance()
local cost = 0
pcall(function() cost = unit:GetUpgradeCost() end)
print("UPGRADE|" .. ut .. "|" .. upgradeType .. "|" .. upName:gsub("|","/") .. "|" .. math.floor(cost) .. "|" .. math.floor(gold))
print("{SENTINEL}")
"""


def build_upgrade_unit(unit_index: int) -> str:
    """Execute unit upgrade (InGame context)."""
    return f"""
{_lua_get_unit(unit_index)}
local params = {{}}
if not UnitManager.CanStartCommand(unit, UnitCommandTypes.UPGRADE, params, true) then
    {_bail("ERR:CANNOT_UPGRADE|Unit cannot be upgraded right now")}
end
local info = GameInfo.Units[unit:GetType()]
local ut = info and info.UnitType or "UNKNOWN"
local upgCol = info and info.UpgradeUnitCollection
local upType = "UNKNOWN"
if upgCol and #upgCol > 0 then upType = upgCol[1].UpgradeUnit or "UNKNOWN" end
UnitManager.RequestCommand(unit, UnitCommandTypes.UPGRADE, params)
print("OK:UPGRADED|" .. ut .. " -> " .. upType)
print("{SENTINEL}")
"""


# ---------------------------------------------------------------------------
# Dedications / Commemorations (InGame context — Gathering Storm era system)
# ---------------------------------------------------------------------------


def build_dedications_query() -> str:
    """Read current era age, available dedications, and active ones."""
    return f"""
local me = Game.GetLocalPlayer()
local pEras = Game.GetEras()
local age = "Normal"
if pEras:HasHeroicGoldenAge(me) then age = "Heroic"
elseif pEras:HasGoldenAge(me) then age = "Golden"
elseif pEras:HasDarkAge(me) then age = "Dark" end
local era = pEras:GetCurrentEra()
local darkT = pEras:GetPlayerDarkAgeThreshold(me) or 0
local goldT = pEras:GetPlayerGoldenAgeThreshold(me) or 0
local allowed = pEras:GetPlayerNumAllowedCommemorations(me)
-- Era score from breakdown
local score = 0
local bd = pEras:GetPlayerCurrentEraScoreBreakdown(me)
if bd then for _, e in ipairs(bd) do score = score + (e.Score or 0) end end
print("STATUS|" .. age .. "|" .. era .. "|" .. score .. "|" .. darkT .. "|" .. goldT .. "|" .. allowed)
-- Active commemorations
local active = pEras:GetPlayerActiveCommemorations(me)
if active then
    for _, a in ipairs(active) do
        local row = GameInfo.CommemorationTypes[a]
        if row then print("ACTIVE|" .. row.CommemorationType) end
    end
end
-- Available choices
local choices = pEras:GetPlayerCommemorateChoices(me)
if choices then
    for _, idx in ipairs(choices) do
        local row = GameInfo.CommemorationTypes[idx]
        if row then
            local norm = row.NormalAgeBonusDescription and Locale.Lookup(row.NormalAgeBonusDescription) or ""
            local gold = row.GoldenAgeBonusDescription and Locale.Lookup(row.GoldenAgeBonusDescription) or ""
            local dark = row.DarkAgeBonusDescription and Locale.Lookup(row.DarkAgeBonusDescription) or ""
            print("CHOICE|" .. idx .. "|" .. row.CommemorationType .. "|" .. norm .. "|" .. gold .. "|" .. dark)
        end
    end
end
print("{SENTINEL}")
"""


def build_choose_dedication(dedication_index: int) -> str:
    """Select a dedication/commemoration by its index."""
    return f"""
local me = Game.GetLocalPlayer()
local pEras = Game.GetEras()
local allowed = pEras:GetPlayerNumAllowedCommemorations(me)
if allowed <= 0 then
    print("ERR:NO_DEDICATION_NEEDED|No dedication selection required (already chosen or not available)")
    print("{SENTINEL}"); return
end
local row = GameInfo.CommemorationTypes[{dedication_index}]
if not row then
    print("ERR:INVALID_INDEX|Dedication index {dedication_index} not found")
    print("{SENTINEL}"); return
end
local params = {{}}
params[PlayerOperations.PARAM_COMMEMORATION_TYPE] = {dedication_index}
UI.RequestPlayerOperation(me, PlayerOperations.COMMEMORATE, params)
print("OK:DEDICATION_CHOSEN|" .. row.CommemorationType)
print("{SENTINEL}")
"""


# ---------------------------------------------------------------------------
# Response parsers
# ---------------------------------------------------------------------------


def parse_overview_response(lines: list[str]) -> GameOverview:
    if not lines:
        raise ValueError("Empty overview response")
    parts = lines[0].split("|")
    if len(parts) < 13:
        raise ValueError(f"Overview response has {len(parts)} fields, expected 13: {lines[0]}")
    rankings: list[ScoreEntry] = []
    for line in lines[1:]:
        if line.startswith("RANK|"):
            rp = line.split("|")
            if len(rp) >= 4:
                rankings.append(ScoreEntry(
                    player_id=int(rp[1]),
                    civ_name=rp[2],
                    score=int(rp[3]),
                ))
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
        rankings=rankings if rankings else None,
    )


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
        units.append(UnitInfo(
            unit_id=int(parts[0]),
            unit_index=int(parts[1]),
            name=parts[2],
            unit_type=parts[3],
            x=int(x_str),
            y=int(y_str),
            moves_remaining=int(moves_cur),
            max_moves=int(moves_max),
            health=int(hp_cur),
            max_health=int(hp_max),
            combat_strength=cs,
            ranged_strength=rs,
            build_charges=charges,
            targets=targets,
            needs_promotion=needs_promo,
        ))
    return units


def parse_cities_response(lines: list[str]) -> list[CityInfo]:
    cities = []
    for line in lines:
        parts = line.split("|")
        if len(parts) < 14:
            continue
        x_str, y_str = parts[2].split(",")
        cities.append(CityInfo(
            city_id=int(parts[0]),
            name=parts[1],
            x=int(x_str),
            y=int(y_str),
            population=int(parts[3]),
            food=float(parts[4]),
            production=float(parts[5]),
            gold=float(parts[6]),
            science=float(parts[7]),
            culture=float(parts[8]),
            faith=float(parts[9]),
            housing=float(parts[10]),
            amenities=int(parts[11]),
            turns_to_grow=int(parts[12]),
            currently_building=parts[13],
            production_turns_left=int(parts[14]) if len(parts) > 14 else 0,
        ))
    return cities


def parse_map_response(lines: list[str]) -> list[TileInfo]:
    tiles = []
    for line in lines:
        parts = line.split("|")
        if len(parts) < 9:
            continue
        x_str, y_str = parts[0].split(",")
        unit_list = None
        if len(parts) > 9 and parts[9] != "none":
            unit_list = parts[9].split(";")
        visibility = "visible"
        if len(parts) > 10:
            visibility = parts[10]
        is_fresh_water = False
        if len(parts) > 11:
            is_fresh_water = parts[11] == "1"
        yields = None
        if len(parts) > 12 and parts[12] != "0,0,0,0,0,0":
            yield_parts = parts[12].split(",")
            if len(yield_parts) == 6:
                yields = tuple(int(float(y)) for y in yield_parts)
        elif len(parts) > 12 and visibility == "visible":
            # Visible tile with all-zero yields — still valid
            yields = (0, 0, 0, 0, 0, 0)
        # Parse resource field — may contain "RESOURCE_X:RESOURCECLASS_Y" or "none"
        resource_name = None
        resource_class = None
        if parts[3] != "none":
            res_parts = parts[3].split(":", 1)
            resource_name = res_parts[0]
            if len(res_parts) > 1:
                _CLASS_MAP = {
                    "RESOURCECLASS_STRATEGIC": "strategic",
                    "RESOURCECLASS_LUXURY": "luxury",
                    "RESOURCECLASS_BONUS": "bonus",
                }
                resource_class = _CLASS_MAP.get(res_parts[1])
        tiles.append(TileInfo(
            x=int(x_str),
            y=int(y_str),
            terrain=parts[1],
            feature=None if parts[2] == "none" else parts[2],
            resource=resource_name,
            is_hills=parts[4] == "1",
            is_river=parts[5] == "1",
            is_coastal=parts[6] == "1",
            improvement=None if parts[7] == "none" else parts[7],
            owner_id=int(parts[8]),
            visibility=visibility,
            is_fresh_water=is_fresh_water,
            yields=yields,
            units=unit_list,
            resource_class=resource_class,
        ))
    return tiles


def parse_diplomacy_response(lines: list[str]) -> list[CivInfo]:
    civs: dict[int, CivInfo] = {}
    for line in lines:
        if line.startswith("CIV|"):
            parts = line.split("|")
            if len(parts) < 13:
                continue
            pid = int(parts[1])
            total_score = 0  # will sum modifiers below
            civs[pid] = CivInfo(
                player_id=pid,
                civ_name=parts[2],
                leader_name=parts[3],
                has_met=parts[4] == "1",
                is_at_war=parts[5] == "1",
                diplomatic_state=parts[6],
                grievances=int(parts[7]),
                access_level=int(parts[8]),
                has_delegation=parts[9] == "1",
                has_embassy=parts[10] == "1",
                they_have_delegation=parts[11] == "1",
                they_have_embassy=parts[12] == "1",
                modifiers=[],
                available_actions=[],
            )
        elif line.startswith("MOD|"):
            parts = line.split("|")
            if len(parts) >= 4:
                pid = int(parts[1])
                if pid in civs:
                    civs[pid].modifiers.append(DiplomacyModifier(
                        score=int(parts[2]),
                        text=parts[3],
                    ))
                    civs[pid].relationship_score += int(parts[2])
        elif line.startswith("ACTIONS|"):
            parts = line.split("|")
            if len(parts) >= 3:
                pid = int(parts[1])
                if pid in civs:
                    civs[pid].available_actions = parts[2].split(",")
    return list(civs.values())


def parse_tech_civics_response(lines: list[str]) -> TechCivicStatus:
    current_research = "None"
    current_research_turns = -1
    current_civic = "None"
    current_civic_turns = -1
    available_techs: list[str] = []
    available_civics: list[str] = []

    for line in lines:
        if line.startswith("CURRENT|"):
            parts = line.split("|")
            current_research = parts[1]
            current_research_turns = int(parts[2])
            current_civic = parts[3]
            current_civic_turns = int(parts[4])
        elif line.startswith("TECH|"):
            parts = line.split("|")
            available_techs.append(f"{parts[1]} ({parts[2]})")
        elif line.startswith("CIVIC|"):
            parts = line.split("|")
            available_civics.append(f"{parts[1]} ({parts[2]})")

    return TechCivicStatus(
        current_research=current_research,
        current_research_turns=current_research_turns,
        current_civic=current_civic,
        current_civic_turns=current_civic_turns,
        available_techs=available_techs,
        available_civics=available_civics,
    )


def parse_diplomacy_sessions(lines: list[str]) -> list[DiplomacySession]:
    """Parse open diplomacy session output."""
    sessions = []
    for line in lines:
        if line == "NONE":
            break
        if line.startswith("SESSION|"):
            parts = line.split("|")
            if len(parts) >= 5:
                sessions.append(DiplomacySession(
                    session_id=int(parts[1]),
                    other_player_id=int(parts[2]),
                    other_civ_name=parts[3],
                    other_leader_name=parts[4],
                    choices=[],
                ))
    return sessions


def parse_city_production_response(lines: list[str]) -> list[ProductionOption]:
    """Parse available production options from build_city_production_query query."""
    options = []
    for line in lines:
        if line.startswith(("UNITS:", "BUILDINGS:", "DISTRICTS:")):
            continue
        parts = line.split("|")
        if len(parts) >= 3 and parts[0] in ("UNIT", "BUILDING", "DISTRICT"):
            options.append(ProductionOption(
                category=parts[0],
                item_name=parts[1],
                cost=int(parts[2]),
                turns=int(parts[3]) if len(parts) > 3 else 0,
                gold_cost=int(parts[4]) if len(parts) > 4 else -1,
            ))
    return options


def parse_notifications_response(lines: list[str]) -> list[GameNotification]:
    """Parse NOTIF| lines from build_notifications_query."""
    notifs = []
    for line in lines:
        if not line.startswith("NOTIF|"):
            continue
        parts = line.split("|")
        if len(parts) < 5:
            continue
        x_str, y_str = parts[4].split(",")
        type_name = parts[1]
        is_action = any(kw in type_name.upper() for kw in _ACTION_KEYWORDS)
        hint = NOTIFICATION_TOOL_MAP.get(type_name)
        notifs.append(GameNotification(
            type_name=type_name,
            message=parts[2],
            turn=int(parts[3]),
            x=int(x_str),
            y=int(y_str),
            is_action_required=is_action,
            resolution_hint=hint,
        ))
    return notifs


def parse_settle_advisor_response(lines: list[str]) -> list[SettleCandidate]:
    candidates = []
    for line in lines:
        if line == "NONE":
            break
        if not line.startswith("SETTLE|"):
            continue
        parts = line.split("|")
        if len(parts) < 8:
            continue
        x_str, y_str = parts[1].split(",")
        resources = [r for r in parts[7].split(",") if r] if parts[7] else []
        lux = sum(1 for r in resources if r.startswith("L:"))
        strat = sum(1 for r in resources if r.startswith("S:"))
        candidates.append(SettleCandidate(
            x=int(x_str),
            y=int(y_str),
            score=float(parts[2]),
            total_food=int(parts[3]),
            total_prod=int(parts[4]),
            water_type=parts[5],
            resources=resources,
            defense_score=int(parts[6]),
            luxury_count=lux,
            strategic_count=strat,
        ))
    return candidates


def parse_empire_resources_response(
    lines: list[str],
) -> tuple[list[ResourceStockpile], list[OwnedResource], list[NearbyResource], dict[str, int]]:
    """Returns (stockpiles, owned_tiles, nearby_unclaimed, luxury_counts)."""
    stockpiles = []
    owned = []
    nearby = []
    luxuries: dict[str, int] = {}
    for line in lines:
        if line.startswith("STOCKPILE|"):
            parts = line.split("|")
            if len(parts) < 7:
                continue
            stockpiles.append(ResourceStockpile(
                name=parts[1],
                amount=int(parts[2]),
                cap=int(parts[3]),
                per_turn=int(parts[4]),
                demand=int(parts[5]),
                imported=int(parts[6]),
            ))
        elif line.startswith("LUXURY_OWNED|"):
            parts = line.split("|")
            if len(parts) >= 3:
                luxuries[parts[1]] = int(parts[2])
        elif line.startswith("OWNED|"):
            parts = line.split("|")
            if len(parts) < 5:
                continue
            x_str, y_str = parts[4].split(",")
            owned.append(OwnedResource(
                name=parts[1],
                resource_class=parts[2],
                improved=parts[3] == "1",
                x=int(x_str),
                y=int(y_str),
            ))
        elif line.startswith("NEARBY|"):
            parts = line.split("|")
            if len(parts) < 6:
                continue
            x_str, y_str = parts[3].split(",")
            nearby.append(NearbyResource(
                name=parts[1],
                resource_class=parts[2],
                x=int(x_str),
                y=int(y_str),
                nearest_city=parts[4],
                distance=int(parts[5]),
            ))
    return stockpiles, owned, nearby, luxuries


def parse_threat_scan_response(lines: list[str]) -> list[ThreatInfo]:
    threats = []
    for line in lines:
        if not line.startswith("THREAT|"):
            continue
        parts = line.split("|")
        if len(parts) < 5:
            continue
        x_str, y_str = parts[3].split(",")
        threats.append(ThreatInfo(
            city_name=parts[1],
            unit_desc=parts[2],
            x=int(x_str),
            y=int(y_str),
            distance=int(parts[4]),
        ))
    return threats


def parse_pending_deals_response(lines: list[str]) -> list[PendingDeal]:
    """Parse DEAL| and ITEM| lines from build_pending_deals_query."""
    deals: dict[int, PendingDeal] = {}
    for line in lines:
        if line.startswith("DEAL|"):
            parts = line.split("|")
            if len(parts) >= 4:
                pid = int(parts[1])
                deals[pid] = PendingDeal(
                    other_player_id=pid,
                    other_player_name=parts[2],
                    other_leader_name=parts[3],
                )
        elif line.startswith("ITEM|"):
            parts = line.split("|")
            if len(parts) >= 7:
                pid = int(parts[1])
                if pid not in deals:
                    continue
                is_from_us = parts[2] == "US"
                item = DealItem(
                    from_player_id=-1 if is_from_us else pid,
                    from_player_name="Us" if is_from_us else deals[pid].other_player_name,
                    item_type=parts[3],
                    name=parts[4],
                    amount=int(parts[5]),
                    duration=int(parts[6]),
                    is_from_us=is_from_us,
                )
                if is_from_us:
                    deals[pid].items_from_us.append(item)
                else:
                    deals[pid].items_from_them.append(item)
    return list(deals.values())


def parse_end_turn_blocking(lines: list[str]) -> tuple[str | None, str]:
    """Parse blocking query response. Returns (blocking_type, message) or (None, "")."""
    if not lines or lines[0] == "NONE":
        return None, ""
    line = lines[0]
    if line.startswith("BLOCKING|"):
        parts = line.split("|")
        blocking_type = parts[1] if len(parts) > 1 else "UNKNOWN"
        msg = parts[2] if len(parts) > 2 else ""
        return blocking_type, msg
    return None, ""


def parse_policies_response(lines: list[str]) -> GovernmentStatus:
    """Parse GOV|, SLOT|, AVAIL| lines from build_policies_query."""
    gov_name = "None"
    gov_type = "NONE"
    slots: list[PolicySlot] = []
    available: list[PolicyInfo] = []

    for line in lines:
        if line.startswith("GOV|"):
            parts = line.split("|")
            if len(parts) >= 4:
                gov_type = parts[1]
                gov_name = parts[2]
        elif line.startswith("SLOT|"):
            parts = line.split("|")
            if len(parts) >= 5:
                policy_type = None if parts[3] == "NONE" else parts[3]
                policy_name = None if parts[4] == "Empty" else parts[4]
                slots.append(PolicySlot(
                    slot_index=int(parts[1]),
                    slot_type=parts[2],
                    current_policy=policy_type,
                    current_policy_name=policy_name,
                ))
        elif line.startswith("AVAIL|"):
            parts = line.split("|")
            if len(parts) >= 5:
                available.append(PolicyInfo(
                    policy_type=parts[1],
                    name=parts[2],
                    description=parts[3],
                    slot_type=parts[4],
                ))

    return GovernmentStatus(
        government_name=gov_name,
        government_type=gov_type,
        slots=slots,
        available_policies=available,
    )


def parse_governors_response(lines: list[str]) -> GovernorStatus:
    """Parse STATUS|, APPOINTED|, AVAILABLE| lines from build_governors_query."""
    pts_avail = 0
    pts_spent = 0
    can_appoint = False
    appointed: list[AppointedGovernor] = []
    available: list[GovernorInfo] = []

    for line in lines:
        if line.startswith("STATUS|"):
            parts = line.split("|")
            if len(parts) >= 4:
                pts_avail = int(parts[1])
                pts_spent = int(parts[2])
                can_appoint = parts[3] == "1"
        elif line.startswith("APPOINTED|"):
            parts = line.split("|")
            if len(parts) >= 7:
                appointed.append(AppointedGovernor(
                    governor_type=parts[1],
                    name=parts[2],
                    assigned_city_id=int(parts[4]),
                    assigned_city_name=parts[5],
                    is_established=parts[6] == "1",
                    turns_to_establish=int(parts[7]) if len(parts) >= 8 else 0,
                ))
        elif line.startswith("AVAILABLE|"):
            parts = line.split("|")
            if len(parts) >= 4:
                available.append(GovernorInfo(
                    governor_type=parts[1],
                    name=parts[2],
                    title=parts[3],
                ))

    return GovernorStatus(
        points_available=pts_avail,
        points_spent=pts_spent,
        can_appoint=can_appoint,
        appointed=appointed,
        available_to_appoint=available,
    )


def parse_unit_promotions_response(lines: list[str]) -> UnitPromotionStatus:
    """Parse UNIT| and PROMO| lines from build_unit_promotions_query."""
    unit_id = 0
    unit_index = 0
    unit_type = "UNKNOWN"
    promotions: list[PromotionOption] = []

    for line in lines:
        if line.startswith("ERR:"):
            raise ValueError(line[4:])
        if line.startswith("UNIT|"):
            parts = line.split("|")
            if len(parts) >= 4:
                unit_id = int(parts[1])
                unit_index = int(parts[2])
                unit_type = parts[3]
        elif line.startswith("PROMO|"):
            parts = line.split("|")
            if len(parts) >= 4:
                promotions.append(PromotionOption(
                    promotion_type=parts[1],
                    name=parts[2],
                    description=parts[3],
                ))

    return UnitPromotionStatus(
        unit_id=unit_id,
        unit_index=unit_index,
        unit_type=unit_type,
        promotions=promotions,
    )


def parse_city_states_response(lines: list[str]) -> EnvoyStatus:
    """Parse TOKENS| and CS| lines from build_city_states_query."""
    tokens = 0
    city_states: list[CityStateInfo] = []

    for line in lines:
        if line.startswith("TOKENS|"):
            tokens = int(line.split("|")[1])
        elif line.startswith("CS|"):
            parts = line.split("|")
            if len(parts) >= 8:
                city_states.append(CityStateInfo(
                    player_id=int(parts[1]),
                    name=parts[2],
                    city_state_type=parts[3],
                    envoys_sent=int(parts[4]),
                    suzerain_id=int(parts[5]),
                    suzerain_name=parts[6],
                    can_send_envoy=parts[7] == "1",
                ))

    return EnvoyStatus(tokens_available=tokens, city_states=city_states)


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


def parse_dedications_response(lines: list[str]) -> DedicationStatus:
    """Parse STATUS|, ACTIVE|, and CHOICE| lines from build_dedications_query."""
    age_type = "Normal"
    era = 0
    era_score = 0
    dark_threshold = 0
    golden_threshold = 0
    selections_allowed = 0
    active: list[str] = []
    choices: list[DedicationChoice] = []

    for line in lines:
        if line.startswith("STATUS|"):
            parts = line.split("|")
            if len(parts) >= 7:
                age_type = parts[1]
                era = int(parts[2])
                era_score = int(parts[3])
                dark_threshold = int(parts[4])
                golden_threshold = int(parts[5])
                selections_allowed = int(parts[6])
        elif line.startswith("ACTIVE|"):
            active.append(line.split("|", 1)[1])
        elif line.startswith("CHOICE|"):
            parts = line.split("|", 5)
            if len(parts) >= 6:
                choices.append(DedicationChoice(
                    index=int(parts[1]),
                    name=parts[2],
                    normal_desc=parts[3],
                    golden_desc=parts[4],
                    dark_desc=parts[5],
                ))

    return DedicationStatus(
        age_type=age_type,
        era=era,
        era_score=era_score,
        dark_threshold=dark_threshold,
        golden_threshold=golden_threshold,
        selections_allowed=selections_allowed,
        active=active,
        choices=choices,
    )
