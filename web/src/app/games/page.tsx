"use client"

import { useRouter } from "next/navigation"
import { NavBar } from "@/components/nav-bar"
import { useDiaryList } from "@/lib/use-diary"
import { getCivColors } from "@/lib/civ-colors"
import { getCivSymbol } from "@/lib/civ-images"
import { getModelMeta, formatModelName } from "@/lib/model-registry"
import { LeaderPortrait } from "@/components/leader-portrait"
import { GameStatusBadge } from "@/components/game-status-badge"

function slugFromFilename(filename: string): string {
  return filename.replace(/^diary_/, "").replace(/\.jsonl$/, "")
}

export default function GamesPage() {
  const router = useRouter()
  const games = useDiaryList()

  // Live games first, then by turn count descending
  const sorted = [...games].sort((a, b) => {
    if (a.status === "live" && b.status !== "live") return -1
    if (b.status === "live" && a.status !== "live") return 1
    return b.count - a.count
  })

  return (
    <div className="flex min-h-screen flex-col">
      <NavBar active="games" />

      <main className="flex-1 px-3 py-6 sm:px-6 sm:py-10">
        <div className="mx-auto max-w-5xl">
          <h2 className="font-display text-xl font-bold tracking-[0.1em] uppercase text-marble-800">
            Games
          </h2>
          <p className="mt-1 text-sm text-marble-500">
            Turn-by-turn diaries, agent reflections, and tool call logs.
          </p>

          {games.length === 0 ? (
            <div className="mt-12 flex items-center justify-center">
              <p className="font-display text-sm tracking-[0.12em] uppercase text-marble-500">
                No games yet
              </p>
            </div>
          ) : (
            <div className="mt-6 overflow-x-auto rounded-sm border border-marble-300/50">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-marble-300/50 bg-marble-100 text-left text-[10px] font-bold uppercase tracking-[0.1em] text-marble-500">
                    <th className="px-3 py-2.5">Game</th>
                    <th className="hidden px-3 py-2.5 sm:table-cell">Model</th>
                    <th className="px-3 py-2.5 text-right">Result</th>
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((game) => {
                    const slug = slugFromFilename(game.filename)
                    const colors = getCivColors(game.label, game.leader)
                    const symbol = getCivSymbol(game.label)
                    const modelMeta = game.agentModel ? getModelMeta(game.agentModel) : null

                    return (
                      <tr
                        key={game.filename}
                        className="border-b border-marble-300/30 last:border-0 transition-colors hover:bg-marble-100/50 cursor-pointer"
                        style={{ borderLeftWidth: 5, borderLeftColor: colors.primary }}
                        onClick={() => { router.push(`/games/${slug}`) }}
                      >
                        {/* Game — portrait + civ info */}
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-2.5">
                            <LeaderPortrait
                              leader={game.leader}
                              agentModel={game.agentModel}
                              fallbackColor={colors.primary}
                              size="md"
                            />
                            <div className="min-w-0">
                              <div className="flex items-center gap-1.5">
                                {symbol && (
                                  <img src={symbol} alt="" className="h-3.5 w-3.5 shrink-0 rounded-full object-cover" />
                                )}
                                <span className="font-display text-xs font-bold tracking-wide uppercase text-marble-800">
                                  {game.label}
                                </span>
                              </div>
                              {game.leader && (
                                <p className="mt-0.5 text-[10px] text-marble-500 truncate">
                                  {game.leader}
                                </p>
                              )}
                            </div>
                          </div>
                        </td>

                        {/* Model */}
                        <td className="hidden px-3 py-2 sm:table-cell">
                          {modelMeta ? (
                            <div className="flex items-center gap-1.5">
                              {modelMeta.providerLogo && (
                                <img src={modelMeta.providerLogo} alt="" className="h-3.5 w-3.5" />
                              )}
                              <span className="text-xs text-marble-600">
                                {formatModelName(game.agentModel!)}
                              </span>
                            </div>
                          ) : (
                            <span className="text-xs text-marble-400">&mdash;</span>
                          )}
                        </td>

                        {/* Result — merged status + outcome + turns */}
                        <td className="px-3 py-2">
                          <GameStatusBadge
                            status={game.status}
                            outcome={game.outcome}
                            turnCount={game.count}
                          />
                          {game.outcome?.winnerLeader && (
                            <p className="mt-0.5 text-right text-[10px] text-marble-400">
                              {game.outcome.winnerLeader}
                            </p>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
