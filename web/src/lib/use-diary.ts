"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import type { DiaryEntry, DiaryFile } from "./diary-types"

const POLL_INTERVAL = 3000

export function useDiaryList() {
  const [diaries, setDiaries] = useState<DiaryFile[]>([])

  useEffect(() => {
    const poll = () =>
      fetch("/api/diary")
        .then((r) => r.json())
        .then((data) => setDiaries(data.diaries || []))
        .catch(() => {})

    poll()
    const id = setInterval(poll, 10000)
    return () => clearInterval(id)
  }, [])

  return diaries
}

export function useDiary(filename: string | null, live: boolean = true) {
  const [entries, setEntries] = useState<DiaryEntry[]>([])
  const [loading, setLoading] = useState(false)
  const prevCount = useRef(0)

  const load = useCallback(async () => {
    if (!filename) return
    // Only show loading spinner on first fetch
    if (prevCount.current === 0) setLoading(true)
    try {
      const res = await fetch(`/api/diary?file=${encodeURIComponent(filename)}`)
      const data = await res.json()
      const newEntries: DiaryEntry[] = data.entries || []
      prevCount.current = newEntries.length
      setEntries(newEntries)
    } catch {
      setEntries([])
    } finally {
      setLoading(false)
    }
  }, [filename])

  // Initial load
  useEffect(() => {
    prevCount.current = 0
    load()
  }, [load])

  // Poll when live
  useEffect(() => {
    if (!live) return
    const id = setInterval(load, POLL_INTERVAL)
    return () => clearInterval(id)
  }, [live, load])

  return { entries, loading, reload: load }
}
