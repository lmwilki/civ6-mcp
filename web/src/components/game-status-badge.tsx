"use client";

import type { LucideIcon } from "lucide-react";
import {
  Trophy,
  FlaskConical,
  Swords,
  Church,
  Landmark,
  Luggage,
} from "lucide-react";
import type { GameOutcome } from "@/lib/diary-types";
import { CIV6_COLORS } from "@/lib/civ-colors";
import { CivIcon } from "./civ-icon";
import { PulsingDot } from "./pulsing-dot";

const STATUS_COLORS = {
  live: "#7A9B8A",
  victory: "#3D8B6E",
  defeat: "#C0503A",
  unfinished: "#B0A99F",
} as const;

/** Returns the semantic color for a game's current state. */
export function getGameStatusColor(
  status?: "live" | "completed",
  outcome?: GameOutcome | null,
): string {
  if (status === "live") return STATUS_COLORS.live;
  if (outcome?.result === "victory") return STATUS_COLORS.victory;
  if (outcome?.result === "defeat") return STATUS_COLORS.defeat;
  return STATUS_COLORS.unfinished;
}

interface VictoryMeta {
  icon: LucideIcon;
  color: string;
  label: string;
}

const VICTORY_TYPE_MAP: Record<string, VictoryMeta> = {
  technology: { icon: FlaskConical, color: CIV6_COLORS.science, label: "Science" },
  science: { icon: FlaskConical, color: CIV6_COLORS.science, label: "Science" },
  conquest: { icon: Swords, color: CIV6_COLORS.military, label: "Domination" },
  domination: { icon: Swords, color: CIV6_COLORS.military, label: "Domination" },
  religious: { icon: Church, color: CIV6_COLORS.faith, label: "Religious" },
  diplomatic: { icon: Landmark, color: CIV6_COLORS.favor, label: "Diplomatic" },
  culture: { icon: Luggage, color: CIV6_COLORS.tourism, label: "Cultural" },
  cultural: { icon: Luggage, color: CIV6_COLORS.tourism, label: "Cultural" },
  score: { icon: Trophy, color: CIV6_COLORS.goldMetal, label: "Score" },
};

const FALLBACK_VICTORY: VictoryMeta = {
  icon: Trophy,
  color: CIV6_COLORS.goldMetal,
  label: "Unknown",
};

/** Resolve victory type string to icon, color, and display label. */
export function getVictoryTypeMeta(victoryType?: string): VictoryMeta {
  if (!victoryType) return FALLBACK_VICTORY;
  return VICTORY_TYPE_MAP[victoryType.toLowerCase()] ?? { ...FALLBACK_VICTORY, label: victoryType };
}

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
          <PulsingDot />
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
    const vt = getVictoryTypeMeta(outcome.victoryType);
    const Icon = vt.icon;
    return (
      <div className="text-right">
        <div className="flex items-center justify-end gap-1">
          <span
            className="font-display text-[10px] font-bold uppercase tracking-[0.08em]"
            style={{ color: isVictory ? STATUS_COLORS.victory : STATUS_COLORS.defeat }}
          >
            {isVictory ? "Victory" : "Defeated"}
          </span>
          <span className="font-mono text-[10px] tabular-nums text-marble-500">
            T{outcome.turn}
          </span>
        </div>
        <div className="mt-0.5 flex items-center justify-end gap-1">
          <CivIcon icon={Icon} color={vt.color} size="sm" />
          <span className="text-[10px]" style={{ color: vt.color }}>{vt.label}</span>
        </div>
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
