"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { PlayerRow, CityRow, TurnData, DiaryFile } from "./diary-types";
import { groupTurnData } from "./diary-types";
import { CONVEX_MODE } from "@/components/convex-provider";
import { useDiaryListConvex, useDiaryConvex } from "./use-diary-convex";

const POLL_INTERVAL = 3000;

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

function useDiaryFs(
  filename: string | null,
  live: boolean = true,
): { turns: TurnData[]; loading: boolean; reload: () => Promise<void> } {
  const [turns, setTurns] = useState<TurnData[]>([]);
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
      setTurns(grouped);
    } catch {
      setTurns([]);
    } finally {
      setLoading(false);
    }
  }, [filename]);

  // Initial load
  useEffect(() => {
    prevCount.current = 0;
    load();
  }, [load]);

  // Poll when live
  useEffect(() => {
    if (!live) return;
    const id = setInterval(load, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [live, load]);

  return { turns, loading, reload: load };
}

export const useDiary = CONVEX_MODE ? useDiaryConvex : useDiaryFs;
