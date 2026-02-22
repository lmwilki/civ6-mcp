"use client"

import { useMemo } from "react"
import type { TurnData, NumericPlayerField } from "@/lib/diary-types"
import { AnimatedNumber } from "./animated-number"

interface ScoreSparklineProps {
  turns: TurnData[]
  currentIndex: number
  field: NumericPlayerField
  label: string
  color: string
  height?: number
}

export function ScoreSparkline({
  turns,
  currentIndex,
  field,
  label,
  color,
  height = 40,
}: ScoreSparklineProps) {
  const w = 300
  const padding = 2

  const { values, points, min, range } = useMemo(() => {
    const vals = turns.map((t) => (t.agent[field] as number) ?? 0)
    const mn = Math.min(...vals)
    const mx = Math.max(...vals)
    const rng = mx - mn || 1
    const pts = vals
      .map((v, i) => {
        const x = padding + (i / (vals.length - 1)) * (w - 2 * padding)
        const y = height - padding - ((v - mn) / rng) * (height - 2 * padding)
        return `${x},${y}`
      })
      .join(" ")
    return { values: vals, points: pts, min: mn, range: rng }
  }, [turns, field, height])

  if (turns.length < 2) return null

  const cx = padding + (currentIndex / (values.length - 1)) * (w - 2 * padding)
  const cy =
    height -
    padding -
    ((values[currentIndex] - min) / range) * (height - 2 * padding)

  return (
    <div className="flex items-center gap-2">
      <span className="w-14 text-right text-xs font-medium uppercase tracking-wider text-marble-600">
        {label}
      </span>
      <svg
        viewBox={`0 0 ${w} ${height}`}
        className="h-10 flex-1"
        preserveAspectRatio="none"
      >
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinejoin="round"
          opacity="0.7"
        />
        <g style={{
          transform: `translate(${cx}px, ${cy}px)`,
          transition: "transform 400ms cubic-bezier(0.33, 1, 0.68, 1)",
        }}>
          <circle r="4" fill={color} />
        </g>
      </svg>
      <span className="w-12 font-mono text-xs tabular-nums text-marble-700">
        <AnimatedNumber value={values[currentIndex]} />
      </span>
    </div>
  )
}
