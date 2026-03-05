"""CivBench scenario definitions.

Three benchmark scenarios ordered by difficulty, each isolating a specific
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
    map_type: str  # e.g. "Pangaea", "Six-Armed Snowflake"
    map_size: str  # e.g. "Standard", "Small", "Tiny"
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


# --- A: Ground Control (Prince) --------------------------------------------

ground_control = _register(
    Scenario(
        scenario_id="ground_control",
        name="Ground Control",
        save_file="0A_GROUND_CONTROL.Civ6Save",
        turn_limit=330,
        difficulty="Prince",
        map_type="Pangaea",
        map_size="Standard",
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
            "Experimental control. Science is the correct path and Prince "
            "provides a level playing field. Tests whether the agent monitors "
            "the race it thinks it's winning: victory progress checks, "
            "Great Scientist competition, eureka engagement."
        ),
    )
)

# --- B: Snowflake (King, Domination only) ----------------------------------

snowflake = _register(
    Scenario(
        scenario_id="snowflake",
        name="Snowflake",
        save_file="0B_SNOWFLAKE.Civ6Save",
        turn_limit=330,
        difficulty="King",
        map_type="Six-Armed Snowflake",
        map_size="Small",
        civilization="Korea (Seondeok)",
        opponents=(
            "Macedon (Alexander)",
            "Aztec (Montezuma)",
            "Scythia (Tomyris)",
            "Brazil (Pedro II)",
            "Kongo (Mvemba a Nzinga)",
        ),
        blind_spot="Strategic reframing",
        objective=(
            "Play as Korea on a Six-Armed Snowflake map. The map generates "
            "six peninsular arms radiating from a resource-rich central hub. "
            "Each arm has room for a few cities but late-game strategic "
            "resources (niter, coal, oil) are concentrated in the center. "
            "Only domination victory is enabled — all other victory types "
            "are disabled. Leverage your science advantage to field superior "
            "military units and conquer."
        ),
        description=(
            "Tests strategic reframing: a science civ with science victory "
            "disabled. Korea's Seowon engine still works but must serve "
            "domination, not a space race. The Snowflake map concentrates "
            "late-game strategic resources in the center — the agent must "
            "push through chokepoints to access niter/coal/oil. Three "
            "opponents (Macedon, Aztec, Scythia) are aggressive and will "
            "contest the center; two (Brazil, Kongo) are passive targets. "
            "King difficulty keeps survival manageable so the variable "
            "under test is strategic adaptation, not raw difficulty."
        ),
    )
)

# --- C: Cry Havoc (Immortal) -----------------------------------------------

cry_havoc = _register(
    Scenario(
        scenario_id="cry_havoc",
        name="Cry Havoc",
        save_file="0C_CRY_HAVOC.Civ6Save",
        turn_limit=330,
        difficulty="Immortal",
        map_type="Pangaea",
        map_size="Tiny",
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
