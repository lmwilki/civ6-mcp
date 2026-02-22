"use client"

import type { PlayerRow } from "@/lib/diary-types"
import { DIPLO_STATE_NAMES, DIPLO_STATE_COLORS } from "@/lib/diary-types"
import { CollapsiblePanel } from "./collapsible-panel"
import { CivIcon } from "./civ-icon"
import { CIV6_COLORS } from "@/lib/civ-colors"
import { Crown, Handshake } from "lucide-react"

interface DiplomacyPanelProps {
  agent: PlayerRow
}

export function DiplomacyPanel({ agent }: DiplomacyPanelProps) {
  const diplo = agent.diplo_states
  const trade = agent.trade_routes
  const envoysSent = agent.envoys_sent
  const hasContent =
    (diplo && Object.keys(diplo).length > 0) ||
    trade ||
    (envoysSent && Object.keys(envoysSent).length > 0)

  if (!hasContent) return null

  return (
    <CollapsiblePanel
      icon={<CivIcon icon={Handshake} color={CIV6_COLORS.favor} size="sm" />}
      title="Diplomacy"
    >
      <div className="space-y-3">
        {/* Diplo states table */}
        {diplo && Object.keys(diplo).length > 0 && (
          <div>
            <h4 className="mb-1 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
              Relations
            </h4>
            <table className="w-full text-xs">
              <thead>
                <tr className="text-[10px] uppercase tracking-wider text-marble-500">
                  <th className="py-1 px-1 text-left">Civ</th>
                  <th className="py-1 px-1 text-left">State</th>
                  <th className="py-1 px-1 text-left">Alliance</th>
                  <th className="py-1 px-1 text-right">Grievances</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(diplo).map(([civ, ds]) => (
                  <tr key={civ} className="border-t border-marble-200/50">
                    <td className="py-1 px-1 font-medium text-marble-700">{civ}</td>
                    <td className={`py-1 px-1 ${DIPLO_STATE_COLORS[ds.state] ?? "text-marble-600"}`}>
                      {DIPLO_STATE_NAMES[ds.state] ?? `State ${ds.state}`}
                    </td>
                    <td className="py-1 px-1 font-mono text-marble-600">
                      {ds.alliance ? `${ds.alliance.replace(/_/g, " ")} (L${ds.alliance_level})` : "—"}
                    </td>
                    <td className={`py-1 px-1 text-right font-mono tabular-nums ${ds.grievances > 0 ? "text-terracotta" : "text-marble-600"}`}>
                      {ds.grievances}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Envoys */}
        {(agent.envoys_available !== undefined || (envoysSent && Object.keys(envoysSent).length > 0)) && (
          <div>
            <h4 className="mb-1 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
              City-States
            </h4>
            <div className="mb-1.5 flex gap-4 text-xs">
              {agent.envoys_available !== undefined && (
                <span className="text-marble-600">
                  Available: <span className="font-mono tabular-nums text-marble-800">{agent.envoys_available}</span>
                </span>
              )}
              {agent.suzerainties !== undefined && (
                <span className="text-marble-600">
                  Suzerainties: <span className="font-mono tabular-nums text-marble-800">{agent.suzerainties}</span>
                </span>
              )}
            </div>
            {envoysSent && Object.keys(envoysSent).length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(envoysSent)
                  .sort(([, a], [, b]) => b - a)
                  .map(([rawCs, count]) => {
                    const isSuzerain = rawCs.endsWith("*")
                    const cs = isSuzerain ? rawCs.slice(0, -1) : rawCs
                    return (
                      <div key={cs} className={`flex items-center gap-1 rounded-sm px-2 py-0.5 ${isSuzerain ? "bg-gold/10 ring-1 ring-gold/25" : "bg-marble-100"}`}>
                        {isSuzerain && <Crown className="h-3 w-3 text-gold" />}
                        <span className="font-mono text-xs text-marble-700">
                          {cs} <span className="text-marble-500">x{count}</span>
                        </span>
                      </div>
                    )
                  })}
              </div>
            )}
          </div>
        )}

        {/* Trade routes */}
        {trade && (
          <div>
            <h4 className="mb-1 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
              Trade Routes
            </h4>
            <div className="flex gap-4 text-xs">
              <span className="text-marble-600">
                Active: <span className="font-mono tabular-nums text-marble-800">{trade.active}/{trade.capacity}</span>
              </span>
              <span className="text-marble-600">
                Domestic: <span className="font-mono tabular-nums text-marble-800">{trade.domestic}</span>
              </span>
              <span className="text-marble-600">
                International: <span className="font-mono tabular-nums text-marble-800">{trade.international}</span>
              </span>
            </div>
          </div>
        )}
      </div>
    </CollapsiblePanel>
  )
}
