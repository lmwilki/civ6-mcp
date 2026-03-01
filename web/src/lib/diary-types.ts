// === Display helpers ===

/** Strip Civ 6 prefixes and title-case: TECH_POTTERY → "Pottery" */
export function cleanCivName(s: string): string {
  return s
    .replace(
      /^(CIVILIZATION_|GOVERNMENT_|ERA_|TECH_|CIVIC_|BELIEF_|RELIGION_|POLICY_|BUILDING_|UNIT_|DISTRICT_|PROJECT_|GREAT_PERSON_CLASS_)/,
      "",
    )
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

// === Diplomacy state mapping ===

export const DIPLO_STATE_NAMES: Record<number, string> = {
  0: "Allied",
  1: "Friendly",
  2: "Neutral",
  3: "Unfriendly",
  4: "Denounced",
  5: "Hostile",
  6: "War",
};

export const DIPLO_STATE_COLORS: Record<number, string> = {
  0: "text-blue-600",
  1: "text-patina",
  2: "text-marble-600",
  3: "text-amber-600",
  4: "text-orange-600",
  5: "text-terracotta",
  6: "text-red-700 font-semibold",
};

// === Sub-types ===

export interface DiploState {
  state: number;
  alliance: string | null;
  alliance_level: number;
  grievances: number;
}

export interface GovernorEntry {
  type: string;
  city: string;
  established: boolean;
  promotions: string[];
}

export interface TradeRouteSummary {
  capacity: number;
  active: number;
  domestic: number;
  international: number;
}

export interface Reflections {
  tactical: string;
  strategic: string;
  tooling: string;
  planning: string;
  hypothesis: string;
}

// === Raw JSONL row types (1:1 with disk format) ===

export interface PlayerRow {
  v: number;
  turn: number;
  game: string;
  timestamp: string;
  pid: number;
  civ: string;
  leader: string;
  is_agent: boolean;
  // Score & yields
  score: number;
  cities: number;
  pop: number;
  science: number;
  culture: number;
  gold: number;
  gold_per_turn: number;
  faith: number;
  faith_per_turn: number;
  favor: number;
  favor_per_turn: number;
  // Military
  military: number;
  units_total: number;
  units_military: number;
  units_civilian: number;
  units_support: number;
  unit_composition: Record<string, number>;
  // Progress
  techs_completed: number;
  civics_completed: number;
  techs: string[];
  civics: string[];
  current_research: string;
  current_civic: string;
  // Infrastructure
  districts: number;
  wonders: number;
  great_works: number;
  territory: number;
  improvements: number;
  // Governance
  era: string;
  era_score: number;
  age: string;
  government: string;
  policies: string[];
  pantheon: string;
  religion: string;
  religion_beliefs: string[];
  // Victory
  sci_vp: number;
  diplo_vp: number;
  tourism: number;
  staycationers: number;
  religion_cities: number;
  // Resources
  stockpiles: Record<string, number>;
  luxuries: Record<string, number>;
  exploration_pct: number;
  // Agent-only (present when is_agent=true)
  diplo_states?: Record<string, DiploState>;
  suzerainties?: number;
  envoys_available?: number;
  envoys_sent?: Record<string, number>;
  gp_points?: Record<string, number>;
  governors?: GovernorEntry[];
  trade_routes?: TradeRouteSummary;
  reflections?: Reflections;
  agent_client?: string;
  agent_client_ver?: string;
  agent_model?: string;
}

/** Numeric fields on PlayerRow suitable for sparklines / charts */
export type NumericPlayerField = Exclude<
  {
    [K in keyof PlayerRow]: PlayerRow[K] extends number ? K : never;
  }[keyof PlayerRow],
  undefined
>;

/** Extended field type for sparklines — includes synthetic spatial metrics */
export type SparklineField =
  | NumericPlayerField
  | "spatial_tiles"
  | "spatial_actions"
  | "spatial_cumulative";

export interface CityRow {
  v: number;
  turn: number;
  game: string;
  pid: number;
  city_id: number;
  city: string;
  pop: number;
  food: number;
  production: number;
  gold: number;
  science: number;
  culture: number;
  faith: number;
  housing: number;
  amenities: number;
  amenities_needed: number;
  districts: string; // comma-separated short names
  producing: string;
  loyalty: number;
  loyalty_per_turn: number;
}

// === Precomputed sparkline series (from games doc) ===

export interface TurnSeriesPlayer {
  civ: string;
  leader: string;
  is_agent: boolean;
  metrics: Record<string, number[]>;
}

export interface TurnSeries {
  turns: number[];
  players: Record<string, TurnSeriesPlayer>; // keyed by pid
}

// === Spatial attention (pre-aggregated per turn) ===

export interface SpatialTurn {
  turn: number;
  tiles_observed: number;
  tool_calls: number;
  cumulative_tiles: number;
  total_ms: number;
  by_type: {
    deliberate_scan: number;
    deliberate_action: number;
    survey: number;
    peripheral: number;
    reactive: number;
  };
}

// === Spatial tile map (one blob per game, for hex heatmap) ===

export interface SpatialTile {
  x: number;
  y: number;
  total: number;
  ds: number; // deliberate_scan
  da: number; // deliberate_action
  sv: number; // survey
  pe: number; // peripheral
  re: number; // reactive
  firstTurn: number;
  lastTurn: number;
}

const SPATIAL_TILE_STRIDE = 10;

/** Unpack flat stride-10 tile array into SpatialTile objects */
export function unpackSpatialTiles(flat: number[]): SpatialTile[] {
  const tiles: SpatialTile[] = [];
  for (let i = 0; i < flat.length; i += SPATIAL_TILE_STRIDE) {
    tiles.push({
      x: flat[i],
      y: flat[i + 1],
      total: flat[i + 2],
      ds: flat[i + 3],
      da: flat[i + 4],
      sv: flat[i + 5],
      pe: flat[i + 6],
      re: flat[i + 7],
      firstTurn: flat[i + 8],
      lastTurn: flat[i + 9],
    });
  }
  return tiles;
}

// === Strategic map data (pre-aggregated per game) ===

/** Shape of the Convex mapData document (one per game). */
/** Raw shape from Convex — large arrays stored as JSON strings (Convex 8192 array cap) */
export interface MapDataDoc {
  gridW: number;
  gridH: number;
  terrain: string;
  initialOwners: string;
  initialRoutes?: string;
  initialTurn: number;
  ownerFrames: string;
  cityFrames: string;
  roadFrames: string;
  players: { pid: number; civ: string; csType?: string }[];
  maxTurn: number;
}

export interface MapTile {
  terrain: number;
  feature: number;
  hills: boolean;
  river: boolean;
  coastal: boolean;
  resource: number;
}

export interface MapOwnerChange {
  tileIdx: number;
  owner: number;
}

export interface MapFrame {
  turn: number;
  changes: MapOwnerChange[];
}

export interface MapCitySnapshot {
  x: number;
  y: number;
  pid: number;
  pop: number;
}

export interface MapCityFrame {
  turn: number;
  cities: MapCitySnapshot[];
}

const MAP_TERRAIN_STRIDE = 6;

/** Unpack stride-6 flat terrain array into MapTile objects (row-major) */
export function unpackTerrain(flat: number[]): MapTile[] {
  const tiles: MapTile[] = [];
  for (let i = 0; i < flat.length; i += MAP_TERRAIN_STRIDE) {
    tiles.push({
      terrain: flat[i],
      feature: flat[i + 1],
      hills: flat[i + 2] === 1,
      river: flat[i + 3] === 1,
      coastal: flat[i + 4] === 1,
      resource: flat[i + 5],
    });
  }
  return tiles;
}

/** Unpack packed [turn, count, tileIdx, owner, ...] into MapFrame[] */
export function unpackOwnerFrames(flat: number[]): MapFrame[] {
  const frames: MapFrame[] = [];
  let i = 0;
  while (i < flat.length) {
    const turn = flat[i];
    const count = flat[i + 1];
    i += 2;
    const changes: MapOwnerChange[] = [];
    for (let j = 0; j < count; j++) {
      changes.push({ tileIdx: flat[i], owner: flat[i + 1] });
      i += 2;
    }
    frames.push({ turn, changes });
  }
  return frames;
}

/** Unpack packed [turn, count, x, y, pid, pop, ...] into MapCityFrame[] */
export function unpackCityFrames(flat: number[]): MapCityFrame[] {
  const frames: MapCityFrame[] = [];
  let i = 0;
  while (i < flat.length) {
    const turn = flat[i];
    const count = flat[i + 1];
    i += 2;
    const cities: MapCitySnapshot[] = [];
    for (let j = 0; j < count; j++) {
      cities.push({ x: flat[i], y: flat[i + 1], pid: flat[i + 2], pop: flat[i + 3] });
      i += 4;
    }
    frames.push({ turn, cities });
  }
  return frames;
}

/** Unpack packed road frames — same shape as owner frames [turn, count, tileIdx, routeType, ...] */
export function unpackRoadFrames(flat: number[]): MapFrame[] {
  return unpackOwnerFrames(flat); // Same binary layout
}

// === Grouped view (client-side computed) ===

export interface TurnData {
  turn: number;
  timestamp: string;
  agent: PlayerRow;
  rivals: PlayerRow[];
  agentCities: CityRow[];
  allCities: CityRow[];
}

export interface GameOutcome {
  result: "victory" | "defeat";
  winnerCiv: string;
  winnerLeader: string;
  victoryType: string;
  turn: number;
  playerAlive: boolean;
}

export interface DiaryFile {
  filename: string;
  label: string;
  count: number;
  hasCities: boolean;
  leader?: string;
  status?: "live" | "completed";
  outcome?: GameOutcome | null;
  agentModel?: string;
  lastUpdated?: number;
  score?: number;
}

// === Shared helpers ===

/** diary_india_123.jsonl → india_123 */
export function slugFromFilename(filename: string): string {
  return filename.replace(/^diary_/, "").replace(/\.jsonl$/, "");
}

/** Sort games: live first, then by turn count descending */
export function sortGamesLiveFirst(games: DiaryFile[]): DiaryFile[] {
  return [...games].sort((a, b) => {
    if (a.status === "live" && b.status !== "live") return -1;
    if (b.status === "live" && a.status !== "live") return 1;
    return b.count - a.count;
  });
}

/** Group raw player + city rows into per-turn snapshots */
export function groupTurnData(
  players: PlayerRow[],
  cities: CityRow[],
): TurnData[] {
  const turnMap = new Map<
    number,
    { players: PlayerRow[]; cities: CityRow[] }
  >();

  // Deduplicate players per (turn, pid) — last row wins (handles interrupted writes)
  const deduped = new Map<string, PlayerRow>();
  for (const p of players) {
    deduped.set(`${p.turn}:${p.pid}`, p);
  }
  for (const p of deduped.values()) {
    if (!turnMap.has(p.turn)) turnMap.set(p.turn, { players: [], cities: [] });
    turnMap.get(p.turn)!.players.push(p);
  }
  // Deduplicate cities per (turn, city_id) — last row wins
  const dedupedCities = new Map<string, CityRow>();
  for (const c of cities) {
    dedupedCities.set(`${c.turn}:${c.city_id}`, c);
  }
  for (const c of dedupedCities.values()) {
    if (!turnMap.has(c.turn)) turnMap.set(c.turn, { players: [], cities: [] });
    turnMap.get(c.turn)!.cities.push(c);
  }

  const result: TurnData[] = [];
  for (const [turn, data] of [...turnMap.entries()].sort(([a], [b]) => a - b)) {
    const agent = data.players.find((p) => p.is_agent);
    if (!agent) continue; // skip turns with no agent row
    const rivals = data.players
      .filter((p) => !p.is_agent)
      .sort((a, b) => b.score - a.score);
    const agentCities = data.cities.filter((c) => c.pid === agent.pid);
    result.push({
      turn,
      timestamp: agent.timestamp,
      agent,
      rivals,
      agentCities,
      allCities: data.cities,
    });
  }
  return result;
}
