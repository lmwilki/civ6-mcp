"use client"

import type { GameOverview, CityInfo, UnitInfo } from "@/lib/game-types"
import {
  Coins,
  FlaskConical,
  Palette,
  Flame,
  Microscope,
  BookOpen,
  Building2,
  Swords,
  Trophy,
  Sword,
  Target,
  Hammer,
  Flag,
  Package,
  Compass,
  Heart,
  Users,
  Shield,
  Star,
  CircleDot,
} from "lucide-react"

// Map unit types to icons
function unitIcon(unitType: string) {
  const t = unitType.toUpperCase()
  if (t.includes("ARCHER") || t.includes("CROSSBOW") || t.includes("SLINGER"))
    return <Target className="h-3 w-3 text-terracotta" />
  if (t.includes("WARRIOR") || t.includes("SWORDSMAN") || t.includes("MAN_AT_ARMS") || t.includes("MUSKET"))
    return <Sword className="h-3 w-3 text-terracotta" />
  if (t.includes("BUILDER"))
    return <Hammer className="h-3 w-3 text-patina" />
  if (t.includes("SETTLER"))
    return <Flag className="h-3 w-3 text-gold-dark" />
  if (t.includes("TRADER"))
    return <Package className="h-3 w-3 text-gold-dark" />
  if (t.includes("SCOUT") || t.includes("RANGER"))
    return <Compass className="h-3 w-3 text-marble-600" />
  if (t.includes("KNIGHT") || t.includes("CAVALRY") || t.includes("HORSEMAN"))
    return <Shield className="h-3 w-3 text-terracotta" />
  return <CircleDot className="h-3 w-3 text-marble-500" />
}

interface GameOverviewPanelProps {
  overview: GameOverview | null
  cities: CityInfo[]
  units: UnitInfo[]
  connected: boolean
}

function YieldRow({
  icon,
  label,
  value,
  perTurn,
}: {
  icon: React.ReactNode
  label: string
  value: number
  perTurn?: number
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="flex items-center gap-1.5 text-sm text-marble-600">
        {icon}
        {label}
      </span>
      <span className="font-mono text-sm tabular-nums text-marble-800">
        {Math.round(value * 10) / 10}
        {perTurn !== undefined && (
          <span className="text-marble-500"> (+{Math.round(perTurn * 10) / 10})</span>
        )}
      </span>
    </div>
  )
}

export function GameOverviewPanel({ overview, cities, units, connected }: GameOverviewPanelProps) {
  if (!connected) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <p className="font-display text-xs tracking-[0.12em] uppercase text-marble-400">
          Waiting for game...
        </p>
      </div>
    )
  }

  if (!overview) return null

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      {/* Header */}
      <div className="border-b border-marble-300 p-4">
        <h2 className="font-display text-xs font-bold tracking-[0.15em] uppercase text-marble-700">
          {overview.civ_name}
        </h2>
        <p className="mt-1 text-sm text-marble-600">
          {overview.leader_name} — Turn {overview.turn}
        </p>
        <div className="mt-0.5 flex items-center gap-1 font-mono text-xs text-marble-500">
          <Star className="h-3 w-3" />
          {overview.score}
        </div>
      </div>

      {/* Yields */}
      <div className="border-b border-marble-300 p-4">
        <h3 className="font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
          Yields
        </h3>
        <div className="mt-2 space-y-1.5">
          <YieldRow
            icon={<Coins className="h-3.5 w-3.5 text-gold-dark" />}
            label="Gold"
            value={overview.gold}
            perTurn={overview.gold_per_turn}
          />
          <YieldRow
            icon={<FlaskConical className="h-3.5 w-3.5 text-blue-600" />}
            label="Science"
            value={overview.science_yield}
          />
          <YieldRow
            icon={<Palette className="h-3.5 w-3.5 text-purple-600" />}
            label="Culture"
            value={overview.culture_yield}
          />
          <YieldRow
            icon={<Flame className="h-3.5 w-3.5 text-terracotta" />}
            label="Faith"
            value={overview.faith}
          />
        </div>
      </div>

      {/* Research */}
      <div className="border-b border-marble-300 p-4">
        <h3 className="font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
          Research
        </h3>
        <div className="mt-2 space-y-1.5 text-sm">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-marble-600">
              <Microscope className="h-3.5 w-3.5 text-blue-600" />
              Tech
            </span>
            <span className="font-mono text-xs text-marble-700">{overview.current_research || "None"}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-marble-600">
              <BookOpen className="h-3.5 w-3.5 text-purple-600" />
              Civic
            </span>
            <span className="font-mono text-xs text-marble-700">{overview.current_civic || "None"}</span>
          </div>
        </div>
      </div>

      {/* Rankings */}
      {overview.rankings && overview.rankings.length > 0 && (
        <div className="border-b border-marble-300 p-4">
          <h3 className="flex items-center gap-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
            <Trophy className="h-3 w-3" />
            Rankings
          </h3>
          <div className="mt-2 space-y-0.5">
            {overview.rankings.map((r, i) => (
              <div key={i} className="flex justify-between text-xs">
                <span className={r.civ_name === overview.civ_name ? "font-semibold text-gold-dark" : "text-marble-600"}>
                  {r.civ_name}
                </span>
                <span className="font-mono tabular-nums text-marble-500">{r.score}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cities */}
      <div className="border-b border-marble-300 p-4">
        <h3 className="flex items-center gap-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
          <Building2 className="h-3 w-3" />
          Cities ({cities.length})
        </h3>
        <div className="mt-2 space-y-2">
          {cities.map((c) => (
            <div key={c.city_id} className="text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-marble-800">{c.name}</span>
                <span className="flex items-center gap-1 font-mono tabular-nums text-marble-500">
                  <Users className="h-2.5 w-2.5" />
                  {c.population}
                </span>
              </div>
              <div className="mt-0.5 flex items-center gap-1 font-mono text-marble-500">
                <Hammer className="h-2.5 w-2.5 shrink-0" />
                <span className="truncate">
                  {formatProduction(c.currently_building)}
                  {c.production_turns_left > 0 && ` (${c.production_turns_left}t)`}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Units */}
      <div className="p-4">
        <h3 className="flex items-center gap-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
          <Swords className="h-3 w-3" />
          Units ({units.length})
        </h3>
        <div className="mt-2 space-y-1">
          {units.map((u) => (
            <div key={u.unit_id} className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-1.5 text-marble-700">
                {unitIcon(u.unit_type)}
                {u.name}
              </span>
              <span className="font-mono tabular-nums text-marble-500">
                ({u.x},{u.y})
                {u.health < u.max_health && (
                  <span className="ml-1 inline-flex items-center gap-0.5 text-terracotta">
                    <Heart className="h-2.5 w-2.5" />
                    {u.health}
                  </span>
                )}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function formatProduction(raw: string): string {
  if (!raw || raw === "nothing") return "idle"
  return raw
    .replace(/^(UNIT_|BUILDING_|DISTRICT_)/, "")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase())
}
