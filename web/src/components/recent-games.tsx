"use client"

import Link from "next/link"
import { useDiaryList } from "@/lib/use-diary"
import { formatModelName } from "@/lib/diary-types"
import { getCivColors } from "@/lib/civ-colors"
import { getCivSymbol, getLeaderPortrait } from "@/lib/civ-images"
import { Bot } from "lucide-react"

export function RecentGames() {
  const games = useDiaryList()

  if (games.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center rounded-sm border border-marble-300/50 bg-marble-50">
        <p className="text-sm text-marble-500">No games yet</p>
      </div>
    )
  }

  // Live games first, then by turn count descending
  const sorted = [...games].sort((a, b) => {
    if (a.status === "live" && b.status !== "live") return -1
    if (b.status === "live" && a.status !== "live") return 1
    return b.count - a.count
  })

  return (
    <div className="space-y-2">
      {sorted.map((game) => {
        const colors = getCivColors(game.label, game.leader)
        const isLive = game.status === "live"
        const outcome = game.outcome

        return (
          <Link
            key={game.filename}
            href={`/diary?game=${encodeURIComponent(game.filename)}`}
            className="group flex items-stretch gap-0 rounded-sm border border-marble-300/50 bg-marble-50 transition-colors hover:border-marble-400 hover:bg-marble-100"
          >
            {/* Color accent bar */}
            <div
              className="w-1.5 shrink-0 rounded-l-sm"
              style={{ backgroundColor: colors.primary }}
            />

            <div className="flex flex-1 items-center justify-between px-3 py-2.5">
              <div className="flex min-w-0 items-center gap-2.5">
                {(() => {
                  const portrait = game.leader ? getLeaderPortrait(game.leader) : null
                  return portrait ? (
                    <img
                      src={portrait}
                      alt=""
                      className="h-9 w-9 shrink-0 rounded-full border border-marble-300 object-cover object-top"
                    />
                  ) : (
                    <span
                      className="inline-block h-9 w-9 shrink-0 rounded-full"
                      style={{ backgroundColor: colors.primary }}
                    />
                  )
                })()}
                <div>
                  <div className="flex items-center gap-1.5">
                    {(() => {
                      const sym = getCivSymbol(game.label)
                      return sym ? (
                        <img src={sym} alt="" className="h-4 w-4 shrink-0 rounded-full object-cover" />
                      ) : null
                    })()}
                    <span className="font-display text-sm font-bold tracking-wide uppercase text-marble-800">
                      {game.label}
                    </span>
                  </div>
                  {game.leader && (
                    <p className="mt-0.5 text-xs text-marble-500">
                      {game.leader}
                    </p>
                  )}
                  {game.agent_model && (
                    <p className="mt-0.5 flex items-center gap-1 text-xs font-medium text-marble-600">
                      <Bot className="h-3 w-3 text-marble-400" />
                      {formatModelName(game.agent_model)}
                    </p>
                  )}
                </div>
              </div>

              <div className="shrink-0 pl-3 text-right">
                {isLive ? (
                  <div className="flex items-center gap-2">
                    <span className="relative flex h-2 w-2">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-patina opacity-75" />
                      <span className="relative inline-flex h-2 w-2 rounded-full bg-patina" />
                    </span>
                    <span className="font-mono text-xs tabular-nums text-marble-500">
                      T{game.count}
                    </span>
                  </div>
                ) : outcome ? (
                  <div>
                    <span className={`text-xs font-medium ${outcome.result === "victory" ? "text-patina" : "text-terracotta"}`}>
                      {outcome.result === "victory" ? "Victory" : "Defeated"} T{outcome.turn}
                    </span>
                    <p className="text-[10px] leading-tight text-marble-400">
                      {outcome.winnerLeader} ({outcome.victoryType})
                    </p>
                  </div>
                ) : (
                  <span className="font-mono text-xs tabular-nums text-marble-500">
                    {game.count} turns
                  </span>
                )}
              </div>
            </div>
          </Link>
        )
      })}
    </div>
  )
}
