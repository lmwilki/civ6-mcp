"use client"

import type { PlayerRow } from "@/lib/diary-types"
import { cleanCivName } from "@/lib/diary-types"
import { ScoreDelta } from "./agent-overview"
import { CollapsiblePanel } from "./collapsible-panel"
import { CivIcon } from "./civ-icon"
import { CIV6_COLORS } from "@/lib/civ-colors"
import {
  FlaskConical,
  BookOpen,
  ScrollText,
  Church,
  Sparkles,
  Layers,
  UserRound,
} from "lucide-react"

interface ProgressPanelProps {
  agent: PlayerRow
  prevAgent?: PlayerRow
}

export function ProgressPanel({ agent, prevAgent }: ProgressPanelProps) {
  const hasResearch = agent.current_research !== "NONE"
  const hasCivic = agent.current_civic !== "NONE"
  const hasPolicies = agent.policies.length > 0
  const hasReligion = agent.pantheon !== "NONE" || agent.religion !== "NONE"
  const hasGP = agent.gp_points && Object.keys(agent.gp_points).length > 0

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
        <div className="flex gap-4 text-xs">
          {hasResearch && (
            <div className="flex items-center gap-1.5">
              <FlaskConical className="h-3 w-3 text-blue-600" />
              <span className="text-marble-600">Researching:</span>
              <span className="font-medium text-marble-800">{cleanCivName(agent.current_research)}</span>
            </div>
          )}
          {hasCivic && (
            <div className="flex items-center gap-1.5">
              <BookOpen className="h-3 w-3 text-purple-600" />
              <span className="text-marble-600">Studying:</span>
              <span className="font-medium text-marble-800">{cleanCivName(agent.current_civic)}</span>
            </div>
          )}
        </div>

        {/* Completed counts */}
        <div className="flex gap-4 text-xs">
          <span className="text-marble-600">
            Techs: <span className="font-mono tabular-nums text-marble-800">{agent.techs_completed}</span>
            <ScoreDelta current={agent.techs_completed} prev={prevAgent?.techs_completed} />
          </span>
          <span className="text-marble-600">
            Civics: <span className="font-mono tabular-nums text-marble-800">{agent.civics_completed}</span>
            <ScoreDelta current={agent.civics_completed} prev={prevAgent?.civics_completed} />
          </span>
          <span className="text-marble-600">
            Districts: <span className="font-mono tabular-nums text-marble-800">{agent.districts}</span>
            <ScoreDelta current={agent.districts} prev={prevAgent?.districts} />
          </span>
          <span className="text-marble-600">
            Wonders: <span className="font-mono tabular-nums text-marble-800">{agent.wonders}</span>
            <ScoreDelta current={agent.wonders} prev={prevAgent?.wonders} />
          </span>
        </div>

        {/* Active policies */}
        {hasPolicies && (
          <div>
            <h4 className="mb-1 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
              <ScrollText className="mr-1 inline h-3 w-3" />
              Policies
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {agent.policies.map((p) => (
                <div key={p} className="rounded-sm bg-marble-100 px-2 py-0.5">
                  <span className="font-mono text-xs text-marble-700">{cleanCivName(p)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Governors */}
        {agent.governors && agent.governors.length > 0 && (
          <div>
            <h4 className="mb-1 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
              <UserRound className="mr-1 inline h-3 w-3" />
              Governors
            </h4>
            <div className="space-y-1">
              {agent.governors.map((g, i) => (
                <div key={i} className="flex items-center gap-2 rounded-sm bg-marble-100 px-2 py-1 text-xs">
                  <UserRound className="h-3 w-3 text-marble-500" />
                  <span className="font-medium text-marble-700">
                    {g.type.replace(/^GOVERNOR_THE_/, "").replace(/_/g, " ")}
                  </span>
                  {g.city && (
                    <span className="text-marble-500">
                      in {g.city} {g.established ? "" : "(establishing)"}
                    </span>
                  )}
                  {g.promotions.length > 0 && (
                    <span className="text-marble-400">
                      [{g.promotions.length} promo{g.promotions.length !== 1 ? "s" : ""}]
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
            <h4 className="mb-1 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
              <Church className="mr-1 inline h-3 w-3" />
              Religion
            </h4>
            <div className="flex flex-wrap gap-3 text-xs">
              {agent.pantheon !== "NONE" && (
                <span className="text-marble-600">
                  Pantheon: <span className="font-medium text-marble-800">{cleanCivName(agent.pantheon)}</span>
                </span>
              )}
              {agent.religion !== "NONE" && (
                <span className="text-marble-600">
                  Religion: <span className="font-medium text-marble-800">{cleanCivName(agent.religion)}</span>
                </span>
              )}
            </div>
            {agent.religion_beliefs.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1.5">
                {agent.religion_beliefs.map((b) => (
                  <div key={b} className="rounded-sm bg-marble-100 px-2 py-0.5">
                    <span className="font-mono text-xs text-marble-700">{cleanCivName(b)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Great Person points */}
        {hasGP && (
          <div>
            <h4 className="mb-1 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
              <Sparkles className="mr-1 inline h-3 w-3" />
              Great Person Points
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(agent.gp_points!)
                .sort(([, a], [, b]) => b - a)
                .map(([type, pts]) => (
                  <div key={type} className="rounded-sm bg-marble-100 px-2 py-0.5">
                    <span className="font-mono text-xs text-marble-700">
                      {cleanCivName(type)}
                      {" "}
                      <span className="text-marble-500">{pts}</span>
                    </span>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Victory progress */}
        <div>
          <h4 className="mb-1 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
            Victory Progress
          </h4>
          <div className="flex flex-wrap gap-4 text-xs">
            <span className="text-marble-600">
              Science VP: <span className="font-mono tabular-nums text-marble-800">{agent.sci_vp}</span>
            </span>
            <span className="text-marble-600">
              Diplo VP: <span className="font-mono tabular-nums text-marble-800">{agent.diplo_vp}</span>
            </span>
            <span className="text-marble-600">
              Tourism: <span className="font-mono tabular-nums text-marble-800">{agent.tourism}</span>
            </span>
            <span className="text-marble-600">
              Domestic Tourists: <span className="font-mono tabular-nums text-marble-800">{agent.staycationers}</span>
            </span>
            <span className="text-marble-600">
              Religion Cities: <span className="font-mono tabular-nums text-marble-800">{agent.religion_cities}</span>
            </span>
          </div>
        </div>
      </div>
    </CollapsiblePanel>
  )
}
