"use client"

import { useElo } from "@/lib/use-elo"
import { formatModelName } from "@/lib/diary-types"
import { getLeaderPortrait, getCivSymbol } from "@/lib/civ-registry"
import { Bot } from "lucide-react"

export function ModelLeaderboard() {
  const { ratings, gameCount, loading } = useElo()

  if (loading || ratings.length === 0) return null

  return (
    <section>
      <div className="flex items-baseline justify-between">
        <h3 className="font-display text-xs font-bold uppercase tracking-[0.12em] text-marble-500">
          ELO Leaderboard
        </h3>
        <span className="text-[10px] tabular-nums text-marble-400">
          {gameCount} game{gameCount !== 1 ? "s" : ""}
        </span>
      </div>

      <div className="mt-3 overflow-x-auto rounded-sm border border-marble-300/50">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-marble-300/50 bg-marble-100 text-left text-[10px] font-bold uppercase tracking-[0.1em] text-marble-500">
              <th className="px-3 py-2 text-center">#</th>
              <th className="px-3 py-2">Player</th>
              <th className="px-3 py-2 text-right">ELO</th>
              <th className="hidden px-3 py-2 text-right sm:table-cell">W-L</th>
              <th className="hidden px-3 py-2 text-right sm:table-cell">Win%</th>
            </tr>
          </thead>
          <tbody>
            {ratings.map((entry, i) => {
              const winPct =
                entry.games > 0
                  ? Math.round((entry.wins / entry.games) * 100)
                  : 0

              return (
                <tr
                  key={entry.id}
                  className="border-b border-marble-300/30 last:border-0 transition-colors hover:bg-marble-100/50"
                >
                  {/* Rank */}
                  <td className="px-3 py-2 text-center font-mono text-xs tabular-nums text-marble-400">
                    {i + 1}
                  </td>

                  {/* Player */}
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-2">
                      <PlayerAvatar entry={entry} />
                      <div className="min-w-0">
                        <span className="font-display text-xs font-bold tracking-wide uppercase text-marble-800">
                          {entry.type === "model"
                            ? formatModelName(entry.name)
                            : entry.name}
                        </span>
                        <span className="ml-1.5 text-[10px] text-marble-400">
                          {entry.type === "model" ? "LLM" : "AI"}
                        </span>
                      </div>
                    </div>
                  </td>

                  {/* ELO */}
                  <td className="px-3 py-2 text-right">
                    <span
                      className={`font-mono text-sm font-semibold tabular-nums ${
                        entry.elo >= 1500 ? "text-patina" : "text-terracotta"
                      }`}
                    >
                      {entry.elo}
                    </span>
                  </td>

                  {/* W-L */}
                  <td className="hidden px-3 py-2 text-right font-mono text-xs tabular-nums text-marble-600 sm:table-cell">
                    {entry.wins}-{entry.losses}
                  </td>

                  {/* Win% */}
                  <td className="hidden px-3 py-2 text-right font-mono text-xs tabular-nums text-marble-600 sm:table-cell">
                    {winPct}%
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function PlayerAvatar({ entry }: { entry: { type: string; name: string } }) {
  if (entry.type === "model") {
    return (
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-marble-200">
        <Bot className="h-3.5 w-3.5 text-marble-600" />
      </span>
    )
  }

  // AI leader — try portrait, then civ symbol fallback
  const portrait = getLeaderPortrait(entry.name)
  if (portrait) {
    return (
      <img
        src={portrait}
        alt={entry.name}
        className="h-7 w-7 shrink-0 rounded-full border border-marble-300 object-cover object-top"
      />
    )
  }

  // Try civ symbol (entry.name is leader name, but getCivSymbol needs civ name — fallback to colored dot)
  const sym = getCivSymbol(entry.name)
  if (sym) {
    return (
      <img
        src={sym}
        alt={entry.name}
        className="h-7 w-7 shrink-0 rounded-full object-cover"
      />
    )
  }

  return (
    <span className="inline-block h-7 w-7 shrink-0 rounded-full bg-marble-300" />
  )
}
