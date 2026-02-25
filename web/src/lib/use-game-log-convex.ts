"use client";

import { useMemo } from "react";
import { useQuery } from "convex/react";
import { api } from "../../convex/_generated/api";
import type { Doc } from "../../convex/_generated/dataModel";
import type { LogEntry, GameLogInfo } from "./types";

/** Convex-backed game log list — real-time. */
export function useGameLogsConvex(): GameLogInfo[] {
  const games = useQuery(api.logs.listGameLogs) ?? [];
  return games;
}

/** Convex-backed game log entries — real-time subscription. */
export function useGameLogConvex(
  _live: boolean,
  game: string | null,
  session?: string | null,
) {
  const data = useQuery(
    api.logs.getLogEntries,
    game
      ? {
          gameId: game,
          ...(session ? { session } : {}),
        }
      : "skip",
  );

  const entries = useMemo(() => {
    if (!data) return [];
    return data.map((row: Doc<"logEntries">): LogEntry => {
      const { _id, _creationTime, gameId: _, ...fields } = row;
      return fields as LogEntry;
    });
  }, [data]);

  return {
    entries,
    connected: data !== undefined,
  };
}
