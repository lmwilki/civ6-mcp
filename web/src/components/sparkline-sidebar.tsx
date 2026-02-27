"use client";

import type { TurnSeries } from "@/lib/diary-types";
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
  ScanSearch,
} from "lucide-react";

interface SparklineSidebarProps {
  turnSeries: TurnSeries;
  currentIndex: number;
}

export function SparklineSidebar({
  turnSeries,
  currentIndex,
}: SparklineSidebarProps) {
  const hasRivals = Object.values(turnSeries.players).some(
    (p) => !p.is_agent,
  );

  return (
    <>
      <h3 className="mb-3 flex items-center gap-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
        <CivIcon icon={TrendingUp} color={CIV6_COLORS.goldMetal} size="sm" />
        Trends
      </h3>
      <div className="space-y-2">
        <ScoreSparkline
          turnSeries={turnSeries}
          currentIndex={currentIndex}
          field="score"
          label="Score"
          color={CIV6_COLORS.goldMetal}
          icon={Trophy}
        />
        <ScoreSparkline
          turnSeries={turnSeries}
          currentIndex={currentIndex}
          field="science"
          label="Science"
          color={CIV6_COLORS.science}
          icon={FlaskConical}
        />
        <ScoreSparkline
          turnSeries={turnSeries}
          currentIndex={currentIndex}
          field="culture"
          label="Culture"
          color={CIV6_COLORS.culture}
          icon={BookOpen}
        />
        <ScoreSparkline
          turnSeries={turnSeries}
          currentIndex={currentIndex}
          field="gold"
          label="Gold"
          color={CIV6_COLORS.goldDark}
          icon={Coins}
        />
        <ScoreSparkline
          turnSeries={turnSeries}
          currentIndex={currentIndex}
          field="military"
          label="Military"
          color={CIV6_COLORS.military}
          icon={Shield}
        />
        <ScoreSparkline
          turnSeries={turnSeries}
          currentIndex={currentIndex}
          field="faith"
          label="Faith"
          color={CIV6_COLORS.faith}
          icon={Flame}
        />
        <ScoreSparkline
          turnSeries={turnSeries}
          currentIndex={currentIndex}
          field="territory"
          label="Territory"
          color={CIV6_COLORS.marine}
          icon={MapPin}
        />
        <ScoreSparkline
          turnSeries={turnSeries}
          currentIndex={currentIndex}
          field="exploration_pct"
          label="Explored"
          color={CIV6_COLORS.favor}
          icon={Compass}
        />
        <ScoreSparkline
          turnSeries={turnSeries}
          currentIndex={currentIndex}
          field="spatial_tiles"
          label="Scanned"
          color={CIV6_COLORS.spatial}
          icon={ScanSearch}
        />
        <ScoreSparkline
          turnSeries={turnSeries}
          currentIndex={currentIndex}
          field="pop"
          label="Pop"
          color={CIV6_COLORS.growth}
          icon={Users}
        />
      </div>

      {hasRivals && (
        <div className="mt-4 border-t border-marble-300/50 pt-4">
          <MultiCivChart turnSeries={turnSeries} currentIndex={currentIndex} />
        </div>
      )}
    </>
  );
}
