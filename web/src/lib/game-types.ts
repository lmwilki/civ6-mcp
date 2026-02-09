export interface ScoreEntry {
  civ_name: string
  score: number
}

export interface GameOverview {
  turn: number
  player_id: number
  civ_name: string
  leader_name: string
  gold: number
  gold_per_turn: number
  science_yield: number
  culture_yield: number
  faith: number
  current_research: string
  current_civic: string
  num_cities: number
  num_units: number
  score: number
  rankings: ScoreEntry[] | null
}

export interface UnitInfo {
  unit_id: number
  unit_index: number
  name: string
  unit_type: string
  x: number
  y: number
  moves_remaining: number
  max_moves: number
  health: number
  max_health: number
  combat_strength: number
  ranged_strength: number
  build_charges: number
  needs_promotion: boolean
}

export interface CityInfo {
  city_id: number
  name: string
  x: number
  y: number
  population: number
  food: number
  production: number
  gold: number
  science: number
  culture: number
  faith: number
  housing: number
  amenities: number
  turns_to_grow: number
  currently_building: string
  production_turns_left: number
}

export interface TileInfo {
  x: number
  y: number
  terrain: string
  feature: string | null
  resource: string | null
  is_hills: boolean
  is_river: boolean
  is_coastal: boolean
  improvement: string | null
  owner_id: number
  visibility: string
  is_fresh_water: boolean
  yields: number[] | null
  units: string[] | null
  resource_class: string | null
}
