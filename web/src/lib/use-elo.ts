"use client";

import { useEffect, useState } from "react";
import type { EloEntry, EloData } from "./elo";
import { CONVEX_MODE } from "@/components/convex-provider";
import { useEloConvex } from "./use-elo-convex";

function useEloFs(): EloData {
  const [ratings, setRatings] = useState<EloEntry[]>([]);
  const [gameCount, setGameCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let first = true;
    const poll = () =>
      fetch("/api/elo")
        .then((r) => r.json())
        .then((data) => {
          setRatings(data.ratings || []);
          setGameCount(data.gameCount || 0);
          setError(null);
        })
        .catch((e) => {
          setError(e instanceof Error ? e.message : "Failed to load ELO data");
        })
        .finally(() => {
          if (first) {
            setLoading(false);
            first = false;
          }
        });

    poll();
    const id = setInterval(poll, 30_000);
    return () => clearInterval(id);
  }, []);

  return { ratings, gameCount, loading, error };
}

export const useElo = CONVEX_MODE ? useEloConvex : useEloFs;
