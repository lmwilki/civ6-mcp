"use client";

import type { PlayerRow } from "@/lib/diary-types";
import { cleanCivName } from "@/lib/diary-types";
import { ScoreDelta } from "./agent-overview";
import { CollapsiblePanel } from "./collapsible-panel";
import { CivIcon } from "./civ-icon";
import { CIV6_COLORS } from "@/lib/civ-colors";
import {
  FlaskConical,
  BookOpen,
  ScrollText,
  Church,
  Sparkles,
  Layers,
  UserRound,
  Trophy,
  Building2,
  Landmark,
  Luggage,
} from "lucide-react";

interface ProgressPanelProps {
  agent: PlayerRow;
  prevAgent?: PlayerRow;
}

const GP_COLORS: Record<string, string> = {
  GREAT_PERSON_CLASS_GREAT_SCIENTIST: CIV6_COLORS.science,
  GREAT_PERSON_CLASS_GREAT_ENGINEER: CIV6_COLORS.production,
  GREAT_PERSON_CLASS_GREAT_MERCHANT: CIV6_COLORS.goldDark,
  GREAT_PERSON_CLASS_GREAT_GENERAL: CIV6_COLORS.military,
  GREAT_PERSON_CLASS_GREAT_ADMIRAL: CIV6_COLORS.marine,
  GREAT_PERSON_CLASS_GREAT_PROPHET: CIV6_COLORS.faith,
  GREAT_PERSON_CLASS_GREAT_WRITER: CIV6_COLORS.culture,
  GREAT_PERSON_CLASS_GREAT_ARTIST: CIV6_COLORS.tourism,
  GREAT_PERSON_CLASS_GREAT_MUSICIAN: CIV6_COLORS.favor,
};

const VICTORY_TYPES = [
  {
    label: "Science",
    key: "sci_vp" as const,
    max: 4,
    color: CIV6_COLORS.science,
    icon: FlaskConical,
  },
  {
    label: "Diplo",
    key: "diplo_vp" as const,
    max: 20,
    color: CIV6_COLORS.favor,
    icon: Landmark,
  },
  {
    label: "Tourism",
    key: "tourism" as const,
    color: CIV6_COLORS.tourism,
    icon: Luggage,
  },
  {
    label: "Domestic",
    key: "staycationers" as const,
    color: CIV6_COLORS.goldMetal,
    icon: UserRound,
  },
  {
    label: "Religion",
    key: "religion_cities" as const,
    color: CIV6_COLORS.faith,
    icon: Church,
  },
];

export function ProgressPanel({ agent, prevAgent }: ProgressPanelProps) {
  const hasResearch = agent.current_research !== "NONE";
  const hasCivic = agent.current_civic !== "NONE";
  const hasPolicies = agent.policies.length > 0;
  const hasReligion = agent.pantheon !== "NONE" || agent.religion !== "NONE";
  const hasGP = agent.gp_points && Object.keys(agent.gp_points).length > 0;

  return (
    <CollapsiblePanel
      icon={<CivIcon icon={Layers} color={CIV6_COLORS.marine} size="sm" />}
      title="Progress"
      summary={
        <span className="font-mono text-xs tabular-nums text-marble-600">
          {agent.techs_completed}T / {agent.civics_completed}C
        </span>
      }
    >
      <div className="space-y-3">
        {/* Current research + civic */}
        {(hasResearch || hasCivic) && (
          <div className="flex gap-2">
            {hasResearch && (
              <div className="flex flex-1 items-center gap-2 rounded-sm bg-marble-100 px-2.5 py-1.5">
                <CivIcon
                  icon={FlaskConical}
                  color={CIV6_COLORS.science}
                  size="sm"
                />
                <div className="flex flex-col">
                  <span className="text-xs font-medium text-marble-800">
                    {cleanCivName(agent.current_research)}
                  </span>
                  <span className="text-[10px] uppercase tracking-wider text-marble-500">
                    Researching
                  </span>
                </div>
              </div>
            )}
            {hasCivic && (
              <div className="flex flex-1 items-center gap-2 rounded-sm bg-marble-100 px-2.5 py-1.5">
                <CivIcon
                  icon={BookOpen}
                  color={CIV6_COLORS.culture}
                  size="sm"
                />
                <div className="flex flex-col">
                  <span className="text-xs font-medium text-marble-800">
                    {cleanCivName(agent.current_civic)}
                  </span>
                  <span className="text-[10px] uppercase tracking-wider text-marble-500">
                    Studying
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Completed counts */}
        <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-4">
          {[
            {
              icon: FlaskConical,
              color: CIV6_COLORS.science,
              label: "Techs",
              val: agent.techs_completed,
              prev: prevAgent?.techs_completed,
            },
            {
              icon: BookOpen,
              color: CIV6_COLORS.culture,
              label: "Civics",
              val: agent.civics_completed,
              prev: prevAgent?.civics_completed,
            },
            {
              icon: Building2,
              color: CIV6_COLORS.production,
              label: "Districts",
              val: agent.districts,
              prev: prevAgent?.districts,
            },
            {
              icon: Landmark,
              color: CIV6_COLORS.goldMetal,
              label: "Wonders",
              val: agent.wonders,
              prev: prevAgent?.wonders,
            },
          ].map(({ icon, color, label, val, prev }) => (
            <div
              key={label}
              className="flex items-center gap-1.5 rounded-sm bg-marble-100 px-2 py-1"
            >
              <CivIcon icon={icon} color={color} size="sm" />
              <div className="flex flex-col">
                <span className="flex items-baseline gap-0.5 font-mono text-sm tabular-nums text-marble-800">
                  <span>{val}</span>
                  <ScoreDelta current={val} prev={prev} />
                </span>
                <span className="text-[10px] uppercase tracking-wider text-marble-500">
                  {label}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Active policies */}
        {hasPolicies && (
          <div>
            <h4 className="mb-1 flex items-center gap-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
              <CivIcon
                icon={ScrollText}
                color={CIV6_COLORS.culture}
                size="sm"
              />
              Policies
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {agent.policies.map((p) => (
                <div key={p} className="rounded-sm bg-marble-100 px-2 py-0.5">
                  <span className="font-mono text-xs text-marble-700">
                    {cleanCivName(p)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Governors */}
        {agent.governors && agent.governors.length > 0 && (
          <div>
            <h4 className="mb-1 flex items-center gap-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
              <CivIcon
                icon={UserRound}
                color={CIV6_COLORS.goldMetal}
                size="sm"
              />
              Governors
            </h4>
            <div className="space-y-1">
              {agent.governors.map((g, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 rounded-sm bg-marble-100 px-2 py-1 text-xs"
                >
                  <span className="font-medium text-marble-700">
                    {(g.type ?? "Unknown")
                      .replace(/^GOVERNOR_THE_/, "")
                      .replace(/_/g, " ")}
                  </span>
                  {g.city && (
                    <span className="text-marble-500">
                      in {g.city} {g.established ? "" : "(establishing)"}
                    </span>
                  )}
                  {g.promotions?.length > 0 && (
                    <span className="text-marble-400">
                      [{g.promotions.length} promo
                      {g.promotions.length !== 1 ? "s" : ""}]
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Religion / Pantheon */}
        {hasReligion && (
          <div>
            <h4 className="mb-1 flex items-center gap-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
              <CivIcon icon={Church} color={CIV6_COLORS.faith} size="sm" />
              Religion
            </h4>
            <div className="flex flex-wrap gap-3 text-xs">
              {agent.pantheon !== "NONE" && (
                <span className="text-marble-600">
                  Pantheon:{" "}
                  <span className="font-medium text-marble-800">
                    {cleanCivName(agent.pantheon)}
                  </span>
                </span>
              )}
              {agent.religion !== "NONE" && (
                <span className="text-marble-600">
                  Religion:{" "}
                  <span className="font-medium text-marble-800">
                    {cleanCivName(agent.religion)}
                  </span>
                </span>
              )}
            </div>
            {agent.religion_beliefs.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1.5">
                {agent.religion_beliefs.map((b) => (
                  <div key={b} className="rounded-sm bg-marble-100 px-2 py-0.5">
                    <span className="font-mono text-xs text-marble-700">
                      {cleanCivName(b)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Great Person points */}
        {hasGP && (
          <div>
            <h4 className="mb-1 flex items-center gap-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
              <CivIcon
                icon={Sparkles}
                color={CIV6_COLORS.goldMetal}
                size="sm"
              />
              Great Person Points
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(agent.gp_points!)
                .sort(([, a], [, b]) => b - a)
                .map(([type, pts]) => {
                  const color = GP_COLORS[type] ?? CIV6_COLORS.marine;
                  return (
                    <div
                      key={type}
                      className="flex items-center gap-1 rounded-sm bg-marble-100 px-2 py-0.5"
                    >
                      <div
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: color, opacity: 0.75 }}
                      />
                      <span className="font-mono text-xs text-marble-700">
                        {cleanCivName(type)}{" "}
                        <span className="font-extrabold text-marble-800">
                          {pts}
                        </span>
                      </span>
                    </div>
                  );
                })}
            </div>
          </div>
        )}

        {/* Victory progress */}
        <div>
          <h4 className="mb-1.5 flex items-center gap-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
            <CivIcon icon={Trophy} color={CIV6_COLORS.goldMetal} size="sm" />
            Victory Progress
          </h4>
          <div className="grid grid-cols-3 gap-1.5 sm:grid-cols-5">
            {VICTORY_TYPES.map(({ label, key, max, color, icon: Icon }) => {
              const val = agent[key];
              return (
                <div
                  key={key}
                  className="flex flex-col items-center gap-1 rounded-sm bg-marble-100 px-1.5 py-1.5"
                >
                  <CivIcon icon={Icon} color={color} size="sm" />
                  <span className="font-mono text-sm font-bold tabular-nums text-marble-800">
                    {val}
                    {max ? (
                      <span className="text-marble-400">/{max}</span>
                    ) : null}
                  </span>
                  <span className="text-[9px] uppercase tracking-wider text-marble-500">
                    {label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </CollapsiblePanel>
  );
}
