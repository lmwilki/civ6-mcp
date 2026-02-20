"use client"

import type { DiaryEntry } from "@/lib/diary-types"
import { AnimatedNumber } from "./animated-number"

interface ScoreSparklineProps {
  entries: DiaryEntry[]
  currentIndex: number
  field: keyof DiaryEntry["score"]
  label: string
  color: string
  height?: number
}

export function ScoreSparkline({
  entries,
  currentIndex,
  field,
  label,
  color,
  height = 40,
}: ScoreSparklineProps) {
  if (entries.length < 2) return null

  const values = entries.map((e) => (e.score[field] as number) ?? 0)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1

  const w = 300
  const padding = 2

  const points = values
    .map((v, i) => {
      const x = padding + (i / (values.length - 1)) * (w - 2 * padding)
      const y = height - padding - ((v - min) / range) * (height - 2 * padding)
      return `${x},${y}`
    })
    .join(" ")

  // Current position marker
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
