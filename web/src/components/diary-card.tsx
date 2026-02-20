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
  Pickaxe,
  Swords,
  Shield,
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

      {/* Stockpiles */}
      {s.stockpiles && Object.keys(s.stockpiles).length > 0 && (
        <div className="mb-4">
          <h3 className="mb-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
            Strategic Resources
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(s.stockpiles).map(([name, res]) => {
              const net = res.per_turn - res.demand
              const prevRes = ps?.stockpiles?.[name]
              const prevNet = prevRes ? prevRes.per_turn - prevRes.demand : undefined
              const short = name.replace("RESOURCE_", "").charAt(0) + name.replace("RESOURCE_", "").slice(1).toLowerCase()
              return (
                <div
                  key={name}
                  className="flex items-center gap-1 rounded-sm bg-marble-100 px-2 py-1"
                >
                  <Pickaxe className="h-3 w-3 text-marble-500" />
                  <span className="font-mono text-xs tabular-nums text-marble-800">
                    {short}: {res.amount}
                  </span>
                  <span className={`font-mono text-[10px] tabular-nums ${net >= 0 ? "text-patina" : "text-terracotta"}`}>
                    ({net >= 0 ? "+" : ""}{net}/t)
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Rivals */}
      {entry.rivals && entry.rivals.length > 0 && (
        <div className="mb-4 rounded-sm border border-marble-300/50 bg-marble-50">
          <button
            onClick={() => toggleSection("rivals")}
            className="flex w-full items-center gap-2 px-3 py-2 text-left transition-colors hover:bg-marble-100"
          >
            <Swords className="h-3.5 w-3.5 shrink-0 text-terracotta" />
            <span className="flex-1 font-display text-xs font-bold uppercase tracking-[0.1em] text-marble-700">
              Rivals
            </span>
            {expandedSections.has("rivals") ? (
              <ChevronUp className="h-3 w-3 text-marble-400" />
            ) : (
              <ChevronDown className="h-3 w-3 text-marble-400" />
            )}
          </button>
          {expandedSections.has("rivals") && (
            <div className="border-t border-marble-300/30 px-3 py-2 overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-[10px] uppercase tracking-wider text-marble-500">
                    <th className="text-left py-1 pr-2">Civ</th>
                    <th className="text-right py-1 px-1">Score</th>
                    <th className="text-right py-1 px-1">Cities</th>
                    <th className="text-right py-1 px-1">Pop</th>
                    <th className="text-right py-1 px-1">Sci</th>
                    <th className="text-right py-1 px-1">Cul</th>
                    <th className="text-right py-1 px-1">Mil</th>
                  </tr>
                </thead>
                <tbody>
                  {entry.rivals.map((r) => {
                    const prevR = prev?.rivals?.find((pr) => pr.id === r.id)
                    return (
                      <tr key={r.id} className="border-t border-marble-200/50">
                        <td className="py-1 pr-2 font-medium text-marble-700">{r.name}</td>
                        <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                          {r.score}<ScoreDelta current={r.score} prev={prevR?.score} />
                        </td>
                        <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                          {r.cities}<ScoreDelta current={r.cities} prev={prevR?.cities} />
                        </td>
                        <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                          {r.pop}<ScoreDelta current={r.pop} prev={prevR?.pop} />
                        </td>
                        <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                          {Math.round(r.sci)}<ScoreDelta current={r.sci} prev={prevR?.sci} />
                        </td>
                        <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                          {Math.round(r.cul)}<ScoreDelta current={r.cul} prev={prevR?.cul} />
                        </td>
                        <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                          {r.mil}<ScoreDelta current={r.mil} prev={prevR?.mil} />
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

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
