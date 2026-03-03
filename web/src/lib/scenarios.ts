/**
 * CivBench scenario catalog — static TypeScript mirror of evals/scenarios.py.
 *
 * Five benchmark scenarios ordered by difficulty, each isolating a specific
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
    difficulty: "Warlord",
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
      "Experimental control. Science is the correct path and Warlord " +
      "removes survival pressure. Tests whether the agent monitors " +
      "the race it thinks it\u2019s winning: victory progress checks, " +
      "Great Scientist competition, eureka engagement.",
  },
  empty_canvas: {
    id: "empty_canvas",
    name: "Empty Canvas",
    letter: "B",
    difficulty: "Prince",
    civilization: "Kongo",
    leader: "Mvemba a Nzinga",
    mapType: "Pangaea",
    mapSize: "Small",
    gameSpeed: "Quick",
    opponents: [
      "Greece (Pericles)",
      "Brazil (Pedro II)",
      "Babylon (Hammurabi)",
      "Rome (Trajan)",
      "France (Catherine de Medici - Magnificence)",
    ],
    blindSpot: "Own civ kit",
    objective:
      "Play as Kongo on a Small Pangaea map. Develop your " +
      "civilisation and work toward the victory condition that best " +
      "suits your unique abilities. Note: Kongo cannot found a religion.",
    description:
      "Tests civ kit awareness. Kongo has zero science bonuses but " +
      "the strongest cultural kit in the game: 2\u00d7 Great Work slots, " +
      "+50% Great Writer/Artist/Musician/Merchant points, Mbanza " +
      "district. Science victory is possible but actively " +
      "disadvantaged. Cultural victory is overwhelmingly signposted.",
  },
  deus_vult: {
    id: "deus_vult",
    name: "Deus Vult",
    letter: "C",
    difficulty: "King",
    civilization: "Germany",
    leader: "Frederick Barbarossa",
    mapType: "Pangaea",
    mapSize: "Small",
    gameSpeed: "Quick",
    opponents: [
      "Russia (Peter)",
      "Spain (Philip II)",
      "Arabia (Saladin - Vizier)",
      "Rome (Trajan)",
      "Japan (Hojo Tokimune)",
    ],
    blindSpot: "Invisible rival victory",
    objective:
      "Play as Germany on a Small Pangaea map. Build a strong " +
      "empire with a focus on industrial and military development. " +
      "Monitor the global situation and respond to threats as they emerge.",
    description:
      "Tests whether the agent sees what it doesn\u2019t query. Germany " +
      "has zero religious affinity. Three opponents (Russia, Spain, " +
      "Arabia) are aggressive religious civs that will flood the map " +
      "with missionaries. Religious victory requires majority in ALL " +
      "civs \u2014 the agent is a target whether it engages or not.",
  },
  snowflake: {
    id: "snowflake",
    name: "Snowflake",
    letter: "D",
    difficulty: "Emperor",
    civilization: "Korea",
    leader: "Seondeok",
    mapType: "Six-Armed Snowflake",
    mapSize: "Small",
    gameSpeed: "Quick",
    opponents: [
      "Macedon (Alexander)",
      "Zulu (Shaka)",
      "Aztec (Montezuma)",
      "Persia (Cyrus)",
      "Scythia (Tomyris)",
    ],
    blindSpot: "Military threats",
    objective:
      "Play as Korea on a Six-Armed Snowflake map. The map generates " +
      "peninsular arms radiating from a central hub \u2014 expect " +
      "chokepoints. Build your science engine while maintaining " +
      "adequate defences against aggressive neighbours.",
    description:
      "Deliberately adversarial. All five opponents are " +
      "domination-oriented. Korea is a pure science civ with no " +
      "military bonuses. Emperor gives AI +20% yields and +2 combat " +
      "strength. Tests reactive military decision-making \u2014 a missed " +
      "scan means an undetected army at the chokepoint.",
  },
  cry_havoc: {
    id: "cry_havoc",
    name: "Cry Havoc",
    letter: "E",
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
  Warlord: { color: "#6B9F78", order: 0 },
  Prince: { color: "#C4A84D", order: 1 },
  King: { color: "#D4853B", order: 2 },
  Emperor: { color: "#C0503A", order: 3 },
  Immortal: { color: "#8B2E3B", order: 4 },
};
