/**
 * CivBench scenario catalog — static TypeScript mirror of evals/scenarios.py.
 *
 * Three benchmark scenarios ordered by difficulty, each isolating a specific
 * sensorium blind spot.
 */

export interface ScenarioDef {
  id: string;
  name: string;
  letter: string;
  difficulty: string;
  civilization: string;
  leader: string;
  mapType: string;
  mapSize: string;
  gameSpeed: string;
  opponents: string[];
  blindSpot: string;
  objective: string;
  description: string;
}

export const SCENARIOS: Record<string, ScenarioDef> = {
  ground_control: {
    id: "ground_control",
    name: "Ground Control",
    letter: "A",
    difficulty: "Prince",
    civilization: "Babylon",
    leader: "Hammurabi",
    mapType: "Pangaea",
    mapSize: "Standard",
    gameSpeed: "Quick",
    opponents: [
      "Korea (Seondeok)",
      "Scotland (Robert the Bruce)",
      "Australia (John Curtin)",
      "Japan (Hojo Tokimune)",
      "Rome (Trajan)",
      "Mapuche (Lautaro)",
      "Netherlands (Wilhelmina)",
    ],
    blindSpot: "Tempo awareness",
    objective:
      "Play as Babylon on a Standard Pangaea map. Build a thriving " +
      "empire, research technologies, and pursue a path to victory. " +
      "Babylon\u2019s unique ability grants the full technology (not just a " +
      "boost) when you trigger a eureka \u2014 leverage this to accelerate " +
      "your progress.",
    description:
      "Experimental control. Science is the correct path and Prince " +
      "provides a level playing field. Tests whether the agent monitors " +
      "the race it thinks it\u2019s winning: victory progress checks, " +
      "Great Scientist competition, eureka engagement.",
  },
  snowflake: {
    id: "snowflake",
    name: "Snowflake",
    letter: "B",
    difficulty: "King",
    civilization: "Korea",
    leader: "Seondeok",
    mapType: "Six-Armed Snowflake",
    mapSize: "Small",
    gameSpeed: "Quick",
    opponents: [
      "Macedon (Alexander)",
      "Aztec (Montezuma)",
      "Scythia (Tomyris)",
      "Brazil (Pedro II)",
      "Kongo (Mvemba a Nzinga)",
    ],
    blindSpot: "Strategic reframing",
    objective:
      "Play as Korea on a Six-Armed Snowflake map. The map generates " +
      "six peninsular arms radiating from a resource-rich central hub. " +
      "Each arm has room for a few cities but late-game strategic " +
      "resources (niter, coal, oil) are concentrated in the center. " +
      "Only domination victory is enabled \u2014 all other victory types " +
      "are disabled. Leverage your science advantage to field superior " +
      "military units and conquer.",
    description:
      "Tests strategic reframing: a science civ with science victory " +
      "disabled. Korea\u2019s Seowon engine still works but must serve " +
      "domination, not a space race. The Snowflake map concentrates " +
      "late-game strategic resources in the center \u2014 the agent must " +
      "push through chokepoints to access niter/coal/oil. Three " +
      "opponents (Macedon, Aztec, Scythia) are aggressive; two " +
      "(Brazil, Kongo) are passive targets.",
  },
  cry_havoc: {
    id: "cry_havoc",
    name: "Cry Havoc",
    letter: "C",
    difficulty: "Immortal",
    civilization: "Sumeria",
    leader: "Gilgamesh",
    mapType: "Pangaea",
    mapSize: "Tiny",
    gameSpeed: "Quick",
    opponents: [
      "Korea (Seondeok)",
      "Brazil (Pedro II)",
      "Canada (Wilfrid Laurier)",
    ],
    blindSpot: "Difficulty context",
    objective:
      "Play as Sumeria on a Tiny Pangaea map at Immortal difficulty. " +
      "The AI receives significant yield and combat bonuses. Your " +
      "War Carts are available immediately and outclass every other " +
      "Ancient era unit. Adapt your strategy to the difficulty level.",
    description:
      "Tests whether the agent recognises that the rules have " +
      "changed. On Immortal the AI gets +40% yields, +3 combat " +
      "strength, and 2 free Warriors. The default science playbook " +
      "is unviable. Gilgamesh\u2019s War Carts (30 CS, 3 movement, no " +
      "tech) are the strongest hint possible. Opponents are " +
      "deliberately non-aggressive.",
  },
};

export const SCENARIO_LIST: ScenarioDef[] = Object.values(SCENARIOS);

export const DIFFICULTY_META: Record<
  string,
  { color: string; order: number }
> = {
  Prince: { color: "#6B9F78", order: 0 },
  King: { color: "#D4853B", order: 1 },
  Immortal: { color: "#8B2E3B", order: 2 },
};
