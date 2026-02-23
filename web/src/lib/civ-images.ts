import manifest from "./image-manifest.json"

const leaders = manifest.leaders as Record<string, string>
const civs = manifest.civs as Record<string, string>

/** Try exact key, then strip/add trailing 's' (game uses "Ottomans", manifest uses "Ottoman"). */
function fuzzyLookup(map: Record<string, string>, key: string): string | undefined {
  return map[key] ?? map[key.replace(/s$/, "")] ?? map[key + "s"]
}

/** Get the path to a leader's portrait image, or null if not available. */
export function getLeaderPortrait(leader: string): string | null {
  const file = fuzzyLookup(leaders, leader)
  return file ? `/images/leaders/${file}` : null
}

/** Get the path to a civilization's symbol image, or null if not available. */
export function getCivSymbol(civName: string): string | null {
  const file = fuzzyLookup(civs, civName)
  return file ? `/images/civs/${file}` : null
}
