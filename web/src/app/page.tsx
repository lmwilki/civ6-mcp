"use client"

import { useState } from "react"
import { Timeline } from "@/components/timeline"
import { LiveIndicator } from "@/components/live-indicator"
import { NavBar } from "@/components/nav-bar"
import { useGameLog } from "@/lib/use-game-log"

export default function Home() {
  const [live, setLive] = useState(true)
  const { entries, connected } = useGameLog(live)

  const currentTurn = entries.length > 0 ? entries[entries.length - 1].turn : null

  return (
    <div className="flex h-screen flex-col">
      <NavBar active="timeline" turn={currentTurn} />

      {/* Sub-header with event count and live toggle */}
      <div className="shrink-0 border-b border-marble-300 bg-marble-50/50 px-6 py-2">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <span className="font-mono text-xs tabular-nums text-marble-500">
            {entries.length} events
          </span>
          <LiveIndicator
            live={live}
            connected={connected}
            onToggle={() => setLive(!live)}
          />
        </div>
      </div>

      {/* Timeline */}
      <Timeline entries={entries} live={live} />
    </div>
  )
}
