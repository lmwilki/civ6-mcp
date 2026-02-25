"use client";

import { useMemo } from "react";
import { useQuery } from "convex/react";
import { api } from "../../convex/_generated/api";
import type { Doc } from "../../convex/_generated/dataModel";
import type { PlayerRow, CityRow, DiaryFile } from "./diary-types";
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

/** Convex-backed diary data — real-time updates via subscription. */
export function useDiaryConvex(filename: string | null) {
  const gameId = filename ? slugFromFilename(filename) : null;
  const data = useQuery(api.diary.getGameTurns, gameId ? { gameId } : "skip");

  const turns = useMemo(() => {
    if (!data) return [];
    const players = data.playerRows.map(
      (row: Doc<"playerRows">) => stripConvexFields(row) as PlayerRow,
    );
    const cities = data.cityRows.map(
      (row: Doc<"cityRows">) => stripConvexFields(row) as CityRow,
    );
    return groupTurnData(players, cities);
  }, [data]);

  return {
    turns,
    loading: data === undefined,
    reload: async () => {}, // No-op — Convex auto-updates
  };
}
