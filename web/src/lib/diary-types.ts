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
}

export interface DiaryReflections {
  tactical: string
  strategic: string
  tooling: string
  planning: string
  hypothesis: string
}

export interface DiaryEntry {
  turn: number
  civ: string
  timestamp: string
  score: DiaryScore
  reflections: DiaryReflections
}

export interface DiaryFile {
  filename: string
  label: string
  count: number
}
