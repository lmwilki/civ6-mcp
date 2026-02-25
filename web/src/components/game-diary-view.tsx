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
import { useDiary } from "@/lib/use-diary";
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  X,
  BarChart3,
} from "lucide-react";

interface GameDiaryViewProps {
  filename: string;
}

export function GameDiaryView({ filename }: GameDiaryViewProps) {
  const { turns, loading } = useDiary(filename);
  const [showSidebar, setShowSidebar] = useState(false);

  // Navigation state: useReducer keeps userIndex + following in sync atomically
  const [nav, dispatch] = useReducer(
    (
      state: { userIndex: number; following: boolean },
      action: { type: string; max?: number; index?: number },
    ) => {
      switch (action.type) {
        case "prev":
          return {
            userIndex: Math.max(0, state.userIndex - 1),
            following: false,
          };
        case "next": {
          const next = Math.min(action.max!, state.userIndex + 1);
          return { userIndex: next, following: next >= action.max! };
        }
        case "first":
          return { userIndex: 0, following: false };
        case "last":
          return { userIndex: action.max!, following: true };
        case "seek":
          return { userIndex: action.index!, following: false };
        default:
          return state;
      }
    },
    { userIndex: 0, following: true },
  );
  const index = nav.following
    ? Math.max(0, turns.length - 1)
    : Math.min(nav.userIndex, Math.max(0, turns.length - 1));

  // Navigation callbacks
  const goPrev = useCallback(() => dispatch({ type: "prev" }), []);
  const goNext = useCallback(
    () => dispatch({ type: "next", max: turns.length - 1 }),
    [turns.length],
  );
  const goFirst = useCallback(() => dispatch({ type: "first" }), []);
  const goLast = useCallback(
    () => dispatch({ type: "last", max: turns.length - 1 }),
    [turns.length],
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

  const currentTurn = turns[index];
  const prevTurn = index > 0 ? turns[index - 1] : undefined;

  return (
    <>
      {/* Turn navigation controls */}
      <div className="shrink-0 border-b border-marble-300 bg-marble-50/50 px-3 py-2 sm:px-6">
        <div className="mx-auto flex max-w-4xl items-center justify-center gap-1">
          <button
            onClick={goFirst}
            disabled={index === 0}
            className="rounded-sm p-1.5 text-marble-500 transition-colors hover:bg-marble-200 hover:text-marble-700 disabled:opacity-30"
            title="First entry (Home)"
          >
            <ChevronsLeft className="h-4 w-4" />
          </button>
          <button
            onClick={goPrev}
            disabled={index === 0}
            className="rounded-sm p-1.5 text-marble-500 transition-colors hover:bg-marble-200 hover:text-marble-700 disabled:opacity-30"
            title="Previous entry (Left arrow)"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>

          {turns.length > 1 && (
            <input
              type="range"
              min={0}
              max={turns.length - 1}
              value={index}
              onChange={(e) =>
                dispatch({ type: "seek", index: parseInt(e.target.value, 10) })
              }
              className="mx-2 w-24 accent-gold sm:w-48"
            />
          )}

          <button
            onClick={goNext}
            disabled={index >= turns.length - 1}
            className="rounded-sm p-1.5 text-marble-500 transition-colors hover:bg-marble-200 hover:text-marble-700 disabled:opacity-30"
            title="Next entry (Right arrow)"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
          <button
            onClick={goLast}
            disabled={index >= turns.length - 1}
            className="rounded-sm p-1.5 text-marble-500 transition-colors hover:bg-marble-200 hover:text-marble-700 disabled:opacity-30"
            title="Last entry (End)"
          >
            <ChevronsRight className="h-4 w-4" />
          </button>

          {currentTurn && (
            <span className="ml-2 font-mono text-xs tabular-nums text-marble-500">
              Turn {currentTurn.turn}
            </span>
          )}
        </div>
      </div>

      {/* Main content */}
      <div className="flex min-h-0 flex-1">
        {/* Panels */}
        <div className="flex-1 overflow-y-auto px-3 py-4 sm:px-6 sm:py-6">
          {loading && (
            <div className="flex h-full items-center justify-center">
              <p className="font-display text-sm tracking-[0.12em] uppercase text-marble-500">
                Loading diary...
              </p>
            </div>
          )}

          {!loading && turns.length === 0 && (
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
              <AgentOverview
                turnData={currentTurn}
                prevTurnData={prevTurn}
                index={index}
                total={turns.length}
              />
              <LeaderboardTable
                turnData={currentTurn}
                prevTurnData={prevTurn}
              />
              <CitiesPanel cities={currentTurn.agentCities} />
              <MilitaryPanel
                agent={currentTurn.agent}
                prevAgent={prevTurn?.agent}
              />
              <DiplomacyPanel agent={currentTurn.agent} />
              <ProgressPanel
                agent={currentTurn.agent}
                prevAgent={prevTurn?.agent}
              />
              <ReflectionsPanel reflections={currentTurn.agent.reflections} />
            </>
          )}
        </div>

        {/* Sparkline sidebar — desktop */}
        {turns.length > 1 && (
          <div className="hidden w-96 shrink-0 overflow-y-auto border-l border-marble-300 bg-marble-50 p-4 lg:block">
            <SparklineSidebar turns={turns} currentIndex={index} />
          </div>
        )}

        {/* Sparkline sidebar — mobile overlay */}
        {turns.length > 1 && showSidebar && (
          <div className="fixed inset-0 z-40 flex lg:hidden">
            <div
              className="absolute inset-0 bg-black/30"
              onClick={() => setShowSidebar(false)}
            />
            <div className="relative ml-auto h-full w-80 max-w-[85vw] overflow-y-auto bg-marble-50 p-4 shadow-lg">
              <button
                onClick={() => setShowSidebar(false)}
                className="absolute right-3 top-3 rounded-sm p-1 text-marble-500 hover:bg-marble-200 hover:text-marble-700"
              >
                <X className="h-4 w-4" />
              </button>
              <SparklineSidebar turns={turns} currentIndex={index} />
            </div>
          </div>
        )}

        {/* Floating toggle button — mobile only */}
        {turns.length > 1 && (
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
