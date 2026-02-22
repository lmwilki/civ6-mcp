"""All dataclasses for Lua query responses and game state."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScoreEntry:
    player_id: int
    civ_name: str
    score: int


@dataclass
class RivalSnapshot:
    """Per-turn stats for a rival civ, for diary power curves."""

    id: int
    name: str
    score: int
    cities: int
    pop: int
    sci: float
    cul: float
    gold: float
    mil: int
    techs: int
    civics: int
    faith: float
    sci_vp: int
    diplo_vp: int
    stockpiles: dict[str, int] = field(default_factory=dict)


@dataclass
class PlayerRow:
    """One row per player per turn for diary JSONL (long format)."""

    pid: int
    civ: str
    leader: str
    is_agent: bool
    # Score & yields
    score: int
    cities: int
    pop: int
    science: float
    culture: float
    gold: float
    gold_per_turn: float
    faith: float
    faith_per_turn: float
    favor: int
    favor_per_turn: int
    # Military
    military: int = 0
    units_total: int = 0
    units_military: int = 0
    units_civilian: int = 0
    units_support: int = 0
    unit_composition: dict[str, int] = field(default_factory=dict)
    # Progress
    techs_completed: int = 0
    civics_completed: int = 0
    techs: list[str] = field(default_factory=list)
    civics: list[str] = field(default_factory=list)
    current_research: str = "NONE"
    current_civic: str = "NONE"
    # Infrastructure
    districts: int = 0
    wonders: int = 0
    great_works: int = 0
    territory: int = 0
    improvements: int = 0
    exploration_pct: int = 0
    # Governance
    era: str = ""
    era_score: int = 0
    age: str = "NORMAL"
    government: str = "NONE"
    policies: list[str] = field(default_factory=list)
    pantheon: str = "NONE"
    religion: str = "NONE"
    religion_beliefs: list[str] = field(default_factory=list)
    # Victory
    sci_vp: int = 0
    diplo_vp: int = 0
    tourism: int = 0
    staycationers: int = 0
    # Resources
    stockpiles: dict[str, int] = field(default_factory=dict)
    luxuries: dict[str, int] = field(default_factory=dict)
    religion_cities: int = 0


@dataclass
class CityRow:
    """One row per city per turn for diary JSONL."""

    pid: int
    city_id: int
    city: str
    pop: int
    food: float
    production: float
    gold: float
    science: float
    culture: float
    faith: float
    housing: float
    amenities: int
    amenities_needed: int
    districts: str  # comma-separated short names
    producing: str
    loyalty: float
    loyalty_per_turn: float


@dataclass
class AgentExtras:
    """Agent-only data not recorded for AI players."""

    diplo_states: dict[str, dict] = field(default_factory=dict)
    suzerainties: int = 0
    envoys_available: int = 0
    envoys_sent: dict[str, int] = field(default_factory=dict)
    gp_points: dict[str, int] = field(default_factory=dict)
    governors: list[dict] = field(default_factory=list)
    trade_capacity: int = 0
    trade_active: int = 0
    trade_domestic: int = 0
    trade_international: int = 0


@dataclass
class DiarySnapshot:
    """Complete per-turn diary snapshot — players, cities, agent extras."""

    players: list[PlayerRow] = field(default_factory=list)
    cities: list[CityRow] = field(default_factory=list)
    agent: AgentExtras = field(default_factory=AgentExtras)


@dataclass
class ReligionInfo:
    """Religion founded by a civilization."""

    player_id: int
    civ_name: str
    religion_name: str  # e.g. "Eastern Orthodoxy"


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
    diplomatic_favor: int = 0
    favor_per_turn: int = 0
    explored_land: int = 0
    total_land: int = 0
    rankings: list[ScoreEntry] | None = None
    # Religion slot tracking
    religions_founded: int = 0
    religions_max: int = 0
    our_religion: str | None = None  # religion name if we founded one
    founded_religions: list[ReligionInfo] | None = None
    # Era score tracking
    total_population: int = 0
    era_name: str = ""
    era_score: int = 0
    era_dark_threshold: int = 0
    era_golden_threshold: int = 0
    max_turns: int = 0  # 0 = unlimited / not set


@dataclass
class UnitInfo:
    unit_id: int
    unit_index: int
    name: str
    unit_type: str
    x: int
    y: int
    moves_remaining: float
    max_moves: float
    health: int
    max_health: int
    combat_strength: int = 0
    ranged_strength: int = 0
    build_charges: int = 0
    targets: list[str] = field(default_factory=list)
    needs_promotion: bool = False
    can_upgrade: bool = False
    upgrade_target: str = ""
    upgrade_cost: int = 0
    valid_improvements: list[str] = field(default_factory=list)
    religion: str = ""


@dataclass
class SpyInfo:
    unit_id: int  # composite ID (use with spy_action)
    unit_index: int  # per-player index (unit_id % 65536)
    name: str  # e.g. "Artimpasa"
    x: int
    y: int
    rank: int  # 1=Recruit, 2=Agent, 3=Special Agent, 4=Senior Agent
    xp: int
    moves: int
    city_name: str  # city at current position, or "none"
    city_owner: int  # player ID of city owner, or -1
    available_ops: list[str]  # e.g. ["TRAVEL", "COUNTERSPY"]
    current_mission: str = "none"  # active mission e.g. "COUNTERSPY", or "none"


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
    food_surplus: float = 0.0
    food_stored: float = 0.0
    growth_threshold: int = 0
    currently_building: str = "NONE"
    production_turns_left: int = 0
    defense_strength: int = 0
    garrison_hp: int = 0
    garrison_max_hp: int = 0
    wall_hp: int = 0
    wall_max_hp: int = 0
    attack_targets: list[str] = field(default_factory=list)
    pillaged_districts: list[str] = field(default_factory=list)
    pillaged_buildings: list[str] = field(default_factory=list)
    districts: list[str] = field(default_factory=list)
    loyalty: float = 100.0
    loyalty_max: float = 100.0
    loyalty_per_turn: float = 0.0
    turns_to_loyalty_flip: int = 0
    garrison_unit: str = ""


@dataclass
class ProductionOption:
    category: str  # "UNIT", "BUILDING", "DISTRICT"
    item_name: str  # "UNIT_WARRIOR", "BUILDING_MONUMENT"
    cost: int  # production cost
    turns: int = 0  # estimated turns to produce
    gold_cost: int = -1  # gold purchase cost (-1 = not purchasable)


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
    visibility: str = "visible"  # "visible", "revealed", or "unexplored"
    is_fresh_water: bool = False
    yields: tuple[int, ...] | None = None  # (food, prod, gold, science, culture, faith)
    units: list[str] | None = None  # visible foreign units, e.g. ["Barbarian WARRIOR"]
    own_units: list[str] | None = None  # player's own units on this tile, e.g. ["WARRIOR", "BUILDER"]
    resource_class: str | None = None  # "strategic", "luxury", "bonus"
    is_pillaged: bool = False
    district: str | None = None  # e.g. "DISTRICT_CAMPUS", None if no district
    owner_name: str | None = None  # resolved name, e.g. "Vatican City" (with :CS suffix for city-states)


@dataclass
class DiplomacyModifier:
    score: int
    text: str


@dataclass
class VisibleCity:
    name: str
    x: int
    y: int
    population: int
    loyalty: float = 100.0
    loyalty_per_turn: float = 0.0
    has_walls: bool = False
    defense_strength: int = 0


@dataclass
class CivInfo:
    player_id: int
    civ_name: str
    leader_name: str
    has_met: bool
    is_at_war: bool
    diplomatic_state: str = "UNKNOWN"  # FRIENDLY, NEUTRAL, UNFRIENDLY, etc.
    relationship_score: int = 0
    modifiers: list[DiplomacyModifier] | None = None
    grievances: int = 0
    access_level: int = 0  # 0=None, higher=more visibility
    has_delegation: bool = False
    has_embassy: bool = False
    they_have_delegation: bool = False
    they_have_embassy: bool = False
    available_actions: list[str] | None = None  # actions we can take
    alliance_type: str | None = None
    alliance_level: int = 0
    defensive_pacts: list[int] = field(
        default_factory=list
    )  # player IDs with defensive pacts
    military_strength: int = 0  # their military strength
    num_cities: int = 0  # number of cities they own
    visible_cities: list[VisibleCity] = field(default_factory=list)


@dataclass
class LockedCivic:
    name: str
    civic_type: str
    missing_prereqs: list[str]  # localized names of unmet prerequisites


@dataclass
class TechOption:
    """An available technology for research."""

    name: str
    tech_type: str  # e.g. "TECHNOLOGY_MINING"
    cost: int
    progress_pct: int  # 0-100
    turns: int
    boosted: bool
    boost_desc: str  # trigger description, empty if none
    unlocks: str  # comma-separated unlock names


@dataclass
class CivicOption:
    """An available civic for progression."""

    name: str
    civic_type: str  # e.g. "CIVIC_CODE_OF_LAWS"
    cost: int
    progress_pct: int  # 0-100
    turns: int
    boosted: bool
    boost_desc: str  # trigger description, empty if none


@dataclass
class TechCivicStatus:
    current_research: str
    current_research_turns: int
    current_civic: str
    current_civic_turns: int
    available_techs: list[TechOption]
    available_civics: list[CivicOption]
    completed_tech_count: int = 0
    completed_civic_count: int = 0
    locked_civics: list[LockedCivic] | None = None


@dataclass
class DiplomacyChoice:
    key: str  # e.g. "CHOICE_POSITIVE", "CHOICE_EXIT"
    text: str  # localized display text


@dataclass
class DiplomacySession:
    session_id: int
    other_player_id: int
    other_civ_name: str
    other_leader_name: str
    choices: list[DiplomacyChoice]
    dialogue_text: str = ""  # leader's spoken text (from UI controls)
    reason_text: str = ""  # agenda/reason subtext
    buttons: str = (
        ""  # semicolon-separated visible button labels; "GOODBYE" if goodbye phase
    )
    deal_summary: str = ""  # human-readable deal content when AI proposes a deal (e.g. "They offer: Research Alliance (25 turns)")


@dataclass
class CitySnapshot:
    """Minimal city state for diffing between turns."""

    city_id: int
    name: str
    population: int
    currently_building: str
    food_surplus: float = 0.0
    turns_to_grow: int = 0


@dataclass
class TurnSnapshot:
    """Full game state snapshot taken before/after end_turn."""

    turn: int
    units: dict[int, UnitInfo]  # keyed by unit_id
    cities: dict[int, CitySnapshot]  # keyed by city_id
    current_research: str
    current_civic: str
    stockpiles: list[ResourceStockpile] = field(default_factory=list)


@dataclass
class TurnEvent:
    """An event detected by diffing two snapshots."""

    priority: int  # 1=critical, 2=important, 3=info
    category: str  # "unit", "city", "research", "civic"
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
class CombatEstimate:
    """Predicted combat outcome."""

    attacker_type: str
    defender_type: str
    attacker_cs: int
    defender_cs: int
    is_ranged: bool
    modifiers: list[str]  # ["fortified +6", "hills +3"]
    est_damage_to_defender: int
    est_damage_to_attacker: int  # 0 for ranged
    defender_hp: int
    attacker_hp: int


@dataclass
class SettleCandidate:
    """A candidate location for founding a city."""

    x: int
    y: int
    score: float
    total_food: int
    total_prod: int
    water_type: str  # "fresh", "coast", "none"
    resources: list[str]  # classified: ["S:IRON", "L:DIAMONDS", "B:WHEAT"]
    defense_score: int = 0
    luxury_count: int = 0
    strategic_count: int = 0
    loyalty_pressure: float = (
        0.0  # approx loyalty/turn from population pressure, negative = bad
    )


@dataclass
class FogBoundary:
    """Fog-of-war boundary distances from a city in 6 hex directions."""

    city_name: str
    city_x: int
    city_y: int
    fog_distances: list[int]  # NE,E,SE,SW,W,NW — -1 means all explored


@dataclass
class UnclaimedResource:
    """A luxury or strategic resource on revealed, unowned land."""

    resource_type: str
    x: int
    y: int
    resource_class: str  # "RESOURCECLASS_LUXURY" or "RESOURCECLASS_STRATEGIC"


@dataclass
class StrategicMapData:
    """Strategic map overview: fog boundaries and unclaimed resources."""

    fog_boundaries: list[FogBoundary]
    unclaimed_resources: list[UnclaimedResource]


@dataclass
class MinimapData:
    """ASCII minimap data."""

    width: int
    height: int
    rows: dict[int, str]  # y -> row string


@dataclass
class ResourceStockpile:
    """Strategic resource stockpile info."""

    name: str
    amount: int
    cap: int
    per_turn: int  # accumulation per turn
    demand: int  # unit upkeep demand per turn
    imported: int  # from trade deals


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
    """A hostile military unit spotted near our empire."""

    unit_type: str
    x: int
    y: int
    hp: int
    max_hp: int
    combat_strength: int
    ranged_strength: int
    distance: int
    owner_id: int = 63
    owner_name: str = "Barbarian"
    is_city_state: bool = False
    unit_id: int = 0


@dataclass
class VictoryPlayerProgress:
    """Victory progress for a single civilization."""

    player_id: int
    name: str  # "Unmet" if not met
    score: int
    science_vp: int  # space race VP (0-50)
    science_vp_needed: int
    diplomatic_vp: int  # need 20 to win
    tourism: int
    military_strength: int
    techs_researched: int
    civics_completed: int
    religion_cities: int  # cities following their religion
    # Culture dominance (only for our civ)
    staycationers: int = 0  # domestic tourists
    # Religion details (only meaningful if they founded one)
    has_religion: bool = False
    # Rival intel
    num_cities: int = 0
    science_yield: float = 0.0
    culture_yield: float = 0.0
    gold_yield: float = 0.0
    # Space race
    spaceports: int = 0
    space_progress: str = ""  # e.g. "3/20"


@dataclass
class DemographicEntry:
    """A single demographics metric (mirrors in-game Demographics panel)."""

    rank: int  # 1-based (1 = best)
    value: float  # our value
    best: float
    average: float
    worst: float


@dataclass
class VictoryProgress:
    """Full victory progress snapshot."""

    players: list[VictoryPlayerProgress]
    # Culture victory details (our perspective)
    our_tourists_from: dict[str, int] = field(
        default_factory=dict
    )  # civ_name -> tourists
    their_staycationers: dict[str, int] = field(
        default_factory=dict
    )  # civ_name -> domestic tourists
    # Domination: who holds their original capital?
    capitals_held: dict[str, bool] = field(
        default_factory=dict
    )  # civ_name -> still_holds_own_capital
    # Religion majority per civ
    religion_majority: dict[str, str] = field(
        default_factory=dict
    )  # civ_name -> religion name
    # Religion slot tracking
    religion_founded_names: dict[str, str] = field(
        default_factory=dict
    )  # civ_name -> religion display name
    religions_founded: int = 0
    religions_max: int = 0
    # Demographics (anonymized aggregates for all civs, mirrors in-game panel)
    demographics: dict[str, DemographicEntry] = field(default_factory=dict)


@dataclass
class DealItem:
    """A single item in a trade deal."""

    from_player_id: int
    from_player_name: str
    item_type: str  # "GOLD", "RESOURCE", "AGREEMENT", "FAVOR", "CITY", "GREAT_WORK"
    name: str  # human-readable: "Gold", "Tobacco", "Open Borders"
    amount: int
    duration: int  # 0 = lump sum, >0 = per-turn
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
class DealOptions:
    """What's available to trade with a civilization."""

    other_player_id: int
    other_civ_name: str
    our_gold: int = 0
    our_gpt: int = 0
    our_favor: int = 0
    their_gold: int = 0
    their_gpt: int = 0
    their_favor: int = 0
    our_luxuries: list[str] = field(default_factory=list)
    our_strategics: list[str] = field(default_factory=list)
    their_luxuries: list[str] = field(default_factory=list)
    their_strategics: list[str] = field(default_factory=list)
    has_open_borders: bool = False
    alliance_eligible: bool = False
    current_alliance: str | None = None


@dataclass
class PolicySlot:
    """A government policy slot with its current policy."""

    slot_index: int
    slot_type: (
        str  # "SLOT_MILITARY", "SLOT_ECONOMIC", "SLOT_DIPLOMATIC", "SLOT_WILDCARD"
    )
    current_policy: str | None
    current_policy_name: str | None


@dataclass
class PolicyInfo:
    """An available (unlocked) policy."""

    policy_type: str  # e.g. "POLICY_AGOGE"
    name: str
    description: str
    slot_type: str  # compatible slot type


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
class GovernorPromotion:
    """A promotion available for a governor."""

    promotion_type: str
    name: str
    description: str


@dataclass
class AppointedGovernor:
    """A governor the player has appointed."""

    governor_type: str
    name: str
    assigned_city_id: int  # -1 = unassigned
    assigned_city_name: str  # "Unassigned" if not placed
    is_established: bool
    turns_to_establish: int = 0
    available_promotions: list[GovernorPromotion] = field(default_factory=list)


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
    city_state_type: str  # "Scientific", "Industrial", "Trade", etc.
    envoys_sent: int  # envoys we've sent
    suzerain_id: int  # player ID of suzerain (-1 = none)
    suzerain_name: str  # "None" or civ name
    can_send_envoy: bool


@dataclass
class EnvoyStatus:
    """Full envoy status for the player."""

    tokens_available: int
    city_states: list[CityStateInfo] = field(default_factory=list)


@dataclass
class BeliefInfo:
    """A pantheon belief available for selection."""

    belief_type: str  # e.g. "BELIEF_DANCE_OF_THE_AURORA"
    name: str
    description: str


@dataclass
class PantheonStatus:
    """Current pantheon status and available beliefs."""

    has_pantheon: bool
    current_belief: str | None  # belief type if has pantheon
    current_belief_name: str | None
    faith_balance: float
    available_beliefs: list[BeliefInfo] = field(default_factory=list)


@dataclass
class UnitUpgradeInfo:
    """Info about a unit's upgrade path."""

    unit_id: int
    current_type: str
    upgrade_type: str  # e.g. "UNIT_ARCHER"
    upgrade_name: str
    gold_cost: int
    can_upgrade: bool
    reason: str = ""  # failure reason if can't upgrade


@dataclass
class DedicationChoice:
    """A dedication/commemoration available for selection."""

    index: int
    name: str  # e.g. "COMMEMORATION_SCIENTIFIC"
    normal_desc: str  # bonus in Normal age
    golden_desc: str  # bonus in Golden/Heroic age
    dark_desc: str  # bonus in Dark age


@dataclass
class DedicationStatus:
    """Current dedication/commemoration state."""

    age_type: str  # "Normal", "Golden", "Dark", "Heroic"
    era: int
    era_score: int
    dark_threshold: int
    golden_threshold: int
    selections_allowed: int
    active: list[str] = field(default_factory=list)
    choices: list[DedicationChoice] = field(default_factory=list)


@dataclass
class DistrictPlacement:
    """A valid tile for placing a district, with adjacency bonuses."""

    x: int
    y: int
    adjacency: dict[str, int]  # yield_type -> bonus (e.g. {"science": 3})
    total_adjacency: int
    terrain_desc: str  # e.g. "Plains Hills"


@dataclass
class WonderPlacement:
    """A valid tile for placing a wonder, ranked by displacement cost."""

    x: int
    y: int
    terrain: str          # e.g. "TERRAIN_GRASS_HILLS"
    feature: str          # e.g. "FEATURE_JUNGLE" or "none"
    has_river: bool
    is_coastal: bool
    resource: str         # e.g. "RESOURCE_IRON" or "none"
    improvement: str      # e.g. "IMPROVEMENT_FARM" or "none"
    displacement_score: int  # 0 = empty bare tile (best), higher = more valuable yields lost


@dataclass
class PurchasableTile:
    """A tile that can be purchased with gold."""

    x: int
    y: int
    cost: int
    terrain: str
    resource: str | None
    resource_class: str | None  # "strategic", "luxury", "bonus"


@dataclass
class GreatPersonInfo:
    """Info about an available or claimed Great Person."""

    class_name: str  # e.g. "Great Scientist"
    individual_name: str  # e.g. "Hypatia"
    era_name: str
    cost: int  # great person points needed to recruit
    claimant: str  # civ name or "Unclaimed"
    player_points: int  # our points toward this class
    ability: str = ""  # activation/passive ability description
    gold_cost: int = 0  # gold patronize cost
    faith_cost: int = 0  # faith patronize cost
    can_recruit: bool = False  # have enough GP points
    individual_id: int = 0  # GameInfo index for recruit/patronize actions


@dataclass
class TradeDestination:
    """A valid trade route destination city."""

    city_name: str
    owner_name: str  # civ/city-state name, or "Domestic"
    x: int
    y: int
    is_domestic: bool
    is_city_state: bool = False
    has_quest: bool = False  # city-state wants a trade route
    has_trading_post: bool = False  # established trading post (bonus yields)
    origin_yields: str = ""  # e.g. "Food:3 Prod:2 Gold:4"
    dest_yields: str = ""  # food+prod for domestic routes
    pressure_out: float = 0.0  # our religion → destination
    religion_out: str = ""  # our majority religion name
    pressure_in: float = 0.0  # their religion → our city
    religion_in: str = ""  # destination's majority religion name


@dataclass
class TraderInfo:
    """A trader unit with its route status."""

    unit_id: int
    x: int
    y: int
    has_moves: bool
    on_route: bool = False
    route_origin: str = ""  # origin city name
    route_dest: str = ""  # destination city name
    route_owner: str = ""  # civ/city-state name
    is_domestic: bool = False
    origin_yields: str = ""  # e.g. "Food:3 Prod:2 Gold:4"
    dest_yields: str = ""
    pressure_out: float = 0.0  # our religion → destination
    religion_out: str = ""
    pressure_in: float = 0.0  # their religion → our city
    religion_in: str = ""
    has_quest: bool = False
    is_city_state: bool = False


@dataclass
class TradeRouteStatus:
    """Trade route capacity and trader status."""

    capacity: int
    active_count: int
    traders: list[TraderInfo] = field(default_factory=list)
    ghost_count: int = 0  # ghost route records inflating engine count


@dataclass
class CongressResolution:
    """A resolution to vote on or that has been passed."""

    resolution_type: str  # e.g. "WC_RES_MERCENARY_COMPANIES"
    resolution_hash: int  # e.g. -1027166762
    name: str  # e.g. "Mercenary Companies"
    target_kind: str  # e.g. "YIELD", "RELIGION", "PLAYER"
    effect_a: str  # description of option A
    effect_b: str  # description of option B
    possible_targets: list[str]  # ["Production", "Gold", ...] or player names etc.
    is_passed: bool = False
    winner: int = -1  # 0=A won, 1=B won
    chosen_thing: str = ""  # target that was chosen


@dataclass
class CongressProposal:
    """A discussion proposal to vote on."""

    sender_id: int
    sender_name: str
    target_id: int
    target_name: str
    proposal_type: int
    description: str


@dataclass
class WorldCongressStatus:
    """Full World Congress state."""

    is_in_session: bool
    turns_until_next: int
    favor: int
    max_votes: int
    favor_costs: list[int]  # [0, 10, 30, 60, 100, 150]
    resolutions: list[CongressResolution]
    proposals: list[CongressProposal]


# --- Scattered dataclasses (originally defined mid-file near their builders) ---


@dataclass
class GameOverStatus:
    is_game_over: bool
    is_defeat: bool  # True = we lost, False = we won
    winner_name: str
    victory_type: str  # e.g. "VICTORY_RELIGIOUS", "VICTORY_SCIENCE"
    player_alive: bool


@dataclass
class ReligionBeliefOption:
    """A belief available for selection when founding/enhancing a religion."""

    belief_class: str  # BELIEF_CLASS_FOLLOWER, BELIEF_CLASS_FOUNDER, etc.
    belief_type: str  # e.g. BELIEF_WORK_ETHIC
    name: str
    description: str


@dataclass
class ReligionFoundingStatus:
    """Religion founding status and available options."""

    has_religion: bool
    religion_type: str | None  # e.g. RELIGION_HINDUISM
    religion_name: str | None
    pantheon_index: int
    faith_balance: float
    available_religions: list[tuple[str, str]] = field(
        default_factory=list
    )  # (type, name) pairs
    beliefs_by_class: dict[str, list[ReligionBeliefOption]] = field(
        default_factory=dict
    )


@dataclass
class CityReligionInfo:
    player_id: int
    civ_name: str
    city_name: str
    majority_religion: str  # display name or "none"
    population: int
    followers: dict[str, int]  # religion_name -> follower count


@dataclass
class ReligionSummary:
    religion_name: str
    civs_with_majority: int
    total_majors: int


@dataclass
class ReligionStatus:
    cities: list[CityReligionInfo]
    summary: list[ReligionSummary]
