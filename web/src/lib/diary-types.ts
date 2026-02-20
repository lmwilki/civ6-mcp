export interface StockpileEntry {
  amount: number
  per_turn: number
  demand: number
}

export interface DiaryScore {
  total: number
  cities: number
  population?: number
  science: number
  culture: number
  gold: number
  gold_per_turn: number
  faith: number
  favor: number
  exploration_pct: number
  era: string
  era_score: number
  leader_score: number
  stockpiles?: Record<string, StockpileEntry>
}

export interface DiaryReflections {
  tactical: string
  strategic: string
  tooling: string
  planning: string
  hypothesis: string
}

export interface DiaryRival {
  id: number
  name: string
  score: number
  cities: number
  pop: number
  sci: number
  cul: number
  gold: number
  mil: number
  techs: number
  civics: number
  faith: number
  sci_vp: number
  diplo_vp: number
  stockpiles?: Record<string, number>
}

export interface DiaryEntry {
  turn: number
  civ: string
  timestamp: string
  score: DiaryScore
  reflections: DiaryReflections
  rivals?: DiaryRival[]
}

export interface DiaryFile {
  filename: string
  label: string
  count: number
}
