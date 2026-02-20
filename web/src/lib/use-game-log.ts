"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import type { LogEntry, SessionInfo } from "./types"

const POLL_INTERVAL = 2000

export function useSessions() {
  const [sessions, setSessions] = useState<SessionInfo[]>([])

  useEffect(() => {
    let mounted = true
    async function load() {
      try {
        const res = await fetch("/api/log/sessions")
        if (res.ok && mounted) setSessions(await res.json())
      } catch { /* ignore */ }
    }
    load()
    const id = setInterval(load, 30_000)
    return () => { mounted = false; clearInterval(id) }
  }, [])

  return sessions
}

export function useGameLog(live: boolean, session: string | null) {
  const [entries, setEntries] = useState<LogEntry[]>([])
  const [connected, setConnected] = useState(false)
  const lastLine = useRef(0)
  const sessionRef = useRef(session)

  // Reset when session changes
  useEffect(() => {
    if (session !== sessionRef.current) {
      sessionRef.current = session
      setEntries([])
      lastLine.current = 0
    }
  }, [session])

  const fetchEntries = useCallback(async () => {
    try {
      const params = new URLSearchParams({ after: String(lastLine.current) })
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

  // Initial fetch + refetch on session change
  useEffect(() => {
    fetchEntries()
  }, [fetchEntries, session])

  // Polling when live
  useEffect(() => {
    if (!live) return
    const id = setInterval(fetchEntries, POLL_INTERVAL)
    return () => clearInterval(id)
  }, [live, fetchEntries])

  return { entries, connected }
}
