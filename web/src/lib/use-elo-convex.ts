"use client";

import { useQuery } from "convex/react";
import { api } from "../../convex/_generated/api";
import { useMemo } from "react";
import {
  computeElo,
  type EloData,
  type GameResult,
  type Participant,
} from "./elo";

export function useEloConvex(): EloData {
  const raw = useQuery(api.diary.getEloData);

  return useMemo(() => {
    if (raw === undefined) return { ratings: [], gameCount: 0, loading: true };
    if (!raw || raw.length === 0)
      return { ratings: [], gameCount: 0, loading: false };

    const results: GameResult[] = raw.map((g) => {
      const participants: Participant[] = g.players.map((p) => {
        const isAgent = p.is_agent;
        const id =
          isAgent && p.agent_model
            ? `model:${p.agent_model}`
            : `ai:${p.leader}`;
        return {
          id,
          name: isAgent && p.agent_model ? p.agent_model : p.leader,
          type: (isAgent && p.agent_model ? "model" : "ai_leader") as
            | "model"
            | "ai_leader",
          civ: p.civ,
          won: p.civ === g.winnerCiv,
        };
      });
      return { gameId: g.gameId, participants };
    });

    return {
      ratings: computeElo(results),
      gameCount: results.length,
      loading: false,
    };
  }, [raw]);
}
