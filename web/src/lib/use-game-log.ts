"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import type { LogEntry, GameLogInfo } from "./types"
import { CONVEX_MODE } from "@/components/convex-provider"
import { useGameLogsConvex, useGameLogConvex } from "./use-game-log-convex"

const POLL_INTERVAL = 2000

function useGameLogsFs(): GameLogInfo[] {
  const [games, setGames] = useState<GameLogInfo[]>([])

  useEffect(() => {
    let mounted = true
    async function load() {
      try {
        const res = await fetch("/api/log/sessions")
        if (res.ok && mounted) setGames(await res.json())
      } catch { /* ignore */ }
    }
    load()
    const id = setInterval(load, 30_000)
    return () => { mounted = false; clearInterval(id) }
  }, [])

  return games
}

export const useGameLogs = CONVEX_MODE ? useGameLogsConvex : useGameLogsFs

function useGameLogFs(live: boolean, game: string | null, session?: string | null): { entries: LogEntry[]; connected: boolean } {
  const [entries, setEntries] = useState<LogEntry[]>([])
  const [connected, setConnected] = useState(false)
  const lastLine = useRef(0)

  // Reset entries when game or session changes (adjust-state-during-render pattern)
  const [prevGame, setPrevGame] = useState(game)
  const [prevSession, setPrevSession] = useState(session)
  if (game !== prevGame || session !== prevSession) {
    setPrevGame(game)
    setPrevSession(session)
    setEntries([])
  }

  // Reset cursor ref when game/session changes (effect, not during render)
  useEffect(() => {
    lastLine.current = 0
  }, [game, session])

  const fetchEntries = useCallback(async () => {
    if (!game) return
    try {
      const params = new URLSearchParams({
        after: String(lastLine.current),
        game,
      })
      if (session) params.set("session", session)
      const res = await fetch(`/api/log?${params}`)
      if (!res.ok) return
      const data: LogEntry[] = await res.json()
      if (data.length > 0) {
        lastLine.current = data[data.length - 1].line
        setEntries((prev) => [...prev, ...data])
      }
      setConnected(true)
    } catch {
      setConnected(false)
    }
  }, [game, session])

  // Initial fetch + refetch on game/session change
  useEffect(() => {
    fetchEntries()
  }, [fetchEntries])

  // Polling when live
  useEffect(() => {
    if (!live) return
    const id = setInterval(fetchEntries, POLL_INTERVAL)
    return () => clearInterval(id)
  }, [live, fetchEntries])

  return { entries, connected }
}

export const useGameLog = CONVEX_MODE ? useGameLogConvex : useGameLogFs
