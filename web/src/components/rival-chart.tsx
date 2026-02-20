"use client"

import type { DiaryEntry } from "@/lib/diary-types"

const RIVAL_COLORS = [
  "#E63946", // red
  "#457B9D", // steel blue
  "#2A9D8F", // teal
  "#E9C46A", // sand
  "#F4A261", // orange
  "#264653", // dark teal
  "#9B5DE5", // purple
  "#F15BB5", // pink
]

interface RivalChartProps {
  entries: DiaryEntry[]
  currentIndex: number
}

export function RivalChart({ entries, currentIndex }: RivalChartProps) {
  // Collect all rival IDs across all entries
  const rivalMap = new Map<number, { name: string; color: string }>()
  let colorIdx = 0
  for (const e of entries) {
    if (!e.rivals) continue
    for (const r of e.rivals) {
      if (!rivalMap.has(r.id)) {
        rivalMap.set(r.id, { name: r.name, color: RIVAL_COLORS[colorIdx % RIVAL_COLORS.length] })
        colorIdx++
      }
    }
  }

  if (rivalMap.size === 0) return null

  // Build score series: player + each rival
  const playerScores = entries.map((e) => e.score.total)
  const rivalSeries = new Map<number, (number | null)[]>()
  for (const id of rivalMap.keys()) {
    rivalSeries.set(
      id,
      entries.map((e) => {
        const r = e.rivals?.find((rv) => rv.id === id)
        return r?.score ?? null
      })
    )
  }

  // Compute global min/max
  let allValues: number[] = [...playerScores]
  for (const series of rivalSeries.values()) {
    for (const v of series) {
      if (v !== null) allValues.push(v)
    }
  }
  const min = Math.min(...allValues)
  const max = Math.max(...allValues)
  const range = max - min || 1

  const w = 300
  const h = 100
  const pad = 4

  function toPoints(values: (number | null)[]): string {
    return values
      .map((v, i) => {
        if (v === null) return null
        const x = pad + (i / Math.max(values.length - 1, 1)) * (w - 2 * pad)
        const y = h - pad - ((v - min) / range) * (h - 2 * pad)
        return `${x},${y}`
      })
      .filter(Boolean)
      .join(" ")
  }

  // Current position line
  const cx = pad + (currentIndex / Math.max(entries.length - 1, 1)) * (w - 2 * pad)

  // Current scores for legend
  const currentEntry = entries[currentIndex]
  const currentRivals = currentEntry?.rivals ?? []

  return (
    <div>
      <h3 className="mb-2 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
        Score Comparison
      </h3>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full" preserveAspectRatio="none" style={{ height: 100 }}>
        {/* Rival lines */}
        {Array.from(rivalSeries.entries()).map(([id, values]) => (
          <polyline
            key={id}
            points={toPoints(values)}
            fill="none"
            stroke={rivalMap.get(id)!.color}
            strokeWidth="1.5"
            strokeLinejoin="round"
            opacity="0.6"
          />
        ))}
        {/* Player line (on top) */}
        <polyline
          points={toPoints(playerScores)}
          fill="none"
          stroke="#D4A853"
          strokeWidth="2.5"
          strokeLinejoin="round"
          opacity="0.9"
        />
        {/* Current position indicator */}
        <line
          x1={cx}
          y1={pad}
          x2={cx}
          y2={h - pad}
          stroke="#5C5549"
          strokeWidth="1"
          strokeDasharray="3,3"
          opacity="0.4"
          style={{ transition: "x1 400ms ease-out, x2 400ms ease-out" }}
        />
      </svg>
      {/* Legend */}
      <div className="mt-1.5 space-y-0.5">
        <div className="flex items-center gap-1.5">
          <div className="h-2 w-3 rounded-sm" style={{ backgroundColor: "#D4A853" }} />
          <span className="flex-1 text-[10px] text-marble-600">{currentEntry?.civ ?? "You"}</span>
          <span className="font-mono text-[10px] tabular-nums text-marble-700">
            {playerScores[currentIndex]}
          </span>
        </div>
        {Array.from(rivalMap.entries()).map(([id, { name, color }]) => {
          const rivalScore = currentRivals.find((r) => r.id === id)?.score
          return (
            <div key={id} className="flex items-center gap-1.5">
              <div className="h-2 w-3 rounded-sm" style={{ backgroundColor: color }} />
              <span className="flex-1 text-[10px] text-marble-600">{name}</span>
              <span className="font-mono text-[10px] tabular-nums text-marble-700">
                {rivalScore ?? "—"}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
