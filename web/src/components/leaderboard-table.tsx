"use client"

import type { TurnData, PlayerRow } from "@/lib/diary-types"
import { ScoreDelta } from "./agent-overview"
import { CollapsiblePanel } from "./collapsible-panel"
import { Swords } from "lucide-react"

interface LeaderboardTableProps {
  turnData: TurnData
  prevTurnData?: TurnData
}

export function LeaderboardTable({ turnData, prevTurnData }: LeaderboardTableProps) {
  const allPlayers = [turnData.agent, ...turnData.rivals].sort((a, b) => b.score - a.score)

  function findPrev(pid: number): PlayerRow | undefined {
    if (!prevTurnData) return undefined
    if (prevTurnData.agent.pid === pid) return prevTurnData.agent
    return prevTurnData.rivals.find((r) => r.pid === pid)
  }

  return (
    <CollapsiblePanel
      icon={<Swords className="h-3.5 w-3.5 shrink-0 text-terracotta" />}
      title={`Leaderboard (${allPlayers.length} civs)`}
      defaultOpen
    >
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-[10px] uppercase tracking-wider text-marble-500">
              <th className="py-1 pr-1 text-right">#</th>
              <th className="py-1 px-1 text-left">Civ</th>
              <th className="py-1 px-1 text-right">Score</th>
              <th className="py-1 px-1 text-right">Cities</th>
              <th className="py-1 px-1 text-right">Pop</th>
              <th className="py-1 px-1 text-right">Sci</th>
              <th className="py-1 px-1 text-right">Cul</th>
              <th className="py-1 px-1 text-right">Gold</th>
              <th className="py-1 px-1 text-right">Mil</th>
              <th className="py-1 px-1 text-right">Techs</th>
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
                    {p.civ}
                  </td>
                  <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                    {p.score}<ScoreDelta current={p.score} prev={prev?.score} />
                  </td>
                  <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                    {p.cities}<ScoreDelta current={p.cities} prev={prev?.cities} />
                  </td>
                  <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                    {p.pop}<ScoreDelta current={p.pop} prev={prev?.pop} />
                  </td>
                  <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                    {Math.round(p.science)}<ScoreDelta current={p.science} prev={prev?.science} />
                  </td>
                  <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                    {Math.round(p.culture)}<ScoreDelta current={p.culture} prev={prev?.culture} />
                  </td>
                  <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                    {Math.round(p.gold)}<ScoreDelta current={p.gold} prev={prev?.gold} />
                  </td>
                  <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
                    {p.military}<ScoreDelta current={p.military} prev={prev?.military} />
                  </td>
                  <td className="py-1 px-1 text-right font-mono tabular-nums text-marble-700">
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
