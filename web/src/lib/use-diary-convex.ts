"use client"

import { useMemo } from "react"
import { useQuery } from "convex/react"
import { api } from "../../convex/_generated/api"
import type { PlayerRow, CityRow, TurnData, DiaryFile } from "./diary-types"

/** Extract gameId from diary filename: diary_india_123.jsonl → india_123 */
function filenameToGameId(filename: string): string {
  return filename.replace(/^diary_/, "").replace(/\.jsonl$/, "")
}

interface GameDoc {
  gameId: string
  filename: string
  label: string
  count: number
  hasCities: boolean
}

/** Convex-backed diary list — real-time, no polling. */
export function useDiaryListConvex(): DiaryFile[] {
  const games: GameDoc[] = useQuery(api.diary.listGames) ?? []
  return games.map((g: GameDoc) => ({
    filename: g.filename,
    label: g.label,
    count: g.count,
    hasCities: g.hasCities,
  }))
}

/** Group raw player + city rows into per-turn snapshots (shared with filesystem mode) */
function groupByTurn(players: PlayerRow[], cities: CityRow[]): TurnData[] {
  const turnMap = new Map<number, { players: PlayerRow[]; cities: CityRow[] }>()

  const deduped = new Map<string, PlayerRow>()
  for (const p of players) {
    deduped.set(`${p.turn}:${p.pid}`, p)
  }
  for (const p of deduped.values()) {
    if (!turnMap.has(p.turn)) turnMap.set(p.turn, { players: [], cities: [] })
    turnMap.get(p.turn)!.players.push(p)
  }
  const dedupedCities = new Map<string, CityRow>()
  for (const c of cities) {
    dedupedCities.set(`${c.turn}:${c.city_id}`, c)
  }
  for (const c of dedupedCities.values()) {
    if (!turnMap.has(c.turn)) turnMap.set(c.turn, { players: [], cities: [] })
    turnMap.get(c.turn)!.cities.push(c)
  }

  const result: TurnData[] = []
  for (const [turn, data] of [...turnMap.entries()].sort(([a], [b]) => a - b)) {
    const agent = data.players.find((p) => p.is_agent)
    if (!agent) continue
    const rivals = data.players
      .filter((p) => !p.is_agent)
      .sort((a, b) => b.score - a.score)
    const agentCities = data.cities.filter((c) => c.pid === agent.pid)
    result.push({
      turn,
      timestamp: agent.timestamp,
      agent,
      rivals,
      agentCities,
      allCities: data.cities,
    })
  }
  return result
}

interface GameTurnsResult {
  playerRows: (PlayerRow & { _id: string; _creationTime: number; gameId: string })[]
  cityRows: (CityRow & { _id: string; _creationTime: number; gameId: string })[]
}

/** Convex-backed diary data — real-time updates via subscription. */
export function useDiaryConvex(filename: string | null) {
  const gameId = filename ? filenameToGameId(filename) : null
  const data: GameTurnsResult | undefined = useQuery(
    api.diary.getGameTurns,
    gameId ? { gameId } : "skip"
  )

  const turns = useMemo(() => {
    if (!data) return []
    // Strip Convex internal fields before passing to groupByTurn
    const players = data.playerRows.map(({ _id, _creationTime, gameId: _, ...rest }) => rest as PlayerRow)
    const cities = data.cityRows.map(({ _id, _creationTime, gameId: _, ...rest }) => rest as CityRow)
    return groupByTurn(players, cities)
  }, [data])

  return {
    turns,
    loading: data === undefined,
    reload: async () => {}, // No-op — Convex auto-updates
  }
}
