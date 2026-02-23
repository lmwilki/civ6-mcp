"use client"

import { useState, useMemo, useEffect, useCallback, useRef } from "react"
import type { TurnData, NumericPlayerField, PlayerRow } from "@/lib/diary-types"
import { CIV6_COLORS, getCivColors } from "@/lib/civ-colors"
import { CivIcon } from "./civ-icon"
import { BarChart3, Play, Pause } from "lucide-react"

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
  const [rotating, setRotating] = useState(false)
  const rotatingRef = useRef(rotating)
  rotatingRef.current = rotating

  const advanceMetric = useCallback(() => {
    setMetric((prev) => {
      const idx = METRIC_OPTIONS.findIndex((o) => o.value === prev)
      return METRIC_OPTIONS[(idx + 1) % METRIC_OPTIONS.length].value
    })
  }, [])

  useEffect(() => {
    if (!rotating) return
    const id = setInterval(advanceMetric, 10_000)
    return () => clearInterval(id)
  }, [rotating, advanceMetric])

  const getValue = (p: PlayerRow): number | null => {
    const v = p[metric]
    return typeof v === "number" ? v : null
  }

  // Memoize: civ color map, all polyline point strings, agent values
  const { civMap, agentValues, agentPoints, rivalLines } = useMemo(() => {
    // Collect all rival civs, assign stable colors
    const cMap = new Map<number, { name: string; color: string }>()
    for (const t of turns) {
      for (const r of t.rivals) {
        if (!cMap.has(r.pid)) {
          cMap.set(r.pid, {
            name: r.civ,
            color: getCivColors(r.civ, r.leader).primary,
          })
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
  const agentColor = currentTurn
    ? getCivColors(currentTurn.agent.civ, currentTurn.agent.leader).primary
    : CIV6_COLORS.goldMetal

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <h3 className="flex items-center gap-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
          <CivIcon icon={BarChart3} color={CIV6_COLORS.marine} size="sm" />
          Comparison
        </h3>
        <div className="flex items-center gap-1">
          <select
            value={metric}
            onChange={(e) => {
              setMetric(e.target.value as NumericPlayerField)
              setRotating(false)
            }}
            className="rounded-sm border border-marble-300 bg-marble-100 px-1.5 py-0.5 font-mono text-[10px] text-marble-700"
          >
            {METRIC_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <button
            onClick={() => setRotating((r) => !r)}
            className={`rounded-sm p-0.5 transition-colors ${rotating ? "text-patina" : "text-marble-400 hover:text-marble-600"}`}
            title={rotating ? "Stop auto-rotate" : "Auto-rotate metrics"}
          >
            {rotating ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3" />}
          </button>
        </div>
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
          stroke={agentColor}
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
      {/* Legend — sorted by selected metric */}
      <div className="mt-1.5 space-y-0.5">
        {(() => {
          const agentVal = agentValues[currentIndex] ?? 0
          const entries: { key: string; name: string; color: string; value: number | null; isAgent: boolean }[] = [
            { key: "agent", name: currentTurn?.agent.civ ?? "You", color: agentColor, value: agentVal, isAgent: true },
            ...Array.from(civMap.entries()).map(([pid, { name, color }]) => {
              const rival = currentTurn?.rivals.find((r) => r.pid === pid)
              return { key: String(pid), name, color, value: rival ? getValue(rival) : null, isAgent: false }
            }),
          ]
          entries.sort((a, b) => (b.value ?? -Infinity) - (a.value ?? -Infinity))
          return entries.map((e) => (
            <div key={e.key} className="flex items-center gap-1.5">
              <span className="inline-block h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: e.color }} />
              <span className={`flex-1 text-[10px] ${e.isAgent ? "font-medium text-marble-700" : "text-marble-600"}`}>{e.name}</span>
              <span className="font-mono text-[10px] tabular-nums text-marble-700">
                {e.value ?? "—"}
              </span>
            </div>
          ))
        })()}
      </div>
    </div>
  )
}
