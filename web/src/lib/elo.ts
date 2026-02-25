// ─── Types ──────────────────────────────────────────────────────────────────

export interface Participant {
  /** Unique ID: "model:<agent_model>" or "ai:<leader>" */
  id: string;
  /** Display name */
  name: string;
  /** Whether this is an LLM model or a Civ6 AI leader */
  type: "model" | "ai_leader";
  /** Civ played (e.g. "RUSSIA") */
  civ: string;
  /** Did this participant win the game? */
  won: boolean;
}

export interface GameResult {
  gameId: string;
  participants: Participant[];
}

export interface EloEntry {
  id: string;
  name: string;
  type: "model" | "ai_leader";
  elo: number;
  games: number;
  wins: number;
  losses: number;
}

// ─── ELO computation ────────────────────────────────────────────────────────

const BASE_ELO = 1500;
const K = 32;

/**
 * Compute ELO ratings from a list of game results.
 *
 * Each game is treated as a free-for-all: the winner beats every loser
 * (pairwise). Elo deltas are computed from N-1 pairwise matchups, but
 * win/loss/game counters are per-game: the winner gets 1 win and 1 game,
 * each loser gets 1 loss and 1 game.
 *
 * K is scaled by 1/sqrt(N-1) to prevent rating inflation in large games.
 *
 * All expected-score calculations use pre-game Elos (snapshotted before the
 * loop) so that results are independent of iteration order.
 */
export function computeElo(results: GameResult[]): EloEntry[] {
  const ratings = new Map<string, EloEntry>();

  function getOrCreate(p: Participant): EloEntry {
    let entry = ratings.get(p.id);
    if (!entry) {
      entry = {
        id: p.id,
        name: p.name,
        type: p.type,
        elo: BASE_ELO,
        games: 0,
        wins: 0,
        losses: 0,
      };
      ratings.set(p.id, entry);
    }
    return entry;
  }

  for (const game of results) {
    const { participants } = game;
    if (participants.length < 2) continue;

    const winner = participants.find((p) => p.won);
    if (!winner) continue;

    const losers = participants.filter((p) => !p.won);
    const n = participants.length;
    const kEff = K / Math.sqrt(n - 1);

    const winnerEntry = getOrCreate(winner);
    winnerEntry.games++;
    winnerEntry.wins++;

    // Snapshot pre-game Elos so iteration order doesn't affect results
    const winnerEloPre = winnerEntry.elo;
    const loserDeltas = new Map<string, number>();
    let winnerDelta = 0;

    for (const loser of losers) {
      const loserEntry = getOrCreate(loser);
      loserEntry.games++;
      loserEntry.losses++;

      const loserEloPre = loserEntry.elo;

      // Standard ELO expected score using pre-game ratings
      const expectedW =
        1 / (1 + Math.pow(10, (loserEloPre - winnerEloPre) / 400));
      const expectedL = 1 - expectedW;

      // Winner scored 1, loser scored 0
      winnerDelta += kEff * (1 - expectedW);
      loserDeltas.set(
        loser.id,
        (loserDeltas.get(loser.id) ?? 0) + kEff * (0 - expectedL),
      );
    }

    // Apply all deltas after the loop
    winnerEntry.elo += winnerDelta;
    for (const [loserId, delta] of loserDeltas) {
      ratings.get(loserId)!.elo += delta;
    }
  }

  return [...ratings.values()]
    .map((e) => ({ ...e, elo: Math.round(e.elo) }))
    .sort((a, b) => b.elo - a.elo);
}
