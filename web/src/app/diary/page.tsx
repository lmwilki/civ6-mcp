"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { NavBar } from "@/components/nav-bar"
import { DiaryCard } from "@/components/diary-card"
import { ScoreSparkline } from "@/components/score-sparkline"
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
  const { entries, loading } = useDiary(selectedFile)
  const [index, setIndex] = useState(0)
  const followingRef = useRef(true) // true = auto-scroll to latest entry

  // Auto-select first diary
  useEffect(() => {
    if (diaries.length > 0 && !selectedFile) {
      setSelectedFile(diaries[0].filename)
    }
  }, [diaries, selectedFile])

  // Auto-follow: jump to latest entry only if user is on the last entry
  useEffect(() => {
    if (entries.length > 0) {
      if (followingRef.current) {
        setIndex(entries.length - 1)
      }
    }
  }, [entries.length])

  // Track whether user is "following" (viewing last entry)
  useEffect(() => {
    followingRef.current = index >= entries.length - 1
  }, [index, entries.length])

  // Keyboard navigation
  const goPrev = useCallback(() => setIndex((i) => Math.max(0, i - 1)), [])
  const goNext = useCallback(
    () => setIndex((i) => Math.min(entries.length - 1, i + 1)),
    [entries.length]
  )
  const goFirst = useCallback(() => setIndex(0), [])
  const goLast = useCallback(() => setIndex(entries.length - 1), [entries.length])

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

  const currentEntry = entries[index]
  const prevEntry = index > 0 ? entries[index - 1] : undefined
  const currentTurn = currentEntry?.turn ?? null

  return (
    <div className="flex h-screen flex-col">
      <NavBar active="diary" turn={currentTurn} />

      {/* Diary selector + controls */}
      <div className="shrink-0 border-b border-marble-300 bg-marble-50/50 px-6 py-2">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          {/* Diary file picker */}
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

          {/* Navigation */}
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

            {/* Turn scrubber */}
            {entries.length > 1 && (
              <input
                type="range"
                min={0}
                max={entries.length - 1}
                value={index}
                onChange={(e) => setIndex(parseInt(e.target.value, 10))}
                className="mx-2 w-48 accent-gold"
              />
            )}

            <button
              onClick={goNext}
              disabled={index >= entries.length - 1}
              className="rounded-sm p-1.5 text-marble-500 transition-colors hover:bg-marble-200 hover:text-marble-700 disabled:opacity-30"
              title="Next entry (Right arrow)"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
            <button
              onClick={goLast}
              disabled={index >= entries.length - 1}
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
        {/* Diary card */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {loading && (
            <div className="flex h-full items-center justify-center">
              <p className="font-display text-sm tracking-[0.12em] uppercase text-marble-500">
                Loading diary...
              </p>
            </div>
          )}

          {!loading && entries.length === 0 && (
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

          {!loading && currentEntry && (
            <DiaryCard
              entry={currentEntry}
              prev={prevEntry}
              index={index}
              total={entries.length}
            />
          )}
        </div>

        {/* Sparkline sidebar */}
        {entries.length > 1 && (
          <div className="w-96 shrink-0 overflow-y-auto border-l border-marble-300 bg-marble-50 p-4">
            <h3 className="mb-3 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
              Trends
            </h3>
            <div className="space-y-2">
              <ScoreSparkline entries={entries} currentIndex={index} field="total" label="Score" color="#D4A853" />
              <ScoreSparkline entries={entries} currentIndex={index} field="science" label="Science" color="#2563eb" />
              <ScoreSparkline entries={entries} currentIndex={index} field="culture" label="Culture" color="#9333ea" />
              <ScoreSparkline entries={entries} currentIndex={index} field="gold" label="Gold" color="#8C6E2C" />
              <ScoreSparkline entries={entries} currentIndex={index} field="faith" label="Faith" color="#C4785C" />
              <ScoreSparkline entries={entries} currentIndex={index} field="cities" label="Cities" color="#5C5549" />
              <ScoreSparkline entries={entries} currentIndex={index} field="population" label="Pop" color="#7A7269" />
              <ScoreSparkline entries={entries} currentIndex={index} field="exploration_pct" label="Explore" color="#7A9B8A" />
              <ScoreSparkline entries={entries} currentIndex={index} field="era_score" label="Era" color="#D4A853" height={30} />
              <ScoreSparkline entries={entries} currentIndex={index} field="leader_score" label="Leader" color="#C4785C" height={30} />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
