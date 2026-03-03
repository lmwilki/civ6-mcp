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
import type { EloFilter } from "./use-elo";

export function useEloConvex(filter?: EloFilter): EloData {
  const raw = useQuery(api.diary.getEloData);

  return useMemo(() => {
    if (raw === undefined) return { ratings: [], gameCount: 0, loading: true, error: null };
    if (!raw || raw.length === 0)
      return { ratings: [], gameCount: 0, loading: false, error: null };

    // Apply optional filters before ELO computation
    let games = raw;
    if (filter?.scenarioId) {
      games = games.filter((g) => g.scenarioId === filter.scenarioId);
    }
    if (filter?.evalTrack) {
      games = games.filter((g) => g.evalTrack === filter.evalTrack);
    }

    const results: GameResult[] = games.map((g) => {
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
      error: null,
    };
  }, [raw, filter?.scenarioId, filter?.evalTrack]);
}
