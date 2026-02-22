"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { NavBar } from "@/components/nav-bar"
import { AgentOverview } from "@/components/agent-overview"
import { LeaderboardTable } from "@/components/leaderboard-table"
import { CitiesPanel } from "@/components/cities-panel"
import { MilitaryPanel } from "@/components/military-panel"
import { DiplomacyPanel } from "@/components/diplomacy-panel"
import { ProgressPanel } from "@/components/progress-panel"
import { ReflectionsPanel } from "@/components/reflections-panel"
import { ScoreSparkline } from "@/components/score-sparkline"
import { MultiCivChart } from "@/components/multi-civ-chart"
import { useDiaryList, useDiary } from "@/lib/use-diary"
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react"

export default function DiaryPage() {
  const diaries = useDiaryList()
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const { turns, loading } = useDiary(selectedFile)
  const [index, setIndex] = useState(0)
  const followingRef = useRef(true)

  // Auto-select first diary
  useEffect(() => {
    if (diaries.length > 0 && !selectedFile) {
      setSelectedFile(diaries[0].filename)
    }
  }, [diaries, selectedFile])

  // Auto-follow: jump to latest turn
  useEffect(() => {
    if (turns.length > 0 && followingRef.current) {
      setIndex(turns.length - 1)
    }
  }, [turns.length])

  // Track whether user is "following"
  useEffect(() => {
    followingRef.current = index >= turns.length - 1
  }, [index, turns.length])

  // Navigation
  const goPrev = useCallback(() => setIndex((i) => Math.max(0, i - 1)), [])
  const goNext = useCallback(
    () => setIndex((i) => Math.min(turns.length - 1, i + 1)),
    [turns.length]
  )
  const goFirst = useCallback(() => setIndex(0), [])
  const goLast = useCallback(() => setIndex(turns.length - 1), [turns.length])

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault()
        goPrev()
      } else if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault()
        goNext()
      } else if (e.key === "Home") {
        e.preventDefault()
        goFirst()
      } else if (e.key === "End") {
        e.preventDefault()
        goLast()
      }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [goPrev, goNext, goFirst, goLast])

  const currentTurn = turns[index]
  const prevTurn = index > 0 ? turns[index - 1] : undefined
  const turnNumber = currentTurn?.turn ?? null

  return (
    <div className="flex h-screen flex-col">
      <NavBar active="diary" turn={turnNumber} />

      {/* Diary selector + controls */}
      <div className="shrink-0 border-b border-marble-300 bg-marble-50/50 px-6 py-2">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <div className="flex items-center gap-3">
            <select
              value={selectedFile || ""}
              onChange={(e) => setSelectedFile(e.target.value || null)}
              className="rounded-sm border border-marble-300 bg-marble-100 px-2 py-1 font-mono text-xs text-marble-700"
            >
              {diaries.map((d) => (
                <option key={d.filename} value={d.filename}>
                  {d.label} ({d.count} entries)
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1">
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
                onChange={(e) => setIndex(parseInt(e.target.value, 10))}
                className="mx-2 w-48 accent-gold"
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
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex min-h-0 flex-1">
        {/* Panels */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
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

        {/* Sparkline sidebar */}
        {turns.length > 1 && (
          <div className="w-96 shrink-0 overflow-y-auto border-l border-marble-300 bg-marble-50 p-4">
            <h3 className="mb-3 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
              Trends
            </h3>
            <div className="space-y-2">
              <ScoreSparkline turns={turns} currentIndex={index} field="score" label="Score" color="#D4A853" />
              <ScoreSparkline turns={turns} currentIndex={index} field="science" label="Science" color="#2563eb" />
              <ScoreSparkline turns={turns} currentIndex={index} field="culture" label="Culture" color="#9333ea" />
              <ScoreSparkline turns={turns} currentIndex={index} field="gold" label="Gold" color="#8C6E2C" />
              <ScoreSparkline turns={turns} currentIndex={index} field="military" label="Military" color="#5C5549" />
              <ScoreSparkline turns={turns} currentIndex={index} field="faith" label="Faith" color="#C4785C" />
              <ScoreSparkline turns={turns} currentIndex={index} field="territory" label="Territory" color="#7A9B8A" />
              <ScoreSparkline turns={turns} currentIndex={index} field="exploration_pct" label="Explored" color="#4A90A4" />
              <ScoreSparkline turns={turns} currentIndex={index} field="pop" label="Pop" color="#7A7269" />
            </div>

            {turns.some((t) => t.rivals.length > 0) && (
              <div className="mt-4 border-t border-marble-300/50 pt-4">
                <MultiCivChart turns={turns} currentIndex={index} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
