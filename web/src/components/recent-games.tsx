"use client"

import Link from "next/link"
import { useDiaryList } from "@/lib/use-diary"
import { getCivColors } from "@/lib/civ-colors"

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
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span
                    className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
                    style={{ backgroundColor: colors.primary }}
                  />
                  <span className="font-display text-sm font-bold tracking-wide uppercase text-marble-800">
                    {game.label}
                  </span>
                </div>
                {game.leader && (
                  <p className="mt-0.5 pl-[18px] text-xs text-marble-500">
                    {game.leader}
                  </p>
                )}
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
