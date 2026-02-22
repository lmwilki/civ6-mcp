"use client"

import type { TurnData } from "@/lib/diary-types"
import { cleanCivName } from "@/lib/diary-types"
import { AnimatedNumber } from "./animated-number"
import {
  Coins,
  FlaskConical,
  Palette,
  Flame,
  Building2,
  Users,
  Compass,
  Star,
  Trophy,
  MapPin,
  Hammer,
  Pickaxe,
  Swords as SwordsIcon,
  Anvil,
  ChessKnight,
  Factory,
  Droplet,
  Rocket,
  Radiation,
  Flame as FlameIcon,
  Crown,
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

const RESOURCE_META: Record<string, { icon: React.ComponentType<React.SVGProps<SVGSVGElement>>; color: string }> = {
  HORSES: { icon: ChessKnight, color: "text-amber-700" },
  IRON: { icon: Anvil, color: "text-slate-500" },
  NITER: { icon: FlameIcon, color: "text-orange-500" },
  COAL: { icon: Factory, color: "text-stone-600" },
  OIL: { icon: Droplet, color: "text-amber-950" },
  ALUMINUM: { icon: Rocket, color: "text-sky-400" },
  URANIUM: { icon: Radiation, color: "text-lime-500" },
}

const AGE_COLORS: Record<string, string> = {
  GOLDEN: "text-gold-dark",
  HEROIC: "text-purple-600",
  DARK: "text-red-700",
  NORMAL: "text-marble-600",
}


interface AgentOverviewProps {
  turnData: TurnData
  prevTurnData?: TurnData
  index: number
  total: number
}

export function AgentOverview({ turnData, prevTurnData, index, total }: AgentOverviewProps) {
  const a = turnData.agent
  const pa = prevTurnData?.agent

  const timestamp = new Date(a.timestamp).toLocaleString("en-US", {
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
            Turn {a.turn}
          </h2>
          <p className="mt-0.5 text-sm text-marble-600">
            {a.civ} ({a.leader}) &middot; {cleanCivName(a.era)} &middot; {timestamp}
          </p>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1.5 font-mono text-lg tabular-nums text-marble-800">
            <Star className="h-4 w-4 text-gold" />
            <AnimatedNumber value={a.score} decimals={0} />
            <ScoreDelta current={a.score} prev={pa?.score} />
          </div>
          <p className="font-mono text-xs tabular-nums text-marble-600">
            Entry {index + 1} / {total}
          </p>
        </div>
      </div>

      {/* Yield grid */}
      <div className="mb-4 grid grid-cols-4 gap-2">
        <YieldPill icon={<FlaskConical className="h-3.5 w-3.5 text-blue-600" />} value={a.science} prev={pa?.science} label="Science" suffix="/t" />
        <YieldPill icon={<Palette className="h-3.5 w-3.5 text-purple-600" />} value={a.culture} prev={pa?.culture} label="Culture" suffix="/t" />
        <YieldPill icon={<Coins className="h-3.5 w-3.5 text-gold-dark" />} value={a.gold} prev={pa?.gold} label="Gold" />
        <YieldPill icon={<Coins className="h-3 w-3 text-gold" />} value={a.gold_per_turn} prev={pa?.gold_per_turn} label="GPT" suffix="/t" />
        <YieldPill icon={<Flame className="h-3.5 w-3.5 text-terracotta" />} value={a.faith} prev={pa?.faith} label="Faith" />
        <YieldPill icon={<Flame className="h-3 w-3 text-terracotta/70" />} value={a.faith_per_turn} prev={pa?.faith_per_turn} label="Faith/t" suffix="/t" />
        <YieldPill icon={<Building2 className="h-3.5 w-3.5 text-marble-700" />} value={a.cities} prev={pa?.cities} label="Cities" />
        <YieldPill icon={<Users className="h-3.5 w-3.5 text-marble-600" />} value={a.pop} prev={pa?.pop} label="Pop" />
        <YieldPill icon={<Shield className="h-3.5 w-3.5 text-marble-500" />} value={a.favor} prev={pa?.favor} label="Favor" />
        <YieldPill icon={<MapPin className="h-3.5 w-3.5 text-patina" />} value={a.territory} prev={pa?.territory} label="Territory" />
        <YieldPill icon={<Compass className="h-3.5 w-3.5 text-patina" />} value={a.exploration_pct ?? 0} prev={pa?.exploration_pct} label="Explored" suffix="%" />
        <YieldPill icon={<Hammer className="h-3.5 w-3.5 text-marble-600" />} value={a.improvements} prev={pa?.improvements} label="Improved" />
      </div>

      {/* Era / age / government row */}
      <div className="mb-4 flex flex-wrap gap-2">
        <div className="flex items-center gap-1.5 rounded-sm bg-marble-100 px-2 py-1">
          <Trophy className="h-3.5 w-3.5 text-gold-dark" />
          <div className="flex flex-col">
            <span className="font-mono text-sm tabular-nums text-marble-800">
              <AnimatedNumber value={a.era_score} decimals={0} />
              <ScoreDelta current={a.era_score} prev={pa?.era_score} />
            </span>
            <span className="text-[9px] uppercase tracking-wider text-marble-500">Era Score</span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 rounded-sm bg-marble-100 px-2 py-1">
          <Star className={`h-3.5 w-3.5 ${AGE_COLORS[a.age] ?? "text-marble-500"}`} />
          <div className="flex flex-col">
            <span className="font-mono text-sm text-marble-800">{a.age}</span>
            <span className="text-[9px] uppercase tracking-wider text-marble-500">Age</span>
          </div>
        </div>
        {a.government !== "NONE" && (
          <div className="flex items-center gap-1.5 rounded-sm bg-marble-100 px-2 py-1">
            <Crown className="h-3.5 w-3.5 text-marble-600" />
            <div className="flex flex-col">
              <span className="font-mono text-sm text-marble-800">{cleanCivName(a.government)}</span>
              <span className="text-[9px] uppercase tracking-wider text-marble-500">Government</span>
            </div>
          </div>
        )}
      </div>

      {/* Strategic resources */}
      {Object.keys(a.stockpiles).length > 0 && (
        <div className="mb-4">
          <h3 className="mb-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
            Strategic Resources
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(a.stockpiles).map(([name, amt]) => {
              const meta = RESOURCE_META[name]
              const Icon = meta?.icon || Pickaxe
              return (
                <div key={name} className="flex items-center gap-1 rounded-sm bg-marble-100 px-2 py-1">
                  <Icon className={`h-3.5 w-3.5 ${meta?.color || "text-marble-500"}`} />
                  <span className="font-mono text-xs tabular-nums text-marble-800">
                    {name.charAt(0) + name.slice(1).toLowerCase()}: {amt}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Luxury resources */}
      {Object.keys(a.luxuries).length > 0 && (
        <div className="mb-4">
          <h3 className="mb-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
            Luxuries
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(a.luxuries).map(([name, amt]) => (
              <div key={name} className="rounded-sm bg-marble-100 px-2 py-0.5">
                <span className="font-mono text-xs text-marble-700">
                  {name.charAt(0) + name.slice(1).toLowerCase()}{amt > 1 ? ` x${amt}` : ""}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export { ScoreDelta, YieldPill }
