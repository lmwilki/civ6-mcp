"use client";

import { useCallback, useEffect, useReducer, useState } from "react";
import { AgentOverview } from "@/components/agent-overview";
import { LeaderboardTable } from "@/components/leaderboard-table";
import { CitiesPanel } from "@/components/cities-panel";
import { MilitaryPanel } from "@/components/military-panel";
import { DiplomacyPanel } from "@/components/diplomacy-panel";
import { ProgressPanel } from "@/components/progress-panel";
import { ReflectionsPanel } from "@/components/reflections-panel";
import { SparklineSidebar } from "@/components/sparkline-sidebar";
import { useDiarySummary, useDiaryTurn } from "@/lib/use-diary";
import type { GameOutcome } from "@/lib/diary-types";
import { getVictoryTypeMeta } from "@/components/game-status-badge";
import { CivIcon, CivSymbol } from "@/components/civ-icon";
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  X,
  BarChart3,
  Skull,
  Trophy,
  Eye,
  Map,
} from "lucide-react";
import { SCENARIOS, DIFFICULTY_META } from "@/lib/scenarios";

interface GameDiaryViewProps {
  filename: string;
}

const STATUS_COLORS = {
  victory: "#3D8B6E",
  defeat: "#C0503A",
} as const;

function OutcomeBanner({ outcome }: { outcome: GameOutcome }) {
  const isVictory = outcome.result === "victory";
  const vt = getVictoryTypeMeta(outcome.victoryType);
  const VtIcon = vt.icon;
  const bgColor = isVictory
    ? "rgba(61,139,110,0.08)"
    : "rgba(192,80,58,0.08)";
  const borderColor = isVictory
    ? "rgba(61,139,110,0.25)"
    : "rgba(192,80,58,0.25)";
  const headColor = isVictory ? STATUS_COLORS.victory : STATUS_COLORS.defeat;

  return (
    <div
      className="mx-auto w-full max-w-2xl rounded-sm border px-4 py-3"
      style={{ backgroundColor: bgColor, borderColor }}
    >
      <div className="flex items-center gap-3">
        <CivIcon
          icon={isVictory ? Trophy : Skull}
          color={headColor}
          size="md"
        />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span
              className="font-display text-sm font-bold uppercase tracking-[0.08em]"
              style={{ color: headColor }}
            >
              {isVictory ? "Victory" : "Defeated"}
            </span>
            <span className="font-mono text-xs tabular-nums text-marble-500">
              Turn {outcome.turn}
            </span>
          </div>
          <div className="mt-0.5 flex items-center gap-1.5">
            <CivIcon icon={VtIcon} color={vt.color} size="sm" />
            <span className="text-xs" style={{ color: vt.color }}>
              {vt.label} Victory
            </span>
            <span className="text-xs text-marble-500">—</span>
            <CivSymbol civ={outcome.winnerCiv} className="h-3.5 w-3.5" />
            <span className="text-xs text-marble-700">
              {outcome.winnerCiv} ({outcome.winnerLeader})
            </span>
          </div>
        </div>
      </div>
    </div>
  );
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

  // Nav state — index into turnNumbers array
  type NavAction =
    | { type: "prev" }
    | { type: "next"; max: number }
    | { type: "first" }
    | { type: "last"; max: number }
    | { type: "seek"; index: number };

  const [nav, dispatch] = useReducer(
    (state: { userIndex: number; following: boolean }, action: NavAction) => {
      switch (action.type) {
        case "prev":
          return { userIndex: Math.max(0, state.userIndex - 1), following: false };
        case "next": {
          const next = Math.min(action.max, state.userIndex + 1);
          return { userIndex: next, following: next >= action.max };
        }
        case "first":
          return { userIndex: 0, following: false };
        case "last":
          return { userIndex: action.max, following: true };
        case "seek":
          return { userIndex: action.index, following: false };
      }
    },
    { userIndex: 0, following: true },
  );

  const maxIdx = Math.max(0, turnNumbers.length - 1);
  const index = nav.following
    ? maxIdx
    : Math.min(nav.userIndex, maxIdx);

  // Turn detail subscriptions — ~12 docs each
  const selectedTurn = turnNumbers[index];
  const prevTurnNum = index > 0 ? turnNumbers[index - 1] : undefined;

  const currentTurn = useDiaryTurn(filename, selectedTurn, agentModelOverride);
  const prevTurn = useDiaryTurn(filename, prevTurnNum, agentModelOverride);

  // Nav callbacks
  const goPrev = useCallback(() => dispatch({ type: "prev" }), []);
  const goNext = useCallback(
    () => dispatch({ type: "next", max: maxIdx }),
    [maxIdx],
  );
  const goFirst = useCallback(() => dispatch({ type: "first" }), []);
  const goLast = useCallback(
    () => dispatch({ type: "last", max: maxIdx }),
    [maxIdx],
  );

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        goPrev();
      } else if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        goNext();
      } else if (e.key === "Home") {
        e.preventDefault();
        goFirst();
      } else if (e.key === "End") {
        e.preventDefault();
        goLast();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [goPrev, goNext, goFirst, goLast]);

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
              onChange={(e) =>
                dispatch({ type: "seek", index: parseInt(e.target.value, 10) })
              }
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
              className="ml-1.5 rounded-sm px-1.5 py-0.5 font-display text-[9px] font-bold uppercase tracking-[0.08em]"
              style={{
                color: outcome.result === "victory" ? STATUS_COLORS.victory : STATUS_COLORS.defeat,
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
            <div className="flex h-full items-center justify-center">
              <p className="font-display text-sm tracking-[0.12em] uppercase text-marble-500">
                Loading diary...
              </p>
            </div>
          )}

          {!loading && turnNumbers.length === 0 && (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <p className="font-display text-sm tracking-[0.12em] uppercase text-marble-500">
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
                          className="inline-flex items-center gap-1 rounded-sm px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-[0.08em]"
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
                        <span className="font-display text-xs font-bold uppercase tracking-[0.1em] text-marble-800">
                          {scenarioDef.name}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-[10px] text-marble-500">
                        <span className="flex items-center gap-1">
                          <CivSymbol civ={scenarioDef.civilization} className="h-3 w-3" />
                          {scenarioDef.civilization} ({scenarioDef.leader})
                        </span>
                        <span className="flex items-center gap-1">
                          <Map className="h-2.5 w-2.5" />
                          {mapType ?? scenarioDef.mapType}, {mapSize ?? scenarioDef.mapSize}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 text-[10px] text-marble-500">
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
              <ProgressPanel agent={currentTurn.agent} prevAgent={prevTurn?.agent} />
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
