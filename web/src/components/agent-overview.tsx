"use client"

import type { TurnData } from "@/lib/diary-types"
import { cleanCivName, formatModelName } from "@/lib/diary-types"
import { CIV6_COLORS } from "@/lib/civ-colors"
import { getLeaderPortrait, getCivSymbol } from "@/lib/civ-images"
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
  Citrus,
  Coffee,
  Wine,
  Diamond,
  CupSoda,
  Bean,
  Shell,
  Candy,
  Turtle,
  Fish,
  Ribbon,
  Flower2,
  Shirt,
  ToyBrick,
  Sparkles,
  SprayCan,
  PawPrint,
  TreePalm,
  Gem,
  Box,
  Mountain,
  Leaf,
  Snowflake,
  Bone,
  Sprout,
  TreePine,
  Flower,
  PiggyBank,
  Hexagon,
  Bot,
} from "lucide-react"

function ScoreDelta({ current, prev, suffix }: { current: number; prev?: number; suffix?: string }) {
  if (prev === undefined) return null
  const delta = current - prev
  if (delta === 0) return null
  return (
    <span className={`text-[9px] font-medium ${delta > 0 ? "text-patina" : "text-terracotta"}`}>
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
        <span className="flex items-baseline gap-0.5 font-mono text-sm tabular-nums text-marble-800">
          <span><AnimatedNumber value={value} />{suffix}</span>
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

const LUXURY_META: Record<string, { icon: React.ComponentType<React.SVGProps<SVGSVGElement>>; color: string }> = {
  // Fruits & plants
  CITRUS:    { icon: Citrus,    color: "#E8A630" },
  COCOA:     { icon: Bean,      color: "#6B3A2A" },
  COFFEE:    { icon: Coffee,    color: "#5C3A1A" },
  COTTON:    { icon: Flower2,   color: "#C4B8A8" },
  DYES:      { icon: Palette,   color: "#9B3B8C" },
  INCENSE:   { icon: Flame,     color: "#B07040" },
  OLIVES:    { icon: TreePalm,  color: "#6B7A3A" },
  SILK:      { icon: Ribbon,    color: "#C4445C" },
  SPICES:    { icon: Sprout,    color: "#A85C30" },
  SUGAR:     { icon: Candy,     color: "#D4A0C0" },
  TEA:       { icon: CupSoda,   color: "#5A8C4A" },
  TOBACCO:   { icon: Leaf,      color: "#7A6030" },
  WINE:      { icon: Wine,      color: "#8B2252" },
  HONEY:     { icon: Hexagon,   color: "#D4A020" },
  // Minerals & gems
  DIAMONDS:  { icon: Diamond,   color: "#7CB8DC" },
  GYPSUM:    { icon: Mountain,  color: "#C4B898" },
  JADE:      { icon: Gem,       color: "#4A9A5A" },
  MARBLE:    { icon: Box,       color: "#B8B0A4" },
  MERCURY:   { icon: Droplet,   color: "#A0A8B0" },
  SALT:      { icon: Snowflake, color: "#C8C0B0" },
  SILVER:    { icon: Coins,     color: "#A0A8B4" },
  AMBER:     { icon: Gem,       color: "#D4983C" },
  // Animals
  FURS:      { icon: PawPrint,  color: "#8B6E50" },
  IVORY:     { icon: Bone,      color: "#D8D0C0" },
  PEARLS:    { icon: Shell,     color: "#C8B8C8" },
  TRUFFLES:  { icon: PiggyBank, color: "#8C7060" },
  WHALES:    { icon: Fish,      color: "#4A7A9A" },
  TURTLES:   { icon: Turtle,    color: "#5A8A6A" },
  // Great Merchant exclusives
  COSMETICS: { icon: Sparkles,  color: "#D490A0" },
  JEANS:     { icon: Shirt,     color: "#4A6A9A" },
  PERFUME:   { icon: SprayCan,  color: "#B070B8" },
  TOYS:      { icon: ToyBrick,  color: "#D45040" },
  // City-state exclusives
  CINNAMON:  { icon: TreePine,  color: "#9A6830" },
  CLOVES:    { icon: Flower,    color: "#7A5A3A" },
  // Scenario
  GOLD_ORE:  { icon: Coins,     color: "#D4A853" },
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
      <div className="mb-4 flex items-center gap-3">
        {(() => {
          const portrait = getLeaderPortrait(a.leader)
          return portrait ? (
            <img
              src={portrait}
              alt={a.leader}
              className="h-14 w-14 shrink-0 rounded-full border-2 border-marble-300 object-cover object-top"
            />
          ) : null
        })()}
        <div className="flex flex-1 flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
          <div>
            <h2 className="font-display text-2xl font-bold tracking-wide text-marble-800">
              Turn {a.turn}
            </h2>
            <p className="mt-0.5 flex items-center gap-1.5 text-sm text-marble-600">
              {(() => {
                const sym = getCivSymbol(a.civ)
                return sym ? <img src={sym} alt="" className="inline h-4 w-4 rounded-full object-cover" /> : null
              })()}
              {a.civ} ({a.leader}) &middot; {cleanCivName(a.era)} &middot; {timestamp}
            </p>
            {a.agent_model && (
              <span className="mt-1 inline-flex w-fit items-center gap-1.5 rounded-full border border-marble-300 bg-marble-100 px-2.5 py-0.5 text-sm font-medium text-marble-700">
                <Bot className="h-4 w-4 text-marble-500" />
                {formatModelName(a.agent_model)}
              </span>
            )}
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
      </div>

      {/* Yield grid */}
      <div className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
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
            {Object.entries(a.luxuries).map(([name, amt]) => {
              const meta = LUXURY_META[name]
              const label = name.charAt(0) + name.slice(1).toLowerCase().replace(/_/g, " ")
              if (meta) {
                return (
                  <div key={name} className="flex items-center gap-1 rounded-sm bg-marble-100 px-2 py-0.5">
                    <CivIcon icon={meta.icon} color={meta.color} size="sm" />
                    <span className="font-mono text-xs text-marble-700">
                      {label}{amt > 1 ? <span className="text-marble-500"> x{amt}</span> : ""}
                    </span>
                  </div>
                )
              }
              return (
                <div key={name} className="rounded-sm bg-marble-100 px-2 py-0.5">
                  <span className="font-mono text-xs text-marble-700">
                    {label}{amt > 1 ? <span className="text-marble-500"> x{amt}</span> : ""}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

export { ScoreDelta, YieldPill }
