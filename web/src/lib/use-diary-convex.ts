"use client";

import { useMemo } from "react";
import { useQuery } from "convex/react";
import { api } from "../../convex/_generated/api";
import type { Doc } from "../../convex/_generated/dataModel";
import type {
  PlayerRow,
  CityRow,
  TurnData,
  DiaryFile,
  GameOutcome,
  TurnSeries,
} from "./diary-types";
import { slugFromFilename, groupTurnData } from "./diary-types";

/** Convex-backed diary list — real-time, no polling. */
export function useDiaryListConvex(): DiaryFile[] {
  const games = useQuery(api.diary.listGames) ?? [];
  return games.map((g) => ({
    filename: g.filename,
    label: g.label,
    count: g.count,
    hasCities: g.hasCities,
    leader: g.leader,
    status: g.status as "live" | "completed",
    outcome: g.outcome ?? null,
    agentModel: g.agentModel ?? undefined,
    lastUpdated: g.lastUpdated,
    score: g.score ?? undefined,
  }));
}

/** Strip Convex system fields from a document */
function stripConvexFields<
  T extends { _id: unknown; _creationTime: unknown; gameId: unknown },
>(row: T): Omit<T, "_id" | "_creationTime" | "gameId"> {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { _id, _creationTime, gameId: _gameId, ...rest } = row;
  return rest;
}

export interface DiarySummary {
  turnSeries: TurnSeries | null;
  turnNumbers: number[];
  turnCount: number;
  loading: boolean;
  outcome: GameOutcome | null;
  status: "live" | "completed" | undefined;
  agentModelOverride: string | null;
}

/** Game summary subscription — 1 doc read. Returns sparkline series + metadata. */
export function useDiarySummaryConvex(filename: string | null): DiarySummary {
  const gameId = filename ? slugFromFilename(filename) : null;
  const summary = useQuery(
    api.diary.getGameSummary,
    gameId ? { gameId } : "skip",
  );

  const turnSeries = useMemo<TurnSeries | null>(() => {
    if (!summary?.turnSeries) return null;
    return summary.turnSeries as TurnSeries;
  }, [summary]);

  const outcome = useMemo<GameOutcome | null>(() => {
    if (!summary?.outcome) return null;
    return summary.outcome as GameOutcome;
  }, [summary]);

  return {
    turnSeries,
    turnNumbers: turnSeries?.turns ?? [],
    turnCount: summary?.turnCount ?? 0,
    loading: summary === undefined,
    outcome,
    status: (summary?.status as "live" | "completed") ?? undefined,
    agentModelOverride: summary?.agentModelOverride ?? null,
  };
}

/** Single turn detail subscription — ~12 doc reads. */
export function useDiaryTurnConvex(
  filename: string | null,
  turn: number | undefined,
  agentModelOverride: string | null,
): TurnData | null {
  const gameId = filename ? slugFromFilename(filename) : null;
  const detail = useQuery(
    api.diary.getGameTurnDetail,
    gameId && turn !== undefined ? { gameId, turn } : "skip",
  );

  return useMemo(() => {
    if (!detail) return null;
    const players = detail.playerRows.map((row: Doc<"playerRows">) => {
      const p = stripConvexFields(row) as PlayerRow;
      if (p.is_agent && agentModelOverride) p.agent_model = agentModelOverride;
      return p;
    });
    const cities = detail.cityRows.map(
      (row: Doc<"cityRows">) => stripConvexFields(row) as CityRow,
    );
    const grouped = groupTurnData(players, cities);
    return grouped[0] ?? null;
  }, [detail, agentModelOverride]);
}
