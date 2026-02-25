"use client";

import { Trophy, Skull } from "lucide-react";
import type { GameOutcome } from "@/lib/diary-types";

interface GameStatusBadgeProps {
  status?: "live" | "completed";
  outcome?: GameOutcome | null;
  turnCount: number;
}

export function GameStatusBadge({
  status,
  outcome,
  turnCount,
}: GameStatusBadgeProps) {
  if (status === "live") {
    return (
      <div className="text-right">
        <div className="flex items-center justify-end gap-1.5">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-patina opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-patina" />
          </span>
          <span className="font-display text-[10px] font-bold uppercase tracking-[0.08em] text-patina">
            Live
          </span>
          <span className="font-mono text-[10px] tabular-nums text-marble-500">
            T{turnCount}
          </span>
        </div>
      </div>
    );
  }

  if (outcome) {
    const isVictory = outcome.result === "victory";
    return (
      <div className="text-right">
        <div className="flex items-center justify-end gap-1">
          {isVictory ? (
            <Trophy className="h-3 w-3" style={{ color: "#3D8B6E" }} />
          ) : (
            <Skull className="h-3 w-3" style={{ color: "#C0503A" }} />
          )}
          <span
            className="font-display text-[10px] font-bold uppercase tracking-[0.08em]"
            style={{ color: isVictory ? "#3D8B6E" : "#C0503A" }}
          >
            {isVictory ? "Victory" : "Defeated"}
          </span>
          <span className="font-mono text-[10px] tabular-nums text-marble-500">
            T{outcome.turn}
          </span>
        </div>
        <p className="text-[10px] text-marble-400">{outcome.victoryType}</p>
      </div>
    );
  }

  return (
    <div className="text-right">
      <span className="font-mono text-[10px] tabular-nums text-marble-500">
        T{turnCount}
      </span>
    </div>
  );
}
