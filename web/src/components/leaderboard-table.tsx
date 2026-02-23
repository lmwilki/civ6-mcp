"use client"

import type { TurnData, PlayerRow } from "@/lib/diary-types"
import { ScoreDelta } from "./agent-overview"
import { CollapsiblePanel } from "./collapsible-panel"
import { CivIcon } from "./civ-icon"
import { CIV6_COLORS, getCivColors } from "@/lib/civ-colors"
import { Medal } from "lucide-react"

interface LeaderboardTableProps {
  turnData: TurnData
  prevTurnData?: TurnData
}

export function LeaderboardTable({ turnData, prevTurnData }: LeaderboardTableProps) {
  const allPlayers = [turnData.agent, ...turnData.rivals].sort((a, b) => b.score - a.score)

  const best = {
    score: Math.max(...allPlayers.map(p => p.score)),
    cities: Math.max(...allPlayers.map(p => p.cities)),
    pop: Math.max(...allPlayers.map(p => p.pop)),
    science: Math.max(...allPlayers.map(p => p.science)),
    culture: Math.max(...allPlayers.map(p => p.culture)),
    gold: Math.max(...allPlayers.map(p => p.gold)),
    military: Math.max(...allPlayers.map(p => p.military)),
    techs: Math.max(...allPlayers.map(p => p.techs_completed)),
  }

  const b = (val: number, bestVal: number) =>
    val >= bestVal ? "font-extrabold text-marble-900" : "text-marble-600"

  function findPrev(pid: number): PlayerRow | undefined {
    if (!prevTurnData) return undefined
    if (prevTurnData.agent.pid === pid) return prevTurnData.agent
    return prevTurnData.rivals.find((r) => r.pid === pid)
  }

  return (
    <CollapsiblePanel
      icon={<CivIcon icon={Medal} color={CIV6_COLORS.goldMetal} size="sm" />}
      title={`Leaderboard (${allPlayers.length} civs)`}
      defaultOpen
    >
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-[10px] uppercase tracking-wider text-marble-500">
              <th className="py-1 pr-1 text-right">#</th>
              <th className="py-1 px-1 text-left">Civ</th>
              <th className="py-1 px-1 text-left">Score</th>
              <th className="py-1 px-1 text-left">Cities</th>
              <th className="py-1 px-1 text-left">Pop</th>
              <th className="py-1 px-1 text-left">Sci</th>
              <th className="py-1 px-1 text-left">Cul</th>
              <th className="py-1 px-1 text-left">Gold</th>
              <th className="py-1 px-1 text-left">Mil</th>
              <th className="py-1 px-1 text-left">Techs</th>
            </tr>
          </thead>
          <tbody>
            {allPlayers.map((p, rank) => {
              const prev = findPrev(p.pid)
              const isAgent = p.is_agent
              return (
                <tr
                  key={p.pid}
                  className={`border-t border-marble-200/50 ${isAgent ? "bg-gold/5" : ""}`}
                >
                  <td className="py-1 pr-1 text-right font-mono tabular-nums text-marble-500">
                    {rank + 1}
                  </td>
                  <td className={`py-1 px-1 ${isAgent ? "font-semibold text-gold-dark" : "font-medium text-marble-700"}`}>
                    <span className="flex items-center gap-1.5">
                      <span
                        className="inline-block h-2 w-2 shrink-0 rounded-full"
                        style={{ backgroundColor: getCivColors(p.civ, p.leader).primary }}
                      />
                      {p.civ}
                    </span>
                  </td>
                  <td className={`py-1 px-1 font-mono tabular-nums ${b(p.score, best.score)}`}>
                    {p.score} <ScoreDelta current={p.score} prev={prev?.score} />
                  </td>
                  <td className={`py-1 px-1 font-mono tabular-nums ${b(p.cities, best.cities)}`}>
                    {p.cities} <ScoreDelta current={p.cities} prev={prev?.cities} />
                  </td>
                  <td className={`py-1 px-1 font-mono tabular-nums ${b(p.pop, best.pop)}`}>
                    {p.pop} <ScoreDelta current={p.pop} prev={prev?.pop} />
                  </td>
                  <td className={`py-1 px-1 font-mono tabular-nums ${b(p.science, best.science)}`}>
                    {Math.round(p.science)} <ScoreDelta current={p.science} prev={prev?.science} />
                  </td>
                  <td className={`py-1 px-1 font-mono tabular-nums ${b(p.culture, best.culture)}`}>
                    {Math.round(p.culture)} <ScoreDelta current={p.culture} prev={prev?.culture} />
                  </td>
                  <td className={`py-1 px-1 font-mono tabular-nums ${b(p.gold, best.gold)}`}>
                    {Math.round(p.gold)} <ScoreDelta current={p.gold} prev={prev?.gold} />
                  </td>
                  <td className={`py-1 px-1 font-mono tabular-nums ${b(p.military, best.military)}`}>
                    {p.military} <ScoreDelta current={p.military} prev={prev?.military} />
                  </td>
                  <td className={`py-1 px-1 font-mono tabular-nums ${b(p.techs_completed, best.techs)}`}>
                    {p.techs_completed}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </CollapsiblePanel>
  )
}
