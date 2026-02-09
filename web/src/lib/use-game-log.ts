"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import type { LogEntry } from "./types"

const POLL_INTERVAL = 2000

export function useGameLog(live: boolean) {
  const [entries, setEntries] = useState<LogEntry[]>([])
  const [connected, setConnected] = useState(false)
  const lastLine = useRef(0)

  const fetchEntries = useCallback(async () => {
    try {
      const res = await fetch(`/api/log?after=${lastLine.current}`)
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

  // Initial fetch
  useEffect(() => {
    fetchEntries()
  }, [fetchEntries])

  // Polling when live
  useEffect(() => {
    if (!live) return
    const id = setInterval(fetchEntries, POLL_INTERVAL)
    return () => clearInterval(id)
  }, [live, fetchEntries])

  const clear = useCallback(() => {
    setEntries([])
    lastLine.current = 0
  }, [])

  return { entries, connected, clear }
}
