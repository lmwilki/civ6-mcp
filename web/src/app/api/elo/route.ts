import { NextResponse } from "next/server"
import { readdir, readFile } from "fs/promises"
import { join } from "path"
import { computeElo, type GameResult, type Participant } from "@/lib/elo"

const DIARY_DIR = process.env.CIV6_DIARY_DIR || join(process.env.HOME || "~", ".civ6-mcp")

interface RawPlayer {
  pid: number
  civ: string
  leader: string
  is_agent: boolean
  agent_model?: string
}

interface RawOutcome {
  winner_civ: string
}

export async function GET() {
  try {
    const files = await readdir(DIARY_DIR).catch(() => [])

    // Collect diary data (last turn per game) and outcomes from log files
    const gameData = new Map<string, { players: Map<number, RawPlayer>; outcome?: RawOutcome }>()

    // Process diary files for player data
    for (const f of files) {
      if (!f.startsWith("diary_") || !f.endsWith(".jsonl")) continue
      const content = await readFile(join(DIARY_DIR, f), "utf-8").catch(() => "")
      const lines = content.trim().split("\n").filter(Boolean)

      for (const line of lines) {
        try {
          const row = JSON.parse(line)
          if (!row.game || row.pid === undefined) continue
          const gameId = row.game

          if (!gameData.has(gameId)) gameData.set(gameId, { players: new Map() })
          const game = gameData.get(gameId)!

          // Keep latest turn data per player
          const existing = game.players.get(row.pid)
          if (!existing || row.turn > (existing as unknown as { turn: number }).turn) {
            game.players.set(row.pid, {
              pid: row.pid,
              civ: row.civ,
              leader: row.leader,
              is_agent: row.is_agent,
              agent_model: row.agent_model,
            })
          }
        } catch { /* skip malformed lines */ }
      }
    }

    // Process log files for outcomes
    for (const f of files) {
      if (!f.startsWith("log_") || !f.endsWith(".jsonl")) continue
      const content = await readFile(join(DIARY_DIR, f), "utf-8").catch(() => "")
      const lines = content.trim().split("\n").filter(Boolean)

      for (const line of lines) {
        try {
          const entry = JSON.parse(line)
          if (entry.type !== "game_over" || !entry.outcome) continue
          const gameId = entry.game
          if (!gameData.has(gameId)) continue
          gameData.get(gameId)!.outcome = { winner_civ: entry.outcome.winner_civ }
        } catch { /* skip malformed lines */ }
      }
    }

    // Build game results for ELO computation
    const results: GameResult[] = []
    for (const [gameId, data] of gameData) {
      if (!data.outcome || data.players.size < 2) continue

      const participants: Participant[] = []
      for (const p of data.players.values()) {
        const isModel = p.is_agent && !!p.agent_model
        participants.push({
          id: isModel ? `model:${p.agent_model}` : `ai:${p.leader}`,
          name: isModel ? p.agent_model! : p.leader,
          type: isModel ? "model" : "ai_leader",
          civ: p.civ,
          won: p.civ === data.outcome!.winner_civ,
        })
      }
      results.push({ gameId, participants })
    }

    const ratings = computeElo(results)
    return NextResponse.json({ ratings, gameCount: results.length })
  } catch {
    return NextResponse.json({ ratings: [], gameCount: 0 })
  }
}
