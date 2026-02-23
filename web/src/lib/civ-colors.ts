/**
 * Civ 6 game-accurate colors sourced from Civ6_ColorAtlas.xml.
 * Uses the "icon/solid" variant — the most recognizable in-game.
 * Light yields (Gold, Faith, Niter) use darkened variants for white-icon contrast.
 */
export const CIV6_COLORS = {
  // Core yields
  science:    "#44B3EA",
  culture:    "#AF59F5",
  gold:       "#CEC255",
  goldDark:   "#67612B",
  faith:      "#6480A0",
  food:       "#82B22C",
  production: "#D38F3D",

  // Military / combat
  military:   "#BC1616",

  // Score / era
  goldMetal:  "#CBB173",
  tourism:    "#B57466",

  // Map / territory
  marine:     "#4D9B93",

  // Population / growth
  growth:     "#788C46",

  // Diplomatic
  favor:      "#1C9FDC",

  // Strategic resources
  horses:     "#8B6914",
  iron:       "#8C8C8C",
  niter:      "#B8A830",
  coal:       "#4A4A4A",
  oil:        "#5C3A1A",
  aluminum:   "#6A9AB0",
  uranium:    "#5DA000",

  // Ages
  golden:     "#CBB173",
  heroic:     "#7032A0",
  dark:       "#982020",
  normal:     "#7A7269",
} as const

/**
 * Per-civilization colors from the game's PlayerColors.xml / PlayerStandardColors.xml.
 * Keyed by display name (as it appears in PlayerRow.civ).
 * Primary = outer/border color, secondary = inner/icon color.
 * For multi-leader civs, uses the default/most common leader.
 */
export const CIV_PLAYER_COLORS: Record<string, { primary: string; secondary: string }> = {
  // Base game
  "America":       { primary: "#012A6C", secondary: "#F9F9F9" },
  "Arabia":        { primary: "#F7D801", secondary: "#156C30" },
  "Aztec":         { primary: "#7DECE3", secondary: "#780001" },
  "Brazil":        { primary: "#61BF22", secondary: "#F7D801" },
  "China":         { primary: "#156C30", secondary: "#F9F9F9" },
  "Egypt":         { primary: "#014F51", secondary: "#EAE19D" },
  "England":       { primary: "#CA1415", secondary: "#F9F9F9" },
  "France":        { primary: "#004FCE", secondary: "#EAE19D" },
  "Germany":       { primary: "#AEAEAE", secondary: "#181818" },
  "Greece":        { primary: "#74A3F3", secondary: "#F9F9F9" },
  "India":         { primary: "#370065", secondary: "#00C09B" },
  "Japan":         { primary: "#F9F9F9", secondary: "#780001" },
  "Kongo":         { primary: "#F7D801", secondary: "#CA1415" },
  "Norway":        { primary: "#012A6C", secondary: "#CA1415" },
  "Rome":          { primary: "#6D00CD", secondary: "#F7D801" },
  "Russia":        { primary: "#F7D801", secondary: "#181818" },
  "Scythia":       { primary: "#FFB23C", secondary: "#780001" },
  "Spain":         { primary: "#CA1415", secondary: "#F7D801" },
  "Sumeria":       { primary: "#012A6C", secondary: "#FF8112" },
  // DLC
  "Australia":     { primary: "#156C30", secondary: "#F7D801" },
  "Macedon":       { primary: "#AEAEAE", secondary: "#F7D801" },
  "Persia":        { primary: "#B780E6", secondary: "#780001" },
  "Nubia":         { primary: "#EAE19D", secondary: "#783D02" },
  "Indonesia":     { primary: "#780001", secondary: "#00C09B" },
  "Khmer":         { primary: "#750073", secondary: "#FF8112" },
  "Poland":        { primary: "#780001", secondary: "#E57574" },
  // Rise and Fall
  "Korea":         { primary: "#CA1415", secondary: "#74A3F3" },
  "Zulu":          { primary: "#783D02", secondary: "#F9F9F9" },
  "Cree":          { primary: "#012A6C", secondary: "#61BF22" },
  "Georgia":       { primary: "#F9F9F9", secondary: "#FF8112" },
  "Mapuche":       { primary: "#004FCE", secondary: "#7DECE3" },
  "Mongolia":      { primary: "#780001", secondary: "#FF8112" },
  "Netherlands":   { primary: "#FF8112", secondary: "#004FCE" },
  "Scotland":      { primary: "#F9F9F9", secondary: "#004FCE" },
  // Gathering Storm
  "Mali":          { primary: "#780001", secondary: "#EAE19D" },
  "Ottoman":       { primary: "#F9F9F9", secondary: "#156C30" },
  "Inca":          { primary: "#783D02", secondary: "#F7D801" },
  "Hungary":       { primary: "#156C30", secondary: "#FF8112" },
  "Maori":         { primary: "#CA1415", secondary: "#7DECE3" },
  "Phoenicia":     { primary: "#6D00CD", secondary: "#74A3F3" },
  "Canada":        { primary: "#F9F9F9", secondary: "#CA1415" },
  "Sweden":        { primary: "#74A3F3", secondary: "#F7D801" },
  // New Frontier Pass
  "Gran Colombia": { primary: "#012A6C", secondary: "#F7D801" },
  "Maya":          { primary: "#74A3F3", secondary: "#014F51" },
  "Ethiopia":      { primary: "#F7D801", secondary: "#156C30" },
  "Gaul":          { primary: "#156C30", secondary: "#7DECE3" },
  "Byzantium":     { primary: "#370065", secondary: "#EAE19D" },
  "Babylon":       { primary: "#74A3F3", secondary: "#012A6C" },
  "Vietnam":       { primary: "#F7D801", secondary: "#750073" },
  "Portugal":      { primary: "#F9F9F9", secondary: "#012A6C" },
}

/**
 * Leader-specific color overrides for multi-leader civilizations.
 * Keyed by leader display name, or "LeaderName|CivName" when the same
 * leader can appear for different civs (e.g. Eleanor of Aquitaine).
 */
const LEADER_COLOR_OVERRIDES: Record<string, { primary: string; secondary: string }> = {
  "Chandragupta":                    { primary: "#00C09B", secondary: "#370065" },
  "Gorgo":                           { primary: "#780001", secondary: "#74DADB" },
  "Eleanor of Aquitaine|England":    { primary: "#E57574", secondary: "#F9F9F9" },
  "Eleanor of Aquitaine|France":     { primary: "#E57574", secondary: "#EAE19D" },
}

/** Deterministic fallback color for unknown civs (hash name into standard palette). */
const FALLBACK_PALETTE = [
  "#E63946", "#457B9D", "#2A9D8F", "#E9C46A",
  "#F4A261", "#264653", "#9B5DE5", "#F15BB5",
]

export function getCivColors(civName: string, leader?: string): { primary: string; secondary: string } {
  if (leader) {
    const specific = LEADER_COLOR_OVERRIDES[`${leader}|${civName}`]
    if (specific) return specific
    const byLeader = LEADER_COLOR_OVERRIDES[leader]
    if (byLeader) return byLeader
  }
  const known = CIV_PLAYER_COLORS[civName]
    ?? CIV_PLAYER_COLORS[civName.replace(/s$/, "")]
    ?? CIV_PLAYER_COLORS[civName + "s"]
  if (known) return known
  // Simple hash for deterministic fallback
  let hash = 0
  for (let i = 0; i < civName.length; i++) {
    hash = ((hash << 5) - hash + civName.charCodeAt(i)) | 0
  }
  const color = FALLBACK_PALETTE[Math.abs(hash) % FALLBACK_PALETTE.length]
  return { primary: color, secondary: "#F9F9F9" }
}
