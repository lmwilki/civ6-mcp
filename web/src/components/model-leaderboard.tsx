"use client"

import Link from "next/link"
import { useElo } from "@/lib/use-elo"
import { getModelMeta, formatModelName } from "@/lib/model-registry"
import type { EloEntry } from "@/lib/elo"
import { Bot, Trophy, ArrowRight } from "lucide-react"

// ─── Shared ─────────────────────────────────────────────────────────────────

function ModelAvatar({ entry, size = "md" }: { entry: EloEntry; size?: "sm" | "md" }) {
  const px = size === "sm" ? "h-6 w-6" : "h-7 w-7"
  const iconPx = size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5"
  const meta = getModelMeta(entry.name)

  if (meta.providerLogo) {
    return (
      <span className={`flex ${px} shrink-0 items-center justify-center rounded-full bg-marble-200`}>
        <img src={meta.providerLogo} alt={meta.provider} className={`${iconPx}`} />
      </span>
    )
  }

  return (
    <span className={`flex ${px} shrink-0 items-center justify-center rounded-full bg-marble-200`}>
      <Bot className={`${iconPx} text-marble-600`} />
    </span>
  )
}

function EloBadge({ elo }: { elo: number }) {
  return (
    <span
      className={`font-mono text-sm font-semibold tabular-nums ${
        elo >= 1500 ? "text-patina" : "text-terracotta"
      }`}
    >
      {elo}
    </span>
  )
}

const RANK_COLORS = ["text-gold-dark", "text-marble-500", "text-amber-700"]

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
          <Trophy className="h-3.5 w-3.5 text-gold-dark" />
          Model ELO Rankings
        </h3>
        <span className="text-[10px] tabular-nums text-marble-400">
          {gameCount} game{gameCount !== 1 ? "s" : ""}
        </span>
      </div>

      <div className="mt-3 space-y-1.5">
        {top3.map((entry, i) => {
          const meta = getModelMeta(entry.name)
          return (
            <div
              key={entry.id}
              className="flex items-center gap-3 rounded-sm border border-marble-300/50 bg-marble-50 px-3 py-2"
            >
              <span className={`font-mono text-sm font-bold tabular-nums ${RANK_COLORS[i] ?? "text-marble-400"}`}>
                {i + 1}
              </span>
              <ModelAvatar entry={entry} size="sm" />
              <div className="min-w-0 flex-1">
                <span className="font-display text-xs font-bold tracking-wide uppercase text-marble-800">
                  {formatModelName(entry.name)}
                </span>
                <span className="ml-1.5 text-[10px] text-marble-400">
                  {meta.provider}
                </span>
              </div>
              <EloBadge elo={entry.elo} />
            </div>
          )
        })}
      </div>

      <Link
        href="/leaderboard"
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

  return (
    <div className="space-y-10">
      {/* Rankings Table */}
      <section>
        <div className="flex items-baseline justify-between">
          <h2 className="font-display text-xs font-bold uppercase tracking-[0.12em] text-marble-500">
            Model ELO Rankings
          </h2>
          <span className="text-[10px] tabular-nums text-marble-400">
            {gameCount} game{gameCount !== 1 ? "s" : ""} played
          </span>
        </div>

        <div className="mt-3 overflow-x-auto rounded-sm border border-marble-300/50">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-marble-300/50 bg-marble-100 text-left text-[10px] font-bold uppercase tracking-[0.1em] text-marble-500">
                <th className="px-3 py-2 text-center">#</th>
                <th className="px-3 py-2">Model</th>
                <th className="hidden px-3 py-2 sm:table-cell">Provider</th>
                <th className="px-3 py-2 text-right">ELO</th>
                <th className="px-3 py-2 text-right">W-L</th>
                <th className="hidden px-3 py-2 text-right sm:table-cell">Win%</th>
                <th className="hidden px-3 py-2 text-right sm:table-cell">Games</th>
              </tr>
            </thead>
            <tbody>
              {models.map((entry, i) => {
                const meta = getModelMeta(entry.name)
                const winPct =
                  entry.games > 0
                    ? Math.round((entry.wins / entry.games) * 100)
                    : 0

                return (
                  <tr
                    key={entry.id}
                    className="border-b border-marble-300/30 last:border-0 transition-colors hover:bg-marble-100/50"
                  >
                    <td className="px-3 py-2 text-center font-mono text-xs tabular-nums text-marble-400">
                      {i + 1}
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        <ModelAvatar entry={entry} />
                        <span className="font-display text-xs font-bold tracking-wide uppercase text-marble-800">
                          {formatModelName(entry.name)}
                        </span>
                      </div>
                    </td>
                    <td className="hidden px-3 py-2 sm:table-cell">
                      <div className="flex items-center gap-1.5">
                        {meta.providerLogo && (
                          <img src={meta.providerLogo} alt="" className="h-3.5 w-3.5" />
                        )}
                        <span className="text-xs text-marble-500">
                          {meta.provider}
                        </span>
                      </div>
                    </td>
                    <td className="px-3 py-2 text-right">
                      <EloBadge elo={entry.elo} />
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-xs tabular-nums text-marble-600">
                      {entry.wins}-{entry.losses}
                    </td>
                    <td className="hidden px-3 py-2 text-right font-mono text-xs tabular-nums text-marble-600 sm:table-cell">
                      {winPct}%
                    </td>
                    <td className="hidden px-3 py-2 text-right font-mono text-xs tabular-nums text-marble-600 sm:table-cell">
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
        <h2 className="font-display text-xs font-bold uppercase tracking-[0.12em] text-marble-500">
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
                className="rounded-sm border border-marble-300/50 bg-marble-50 p-4"
                style={{ borderLeftColor: meta.color, borderLeftWidth: 3 }}
              >
                <div className="flex items-center gap-2.5">
                  {meta.providerLogo ? (
                    <img src={meta.providerLogo} alt={meta.provider} className="h-5 w-5" />
                  ) : (
                    <Bot className="h-5 w-5 text-marble-500" />
                  )}
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
                      {entry.wins}-{entry.losses}
                    </div>
                    <div className="text-[9px] uppercase tracking-wider text-marble-500">W-L</div>
                  </div>
                  <div className="text-center">
                    <div className="font-mono text-sm font-semibold tabular-nums text-marble-700">
                      {winPct}%
                    </div>
                    <div className="text-[9px] uppercase tracking-wider text-marble-500">Win</div>
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
