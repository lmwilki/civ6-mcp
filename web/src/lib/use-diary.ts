"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type {
  PlayerRow,
  CityRow,
  TurnData,
  DiaryFile,
  GameOutcome,
  TurnSeries,
  NumericPlayerField,
} from "./diary-types";
import { groupTurnData } from "./diary-types";
import { CONVEX_MODE } from "@/components/convex-provider";
import {
  useDiaryListConvex,
  useDiarySummaryConvex,
  useDiaryTurnConvex,
} from "./use-diary-convex";
import type { DiarySummary } from "./use-diary-convex";

const POLL_INTERVAL = 3000;

// Metrics to extract for sparkline series
const SERIES_FIELDS: NumericPlayerField[] = [
  "score", "science", "culture", "gold", "military",
  "faith", "territory", "exploration_pct", "pop", "cities", "tourism",
];

/** Build TurnSeries from full TurnData[] for the FS fallback */
function buildTurnSeries(turns: TurnData[]): TurnSeries {
  const turnNums = turns.map((t) => t.turn);
  const players: TurnSeries["players"] = {};

  for (const t of turns) {
    for (const p of [t.agent, ...t.rivals]) {
      const pid = String(p.pid);
      if (!players[pid]) {
        players[pid] = {
          civ: p.civ,
          leader: p.leader,
          is_agent: p.is_agent,
          metrics: {} as Record<NumericPlayerField, number[]>,
        };
        for (const m of SERIES_FIELDS) {
          players[pid].metrics[m] = [];
        }
      }
    }
  }

  for (const t of turns) {
    const allPlayers = [t.agent, ...t.rivals];
    for (const [pid, ps] of Object.entries(players)) {
      const row = allPlayers.find((p) => String(p.pid) === pid);
      for (const m of SERIES_FIELDS) {
        ps.metrics[m].push(row ? (row[m] as number) ?? 0 : 0);
      }
    }
  }

  return { turns: turnNums, players };
}

// ── Diary list ──────────────────────────────────────────────────────────────

function useDiaryListFs(): DiaryFile[] {
  const [diaries, setDiaries] = useState<DiaryFile[]>([]);

  useEffect(() => {
    const poll = () =>
      fetch("/api/diary")
        .then((r) => r.json())
        .then((data) => setDiaries(data.diaries || []))
        .catch(() => {});
    poll();
    const id = setInterval(poll, 10000);
    return () => clearInterval(id);
  }, []);

  return diaries;
}

export const useDiaryList = CONVEX_MODE ? useDiaryListConvex : useDiaryListFs;

// ── Game summary ────────────────────────────────────────────────────────────

function useDiarySummaryFs(filename: string | null): DiarySummary {
  const [allTurns, setAllTurns] = useState<TurnData[]>([]);
  const [loading, setLoading] = useState(false);
  const prevCount = useRef(0);

  const load = useCallback(async () => {
    if (!filename) return;
    if (prevCount.current === 0) setLoading(true);
    try {
      const [playersRes, citiesRes] = await Promise.all([
        fetch(`/api/diary?file=${encodeURIComponent(filename)}`),
        fetch(`/api/diary?file=${encodeURIComponent(filename)}&cities=1`),
      ]);
      const playersData = await playersRes.json();
      const citiesData = await citiesRes.json();
      const players: PlayerRow[] = playersData.entries || [];
      const cities: CityRow[] = citiesData.entries || [];
      const grouped = groupTurnData(players, cities);
      prevCount.current = grouped.length;
      setAllTurns(grouped);
    } catch {
      setAllTurns([]);
    } finally {
      setLoading(false);
    }
  }, [filename]);

  useEffect(() => {
    prevCount.current = 0;
    load();
  }, [load]);

  useEffect(() => {
    const id = setInterval(load, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [load]);

  const turnSeries = useMemo(
    () => (allTurns.length > 0 ? buildTurnSeries(allTurns) : null),
    [allTurns],
  );

  return {
    turnSeries,
    turnNumbers: allTurns.map((t) => t.turn),
    turnCount: allTurns.length,
    loading,
    outcome: null,
    status: undefined,
    agentModelOverride: null,
  };
}

export const useDiarySummary = CONVEX_MODE
  ? useDiarySummaryConvex
  : useDiarySummaryFs;

// ── Turn detail ─────────────────────────────────────────────────────────────

/** FS fallback: extract single turn from the already-loaded data */
function useDiaryTurnFs(
  filename: string | null,
  turn: number | undefined,
  _agentModelOverride: string | null,
): TurnData | null {
  // In FS mode, the summary hook already fetched all data.
  // We need a way to access it. Use a shared cache keyed by filename.
  const [allTurns, setAllTurns] = useState<TurnData[]>([]);

  const load = useCallback(async () => {
    if (!filename) return;
    try {
      const [playersRes, citiesRes] = await Promise.all([
        fetch(`/api/diary?file=${encodeURIComponent(filename)}`),
        fetch(`/api/diary?file=${encodeURIComponent(filename)}&cities=1`),
      ]);
      const playersData = await playersRes.json();
      const citiesData = await citiesRes.json();
      const players: PlayerRow[] = playersData.entries || [];
      const cities: CityRow[] = citiesData.entries || [];
      setAllTurns(groupTurnData(players, cities));
    } catch {
      setAllTurns([]);
    }
  }, [filename]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const id = setInterval(load, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [load]);

  return useMemo(() => {
    if (allTurns.length === 0 || turn === undefined) return null;
    return allTurns.find((t) => t.turn === turn) ?? null;
  }, [allTurns, turn]);
}

export const useDiaryTurn = CONVEX_MODE
  ? useDiaryTurnConvex
  : useDiaryTurnFs;
