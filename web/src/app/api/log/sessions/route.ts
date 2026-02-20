import { NextResponse } from "next/server"
import { readFileSync, readdirSync, existsSync, statSync } from "fs"
import { join } from "path"
import { getLogDir } from "../shared"

export async function GET() {
  const dir = getLogDir()
  if (!existsSync(dir)) {
    return NextResponse.json([])
  }

  try {
    const files = readdirSync(dir).filter(
      (f) => f.startsWith("game_log_") && f.endsWith(".jsonl")
    )

    const sessions = files.map((f) => {
      const session = f.replace("game_log_", "").replace(".jsonl", "")
      const fullPath = join(dir, f)
      const stat = statSync(fullPath)

      // Read first and last lines for metadata without parsing the entire file
      let count = 0
      let first_ts = 0
      let last_ts = 0
      let min_turn: number | null = null
      let max_turn: number | null = null

      try {
        const content = readFileSync(fullPath, "utf-8")
        const lines = content.split("\n").filter((l) => l.trim())
        count = lines.length

        if (lines.length > 0) {
          const first = JSON.parse(lines[0])
          first_ts = first.ts ?? 0
          if (first.turn != null) min_turn = first.turn

          const last = JSON.parse(lines[lines.length - 1])
          last_ts = last.ts ?? first_ts
          if (last.turn != null) max_turn = last.turn

          // Scan for min_turn if first entry had null turn
          if (min_turn === null && count > 1) {
            for (let i = 1; i < Math.min(lines.length, 50); i++) {
              try {
                const e = JSON.parse(lines[i])
                if (e.turn != null) { min_turn = e.turn; break }
              } catch { /* skip */ }
            }
          }
        }
      } catch {
        // If we can't read, still include with basic stat info
        first_ts = stat.mtimeMs / 1000
        last_ts = first_ts
      }

      return { session, count, first_ts, last_ts, min_turn, max_turn, mtime: stat.mtimeMs }
    })

    sessions.sort((a, b) => b.mtime - a.mtime)

    // Strip mtime from response
    return NextResponse.json(
      sessions.map(({ mtime: _, ...rest }) => rest)
    )
  } catch {
    return NextResponse.json([])
  }
}
