"use client";

import type { PlayerRow } from "@/lib/diary-types";
import { ScoreDelta } from "./agent-overview";
import { AnimatedNumber } from "./animated-number";
import { CollapsiblePanel } from "./collapsible-panel";
import { CivIcon } from "./civ-icon";
import { CIV6_COLORS } from "@/lib/civ-colors";
import { Swords, Shield } from "lucide-react";
import { StatValue } from "./stat-value";

interface MilitaryPanelProps {
  agent: PlayerRow;
  prevAgent?: PlayerRow;
}

export function MilitaryPanel({ agent, prevAgent }: MilitaryPanelProps) {
  const comp = agent.unit_composition;

  return (
    <CollapsiblePanel
      icon={<CivIcon icon={Shield} color={CIV6_COLORS.military} size="sm" />}
      title="Military"
      summary={
        <span className="font-mono text-xs tabular-nums text-marble-600">
          <Swords className="mr-1 inline h-3 w-3" />
          {agent.military}
          <ScoreDelta current={agent.military} prev={prevAgent?.military} />
        </span>
      }
    >
      {/* Unit counts */}
      <div className="mb-2 flex gap-4 text-sm">
        <StatValue label="Total">
          <AnimatedNumber value={agent.units_total} decimals={0} />
        </StatValue>
        <StatValue label="Combat">{agent.units_military}</StatValue>
        <StatValue label="Civilian">{agent.units_civilian}</StatValue>
        <StatValue label="Support">{agent.units_support}</StatValue>
      </div>
      {/* Unit composition pills */}
      {Object.keys(comp).length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(comp)
            .sort(([, a], [, b]) => b - a)
            .map(([type, count]) => (
              <div key={type} className="rounded-sm bg-marble-100 px-2 py-0.5">
                <span className="font-mono text-sm text-marble-700">
                  {type.replace(/_/g, " ")}{" "}
                  <span className="text-marble-500">x{count}</span>
                </span>
              </div>
            ))}
        </div>
      )}
    </CollapsiblePanel>
  );
}
