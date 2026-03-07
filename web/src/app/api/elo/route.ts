import { NextResponse } from "next/server";
import { readdir } from "fs/promises";
import { existsSync } from "fs";
import { join } from "path";
import { computeElo, type GameResult, type Participant } from "@/lib/elo";
import type { PlayerRow } from "@/lib/diary-types";
import { getDiaryDir, readJsonl } from "../shared";

interface LogGameOver {
  type: string;
  game: string;
  turn?: number;
  outcome?: {
    winner_civ?: string;
    winner_leader?: string;
    victory_type?: string;
    is_defeat?: boolean;
    player_alive?: boolean;
  };
}

export async function GET() {
  const dir = getDiaryDir();
  if (!existsSync(dir)) {
    return NextResponse.json({ ratings: [], gameCount: 0 });
  }

  const files = await readdir(dir);

  // 1. Read all diary files → collect participants per game from last recorded turn
  const diaryFiles = files.filter(
    (f) =>
      f.startsWith("diary_") && f.endsWith(".jsonl") && !f.includes("_cities"),
  );

  // Map: gameId → { turn → PlayerRow[] }
  const gameParticipants = new Map<string, Map<number, PlayerRow[]>>();

  for (const df of diaryFiles) {
    const entries = await readJsonl<PlayerRow>(join(dir, df));
    for (const row of entries) {
      if (!row.game) continue;
      let byTurn = gameParticipants.get(row.game);
      if (!byTurn) {
        byTurn = new Map();
        gameParticipants.set(row.game, byTurn);
      }
      let players = byTurn.get(row.turn);
      if (!players) {
        players = [];
        byTurn.set(row.turn, players);
      }
      players.push(row);
    }
  }

  // 2. Read all log files → find game_over entries
  const logFiles = files.filter(
    (f) => f.startsWith("log_") && f.endsWith(".jsonl"),
  );

  // Map: gameId → game_over entry
  const gameOutcomes = new Map<string, LogGameOver>();

  for (const lf of logFiles) {
    const entries = await readJsonl<LogGameOver>(join(dir, lf));
    for (const entry of entries) {
      if (entry.type === "game_over" && entry.game && entry.outcome) {
        gameOutcomes.set(entry.game, entry);
      }
    }
  }

  // 3. Match by gameId → build GameResult[]
  const results: GameResult[] = [];

  for (const [gameId, outcome] of gameOutcomes) {
    const byTurn = gameParticipants.get(gameId);
    if (!byTurn) continue;

    // Use the last recorded turn's player data
    const lastTurn = Math.max(...byTurn.keys());
    const players = byTurn.get(lastTurn);
    if (!players || players.length < 2) continue;

    const winnerCiv = outcome.outcome?.winner_civ;
    if (!winnerCiv) continue;

    // Deduplicate by pid (last row wins)
    const byPid = new Map<number, PlayerRow>();
    for (const p of players) {
      byPid.set(p.pid, p);
    }

    const participants: Participant[] = [];
    for (const p of byPid.values()) {
      const won = p.civ.toUpperCase() === winnerCiv.toUpperCase();
      if (p.is_agent && p.agent_model) {
        participants.push({
          id: `model:${p.agent_model}`,
          name: p.agent_model,
          type: "model",
          civ: p.civ,
          won,
        });
      } else {
        participants.push({
          id: `ai:${p.leader}`,
          name: p.leader,
          type: "ai_leader",
          civ: p.civ,
          won,
        });
      }
    }

    results.push({ gameId, participants });
  }

  // 4. Compute ELO
  const ratings = computeElo(results);

  return NextResponse.json({ ratings, gameCount: results.length });
}
