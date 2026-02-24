"use client"

import Link from "next/link"
import { useElo } from "@/lib/use-elo"
import { getModelMeta, formatModelName } from "@/lib/model-registry"
import { CivIcon } from "@/components/civ-icon"
import { CIV6_COLORS } from "@/lib/civ-colors"
import type { EloEntry } from "@/lib/elo"
import { Bot, Trophy, Medal, ArrowRight, Swords, TrendingUp } from "lucide-react"

// ─── Shared ─────────────────────────────────────────────────────────────────

const MEDAL_COLORS = [CIV6_COLORS.goldMetal, "#C0C0C0", "#CD7F32"] as const

function ModelAvatar({ entry, size = "md" }: { entry: EloEntry; size?: "sm" | "md" }) {
  const px = size === "sm" ? "h-6 w-6" : "h-8 w-8"
  const iconPx = size === "sm" ? "h-3 w-3" : "h-4 w-4"
  const meta = getModelMeta(entry.name)

  const bgColor = meta.providerLogo ? `${meta.color}18` : undefined

  if (meta.providerLogo) {
    return (
      <span
        className={`flex ${px} shrink-0 items-center justify-center rounded-full`}
        style={{ backgroundColor: bgColor }}
      >
        <img src={meta.providerLogo} alt={meta.provider} className={iconPx} />
      </span>
    )
  }

  return (
    <span className={`flex ${px} shrink-0 items-center justify-center rounded-full bg-marble-200`}>
      <Bot className={`${iconPx} text-marble-600`} />
    </span>
  )
}

function RankBadge({ rank }: { rank: number }) {
  if (rank <= 3) {
    return <CivIcon icon={Medal} color={MEDAL_COLORS[rank - 1]} size="sm" />
  }
  return (
    <span className="flex h-5 w-5 items-center justify-center font-mono text-xs tabular-nums text-marble-400">
      {rank}
    </span>
  )
}

function EloBadge({ elo, color }: { elo: number; color?: string }) {
  return (
    <span
      className={`font-mono text-sm font-semibold tabular-nums ${
        elo >= 1500 ? "text-patina" : "text-terracotta"
      }`}
      style={color ? { color } : undefined}
    >
      {elo}
    </span>
  )
}

function WinRateBar({ pct }: { pct: number }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className="relative h-1.5 w-12 overflow-hidden rounded-full bg-marble-200">
        <div
          className="absolute inset-y-0 left-0 rounded-full bg-patina/40"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="font-mono text-xs tabular-nums text-marble-600">
        {pct}%
      </span>
    </div>
  )
}

// ─── Preview (landing page) ─────────────────────────────────────────────────

export function LeaderboardPreview() {
  const { ratings, gameCount, loading } = useElo()

  if (loading) return null

  const models = ratings.filter((e) => e.type === "model")
  if (models.length === 0) return null

  const top3 = models.slice(0, 3)

  return (
    <section>
      <div className="flex items-baseline justify-between">
        <h3 className="flex items-center gap-1.5 font-display text-xs font-bold uppercase tracking-[0.12em] text-marble-500">
          <CivIcon icon={Trophy} color={CIV6_COLORS.goldMetal} size="sm" />
          Model ELO Rankings
        </h3>
        <span className="text-[10px] tabular-nums text-marble-400">
          {gameCount} game{gameCount !== 1 ? "s" : ""}
        </span>
      </div>

      <div className="mt-3 space-y-2">
        {top3.map((entry, i) => {
          const meta = getModelMeta(entry.name)
          return (
            <div
              key={entry.id}
              className="flex items-stretch gap-0 rounded-sm border border-marble-300/50 bg-marble-50"
            >
              <div
                className="w-1.5 shrink-0 rounded-l-sm"
                style={{ backgroundColor: meta.color }}
              />
              <div className="flex flex-1 items-center gap-2.5 pl-3 pr-2 py-2.5">
                <ModelAvatar entry={entry} size="sm" />
                <div className="min-w-0 flex-1">
                  <span className="font-display text-xs font-bold tracking-wide uppercase text-marble-800">
                    {formatModelName(entry.name)}
                  </span>
                  <span className="ml-1.5 text-[10px] text-marble-400">
                    {meta.provider}
                  </span>
                </div>
                <div className="flex flex-col items-end gap-0.5">
                  <span className="font-mono text-xs font-semibold tabular-nums text-marble-700">
                    {entry.elo}
                  </span>
                  <CivIcon icon={Medal} color={MEDAL_COLORS[i]} size="sm" />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <Link
        href="/civbench"
        className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-marble-500 transition-colors hover:text-gold-dark"
      >
        View Full Leaderboard
        <ArrowRight className="h-3.5 w-3.5" />
      </Link>
    </section>
  )
}

// ─── Full Leaderboard (dedicated page) ──────────────────────────────────────

export function FullLeaderboard() {
  const { ratings, gameCount, loading } = useElo()

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-sm text-marble-400">
        Loading ratings...
      </div>
    )
  }

  const models = ratings.filter((e) => e.type === "model")

  if (models.length === 0) {
    return (
      <div className="flex items-center justify-center py-20 text-sm text-marble-400">
        No completed games yet. Play some games to see ELO ratings.
      </div>
    )
  }

  // ELO range for proportional bars
  const eloMin = Math.min(...models.map((e) => e.elo))
  const eloMax = Math.max(...models.map((e) => e.elo))
  const eloRange = eloMax - eloMin || 1

  return (
    <div className="space-y-10">
      {/* Rankings Table */}
      <section>
        <div className="flex items-baseline justify-between">
          <h2 className="flex items-center gap-1.5 font-display text-xs font-bold uppercase tracking-[0.12em] text-marble-500">
            <CivIcon icon={TrendingUp} color={CIV6_COLORS.goldMetal} size="sm" />
            Rankings
          </h2>
          <span className="text-[10px] tabular-nums text-marble-400">
            {gameCount} game{gameCount !== 1 ? "s" : ""} played
          </span>
        </div>

        <div className="mt-3 overflow-x-auto rounded-sm border border-marble-300/50">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-marble-300/50 bg-marble-100 text-left text-[10px] font-bold uppercase tracking-[0.1em] text-marble-500">
                <th className="w-10 px-3 py-2.5 text-center">#</th>
                <th className="px-3 py-2.5">Model</th>
                <th className="hidden px-3 py-2.5 sm:table-cell">Provider</th>
                <th className="px-3 py-2.5 text-right">ELO</th>
                <th className="px-3 py-2.5 text-right">W-L</th>
                <th className="hidden px-3 py-2.5 text-right sm:table-cell">Win Rate</th>
                <th className="hidden px-3 py-2.5 text-right sm:table-cell">Games</th>
              </tr>
            </thead>
            <tbody>
              {models.map((entry, i) => {
                const meta = getModelMeta(entry.name)
                const winPct =
                  entry.games > 0
                    ? Math.round((entry.wins / entry.games) * 100)
                    : 0
                const eloBarWidth = ((entry.elo - eloMin) / eloRange) * 100

                return (
                  <tr
                    key={entry.id}
                    className="border-b border-marble-300/30 last:border-0 transition-colors hover:bg-marble-100/50"
                    style={{ borderLeftWidth: 5, borderLeftColor: meta.color }}
                  >
                    <td className="px-3 py-2.5 text-center">
                      <RankBadge rank={i + 1} />
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-2.5">
                        <ModelAvatar entry={entry} />
                        <span className="font-display text-xs font-bold tracking-wide uppercase text-marble-800">
                          {formatModelName(entry.name)}
                        </span>
                      </div>
                    </td>
                    <td className="hidden px-3 py-2.5 sm:table-cell">
                      <div className="flex items-center gap-1.5">
                        {meta.providerLogo && (
                          <img src={meta.providerLogo} alt="" className="h-3.5 w-3.5" />
                        )}
                        <span className="text-xs text-marble-500">
                          {meta.provider}
                        </span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      <div className="relative inline-flex items-center">
                        <div
                          className="absolute inset-y-0 right-0 rounded-sm opacity-10"
                          style={{
                            backgroundColor: meta.color,
                            width: `${eloBarWidth}%`,
                          }}
                        />
                        <EloBadge elo={entry.elo} />
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono text-xs tabular-nums text-marble-600">
                      <span className="text-patina">{entry.wins}</span>
                      <span className="text-marble-400">-</span>
                      <span className="text-terracotta">{entry.losses}</span>
                    </td>
                    <td className="hidden px-3 py-2.5 sm:table-cell">
                      <div className="flex justify-end">
                        <WinRateBar pct={winPct} />
                      </div>
                    </td>
                    <td className="hidden px-3 py-2.5 text-right font-mono text-xs tabular-nums text-marble-600 sm:table-cell">
                      {entry.games}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Model Cards */}
      <section>
        <h2 className="flex items-center gap-1.5 font-display text-xs font-bold uppercase tracking-[0.12em] text-marble-500">
          <CivIcon icon={Swords} color={CIV6_COLORS.military} size="sm" />
          Model Profiles
        </h2>
        <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {models.map((entry) => {
            const meta = getModelMeta(entry.name)
            const winPct =
              entry.games > 0
                ? Math.round((entry.wins / entry.games) * 100)
                : 0
            return (
              <div
                key={entry.id}
                className="flex items-stretch gap-0 rounded-sm border border-marble-300/50 bg-marble-50"
              >
                <div
                  className="w-1.5 shrink-0 rounded-l-sm"
                  style={{ backgroundColor: meta.color }}
                />
                <div className="flex-1 p-4">
                  <div className="flex items-center gap-2.5">
                    <ModelAvatar entry={entry} />
                    <div>
                      <div className="font-display text-xs font-bold uppercase tracking-wide text-marble-800">
                        {meta.name}
                      </div>
                      <div className="text-[10px] text-marble-500">{meta.provider}</div>
                    </div>
                  </div>
                  <div className="mt-3 grid grid-cols-3 gap-2">
                    <div className="text-center">
                      <div className="font-mono text-lg font-bold tabular-nums">
                        <EloBadge elo={entry.elo} />
                      </div>
                      <div className="text-[9px] uppercase tracking-wider text-marble-500">ELO</div>
                    </div>
                    <div className="text-center">
                      <div className="font-mono text-sm font-semibold tabular-nums text-marble-700">
                        <span className="text-patina">{entry.wins}</span>
                        <span className="text-marble-400">-</span>
                        <span className="text-terracotta">{entry.losses}</span>
                      </div>
                      <div className="text-[9px] uppercase tracking-wider text-marble-500">W-L</div>
                    </div>
                    <div className="text-center">
                      <div className="font-mono text-sm font-semibold tabular-nums text-marble-700">
                        {winPct}%
                      </div>
                      <div className="mt-0.5 mx-auto h-1 w-8 overflow-hidden rounded-full bg-marble-200">
                        <div
                          className="h-full rounded-full bg-patina/50"
                          style={{ width: `${winPct}%` }}
                        />
                      </div>
                      <div className="mt-0.5 text-[9px] uppercase tracking-wider text-marble-500">Win</div>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </section>
    </div>
  )
}
