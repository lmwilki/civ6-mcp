import { NextResponse } from "next/server";
import { readFileSync, readdirSync, existsSync, statSync } from "fs";
import { join } from "path";
import { getLogDir } from "../shared";

/** Scan for per-game log files (log_*.jsonl). */
export async function GET() {
  const dir = getLogDir();
  if (!existsSync(dir)) {
    return NextResponse.json([]);
  }

  try {
    const files = readdirSync(dir).filter(
      (f) => f.startsWith("log_") && f.endsWith(".jsonl"),
    );

    const games = files.map((f) => {
      const fullPath = join(dir, f);
      const stat = statSync(fullPath);

      // log_{civ}_{seed}.jsonl
      const game = f.replace("log_", "").replace(".jsonl", "");
      const lastUnderscore = game.lastIndexOf("_");
      const civ = lastUnderscore > 0 ? game.slice(0, lastUnderscore) : game;
      const seed = lastUnderscore > 0 ? game.slice(lastUnderscore + 1) : "";

      let count = 0;
      let first_ts = 0;
      let last_ts = 0;
      let min_turn: number | null = null;
      let max_turn: number | null = null;
      const sessions: string[] = [];

      try {
        const content = readFileSync(fullPath, "utf-8");
        const lines = content.split("\n").filter((l) => l.trim());
        count = lines.length;

        if (lines.length > 0) {
          const first = JSON.parse(lines[0]);
          first_ts = first.ts ?? 0;
          if (first.turn != null) min_turn = first.turn;
          if (first.session && !sessions.includes(first.session))
            sessions.push(first.session);

          const last = JSON.parse(lines[lines.length - 1]);
          last_ts = last.ts ?? first_ts;
          if (last.turn != null) max_turn = last.turn;
          if (last.session && !sessions.includes(last.session))
            sessions.push(last.session);

          // Scan first 50 entries for min_turn and unique sessions
          if (min_turn === null || sessions.length < 2) {
            for (let i = 1; i < Math.min(lines.length, 50); i++) {
              try {
                const e = JSON.parse(lines[i]);
                if (min_turn === null && e.turn != null) min_turn = e.turn;
                if (e.session && !sessions.includes(e.session))
                  sessions.push(e.session);
              } catch {
                /* skip */
              }
            }
          }
        }
      } catch {
        first_ts = stat.mtimeMs / 1000;
        last_ts = first_ts;
      }

      return {
        game,
        civ,
        seed,
        count,
        first_ts,
        last_ts,
        min_turn,
        max_turn,
        sessions,
        mtime: stat.mtimeMs,
      };
    });

    games.sort((a, b) => b.mtime - a.mtime);

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    return NextResponse.json(games.map(({ mtime: _mtime, ...rest }) => rest));
  } catch {
    return NextResponse.json([]);
  }
}
