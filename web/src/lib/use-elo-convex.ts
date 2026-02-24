"use client"

import { useMemo } from "react"
import { useQuery } from "convex/react"
import { api } from "../../convex/_generated/api"
import { computeElo, type GameResult, type Participant, type EloEntry } from "./elo"

interface EloData {
  ratings: EloEntry[]
  gameCount: number
  loading: boolean
}

/** Convex-backed ELO — real-time, no polling. */
export function useEloConvex(): EloData {
  const data = useQuery(api.diary.getEloData)

  const { ratings, gameCount } = useMemo(() => {
    if (!data) return { ratings: [] as EloEntry[], gameCount: 0 }

    const results: GameResult[] = []
    for (const game of data) {
      const participants: Participant[] = []
      for (const p of game.players) {
        const won = p.civ.toUpperCase() === game.winnerCiv.toUpperCase()
        if (p.is_agent && p.agent_model) {
          participants.push({
            id: `model:${p.agent_model}`,
            name: p.agent_model,
            type: "model",
            civ: p.civ,
            won,
          })
        } else {
          participants.push({
            id: `ai:${p.leader}`,
            name: p.leader,
            type: "ai_leader",
            civ: p.civ,
            won,
          })
        }
      }
      results.push({ gameId: game.gameId, participants })
    }

    return { ratings: computeElo(results), gameCount: results.length }
  }, [data])

  return { ratings, gameCount, loading: data === undefined }
}
