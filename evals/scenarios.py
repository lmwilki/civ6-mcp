"""CivBench scenario definitions.

Each scenario specifies a starting save file, turn budget, and evaluation
context. Scenarios are converted to Inspect `Sample` objects at task launch.
"""

from dataclasses import dataclass
from pathlib import Path

SAVES_DIR = Path(__file__).parent / "saves"


@dataclass(frozen=True)
class Scenario:
    """A single benchmark scenario."""

    scenario_id: str
    save_file: str  # filename relative to evals/saves/
    turn_limit: int
    difficulty: str  # Prince, King, Emperor, etc.
    map_type: str
    civilization: str
    objective: str  # short description shown to the agent
    description: str  # longer description for eval logs

    @property
    def save_path(self) -> Path:
        return SAVES_DIR / self.save_file


# ---------------------------------------------------------------------------
# Initial scenario catalogue
# ---------------------------------------------------------------------------

SCENARIOS: dict[str, Scenario] = {}


def _register(s: Scenario) -> Scenario:
    SCENARIOS[s.scenario_id] = s
    return s


early_game_50 = _register(
    Scenario(
        scenario_id="early_game_50",
        save_file="early_game_50.Civ6Save",
        turn_limit=50,
        difficulty="Prince",
        map_type="Pangaea",
        civilization="Any",
        objective=(
            "Play 50 turns from the Ancient Era start. Expand your empire, "
            "establish economy, explore the map, and build a military."
        ),
        description=(
            "Standard Pangaea start on Prince difficulty. Tests fundamental "
            "4X capabilities: exploration, expansion, exploitation, and "
            "extermination. No specific victory push — measures general "
            "competence in the opening phase."
        ),
    )
)

mid_game_100 = _register(
    Scenario(
        scenario_id="mid_game_100",
        save_file="mid_game_100.Civ6Save",
        turn_limit=100,
        difficulty="Prince",
        map_type="Pangaea",
        civilization="Any",
        objective=(
            "Play 100 turns from the Ancient Era start. Build a thriving "
            "empire with multiple cities, districts, and a coherent "
            "strategy toward a victory condition."
        ),
        description=(
            "Extended Pangaea game on Prince. Tests sustained strategic "
            "reasoning: district placement, tech/civic sequencing, trade "
            "routes, diplomacy, and mid-game military decisions. Long enough "
            "to reveal strategic coherence or drift."
        ),
    )
)

crisis_response = _register(
    Scenario(
        scenario_id="crisis_response",
        save_file="crisis_response.Civ6Save",
        turn_limit=30,
        difficulty="King",
        map_type="Pangaea",
        civilization="Any",
        objective=(
            "Survive and stabilize. Multiple barbarian camps threaten your "
            "cities. Defend your territory, eliminate threats, and resume "
            "economic development."
        ),
        description=(
            "Mid-game save on King difficulty with active barbarian threat "
            "near player cities. Tests reactive military decision-making, "
            "threat prioritization, and recovery under pressure. Short "
            "turn budget forces efficient action."
        ),
    )
)
