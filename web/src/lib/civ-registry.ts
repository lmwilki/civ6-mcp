/**
 * Unified civ/leader registry — single source of truth for display names,
 * slugs, colors, and image paths across the entire frontend.
 *
 * Replaces the previously separate civ-colors, civ-images, and image-manifest
 * modules. Handles diacritics, plural variants, and leader persona suffixes.
 */

// ─── Types ──────────────────────────────────────────────────────────────────

export interface LeaderEntry {
  /** ASCII display name matching diary/Convex data (e.g. "Ba Trieu"). */
  name: string;
  /** Alternate names the game engine may produce (diacritics, variant spellings). */
  aliases?: string[];
  /** Leader portrait filename in /images/leaders/, or null if unavailable. */
  portrait: string | null;
  /** Color override — replaces civ colors when this leader is active. */
  colors?: { primary: string; secondary: string };
}

export interface CivEntry {
  /** Display name as it appears in diary data and Convex (e.g. "Ottoman"). */
  name: string;
  /** Alternate names that resolve to this civ (e.g. ["Ottomans"]). */
  aliases?: string[];
  /** Lowercase slug from CIVILIZATION_TYPE (e.g. "ottoman"). Used in gameId/file paths. */
  slug: string;
  /** Civ symbol filename in /images/civs/, or null if unavailable. */
  symbol: string | null;
  /** Default colors (primary = outer/border, secondary = inner/icon). */
  colors: { primary: string; secondary: string };
  /** Leaders for this civ. First entry is the default leader. */
  leaders: LeaderEntry[];
}

// ─── Registry Data ──────────────────────────────────────────────────────────

export const CIV_REGISTRY: CivEntry[] = [
  // ── Base game ──
  {
    name: "America",
    slug: "america",
    symbol: "america.webp",
    colors: { primary: "#012A6C", secondary: "#F9F9F9" },
    leaders: [
      { name: "Teddy Roosevelt", portrait: "teddy-roosevelt.webp" },
      { name: "Abraham Lincoln", portrait: "abraham-lincoln.webp" },
    ],
  },
  {
    name: "Arabia",
    slug: "arabia",
    symbol: "arabia.webp",
    colors: { primary: "#F7D801", secondary: "#156C30" },
    leaders: [{ name: "Saladin", portrait: "saladin.webp" }],
  },
  {
    name: "Aztec",
    slug: "aztec",
    symbol: "aztec.webp",
    colors: { primary: "#7DECE3", secondary: "#780001" },
    leaders: [{ name: "Montezuma", portrait: "montezuma.webp" }],
  },
  {
    name: "Brazil",
    slug: "brazil",
    symbol: "brazil.webp",
    colors: { primary: "#61BF22", secondary: "#F7D801" },
    leaders: [{ name: "Pedro II", portrait: "pedro-ii.webp" }],
  },
  {
    name: "China",
    slug: "china",
    symbol: "china.webp",
    colors: { primary: "#156C30", secondary: "#F9F9F9" },
    leaders: [
      { name: "Qin Shi Huang", portrait: "qin-shi-huang.webp" },
      { name: "Kublai Khan", portrait: "kublai-khan.webp" },
      { name: "Wu Zetian", portrait: "wu-zetian.webp" },
      { name: "Yongle", portrait: "yongle.webp" },
    ],
  },
  {
    name: "Egypt",
    slug: "egypt",
    symbol: "egypt.webp",
    colors: { primary: "#014F51", secondary: "#EAE19D" },
    leaders: [
      { name: "Cleopatra", portrait: "cleopatra.webp" },
      { name: "Ramesses II", portrait: "ramesses-ii.webp" },
    ],
  },
  {
    name: "England",
    slug: "england",
    symbol: "england.webp",
    colors: { primary: "#CA1415", secondary: "#F9F9F9" },
    leaders: [
      { name: "Victoria", portrait: "victoria.webp" },
      { name: "Elizabeth I", portrait: "elizabeth-i.webp" },
      {
        name: "Eleanor of Aquitaine",
        portrait: "eleanor-of-aquitaine.webp",
        colors: { primary: "#E57574", secondary: "#F9F9F9" },
      },
    ],
  },
  {
    name: "France",
    slug: "france",
    symbol: "france.webp",
    colors: { primary: "#004FCE", secondary: "#EAE19D" },
    leaders: [
      { name: "Catherine de Medici", portrait: "catherine-de-medici.webp" },
      {
        name: "Eleanor of Aquitaine",
        portrait: "eleanor-of-aquitaine.webp",
        colors: { primary: "#E57574", secondary: "#EAE19D" },
      },
    ],
  },
  {
    name: "Germany",
    slug: "germany",
    symbol: "germany.webp",
    colors: { primary: "#AEAEAE", secondary: "#181818" },
    leaders: [
      { name: "Frederick Barbarossa", portrait: "frederick-barbarossa.webp" },
      { name: "Ludwig II", portrait: "ludwig-ii.webp" },
    ],
  },
  {
    name: "Greece",
    slug: "greece",
    symbol: "greece.webp",
    colors: { primary: "#74A3F3", secondary: "#F9F9F9" },
    leaders: [
      { name: "Pericles", portrait: "pericles.webp" },
      {
        name: "Gorgo",
        portrait: "gorgo.webp",
        colors: { primary: "#780001", secondary: "#74DADB" },
      },
    ],
  },
  {
    name: "India",
    slug: "india",
    symbol: "india.webp",
    colors: { primary: "#370065", secondary: "#00C09B" },
    leaders: [
      { name: "Gandhi", portrait: "gandhi.webp" },
      {
        name: "Chandragupta",
        portrait: "chandragupta.webp",
        colors: { primary: "#00C09B", secondary: "#370065" },
      },
    ],
  },
  {
    name: "Japan",
    slug: "japan",
    symbol: "japan.webp",
    colors: { primary: "#F9F9F9", secondary: "#780001" },
    leaders: [
      { name: "Hojo Tokimune", portrait: "hojo-tokimune.webp" },
      { name: "Tokugawa", portrait: "tokugawa.webp" },
    ],
  },
  {
    name: "Kongo",
    slug: "kongo",
    symbol: "kongo.webp",
    colors: { primary: "#F7D801", secondary: "#CA1415" },
    leaders: [
      { name: "Mvemba a Nzinga", portrait: "mvemba-a-nzinga.webp" },
      { name: "Nzinga Mbande", portrait: "nzinga-mbande.webp" },
    ],
  },
  {
    name: "Norway",
    slug: "norway",
    symbol: "norway.webp",
    colors: { primary: "#012A6C", secondary: "#CA1415" },
    leaders: [{ name: "Harald Hardrada", portrait: "harald-hardrada.webp" }],
  },
  {
    name: "Rome",
    slug: "rome",
    symbol: "rome.webp",
    colors: { primary: "#6D00CD", secondary: "#F7D801" },
    leaders: [
      { name: "Trajan", portrait: "trajan.webp" },
      { name: "Julius Caesar", portrait: "julius-caesar.webp" },
    ],
  },
  {
    name: "Russia",
    slug: "russia",
    symbol: "russia.webp",
    colors: { primary: "#F7D801", secondary: "#181818" },
    leaders: [{ name: "Peter", portrait: "peter.webp" }],
  },
  {
    name: "Scythia",
    slug: "scythia",
    symbol: "scythia.webp",
    colors: { primary: "#FFB23C", secondary: "#780001" },
    leaders: [{ name: "Tomyris", portrait: "tomyris.webp" }],
  },
  {
    name: "Spain",
    slug: "spain",
    symbol: "spain.webp",
    colors: { primary: "#CA1415", secondary: "#F7D801" },
    leaders: [{ name: "Philip II", portrait: "philip-ii.webp" }],
  },
  {
    name: "Sumeria",
    slug: "sumeria",
    symbol: "sumeria.webp",
    colors: { primary: "#012A6C", secondary: "#FF8112" },
    leaders: [{ name: "Gilgamesh", portrait: "gilgamesh.webp" }],
  },

  // ── DLC ──
  {
    name: "Australia",
    slug: "australia",
    symbol: "australia.webp",
    colors: { primary: "#156C30", secondary: "#F7D801" },
    leaders: [{ name: "John Curtin", portrait: "john-curtin.webp" }],
  },
  {
    name: "Macedon",
    slug: "macedon",
    symbol: "macedon.webp",
    colors: { primary: "#AEAEAE", secondary: "#F7D801" },
    leaders: [{ name: "Alexander", portrait: "alexander.webp" }],
  },
  {
    name: "Persia",
    slug: "persia",
    symbol: "persia.webp",
    colors: { primary: "#B780E6", secondary: "#780001" },
    leaders: [
      { name: "Cyrus", portrait: "cyrus.webp" },
      { name: "Nader Shah", portrait: "nader-shah.webp" },
    ],
  },
  {
    name: "Nubia",
    slug: "nubia",
    symbol: "nubia.webp",
    colors: { primary: "#EAE19D", secondary: "#783D02" },
    leaders: [{ name: "Amanitore", portrait: "amanitore.webp" }],
  },
  {
    name: "Indonesia",
    slug: "indonesia",
    symbol: "indonesia.webp",
    colors: { primary: "#780001", secondary: "#00C09B" },
    leaders: [{ name: "Gitarja", portrait: "gitarja.webp" }],
  },
  {
    name: "Khmer",
    slug: "khmer",
    symbol: "khmer.webp",
    colors: { primary: "#750073", secondary: "#FF8112" },
    leaders: [{ name: "Jayavarman VII", portrait: "jayavarman-vii.webp" }],
  },
  {
    name: "Poland",
    slug: "poland",
    symbol: "poland.webp",
    colors: { primary: "#780001", secondary: "#E57574" },
    leaders: [{ name: "Jadwiga", portrait: "jadwiga.webp" }],
  },

  // ── Rise and Fall ──
  {
    name: "Korea",
    slug: "korea",
    symbol: "korea.webp",
    colors: { primary: "#CA1415", secondary: "#74A3F3" },
    leaders: [
      { name: "Seondeok", portrait: "seondeok.webp" },
      { name: "Sejong", portrait: "sejong.webp" },
    ],
  },
  {
    name: "Zulu",
    slug: "zulu",
    symbol: "zulu.webp",
    colors: { primary: "#783D02", secondary: "#F9F9F9" },
    leaders: [{ name: "Shaka", portrait: "shaka.webp" }],
  },
  {
    name: "Cree",
    slug: "cree",
    symbol: "cree.webp",
    colors: { primary: "#012A6C", secondary: "#61BF22" },
    leaders: [{ name: "Poundmaker", portrait: "poundmaker.webp" }],
  },
  {
    name: "Georgia",
    slug: "georgia",
    symbol: "georgia.webp",
    colors: { primary: "#F9F9F9", secondary: "#FF8112" },
    leaders: [{ name: "Tamar", portrait: "tamar.webp" }],
  },
  {
    name: "Mapuche",
    slug: "mapuche",
    symbol: "mapuche.webp",
    colors: { primary: "#004FCE", secondary: "#7DECE3" },
    leaders: [{ name: "Lautaro", portrait: "lautaro.webp" }],
  },
  {
    name: "Mongolia",
    slug: "mongolia",
    symbol: "mongolia.webp",
    colors: { primary: "#780001", secondary: "#FF8112" },
    leaders: [
      { name: "Genghis Khan", portrait: "genghis-khan.webp" },
      { name: "Kublai Khan", portrait: "kublai-khan.webp" },
    ],
  },
  {
    name: "Netherlands",
    slug: "netherlands",
    symbol: "netherlands.webp",
    colors: { primary: "#FF8112", secondary: "#004FCE" },
    leaders: [{ name: "Wilhelmina", portrait: "wilhelmina.webp" }],
  },
  {
    name: "Scotland",
    slug: "scotland",
    symbol: "scotland.webp",
    colors: { primary: "#F9F9F9", secondary: "#004FCE" },
    leaders: [{ name: "Robert the Bruce", portrait: "robert-the-bruce.webp" }],
  },

  // ── Gathering Storm ──
  {
    name: "Mali",
    slug: "mali",
    symbol: "mali.webp",
    colors: { primary: "#780001", secondary: "#EAE19D" },
    leaders: [
      { name: "Mansa Musa", portrait: "mansa-musa.webp" },
      { name: "Sundiata Keita", portrait: "sundiata-keita.webp" },
    ],
  },
  {
    name: "Ottoman",
    aliases: ["Ottomans"],
    slug: "ottoman",
    symbol: "ottoman.webp",
    colors: { primary: "#F9F9F9", secondary: "#156C30" },
    leaders: [{ name: "Suleiman", portrait: "suleiman.webp" }],
  },
  {
    name: "Inca",
    slug: "inca",
    symbol: "inca.webp",
    colors: { primary: "#783D02", secondary: "#F7D801" },
    leaders: [{ name: "Pachacuti", portrait: "pachacuti.webp" }],
  },
  {
    name: "Hungary",
    slug: "hungary",
    symbol: "hungary.webp",
    colors: { primary: "#156C30", secondary: "#FF8112" },
    leaders: [
      { name: "Matthias Corvinus", portrait: "matthias-corvinus.webp" },
    ],
  },
  {
    name: "Maori",
    aliases: ["Māori"],
    slug: "maori",
    symbol: "maori.webp",
    colors: { primary: "#CA1415", secondary: "#7DECE3" },
    leaders: [{ name: "Kupe", portrait: "kupe.webp" }],
  },
  {
    name: "Phoenicia",
    slug: "phoenicia",
    symbol: "phoenicia.webp",
    colors: { primary: "#6D00CD", secondary: "#74A3F3" },
    leaders: [{ name: "Dido", portrait: "dido.webp" }],
  },
  {
    name: "Canada",
    slug: "canada",
    symbol: "canada.webp",
    colors: { primary: "#F9F9F9", secondary: "#CA1415" },
    leaders: [{ name: "Wilfrid Laurier", portrait: "wilfrid-laurier.webp" }],
  },
  {
    name: "Sweden",
    slug: "sweden",
    symbol: "sweden.webp",
    colors: { primary: "#74A3F3", secondary: "#F7D801" },
    leaders: [{ name: "Kristina", portrait: "kristina.webp" }],
  },

  // ── New Frontier Pass ──
  {
    name: "Gran Colombia",
    slug: "gran_colombia",
    symbol: "gran-colombia.webp",
    colors: { primary: "#012A6C", secondary: "#F7D801" },
    leaders: [
      {
        name: "Simon Bolivar",
        aliases: ["Simón Bolívar"],
        portrait: "simon-bolivar.webp",
      },
    ],
  },
  {
    name: "Maya",
    slug: "maya",
    symbol: "maya.webp",
    colors: { primary: "#74A3F3", secondary: "#014F51" },
    leaders: [{ name: "Lady Six Sky", portrait: "lady-six-sky.webp" }],
  },
  {
    name: "Ethiopia",
    slug: "ethiopia",
    symbol: "ethiopia.webp",
    colors: { primary: "#F7D801", secondary: "#156C30" },
    leaders: [{ name: "Menelik II", portrait: "menelik-ii.webp" }],
  },
  {
    name: "Gaul",
    slug: "gaul",
    symbol: "gaul.webp",
    colors: { primary: "#156C30", secondary: "#7DECE3" },
    leaders: [{ name: "Ambiorix", portrait: "ambiorix.webp" }],
  },
  {
    name: "Byzantium",
    slug: "byzantium",
    symbol: "byzantium.webp",
    colors: { primary: "#370065", secondary: "#EAE19D" },
    leaders: [
      { name: "Basil II", portrait: "basil-ii.webp" },
      { name: "Theodora", portrait: "theodora.webp" },
    ],
  },
  {
    name: "Babylon",
    slug: "babylon",
    symbol: "babylon.webp",
    colors: { primary: "#74A3F3", secondary: "#012A6C" },
    leaders: [{ name: "Hammurabi", portrait: "hammurabi.webp" }],
  },
  {
    name: "Vietnam",
    slug: "vietnam",
    symbol: "vietnam.webp",
    colors: { primary: "#F7D801", secondary: "#750073" },
    leaders: [
      {
        name: "Ba Trieu",
        aliases: ["Bà Triệu"],
        portrait: "ba-trieu.webp",
      },
    ],
  },
  {
    name: "Portugal",
    slug: "portugal",
    symbol: "portugal.webp",
    colors: { primary: "#F9F9F9", secondary: "#012A6C" },
    leaders: [
      {
        name: "Joao III",
        aliases: ["João III"],
        portrait: "joao-iii.webp",
      },
    ],
  },
];

// ─── Normalization ──────────────────────────────────────────────────────────

/** Normalize a string for lookup: strip diacritics, persona suffixes, lowercase. */
function normalize(s: string): string {
  return s
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "") // strip combining diacritical marks
    .replace(/\s*\(.*?\)\s*$/, "") // strip persona suffix: "Cleopatra (Ptolemaic)" → "Cleopatra"
    .toLowerCase()
    .trim();
}

// ─── Index (built once at module load) ──────────────────────────────────────

const civByNorm = new Map<string, CivEntry>();
const civBySlug = new Map<string, CivEntry>();
const leaderByNorm = new Map<
  string,
  { leader: LeaderEntry; civ: CivEntry }[]
>();

for (const civ of CIV_REGISTRY) {
  civByNorm.set(normalize(civ.name), civ);
  civBySlug.set(civ.slug, civ);
  if (civ.aliases) {
    for (const alias of civ.aliases) {
      civByNorm.set(normalize(alias), civ);
    }
  }

  for (const leader of civ.leaders) {
    const key = normalize(leader.name);
    if (!leaderByNorm.has(key)) leaderByNorm.set(key, []);
    leaderByNorm.get(key)!.push({ leader, civ });
    if (leader.aliases) {
      for (const alias of leader.aliases) {
        const aliasKey = normalize(alias);
        if (!leaderByNorm.has(aliasKey)) leaderByNorm.set(aliasKey, []);
        leaderByNorm.get(aliasKey)!.push({ leader, civ });
      }
    }
  }
}

// ─── Internal lookups ───────────────────────────────────────────────────────

function findCiv(civName: string): CivEntry | undefined {
  return civByNorm.get(normalize(civName));
}

function findLeader(
  leaderName: string,
  civName?: string,
): { leader: LeaderEntry; civ: CivEntry } | undefined {
  const entries = leaderByNorm.get(normalize(leaderName));
  if (!entries || entries.length === 0) return undefined;
  if (civName) {
    const normCiv = normalize(civName);
    const match = entries.find((e) => normalize(e.civ.name) === normCiv);
    if (match) return match;
  }
  return entries[0];
}

// ─── Fallback ───────────────────────────────────────────────────────────────

const FALLBACK_PALETTE = [
  "#E63946",
  "#457B9D",
  "#2A9D8F",
  "#E9C46A",
  "#F4A261",
  "#264653",
  "#9B5DE5",
  "#F15BB5",
];

function hashFallbackColor(name: string): {
  primary: string;
  secondary: string;
} {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = ((hash << 5) - hash + name.charCodeAt(i)) | 0;
  }
  const color = FALLBACK_PALETTE[Math.abs(hash) % FALLBACK_PALETTE.length];
  return { primary: color, secondary: "#F9F9F9" };
}

// ─── Public API ─────────────────────────────────────────────────────────────

/**
 * Get colors for a civ, with optional leader-specific override.
 * Handles diacritics, plural variants, and persona suffixes.
 */
export function getCivColors(
  civName: string,
  leader?: string,
): { primary: string; secondary: string } {
  if (leader) {
    const match = findLeader(leader, civName);
    if (match?.leader.colors) return match.leader.colors;
    if (match) return match.civ.colors;
  }
  const civ = findCiv(civName);
  if (civ) return civ.colors;
  return hashFallbackColor(civName);
}

/** Get leader portrait path, or null if unavailable. */
export function getLeaderPortrait(leader: string): string | null {
  const match = findLeader(leader);
  if (!match?.leader.portrait) return null;
  return `/images/leaders/${match.leader.portrait}`;
}

/** Get civ symbol path, or null if unavailable. */
export function getCivSymbol(civName: string): string | null {
  const civ = findCiv(civName);
  if (!civ?.symbol) return null;
  return `/images/civs/${civ.symbol}`;
}

/** Get slug for a civ display name (e.g. "India" → "india"). */
export function getCivSlug(civName: string): string | null {
  return findCiv(civName)?.slug ?? null;
}

/** Get display name for a slug (e.g. "india" → "India"). */
export function getCivDisplayName(slug: string): string | null {
  return civBySlug.get(slug.toLowerCase())?.name ?? null;
}

/** Resolve a possibly-diacriticked leader name to its canonical form. */
export function canonicalLeaderName(leader: string): string {
  return findLeader(leader)?.leader.name ?? leader;
}

/** Resolve a possibly-variant civ name to its canonical form. */
export function canonicalCivName(civName: string): string {
  return findCiv(civName)?.name ?? civName;
}
