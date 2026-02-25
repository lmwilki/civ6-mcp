"use client";

import type { TurnData } from "@/lib/diary-types";
import { ScoreSparkline } from "./score-sparkline";
import { MultiCivChart } from "./multi-civ-chart";
import { CivIcon } from "./civ-icon";
import { CIV6_COLORS } from "@/lib/civ-colors";
import {
  TrendingUp,
  Trophy,
  FlaskConical,
  BookOpen,
  Coins,
  Shield,
  Flame,
  MapPin,
  Compass,
  Users,
} from "lucide-react";

interface SparklineSidebarProps {
  turns: TurnData[];
  currentIndex: number;
}

export function SparklineSidebar({
  turns,
  currentIndex,
}: SparklineSidebarProps) {
  return (
    <>
      <h3 className="mb-3 flex items-center gap-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
        <CivIcon icon={TrendingUp} color={CIV6_COLORS.goldMetal} size="sm" />
        Trends
      </h3>
      <div className="space-y-2">
        <ScoreSparkline
          turns={turns}
          currentIndex={currentIndex}
          field="score"
          label="Score"
          color={CIV6_COLORS.goldMetal}
          icon={Trophy}
        />
        <ScoreSparkline
          turns={turns}
          currentIndex={currentIndex}
          field="science"
          label="Science"
          color={CIV6_COLORS.science}
          icon={FlaskConical}
        />
        <ScoreSparkline
          turns={turns}
          currentIndex={currentIndex}
          field="culture"
          label="Culture"
          color={CIV6_COLORS.culture}
          icon={BookOpen}
        />
        <ScoreSparkline
          turns={turns}
          currentIndex={currentIndex}
          field="gold"
          label="Gold"
          color={CIV6_COLORS.goldDark}
          icon={Coins}
        />
        <ScoreSparkline
          turns={turns}
          currentIndex={currentIndex}
          field="military"
          label="Military"
          color={CIV6_COLORS.military}
          icon={Shield}
        />
        <ScoreSparkline
          turns={turns}
          currentIndex={currentIndex}
          field="faith"
          label="Faith"
          color={CIV6_COLORS.faith}
          icon={Flame}
        />
        <ScoreSparkline
          turns={turns}
          currentIndex={currentIndex}
          field="territory"
          label="Territory"
          color={CIV6_COLORS.marine}
          icon={MapPin}
        />
        <ScoreSparkline
          turns={turns}
          currentIndex={currentIndex}
          field="exploration_pct"
          label="Explored"
          color={CIV6_COLORS.favor}
          icon={Compass}
        />
        <ScoreSparkline
          turns={turns}
          currentIndex={currentIndex}
          field="pop"
          label="Pop"
          color={CIV6_COLORS.growth}
          icon={Users}
        />
      </div>

      {turns.some((t) => t.rivals.length > 0) && (
        <div className="mt-4 border-t border-marble-300/50 pt-4">
          <MultiCivChart turns={turns} currentIndex={currentIndex} />
        </div>
      )}
    </>
  );
}
