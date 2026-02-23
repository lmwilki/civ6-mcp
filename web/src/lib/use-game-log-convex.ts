"use client"

import { useMemo } from "react"
import { useQuery } from "convex/react"
import { api } from "../../convex/_generated/api"
import type { LogEntry, GameLogInfo } from "./types"

/** Convex-backed game log list — real-time. */
export function useGameLogsConvex(): GameLogInfo[] {
  const games: GameLogInfo[] = useQuery(api.logs.listGameLogs) ?? []
  return games
}

/** Convex-backed game log entries — real-time subscription. */
export function useGameLogConvex(
  _live: boolean,
  game: string | null,
  session?: string | null
) {
  type ConvexLogEntry = LogEntry & { _id: string; _creationTime: number; gameId: string }
  const data: ConvexLogEntry[] | undefined = useQuery(
    api.logs.getLogEntries,
    game
      ? {
          gameId: game,
          ...(session ? { session } : {}),
        }
      : "skip"
  )

  const entries = useMemo(() => {
    if (!data) return []
    return data.map(({ _id, _creationTime, gameId: _, ...rest }) => rest as LogEntry)
  }, [data])

  return {
    entries,
    connected: data !== undefined,
  }
}
