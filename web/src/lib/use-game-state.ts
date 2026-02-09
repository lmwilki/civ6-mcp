"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import type { GameOverview, UnitInfo, CityInfo, TileInfo } from "./game-types"

const API = "http://localhost:8000"

async function fetchJson<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API}${path}`)
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

export function useGameState(interval = 5000) {
  const [overview, setOverview] = useState<GameOverview | null>(null)
  const [units, setUnits] = useState<UnitInfo[]>([])
  const [cities, setCities] = useState<CityInfo[]>([])
  const [connected, setConnected] = useState(false)

  const poll = useCallback(async () => {
    const [ov, u, c] = await Promise.all([
      fetchJson<GameOverview>("/api/overview"),
      fetchJson<UnitInfo[]>("/api/units"),
      fetchJson<CityInfo[]>("/api/cities"),
    ])
    setConnected(ov !== null)
    if (ov) setOverview(ov)
    if (u) setUnits(u)
    if (c) setCities(c)
  }, [])

  useEffect(() => {
    poll()
    const id = setInterval(poll, interval)
    return () => clearInterval(id)
  }, [poll, interval])

  return { overview, units, cities, connected }
}

export function useMapTiles(cities: CityInfo[], interval = 8000) {
  const [tiles, setTiles] = useState<Map<string, TileInfo>>(new Map())
  const citiesRef = useRef(cities)
  citiesRef.current = cities

  const poll = useCallback(async () => {
    const currentCities = citiesRef.current
    if (currentCities.length === 0) return

    const results = await Promise.all(
      currentCities.map((c) =>
        fetchJson<TileInfo[]>(`/api/map?x=${c.x}&y=${c.y}&radius=4`)
      )
    )

    setTiles((prev) => {
      const next = new Map(prev)
      for (const tileset of results) {
        if (!tileset) continue
        for (const tile of tileset) {
          if (tile.visibility !== "fog") {
            next.set(`${tile.x},${tile.y}`, tile)
          }
        }
      }
      return next
    })
  }, [])

  useEffect(() => {
    poll()
    const id = setInterval(poll, interval)
    return () => clearInterval(id)
  }, [poll, interval])

  return tiles
}
