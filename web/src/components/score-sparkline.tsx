"use client";

import { useMemo } from "react";
import type { TurnSeries, NumericPlayerField } from "@/lib/diary-types";
import { AnimatedNumber } from "./animated-number";
import { CivIcon } from "./civ-icon";

interface ScoreSparklineProps {
  turnSeries: TurnSeries;
  currentIndex: number;
  field: NumericPlayerField;
  label: string;
  color: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  height?: number;
}

export function ScoreSparkline({
  turnSeries,
  currentIndex,
  field,
  label,
  color,
  icon,
  height = 40,
}: ScoreSparklineProps) {
  const w = 300;
  const padding = 2;

  const { values, points, min, range } = useMemo(() => {
    const agentEntry = Object.values(turnSeries.players).find(
      (p) => p.is_agent,
    );
    if (!agentEntry) return { values: [], points: "", min: 0, range: 1 };
    const vals = agentEntry.metrics[field] ?? [];
    const mn = Math.min(...vals);
    const mx = Math.max(...vals);
    const rng = mx - mn || 1;
    const pts = vals
      .map((v, i) => {
        const x = padding + (i / (vals.length - 1)) * (w - 2 * padding);
        const y = height - padding - ((v - mn) / rng) * (height - 2 * padding);
        return `${x},${y}`;
      })
      .join(" ");
    return { values: vals, points: pts, min: mn, range: rng };
  }, [turnSeries, field, height]);

  if (values.length < 2) return null;

  const cx = padding + (currentIndex / (values.length - 1)) * (w - 2 * padding);
  const cy =
    height -
    padding -
    ((values[currentIndex] - min) / range) * (height - 2 * padding);

  return (
    <div className="flex items-center gap-2">
      <div className="flex w-20 shrink-0 items-center justify-end gap-1">
        <span className="text-[10px] font-medium uppercase tracking-wider text-marble-600">
          {label}
        </span>
        <CivIcon icon={icon} color={color} size="sm" />
      </div>
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
        <g
          style={{
            transform: `translate(${cx}px, ${cy}px)`,
            transition: "transform 400ms cubic-bezier(0.33, 1, 0.68, 1)",
          }}
        >
          <circle r="4" fill={color} />
        </g>
      </svg>
      <span className="w-12 font-mono text-xs tabular-nums text-marble-700">
        <AnimatedNumber value={values[currentIndex]} />
      </span>
    </div>
  );
}
