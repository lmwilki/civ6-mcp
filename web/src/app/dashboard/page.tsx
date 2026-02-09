"use client"

import { HexMap } from "@/components/hex-map"
import { GameOverviewPanel } from "@/components/game-overview"
import { useGameState, useMapTiles } from "@/lib/use-game-state"
import { NavBar } from "@/components/nav-bar"

export default function Dashboard() {
  const { overview, units, cities, connected } = useGameState(5000)
  const tiles = useMapTiles(cities, 8000)

  return (
    <div className="flex h-screen flex-col">
      <NavBar active="dashboard" connected={connected} turn={overview?.turn ?? null} />

      <div className="flex min-h-0 flex-1">
        {/* Map */}
        <div className="flex-1 overflow-hidden rounded-sm border-r border-marble-300">
          <HexMap tiles={tiles} cities={cities} units={units} />
        </div>

        {/* Sidebar */}
        <div className="w-72 shrink-0 overflow-hidden bg-marble-50">
          <GameOverviewPanel
            overview={overview}
            cities={cities}
            units={units}
            connected={connected}
          />
        </div>
      </div>
    </div>
  )
}
