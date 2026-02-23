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

// Per-civ colors now live in civ-registry.ts — re-exported here for compatibility
export { getCivColors } from "./civ-registry"
