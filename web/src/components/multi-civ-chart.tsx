"use client"

import { useState, useMemo } from "react"
import type { TurnData, NumericPlayerField, PlayerRow } from "@/lib/diary-types"
import { CIV6_COLORS } from "@/lib/civ-colors"

const RIVAL_COLORS = [
  "#E63946", "#457B9D", "#2A9D8F", "#E9C46A",
  "#F4A261", "#264653", "#9B5DE5", "#F15BB5",
]

const METRIC_OPTIONS: { value: NumericPlayerField; label: string }[] = [
  { value: "score", label: "Score" },
  { value: "science", label: "Science" },
  { value: "culture", label: "Culture" },
  { value: "gold", label: "Gold" },
  { value: "military", label: "Military" },
  { value: "territory", label: "Territory" },
  { value: "cities", label: "Cities" },
  { value: "pop", label: "Population" },
  { value: "faith", label: "Faith" },
  { value: "exploration_pct", label: "Explored %" },
  { value: "tourism", label: "Tourism" },
]

const W = 300
const H = 100
const PAD = 4

interface MultiCivChartProps {
  turns: TurnData[]
  currentIndex: number
}

export function MultiCivChart({ turns, currentIndex }: MultiCivChartProps) {
  const [metric, setMetric] = useState<NumericPlayerField>("score")

  const getValue = (p: PlayerRow): number | null => {
    const v = p[metric]
    return typeof v === "number" ? v : null
  }

  // Memoize: civ color map, all polyline point strings, agent values
  const { civMap, agentValues, agentPoints, rivalLines } = useMemo(() => {
    // Collect all rival civs, assign stable colors
    const cMap = new Map<number, { name: string; color: string }>()
    let colorIdx = 0
    for (const t of turns) {
      for (const r of t.rivals) {
        if (!cMap.has(r.pid)) {
          cMap.set(r.pid, {
            name: r.civ,
            color: RIVAL_COLORS[colorIdx % RIVAL_COLORS.length],
          })
          colorIdx++
        }
      }
    }

    // Build series
    const aVals = turns.map((t) => {
      const v = t.agent[metric]
      return typeof v === "number" ? v : 0
    })
    const rSeries: { pid: number; values: (number | null)[] }[] = []
    for (const pid of cMap.keys()) {
      rSeries.push({
        pid,
        values: turns.map((t) => {
          const r = t.rivals.find((rv) => rv.pid === pid)
          if (!r) return null
          const v = r[metric]
          return typeof v === "number" ? v : null
        }),
      })
    }

    // Compute global min/max
    const all: number[] = [...aVals]
    for (const s of rSeries) {
      for (const v of s.values) {
        if (v !== null) all.push(v)
      }
    }
    const min = Math.min(...all)
    const max = Math.max(...all)
    const range = max - min || 1

    function toPoints(values: (number | null)[]): string {
      return values
        .map((v, i) => {
          if (v === null) return null
          const x = PAD + (i / Math.max(values.length - 1, 1)) * (W - 2 * PAD)
          const y = H - PAD - ((v - min) / range) * (H - 2 * PAD)
          return `${x},${y}`
        })
        .filter(Boolean)
        .join(" ")
    }

    return {
      civMap: cMap,
      agentValues: aVals,
      agentPoints: toPoints(aVals),
      rivalLines: rSeries.map((s) => ({
        pid: s.pid,
        points: toPoints(s.values),
      })),
    }
  }, [turns, metric])

  if (civMap.size === 0) return null

  const cx = PAD + (currentIndex / Math.max(turns.length - 1, 1)) * (W - 2 * PAD)
  const currentTurn = turns[currentIndex]

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <h3 className="font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
          Comparison
        </h3>
        <select
          value={metric}
          onChange={(e) => setMetric(e.target.value as NumericPlayerField)}
          className="rounded-sm border border-marble-300 bg-marble-100 px-1.5 py-0.5 font-mono text-[10px] text-marble-700"
        >
          {METRIC_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" preserveAspectRatio="none" style={{ height: 100 }}>
        {rivalLines.map(({ pid, points }) => (
          <polyline
            key={pid}
            points={points}
            fill="none"
            stroke={civMap.get(pid)!.color}
            strokeWidth="1.5"
            strokeLinejoin="round"
            opacity="0.6"
          />
        ))}
        <polyline
          points={agentPoints}
          fill="none"
          stroke={CIV6_COLORS.goldMetal}
          strokeWidth="2.5"
          strokeLinejoin="round"
          opacity="0.9"
        />
        <line
          x1={cx} y1={PAD} x2={cx} y2={H - PAD}
          stroke="#5C5549" strokeWidth="1" strokeDasharray="3,3" opacity="0.4"
          style={{ transition: "x1 400ms ease-out, x2 400ms ease-out" }}
        />
      </svg>
      {/* Legend */}
      <div className="mt-1.5 space-y-0.5">
        <div className="flex items-center gap-1.5">
          <div className="h-2 w-3 rounded-sm" style={{ backgroundColor: CIV6_COLORS.goldMetal }} />
          <span className="flex-1 text-[10px] text-marble-600">{currentTurn?.agent.civ ?? "You"}</span>
          <span className="font-mono text-[10px] tabular-nums text-marble-700">
            {agentValues[currentIndex]}
          </span>
        </div>
        {Array.from(civMap.entries()).map(([pid, { name, color }]) => {
          const rival = currentTurn?.rivals.find((r) => r.pid === pid)
          const rivalVal = rival ? getValue(rival) : null
          return (
            <div key={pid} className="flex items-center gap-1.5">
              <div className="h-2 w-3 rounded-sm" style={{ backgroundColor: color }} />
              <span className="flex-1 text-[10px] text-marble-600">{name}</span>
              <span className="font-mono text-[10px] tabular-nums text-marble-700">
                {rivalVal ?? "—"}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
