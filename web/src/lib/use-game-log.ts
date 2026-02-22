"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import type { LogEntry, GameLogInfo } from "./types"

const POLL_INTERVAL = 2000

export function useGameLogs() {
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

export function useGameLog(live: boolean, game: string | null, session?: string | null) {
  const [entries, setEntries] = useState<LogEntry[]>([])
  const [connected, setConnected] = useState(false)
  const lastLine = useRef(0)
  const gameRef = useRef(game)
  const sessionRef = useRef(session)

  // Reset when game or session changes
  useEffect(() => {
    if (game !== gameRef.current || session !== sessionRef.current) {
      gameRef.current = game
      sessionRef.current = session
      setEntries([])
      lastLine.current = 0
    }
  }, [game, session])

  const fetchEntries = useCallback(async () => {
    if (!gameRef.current) return
    try {
      const params = new URLSearchParams({
        after: String(lastLine.current),
        game: gameRef.current,
      })
      if (sessionRef.current) params.set("session", sessionRef.current)
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
  }, [])

  // Initial fetch + refetch on game/session change
  useEffect(() => {
    fetchEntries()
  }, [fetchEntries, game, session])

  // Polling when live
  useEffect(() => {
    if (!live) return
    const id = setInterval(fetchEntries, POLL_INTERVAL)
    return () => clearInterval(id)
  }, [live, fetchEntries])

  return { entries, connected }
}
