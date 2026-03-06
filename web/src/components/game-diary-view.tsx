"use client";

import { useState } from "react";
import { AgentOverview } from "@/components/agent-overview";
import { LeaderboardTable } from "@/components/leaderboard-table";
import { CitiesPanel } from "@/components/cities-panel";
import { MilitaryPanel } from "@/components/military-panel";
import { DiplomacyPanel } from "@/components/diplomacy-panel";
import { ProgressPanel } from "@/components/progress-panel";
import { ReflectionsPanel } from "@/components/reflections-panel";
import { SparklineSidebar } from "@/components/sparkline-sidebar";
import { useDiarySummary, useDiaryTurn } from "@/lib/use-diary";
import { OutcomeBanner, statusColor } from "@/components/game-status-badge";
import { CivSymbol } from "@/components/civ-icon";
import { useTurnNavigation } from "@/lib/use-turn-navigation";
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  X,
  BarChart3,
  Eye,
  Map,
} from "lucide-react";
import { SCENARIOS, DIFFICULTY_META } from "@/lib/scenarios";
import { SkeletonBlock, SkeletonLine } from "./skeleton";

interface GameDiaryViewProps {
  filename: string;
}

export function GameDiaryView({ filename }: GameDiaryViewProps) {
  const [showSidebar, setShowSidebar] = useState(false);

  // Summary subscription — 1 doc, returns sparklines + turn list + metadata
  const {
    turnSeries,
    turnNumbers,
    loading,
    outcome,
    agentModelOverride,
    scenarioId,
    difficulty,
    mapType,
    mapSize,
  } = useDiarySummary(filename);

  const scenarioDef = scenarioId ? SCENARIOS[scenarioId] : null;

  const maxIdx = Math.max(0, turnNumbers.length - 1);
  const { index, goPrev, goNext, goFirst, goLast, seek } =
    useTurnNavigation(maxIdx);

  // Turn detail subscriptions — ~12 docs each
  const selectedTurn = turnNumbers[index];
  const prevTurnNum = index > 0 ? turnNumbers[index - 1] : undefined;

  const currentTurn = useDiaryTurn(filename, selectedTurn, agentModelOverride);
  const prevTurn = useDiaryTurn(filename, prevTurnNum, agentModelOverride);

  const hasTurns = turnNumbers.length > 1;
  const isLastTurn = index === maxIdx;

  return (
    <>
      {/* Turn navigation */}
      <div className="shrink-0 border-b border-marble-300 bg-marble-50/50 px-3 py-2 sm:px-6">
        <div className="mx-auto flex max-w-4xl items-center justify-center gap-1">
          <button onClick={goFirst} disabled={index === 0} className="rounded-sm p-1.5 text-marble-500 transition-colors hover:bg-marble-200 hover:text-marble-700 disabled:opacity-30" title="First entry (Home)">
            <ChevronsLeft className="h-4 w-4" />
          </button>
          <button onClick={goPrev} disabled={index === 0} className="rounded-sm p-1.5 text-marble-500 transition-colors hover:bg-marble-200 hover:text-marble-700 disabled:opacity-30" title="Previous entry (Left arrow)">
            <ChevronLeft className="h-4 w-4" />
          </button>

          {hasTurns && (
            <input
              type="range"
              min={0}
              max={maxIdx}
              value={index}
              aria-label="Turn navigation"
              onChange={(e) => seek(parseInt(e.target.value, 10))}
              className="mx-2 w-24 accent-gold sm:w-48"
            />
          )}

          <button onClick={goNext} disabled={index >= maxIdx} className="rounded-sm p-1.5 text-marble-500 transition-colors hover:bg-marble-200 hover:text-marble-700 disabled:opacity-30" title="Next entry (Right arrow)">
            <ChevronRight className="h-4 w-4" />
          </button>
          <button onClick={goLast} disabled={index >= maxIdx} className="rounded-sm p-1.5 text-marble-500 transition-colors hover:bg-marble-200 hover:text-marble-700 disabled:opacity-30" title="Last entry (End)">
            <ChevronsRight className="h-4 w-4" />
          </button>

          {currentTurn && (
            <span className="ml-2 font-mono text-xs tabular-nums text-marble-500">
              Turn {currentTurn.turn}
            </span>
          )}
          {outcome && (
            <span
              className="ml-1.5 rounded-sm px-1.5 py-0.5 font-display text-xs font-bold uppercase tracking-[0.08em]"
              style={{
                color: statusColor(outcome.result === "victory" ? "victory" : "defeat"),
                backgroundColor: outcome.result === "victory" ? "rgba(61,139,110,0.1)" : "rgba(192,80,58,0.1)",
              }}
            >
              {outcome.result === "victory" ? "Victory" : "Defeat"} T{outcome.turn}
            </span>
          )}
        </div>
      </div>

      {/* Main content */}
      <div className="flex min-h-0 flex-1">
        <div className="flex-1 overflow-y-auto px-3 py-4 sm:px-6 sm:py-6">
          {loading && (
            <div className="mx-auto max-w-2xl space-y-4">
              {/* Agent overview skeleton */}
              <div className="rounded-sm border border-marble-300/50 bg-marble-50 p-4">
                <div className="flex items-center gap-3">
                  <SkeletonBlock className="h-10 w-10 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <SkeletonLine className="w-40" />
                    <SkeletonLine className="w-24" />
                  </div>
                  <SkeletonLine className="w-16" />
                </div>
                <div className="mt-4 grid grid-cols-4 gap-3">
                  {[0, 1, 2, 3].map((i) => (
                    <SkeletonBlock key={i} className="h-12 w-full" />
                  ))}
                </div>
              </div>
              {/* Leaderboard skeleton */}
              <div className="rounded-sm border border-marble-300/50 bg-marble-50 p-4">
                <SkeletonLine className="mb-3 w-28" />
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center gap-3 py-2">
                    <SkeletonBlock className="h-5 w-5 rounded-full" />
                    <SkeletonLine className="w-28" />
                    <div className="flex-1" />
                    <SkeletonLine className="w-12" />
                  </div>
                ))}
              </div>
              {/* Panel skeletons */}
              {[0, 1].map((i) => (
                <SkeletonBlock key={i} className="h-24 w-full" />
              ))}
            </div>
          )}

          {!loading && turnNumbers.length === 0 && (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <p className="font-display text-sm tracking-[0.08em] uppercase text-marble-500">
                  No diary entries
                </p>
                <p className="mt-2 text-sm text-marble-600">
                  Start a game with diary enabled
                </p>
              </div>
            </div>
          )}

          {!loading && currentTurn && (
            <>
              {outcome && isLastTurn && (
                <div className="mx-auto mb-4 w-full max-w-2xl">
                  <OutcomeBanner outcome={outcome} />
                </div>
              )}
              {scenarioDef && index === 0 && (
                <div className="mx-auto mb-4 w-full max-w-2xl">
                  <div
                    className="flex items-stretch gap-0 rounded-sm border border-marble-300/50 bg-marble-50"
                  >
                    <div
                      className="w-1.5 shrink-0 rounded-l-sm"
                      style={{ backgroundColor: DIFFICULTY_META[scenarioDef.difficulty]?.color }}
                    />
                    <div className="flex-1 px-3 py-2.5 space-y-1">
                      <div className="flex items-center gap-2">
                        <span
                          className="inline-flex items-center gap-1 rounded-sm px-1.5 py-0.5 text-xs font-bold uppercase tracking-[0.08em]"
                          style={{
                            color: DIFFICULTY_META[scenarioDef.difficulty]?.color,
                            backgroundColor: `${DIFFICULTY_META[scenarioDef.difficulty]?.color}15`,
                          }}
                        >
                          <span
                            className="inline-block h-1.5 w-1.5 rounded-full"
                            style={{ backgroundColor: DIFFICULTY_META[scenarioDef.difficulty]?.color }}
                          />
                          {difficulty ?? scenarioDef.difficulty}
                        </span>
                        <span className="font-display text-sm font-bold uppercase tracking-[0.08em] text-marble-800">
                          {scenarioDef.name}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-marble-500">
                        <span className="flex items-center gap-1">
                          <CivSymbol civ={scenarioDef.civilization} className="h-3 w-3" />
                          {scenarioDef.civilization} ({scenarioDef.leader})
                        </span>
                        <span className="flex items-center gap-1">
                          <Map className="h-2.5 w-2.5" />
                          {mapType ?? scenarioDef.mapType}, {mapSize ?? scenarioDef.mapSize}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 text-xs text-marble-500">
                        <Eye className="h-2.5 w-2.5" />
                        Tests: {scenarioDef.blindSpot}
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <AgentOverview
                turnData={currentTurn}
                prevTurnData={prevTurn ?? undefined}
                index={index}
                total={turnNumbers.length}
              />
              <LeaderboardTable
                turnData={currentTurn}
                prevTurnData={prevTurn ?? undefined}
              />
              <CitiesPanel cities={currentTurn.agentCities} />
              <MilitaryPanel agent={currentTurn.agent} prevAgent={prevTurn?.agent} />
              <DiplomacyPanel agent={currentTurn.agent} />
              <ProgressPanel agent={currentTurn.agent} prevAgent={prevTurn?.agent} scenarioId={scenarioId ?? undefined} />
              <ReflectionsPanel reflections={currentTurn.agent.reflections} />
            </>
          )}
        </div>

        {/* Sparkline sidebar — desktop */}
        {hasTurns && turnSeries && (
          <div className="hidden w-96 shrink-0 overflow-y-auto border-l border-marble-300 bg-marble-50 p-4 lg:block">
            <SparklineSidebar turnSeries={turnSeries} currentIndex={index} />
          </div>
        )}

        {/* Sparkline sidebar — mobile overlay */}
        {hasTurns && turnSeries && showSidebar && (
          <div className="fixed inset-0 z-40 flex lg:hidden">
            <div className="absolute inset-0 bg-black/30" onClick={() => setShowSidebar(false)} />
            <div className="relative ml-auto h-full w-80 max-w-[85vw] overflow-y-auto bg-marble-50 p-4 shadow-lg">
              <button onClick={() => setShowSidebar(false)} className="absolute right-3 top-3 rounded-sm p-1 text-marble-500 hover:bg-marble-200 hover:text-marble-700">
                <X className="h-4 w-4" />
              </button>
              <SparklineSidebar turnSeries={turnSeries} currentIndex={index} />
            </div>
          </div>
        )}

        {/* Mobile chart toggle */}
        {hasTurns && (
          <button
            onClick={() => setShowSidebar(true)}
            className="fixed bottom-4 right-4 z-30 flex h-10 w-10 items-center justify-center rounded-full border border-marble-300 bg-marble-50 text-marble-600 shadow-md transition-colors hover:bg-marble-100 lg:hidden"
            title="Show trends"
          >
            <BarChart3 className="h-5 w-5" />
          </button>
        )}
      </div>
    </>
  );
}
