"use client"

import { useState } from "react"
import type { DiaryEntry, DiaryScore } from "@/lib/diary-types"
import { AnimatedNumber } from "./animated-number"
import {
  Coins,
  FlaskConical,
  Palette,
  Flame,
  Building2,
  Users,
  Compass,
  Trophy,
  Star,
  ChevronDown,
  ChevronUp,
  Crosshair,
  Lightbulb,
  Wrench,
  CalendarClock,
  BrainCircuit,
} from "lucide-react"

function ScoreDelta({ current, prev, suffix }: { current: number; prev?: number; suffix?: string }) {
  if (prev === undefined) return null
  const delta = current - prev
  if (delta === 0) return null
  return (
    <span className={`ml-1 text-xs font-medium ${delta > 0 ? "text-patina" : "text-terracotta"}`}>
      {delta > 0 ? "+" : ""}{Math.round(delta * 10) / 10}{suffix}
    </span>
  )
}

function YieldPill({
  icon,
  value,
  prev,
  label,
  suffix,
}: {
  icon: React.ReactNode
  value: number
  prev?: number
  label: string
  suffix?: string
}) {
  return (
    <div className="flex items-center gap-1.5 rounded-sm bg-marble-100 px-2 py-1">
      {icon}
      <div className="flex flex-col">
        <span className="font-mono text-sm tabular-nums text-marble-800">
          <AnimatedNumber value={value} />
          {suffix}
          <ScoreDelta current={value} prev={prev} suffix={suffix} />
        </span>
        <span className="text-[10px] uppercase tracking-wider text-marble-600">{label}</span>
      </div>
    </div>
  )
}

const reflectionConfig = [
  { key: "tactical" as const, label: "Tactical", icon: Crosshair, color: "text-terracotta" },
  { key: "strategic" as const, label: "Strategic", icon: BrainCircuit, color: "text-blue-600" },
  { key: "tooling" as const, label: "Tooling", icon: Wrench, color: "text-marble-600" },
  { key: "planning" as const, label: "Planning", icon: CalendarClock, color: "text-patina" },
  { key: "hypothesis" as const, label: "Hypothesis", icon: Lightbulb, color: "text-gold-dark" },
]

interface DiaryCardProps {
  entry: DiaryEntry
  prev?: DiaryEntry
  index: number
  total: number
}

export function DiaryCard({ entry, prev, index, total }: DiaryCardProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(["tactical", "strategic"])
  )

  const toggleSection = (key: string) => {
    setExpandedSections((s) => {
      const next = new Set(s)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const s = entry.score
  const ps = prev?.score

  const timestamp = new Date(entry.timestamp).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  })

  return (
    <div className="mx-auto w-full max-w-2xl">
      {/* Header */}
      <div className="mb-4 flex items-baseline justify-between">
        <div>
          <h2 className="font-display text-2xl font-bold tracking-wide text-marble-800">
            Turn {entry.turn}
          </h2>
          <p className="mt-0.5 text-sm text-marble-600">
            {entry.civ} &middot; {s.era} &middot; {timestamp}
          </p>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1.5 font-mono text-lg tabular-nums text-marble-800">
            <Star className="h-4 w-4 text-gold" />
            <AnimatedNumber value={s.total} decimals={0} />
            <ScoreDelta current={s.total} prev={ps?.total} />
          </div>
          <p className="font-mono text-xs tabular-nums text-marble-600">
            Entry {index + 1} / {total}
          </p>
        </div>
      </div>

      {/* Score grid */}
      <div className="mb-4 grid grid-cols-4 gap-2">
        <YieldPill icon={<FlaskConical className="h-3.5 w-3.5 text-blue-600" />} value={s.science} prev={ps?.science} label="Science" suffix="/t" />
        <YieldPill icon={<Palette className="h-3.5 w-3.5 text-purple-600" />} value={s.culture} prev={ps?.culture} label="Culture" suffix="/t" />
        <YieldPill icon={<Coins className="h-3.5 w-3.5 text-gold-dark" />} value={s.gold} prev={ps?.gold} label="Gold" />
        <YieldPill icon={<Coins className="h-3 w-3 text-gold" />} value={s.gold_per_turn} prev={ps?.gold_per_turn} label="GPT" suffix="/t" />
        <YieldPill icon={<Flame className="h-3.5 w-3.5 text-terracotta" />} value={s.faith} prev={ps?.faith} label="Faith" />
        <YieldPill icon={<Building2 className="h-3.5 w-3.5 text-marble-700" />} value={s.cities} prev={ps?.cities} label="Cities" />
        <YieldPill icon={<Users className="h-3.5 w-3.5 text-marble-600" />} value={s.population ?? 0} prev={ps?.population} label="Pop" />
        <YieldPill icon={<Compass className="h-3.5 w-3.5 text-patina" />} value={s.exploration_pct} prev={ps?.exploration_pct} label="Explored" suffix="%" />
      </div>

      {/* Era / leader row */}
      <div className="mb-4 flex gap-2">
        <div className="flex items-center gap-1.5 rounded-sm bg-marble-100 px-2 py-1">
          <Trophy className="h-3.5 w-3.5 text-gold-dark" />
          <div className="flex flex-col">
            <span className="font-mono text-sm tabular-nums text-marble-800">
              <AnimatedNumber value={s.era_score} decimals={0} />
              <ScoreDelta current={s.era_score} prev={ps?.era_score} />
            </span>
            <span className="text-[9px] uppercase tracking-wider text-marble-500">Era Score</span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 rounded-sm bg-marble-100 px-2 py-1">
          <Star className="h-3.5 w-3.5 text-terracotta" />
          <div className="flex flex-col">
            <span className="font-mono text-sm tabular-nums text-marble-800">
              <AnimatedNumber value={s.leader_score} decimals={0} />
              <ScoreDelta current={s.leader_score} prev={ps?.leader_score} />
            </span>
            <span className="text-[9px] uppercase tracking-wider text-marble-500">Leader</span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 rounded-sm bg-marble-100 px-2 py-1">
          <Star className="h-3.5 w-3.5 text-marble-500" />
          <div className="flex flex-col">
            <span className="font-mono text-sm tabular-nums text-marble-800">
              <AnimatedNumber value={s.favor} decimals={0} />
              <ScoreDelta current={s.favor} prev={ps?.favor} />
            </span>
            <span className="text-[9px] uppercase tracking-wider text-marble-500">Favor</span>
          </div>
        </div>
      </div>

      {/* Reflections */}
      <div className="space-y-1">
        {reflectionConfig.map(({ key, label, icon: Icon, color }) => {
          const text = entry.reflections[key]
          if (!text) return null
          const expanded = expandedSections.has(key)
          return (
            <div key={key} className="rounded-sm border border-marble-300/50 bg-marble-50">
              <button
                onClick={() => toggleSection(key)}
                className="flex w-full items-center gap-2 px-3 py-2 text-left transition-colors hover:bg-marble-100"
              >
                <Icon className={`h-3.5 w-3.5 shrink-0 ${color}`} />
                <span className="flex-1 font-display text-xs font-bold uppercase tracking-[0.1em] text-marble-700">
                  {label}
                </span>
                {expanded ? (
                  <ChevronUp className="h-3 w-3 text-marble-400" />
                ) : (
                  <ChevronDown className="h-3 w-3 text-marble-400" />
                )}
              </button>
              {expanded && (
                <div className="border-t border-marble-300/30 px-3 py-2">
                  <p className="whitespace-pre-wrap text-sm leading-relaxed text-marble-700">
                    {text}
                  </p>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
