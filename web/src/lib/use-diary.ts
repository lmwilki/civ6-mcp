"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import type { PlayerRow, CityRow, TurnData, DiaryFile } from "./diary-types"

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

/** Group raw player + city rows into per-turn snapshots */
function groupByTurn(players: PlayerRow[], cities: CityRow[]): TurnData[] {
  const turnMap = new Map<number, { players: PlayerRow[]; cities: CityRow[] }>()

  for (const p of players) {
    if (!turnMap.has(p.turn)) turnMap.set(p.turn, { players: [], cities: [] })
    turnMap.get(p.turn)!.players.push(p)
  }
  for (const c of cities) {
    if (!turnMap.has(c.turn)) turnMap.set(c.turn, { players: [], cities: [] })
    turnMap.get(c.turn)!.cities.push(c)
  }

  const result: TurnData[] = []
  for (const [turn, data] of [...turnMap.entries()].sort(([a], [b]) => a - b)) {
    const agent = data.players.find((p) => p.is_agent)
    if (!agent) continue // skip turns with no agent row
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

export function useDiary(filename: string | null, live: boolean = true) {
  const [turns, setTurns] = useState<TurnData[]>([])
  const [loading, setLoading] = useState(false)
  const prevCount = useRef(0)

  const load = useCallback(async () => {
    if (!filename) return
    if (prevCount.current === 0) setLoading(true)
    try {
      const [playersRes, citiesRes] = await Promise.all([
        fetch(`/api/diary?file=${encodeURIComponent(filename)}`),
        fetch(`/api/diary?file=${encodeURIComponent(filename)}&cities=1`),
      ])
      const playersData = await playersRes.json()
      const citiesData = await citiesRes.json()
      const players: PlayerRow[] = playersData.entries || []
      const cities: CityRow[] = citiesData.entries || []
      const grouped = groupByTurn(players, cities)
      prevCount.current = grouped.length
      setTurns(grouped)
    } catch {
      setTurns([])
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

  return { turns, loading, reload: load }
}
