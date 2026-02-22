"use client"

import type { TurnData } from "@/lib/diary-types"
import { cleanCivName } from "@/lib/diary-types"
import { CIV6_COLORS } from "@/lib/civ-colors"
import { CivIcon } from "./civ-icon"
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
  Anvil,
  ChessKnight,
  Factory,
  Droplet,
  Rocket,
  Radiation,
  Zap,
  Crown,
  Globe,
  Hourglass,
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
  HORSES: { icon: ChessKnight, color: CIV6_COLORS.horses },
  IRON: { icon: Anvil, color: CIV6_COLORS.iron },
  NITER: { icon: Zap, color: CIV6_COLORS.niter },
  COAL: { icon: Factory, color: CIV6_COLORS.coal },
  OIL: { icon: Droplet, color: CIV6_COLORS.oil },
  ALUMINUM: { icon: Rocket, color: CIV6_COLORS.aluminum },
  URANIUM: { icon: Radiation, color: CIV6_COLORS.uranium },
}

const AGE_COLORS: Record<string, string> = {
  GOLDEN: CIV6_COLORS.golden,
  HEROIC: CIV6_COLORS.heroic,
  DARK: CIV6_COLORS.dark,
  NORMAL: CIV6_COLORS.normal,
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
            <CivIcon icon={Star} color={CIV6_COLORS.goldMetal} size="sm" />
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
        <YieldPill icon={<CivIcon icon={FlaskConical} color={CIV6_COLORS.science} />} value={a.science} prev={pa?.science} label="Science" suffix="/t" />
        <YieldPill icon={<CivIcon icon={Palette} color={CIV6_COLORS.culture} />} value={a.culture} prev={pa?.culture} label="Culture" suffix="/t" />
        <YieldPill icon={<CivIcon icon={Coins} color={CIV6_COLORS.goldDark} />} value={a.gold} prev={pa?.gold} label="Gold" />
        <YieldPill icon={<CivIcon icon={Coins} color={CIV6_COLORS.gold} />} value={a.gold_per_turn} prev={pa?.gold_per_turn} label="GPT" suffix="/t" />
        <YieldPill icon={<CivIcon icon={Flame} color={CIV6_COLORS.faith} />} value={a.faith} prev={pa?.faith} label="Faith" />
        <YieldPill icon={<CivIcon icon={Flame} color={CIV6_COLORS.faith} />} value={a.faith_per_turn} prev={pa?.faith_per_turn} label="Faith/t" suffix="/t" />
        <YieldPill icon={<CivIcon icon={Building2} color={CIV6_COLORS.growth} />} value={a.cities} prev={pa?.cities} label="Cities" />
        <YieldPill icon={<CivIcon icon={Users} color={CIV6_COLORS.growth} />} value={a.pop} prev={pa?.pop} label="Pop" />
        <YieldPill icon={<CivIcon icon={Globe} color={CIV6_COLORS.favor} />} value={a.favor} prev={pa?.favor} label="Favor" />
        <YieldPill icon={<CivIcon icon={MapPin} color={CIV6_COLORS.marine} />} value={a.territory} prev={pa?.territory} label="Territory" />
        <YieldPill icon={<CivIcon icon={Compass} color={CIV6_COLORS.favor} />} value={a.exploration_pct ?? 0} prev={pa?.exploration_pct} label="Explored" suffix="%" />
        <YieldPill icon={<CivIcon icon={Hammer} color={CIV6_COLORS.production} />} value={a.improvements} prev={pa?.improvements} label="Improved" />
      </div>

      {/* Era / age / government row */}
      <div className="mb-4 flex flex-wrap gap-2">
        <div className="flex items-center gap-1.5 rounded-sm bg-marble-100 px-2 py-1">
          <CivIcon icon={Trophy} color={CIV6_COLORS.goldMetal} size="sm" />
          <div className="flex flex-col">
            <span className="font-mono text-sm tabular-nums text-marble-800">
              <AnimatedNumber value={a.era_score} decimals={0} />
              <ScoreDelta current={a.era_score} prev={pa?.era_score} />
            </span>
            <span className="text-[9px] uppercase tracking-wider text-marble-500">Era Score</span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 rounded-sm bg-marble-100 px-2 py-1">
          <CivIcon icon={Hourglass} color={AGE_COLORS[a.age] ?? CIV6_COLORS.normal} size="sm" />
          <div className="flex flex-col">
            <span className="font-mono text-sm text-marble-800">{a.age}</span>
            <span className="text-[9px] uppercase tracking-wider text-marble-500">Age</span>
          </div>
        </div>
        {a.government !== "NONE" && (
          <div className="flex items-center gap-1.5 rounded-sm bg-marble-100 px-2 py-1">
            <CivIcon icon={Crown} color={CIV6_COLORS.goldMetal} size="sm" />
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
                  <CivIcon icon={Icon} color={meta?.color || CIV6_COLORS.normal} size="sm" />
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
