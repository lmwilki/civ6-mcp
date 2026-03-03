"use client";

import type { TurnData } from "@/lib/diary-types";
import { cleanCivName } from "@/lib/diary-types";
import { CIV6_COLORS } from "@/lib/civ-colors";
import { CivIcon, CivSymbol } from "./civ-icon";
import { LeaderPortrait } from "./leader-portrait";
import { AnimatedNumber } from "./animated-number";
import {
  Coins,
  FlaskConical,
  Flame,
  Palette,
  Building2,
  Users,
  Compass,
  Star,
  Trophy,
  MapPin,
  Hammer,
  Pickaxe,
  Crown,
  Globe,
  Hourglass,
} from "lucide-react";
import { RESOURCE_META, AGE_COLORS, LUXURY_META } from "@/lib/civ-metadata";

function ScoreDelta({
  current,
  prev,
  suffix,
}: {
  current: number;
  prev?: number;
  suffix?: string;
}) {
  if (prev === undefined) return null;
  const delta = current - prev;
  if (delta === 0) return null;
  return (
    <span
      className={`text-[10px] font-medium ${delta > 0 ? "text-patina" : "text-terracotta"}`}
    >
      {delta > 0 ? "+" : ""}
      {Math.round(delta * 10) / 10}
      {suffix}
    </span>
  );
}

function YieldPill({
  icon,
  value,
  prev,
  label,
  suffix,
}: {
  icon: React.ReactNode;
  value: number;
  prev?: number;
  label: string;
  suffix?: string;
}) {
  return (
    <div className="flex items-center gap-1.5 rounded-sm bg-marble-100 px-2 py-1">
      {icon}
      <div className="flex flex-col">
        <span className="flex items-baseline gap-0.5 font-mono text-sm tabular-nums text-marble-800">
          <span>
            <AnimatedNumber value={value} />
            {suffix}
          </span>
          <ScoreDelta current={value} prev={prev} suffix={suffix} />
        </span>
        <span className="text-xs uppercase tracking-wider text-marble-600">
          {label}
        </span>
      </div>
    </div>
  );
}


interface AgentOverviewProps {
  turnData: TurnData;
  prevTurnData?: TurnData;
  index: number;
  total: number;
}

export function AgentOverview({
  turnData,
  prevTurnData,
  index,
  total,
}: AgentOverviewProps) {
  const a = turnData.agent;
  const pa = prevTurnData?.agent;

  const timestamp = new Date(a.timestamp).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });

  return (
    <div className="mx-auto w-full max-w-2xl">
      {/* Header */}
      <div className="mb-4 flex items-center gap-3">
        <LeaderPortrait
          leader={a.leader}
          agentModel={a.agent_model}
          size="lg"
        />
        <div className="flex flex-1 flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
          <div>
            <h2 className="font-display text-2xl font-bold tracking-wide text-marble-800">
              Turn {a.turn}
            </h2>
            <p className="mt-0.5 flex items-center gap-1.5 text-sm text-marble-600">
              <CivSymbol civ={a.civ} className="h-4 w-4" />
              {a.civ} ({a.leader}) &middot; {cleanCivName(a.era)} &middot;{" "}
              {timestamp}
            </p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-1.5 font-mono text-lg tabular-nums text-marble-800">
              <CivIcon icon={Star} color={CIV6_COLORS.goldMetal} size="sm" />
              <AnimatedNumber value={a.score} decimals={0} />
              <ScoreDelta current={a.score} prev={pa?.score} />
            </div>
            <p className="font-mono text-xs tabular-nums text-marble-600">
              Entry {index + 1} / {total}
            </p>
          </div>
        </div>
      </div>

      {/* Yield grid */}
      <div className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <YieldPill
          icon={<CivIcon icon={FlaskConical} color={CIV6_COLORS.science} />}
          value={a.science}
          prev={pa?.science}
          label="Science"
          suffix="/t"
        />
        <YieldPill
          icon={<CivIcon icon={Palette} color={CIV6_COLORS.culture} />}
          value={a.culture}
          prev={pa?.culture}
          label="Culture"
          suffix="/t"
        />
        <YieldPill
          icon={<CivIcon icon={Coins} color={CIV6_COLORS.goldDark} />}
          value={a.gold}
          prev={pa?.gold}
          label="Gold"
        />
        <YieldPill
          icon={<CivIcon icon={Coins} color={CIV6_COLORS.gold} />}
          value={a.gold_per_turn}
          prev={pa?.gold_per_turn}
          label="GPT"
          suffix="/t"
        />
        <YieldPill
          icon={<CivIcon icon={Flame} color={CIV6_COLORS.faith} />}
          value={a.faith}
          prev={pa?.faith}
          label="Faith"
        />
        <YieldPill
          icon={<CivIcon icon={Flame} color={CIV6_COLORS.faith} />}
          value={a.faith_per_turn}
          prev={pa?.faith_per_turn}
          label="Faith/t"
          suffix="/t"
        />
        <YieldPill
          icon={<CivIcon icon={Building2} color={CIV6_COLORS.growth} />}
          value={a.cities}
          prev={pa?.cities}
          label="Cities"
        />
        <YieldPill
          icon={<CivIcon icon={Users} color={CIV6_COLORS.growth} />}
          value={a.pop}
          prev={pa?.pop}
          label="Pop"
        />
        <YieldPill
          icon={<CivIcon icon={Globe} color={CIV6_COLORS.favor} />}
          value={a.favor}
          prev={pa?.favor}
          label="Favor"
        />
        <YieldPill
          icon={<CivIcon icon={MapPin} color={CIV6_COLORS.marine} />}
          value={a.territory}
          prev={pa?.territory}
          label="Territory"
        />
        <YieldPill
          icon={<CivIcon icon={Compass} color={CIV6_COLORS.favor} />}
          value={a.exploration_pct ?? 0}
          prev={pa?.exploration_pct}
          label="Explored"
          suffix="%"
        />
        <YieldPill
          icon={<CivIcon icon={Hammer} color={CIV6_COLORS.production} />}
          value={a.improvements}
          prev={pa?.improvements}
          label="Improved"
        />
      </div>

      {/* Era / age / government row */}
      <div className="mb-4 flex flex-wrap gap-2">
        <div className="flex items-center gap-1.5 rounded-sm bg-marble-100 px-2 py-1">
          <CivIcon icon={Trophy} color={CIV6_COLORS.goldMetal} size="sm" />
          <div className="flex flex-col">
            <span className="font-mono text-sm tabular-nums text-marble-800">
              <AnimatedNumber value={a.era_score} decimals={0} />
              <ScoreDelta current={a.era_score} prev={pa?.era_score} />
            </span>
            <span className="text-xs uppercase tracking-wider text-marble-500">
              Era Score
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 rounded-sm bg-marble-100 px-2 py-1">
          <CivIcon
            icon={Hourglass}
            color={AGE_COLORS[a.age] ?? CIV6_COLORS.normal}
            size="sm"
          />
          <div className="flex flex-col">
            <span className="font-mono text-sm text-marble-800">{a.age}</span>
            <span className="text-xs uppercase tracking-wider text-marble-500">
              Age
            </span>
          </div>
        </div>
        {a.government !== "NONE" && (
          <div className="flex items-center gap-1.5 rounded-sm bg-marble-100 px-2 py-1">
            <CivIcon icon={Crown} color={CIV6_COLORS.goldMetal} size="sm" />
            <div className="flex flex-col">
              <span className="font-mono text-sm text-marble-800">
                {cleanCivName(a.government)}
              </span>
              <span className="text-xs uppercase tracking-wider text-marble-500">
                Government
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Strategic resources */}
      {Object.keys(a.stockpiles).length > 0 && (
        <div className="mb-4">
          <h3 className="mb-1.5 font-display text-xs font-bold uppercase tracking-[0.08em] text-marble-500">
            Strategic Resources
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(a.stockpiles).map(([name, amt]) => {
              const meta = RESOURCE_META[name];
              const Icon = meta?.icon || Pickaxe;
              return (
                <div
                  key={name}
                  className="flex items-center gap-1 rounded-sm bg-marble-100 px-2 py-1"
                >
                  <CivIcon
                    icon={Icon}
                    color={meta?.color || CIV6_COLORS.normal}
                    size="sm"
                  />
                  <span className="font-mono text-xs tabular-nums text-marble-800">
                    {name.charAt(0) + name.slice(1).toLowerCase()}: {amt}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Luxury resources */}
      {Object.keys(a.luxuries).length > 0 && (
        <div className="mb-4">
          <h3 className="mb-1.5 font-display text-xs font-bold uppercase tracking-[0.08em] text-marble-500">
            Luxuries
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(a.luxuries).map(([name, amt]) => {
              const meta = LUXURY_META[name];
              const label =
                name.charAt(0) + name.slice(1).toLowerCase().replace(/_/g, " ");
              if (meta) {
                return (
                  <div
                    key={name}
                    className="flex items-center gap-1 rounded-sm bg-marble-100 px-2 py-0.5"
                  >
                    <CivIcon icon={meta.icon} color={meta.color} size="sm" />
                    <span className="font-mono text-xs text-marble-700">
                      {label}
                      {amt > 1 ? (
                        <span className="text-marble-500"> x{amt}</span>
                      ) : (
                        ""
                      )}
                    </span>
                  </div>
                );
              }
              return (
                <div
                  key={name}
                  className="rounded-sm bg-marble-100 px-2 py-0.5"
                >
                  <span className="font-mono text-xs text-marble-700">
                    {label}
                    {amt > 1 ? (
                      <span className="text-marble-500"> x{amt}</span>
                    ) : (
                      ""
                    )}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export { ScoreDelta, YieldPill };
