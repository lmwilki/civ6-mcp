/**
 * Civ 6-inspired terrain color palette for the strategic map view.
 *
 * Terrain type IDs come from GameInfo.Terrains index order in Civ 6.
 * Each base terrain has 3 variants: flat, hills, mountain (stride of 3).
 * 0=GRASS, 1=GRASS_HILLS, 2=GRASS_MOUNTAIN,
 * 3=PLAINS, 4=PLAINS_HILLS, 5=PLAINS_MOUNTAIN,
 * 6=DESERT, 7=DESERT_HILLS, 8=DESERT_MOUNTAIN,
 * 9=TUNDRA, 10=TUNDRA_HILLS, 11=TUNDRA_MOUNTAIN,
 * 12=SNOW, 13=SNOW_HILLS, 14=SNOW_MOUNTAIN,
 * 15=COAST, 16=OCEAN
 */

/** Base terrain colors (flat variants) — hills/mountains use darker shades */
export const TERRAIN_COLORS: Record<number, string> = {
  // Grassland
  0: "#5a8a4a",  // flat
  1: "#4a7a3a",  // hills (darker)
  2: "#6e6e6e",  // mountain
  // Plains
  3: "#9a8a5a",
  4: "#8a7a4a",
  5: "#6e6e6e",
  // Desert
  6: "#c4a94a",
  7: "#b49a3a",
  8: "#6e6e6e",
  // Tundra
  9: "#7a8a7a",
  10: "#6a7a6a",
  11: "#6e6e6e",
  // Snow
  12: "#d0d0d0",
  13: "#b8b8b8",
  14: "#6e6e6e",
  // Water
  15: "#2a6a9c",  // coast
  16: "#1a3a5c",  // ocean
};

/**
 * Feature overlay colors — rendered semi-transparently on top of terrain.
 * Feature IDs from GameInfo.Features index order.
 */
export const FEATURE_OVERLAY_COLORS: Record<number, string> = {
  0: "#2a5a2a",   // FEATURE_FOREST
  1: "#1a4a1a",   // FEATURE_JUNGLE
  2: "#3a6a5a",   // FEATURE_MARSH
  3: "#2a6aaa",   // FEATURE_OASIS
  4: "#aacccc",   // FEATURE_FLOODPLAINS
  5: "#aacccc",   // FEATURE_FLOODPLAINS_GRASSLAND
  6: "#aacccc",   // FEATURE_FLOODPLAINS_PLAINS
  // Ice, reefs, volcanic, etc. — add as needed
};

/** Feature overlay opacity */
export const FEATURE_OVERLAY_ALPHA = 0.35;

/** Road colors by route type */
export const ROAD_COLORS: Record<number, string> = {
  0: "#8a7a5a",   // Ancient road
  1: "#7a6a4a",   // Classical road
  2: "#5a5a5a",   // Industrial railroad
};

/** Unowned territory tint */
export const UNOWNED_COLOR = "transparent";

/** Territory overlay opacity */
export const TERRITORY_ALPHA = 0.30;

/** City marker settings */
export const CITY_MARKER = {
  baseRadius: 2.5,
  popScale: 0.3,  // radius += sqrt(pop) * popScale
  strokeColor: "#ffffff",
  strokeWidth: 1,
};

/** Fog of war color */
export const FOG_COLOR = "rgba(0, 0, 0, 0.6)";

/** Get terrain color for a tile, with fallback */
export function getTerrainColor(terrainId: number): string {
  return TERRAIN_COLORS[terrainId] ?? "#555555";
}

/** Get feature overlay color, or null if no overlay */
export function getFeatureOverlay(featureId: number): string | null {
  if (featureId < 0) return null;
  return FEATURE_OVERLAY_COLORS[featureId] ?? null;
}
