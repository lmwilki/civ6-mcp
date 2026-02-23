// === Display helpers ===

/** Strip Civ 6 prefixes and title-case: TECH_POTTERY → "Pottery" */
export function cleanCivName(s: string): string {
  return s
    .replace(/^(GOVERNMENT_|ERA_|TECH_|CIVIC_|BELIEF_|RELIGION_|POLICY_|BUILDING_|UNIT_|DISTRICT_|PROJECT_|GREAT_PERSON_CLASS_)/, "")
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase())
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
}

export const DIPLO_STATE_COLORS: Record<number, string> = {
  0: "text-blue-600",
  1: "text-patina",
  2: "text-marble-600",
  3: "text-amber-600",
  4: "text-orange-600",
  5: "text-terracotta",
  6: "text-red-700 font-semibold",
}

// === Sub-types ===

export interface DiploState {
  state: number
  alliance: string | null
  alliance_level: number
  grievances: number
}

export interface GovernorEntry {
  type: string
  city: string
  established: boolean
  promotions: string[]
}

export interface TradeRouteSummary {
  capacity: number
  active: number
  domestic: number
  international: number
}

export interface Reflections {
  tactical: string
  strategic: string
  tooling: string
  planning: string
  hypothesis: string
}

// === Raw JSONL row types (1:1 with disk format) ===

export interface PlayerRow {
  v: number
  turn: number
  game: string
  timestamp: string
  pid: number
  civ: string
  leader: string
  is_agent: boolean
  // Score & yields
  score: number
  cities: number
  pop: number
  science: number
  culture: number
  gold: number
  gold_per_turn: number
  faith: number
  faith_per_turn: number
  favor: number
  favor_per_turn: number
  // Military
  military: number
  units_total: number
  units_military: number
  units_civilian: number
  units_support: number
  unit_composition: Record<string, number>
  // Progress
  techs_completed: number
  civics_completed: number
  techs: string[]
  civics: string[]
  current_research: string
  current_civic: string
  // Infrastructure
  districts: number
  wonders: number
  great_works: number
  territory: number
  improvements: number
  // Governance
  era: string
  era_score: number
  age: string
  government: string
  policies: string[]
  pantheon: string
  religion: string
  religion_beliefs: string[]
  // Victory
  sci_vp: number
  diplo_vp: number
  tourism: number
  staycationers: number
  religion_cities: number
  // Resources
  stockpiles: Record<string, number>
  luxuries: Record<string, number>
  exploration_pct: number
  // Agent-only (present when is_agent=true)
  diplo_states?: Record<string, DiploState>
  suzerainties?: number
  envoys_available?: number
  envoys_sent?: Record<string, number>
  gp_points?: Record<string, number>
  governors?: GovernorEntry[]
  trade_routes?: TradeRouteSummary
  reflections?: Reflections
  agent_client?: string
  agent_client_ver?: string
  agent_model?: string
}

/** Numeric fields on PlayerRow suitable for sparklines / charts */
export type NumericPlayerField = Exclude<{
  [K in keyof PlayerRow]: PlayerRow[K] extends number ? K : never
}[keyof PlayerRow], undefined>

export interface CityRow {
  v: number
  turn: number
  game: string
  pid: number
  city_id: number
  city: string
  pop: number
  food: number
  production: number
  gold: number
  science: number
  culture: number
  faith: number
  housing: number
  amenities: number
  amenities_needed: number
  districts: string // comma-separated short names
  producing: string
  loyalty: number
  loyalty_per_turn: number
}

// === Grouped view (client-side computed) ===

export interface TurnData {
  turn: number
  timestamp: string
  agent: PlayerRow
  rivals: PlayerRow[]
  agentCities: CityRow[]
  allCities: CityRow[]
}

export interface GameOutcome {
  result: "victory" | "defeat"
  winnerCiv: string
  winnerLeader: string
  victoryType: string
  turn: number
  playerAlive: boolean
}

export interface DiaryFile {
  filename: string
  label: string
  count: number
  hasCities: boolean
  leader?: string
  status?: "live" | "completed"
  outcome?: GameOutcome | null
}
