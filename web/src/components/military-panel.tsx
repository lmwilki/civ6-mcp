"use client";

import type { PlayerRow } from "@/lib/diary-types";
import { ScoreDelta } from "./agent-overview";
import { AnimatedNumber } from "./animated-number";
import { CollapsiblePanel } from "./collapsible-panel";
import { CivIcon } from "./civ-icon";
import { CIV6_COLORS } from "@/lib/civ-colors";
import { Swords, Shield } from "lucide-react";

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
      <div className="mb-2 flex gap-4 text-xs">
        <span className="text-marble-600">
          Total:{" "}
          <span className="font-mono tabular-nums text-marble-800">
            <AnimatedNumber value={agent.units_total} decimals={0} />
          </span>
        </span>
        <span className="text-marble-600">
          Combat:{" "}
          <span className="font-mono tabular-nums text-marble-800">
            {agent.units_military}
          </span>
        </span>
        <span className="text-marble-600">
          Civilian:{" "}
          <span className="font-mono tabular-nums text-marble-800">
            {agent.units_civilian}
          </span>
        </span>
        <span className="text-marble-600">
          Support:{" "}
          <span className="font-mono tabular-nums text-marble-800">
            {agent.units_support}
          </span>
        </span>
      </div>
      {/* Unit composition pills */}
      {Object.keys(comp).length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(comp)
            .sort(([, a], [, b]) => b - a)
            .map(([type, count]) => (
              <div key={type} className="rounded-sm bg-marble-100 px-2 py-0.5">
                <span className="font-mono text-xs text-marble-700">
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
