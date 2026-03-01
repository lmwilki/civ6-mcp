"""CivBench scenario definitions.

Five benchmark scenarios ordered by difficulty, each isolating a specific
Sensorium Effect blind spot. See docs/paper/scenario-spec.md for rationale.

Each scenario specifies a single starting save file, turn budget, and
evaluation context. One save per scenario ensures comparison clarity —
all models play the exact same map. Scenarios are converted to Inspect
Sample objects at task launch.
"""

from dataclasses import dataclass
from pathlib import Path

SAVES_DIR = Path(__file__).parent / "saves"


@dataclass(frozen=True)
class Scenario:
    """A single benchmark scenario."""

    scenario_id: str
    name: str  # human-readable, e.g. "Ground Control"
    save_file: str  # single save for comparison clarity
    turn_limit: int  # Quick speed turn budget
    difficulty: str  # Warlord/Prince/King/Emperor/Immortal
    map_type: str  # e.g. "Pangaea, Standard"
    civilization: str  # e.g. "Babylon (Hammurabi)"
    game_speed: str = "Quick"  # Online/Quick/Standard/Epic/Marathon
    opponents: tuple[str, ...] = ()
    blind_spot: str = ""  # what the scenario tests (not shown to agent)
    objective: str = ""  # shown to agent as user message
    description: str = ""  # longer context for eval logs

    def save_path(self) -> Path:
        return SAVES_DIR / self.save_file


# ---------------------------------------------------------------------------
# Scenario catalogue — ordered by difficulty
# ---------------------------------------------------------------------------

SCENARIOS: dict[str, Scenario] = {}


def _register(s: Scenario) -> Scenario:
    SCENARIOS[s.scenario_id] = s
    return s


# --- A: Ground Control (Warlord) -------------------------------------------

ground_control = _register(
    Scenario(
        scenario_id="ground_control",
        name="Ground Control",
        save_file="GROUND_CONTROL_SA.Civ6Save",
        turn_limit=350,
        difficulty="Warlord",
        map_type="Pangaea, Standard",
        civilization="Babylon (Hammurabi)",
        opponents=(
            "Korea (Seondeok)",
            "Scotland (Robert the Bruce)",
            "Australia (John Curtin)",
            "Japan (Hojo Tokimune)",
            "Rome (Trajan)",
            "Mapuche (Lautaro)",
            "Netherlands (Wilhelmina)",
        ),
        blind_spot="Tempo awareness",
        objective=(
            "Play as Babylon on a Standard Pangaea map. Build a thriving "
            "empire, research technologies, and pursue a path to victory. "
            "Babylon's unique ability grants the full technology (not just a "
            "boost) when you trigger a eureka — leverage this to accelerate "
            "your progress."
        ),
        description=(
            "Experimental control. Science is the correct path and Warlord "
            "removes survival pressure. Tests whether the agent monitors "
            "the race it thinks it's winning: victory progress checks, "
            "Great Scientist competition, eureka engagement."
        ),
    )
)

# --- B: Empty Canvas (Prince) ----------------------------------------------

empty_canvas = _register(
    Scenario(
        scenario_id="empty_canvas",
        name="Empty Canvas",
        save_file="EMPTY_CANVAS_SB.Civ6Save",
        turn_limit=350,
        difficulty="Prince",
        map_type="Pangaea, Small",
        civilization="Kongo (Mvemba a Nzinga)",
        opponents=(
            "Greece (Pericles)",
            "Brazil (Pedro II)",
            "Babylon (Hammurabi)",
            "Rome (Trajan)",
            "France (Catherine de Medici - Magnificence)",
        ),
        blind_spot="Own civ kit",
        objective=(
            "Play as Kongo on a Small Pangaea map. Develop your "
            "civilisation and work toward the victory condition that best "
            "suits your unique abilities. Note: Kongo cannot found a "
            "religion."
        ),
        description=(
            "Tests civ kit awareness. Kongo has zero science bonuses but "
            "the strongest cultural kit in the game: 2x Great Work slots, "
            "+50% Great Writer/Artist/Musician/Merchant points, Mbanza "
            "district. Science victory is possible but actively "
            "disadvantaged. Cultural victory is overwhelmingly signposted."
        ),
    )
)

# --- C: Deus Vult (King) ---------------------------------------------------

deus_vult = _register(
    Scenario(
        scenario_id="deus_vult",
        name="Deus Vult",
        save_file="DEUS_VULT_SC.Civ6Save",
        turn_limit=350,
        difficulty="King",
        map_type="Pangaea, Small",
        civilization="Germany (Frederick Barbarossa)",
        opponents=(
            "Russia (Peter)",
            "Spain (Philip II)",
            "Arabia (Saladin - Vizier)",
            "Rome (Trajan)",
            "Japan (Hojo Tokimune)",
        ),
        blind_spot="Invisible rival victory",
        objective=(
            "Play as Germany on a Small Pangaea map. Build a strong "
            "empire with a focus on industrial and military development. "
            "Monitor the global situation and respond to threats as they "
            "emerge."
        ),
        description=(
            "Tests whether the agent sees what it doesn't query. Germany "
            "has zero religious affinity. Three opponents (Russia, Spain, "
            "Arabia) are aggressive religious civs that will flood the map "
            "with missionaries. Religious victory requires majority in ALL "
            "civs — the agent is a target whether it engages or not. "
            "Historical call frequency for get_religion_spread: near zero."
        ),
    )
)

# --- D: Snowflake (Emperor) ------------------------------------------------

snowflake = _register(
    Scenario(
        scenario_id="snowflake",
        name="Snowflake",
        save_file="SNOWFLAKE_SD.Civ6Save",
        turn_limit=350,
        difficulty="Emperor",
        map_type="Six-Armed Snowflake, Small",
        civilization="Korea (Seondeok)",
        opponents=(
            "Macedon (Alexander)",
            "Zulu (Shaka)",
            "Aztec (Montezuma)",
            "Persia (Cyrus)",
            "Scythia (Tomyris)",
        ),
        blind_spot="Military threats",
        objective=(
            "Play as Korea on a Six-Armed Snowflake map. The map generates "
            "peninsular arms radiating from a central hub — expect "
            "chokepoints. Build your science engine while maintaining "
            "adequate defences against aggressive neighbours."
        ),
        description=(
            "Deliberately adversarial. All five opponents are "
            "domination-oriented. Korea is a pure science civ with no "
            "military bonuses. Emperor gives AI +20% yields and +2 combat "
            "strength. Tests reactive military decision-making — a missed "
            "get_map_area scan means an undetected army at the chokepoint."
        ),
    )
)

# --- E: Cry Havoc (Immortal) -----------------------------------------------

cry_havoc = _register(
    Scenario(
        scenario_id="cry_havoc",
        name="Cry Havoc",
        save_file="CRY_HAVOC_SE.Civ6Save",
        turn_limit=350,
        difficulty="Immortal",
        map_type="Pangaea, Tiny",
        civilization="Sumeria (Gilgamesh)",
        opponents=(
            "Korea (Seondeok)",
            "Brazil (Pedro II)",
            "Canada (Wilfrid Laurier)",
        ),
        blind_spot="Difficulty context",
        objective=(
            "Play as Sumeria on a Tiny Pangaea map at Immortal difficulty. "
            "The AI receives significant yield and combat bonuses. Your "
            "War Carts are available immediately and outclass every other "
            "Ancient era unit. Adapt your strategy to the difficulty level."
        ),
        description=(
            "Tests whether the agent recognises that the rules have "
            "changed. On Immortal the AI gets +40% yields, +3 combat "
            "strength, and 2 free Warriors. The default science playbook "
            "is unviable. Gilgamesh's War Carts (30 CS, 3 movement, no "
            "tech) are the strongest hint possible. Opponents are "
            "deliberately non-aggressive."
        ),
    )
)
