"use client"

import { useMemo, useState } from "react"
import { Timeline } from "@/components/timeline"
import { LiveIndicator } from "@/components/live-indicator"
import { NavBar } from "@/components/nav-bar"
import { useGameLog, useGameLogs } from "@/lib/use-game-log"
import { getToolCategory } from "@/lib/types"
import type { LogEntry } from "@/lib/types"

type ToolCategory = "query" | "action" | "turn" | "error"

const CATEGORY_LABELS: Record<ToolCategory, string> = {
  query: "Queries",
  action: "Actions",
  turn: "Turns",
  error: "Errors",
}

const CATEGORY_STYLES: Record<ToolCategory, { on: string; off: string }> = {
  query: {
    on: "bg-marble-200 text-marble-700 border-marble-400",
    off: "bg-marble-50 text-marble-400 border-marble-200",
  },
  action: {
    on: "bg-gold/15 text-gold-dark border-gold/40",
    off: "bg-marble-50 text-marble-400 border-marble-200",
  },
  turn: {
    on: "bg-gold/20 text-gold-dark border-gold-dark/30",
    off: "bg-marble-50 text-marble-400 border-marble-200",
  },
  error: {
    on: "bg-terracotta/10 text-terracotta border-terracotta/30",
    off: "bg-marble-50 text-marble-400 border-marble-200",
  },
}

function formatGameLabel(g: { game: string; civ: string; count: number; min_turn: number | null; max_turn: number | null }): string {
  const civ = g.civ.replace(/\b\w/g, (c) => c.toUpperCase())
  const turns = g.min_turn != null && g.max_turn != null ? `T${g.min_turn}-${g.max_turn}` : "no turns"
  return `${civ} (${turns}, ${g.count})`
}

export default function Home() {
  const [live, setLive] = useState(true)
  const [selectedGame, setSelectedGame] = useState<string | null>(null)
  const [selectedSession, setSelectedSession] = useState<string | null>(null)
  const [hiddenCategories, setHiddenCategories] = useState<Set<ToolCategory>>(new Set())
  const [hiddenTools, setHiddenTools] = useState<Set<string>>(new Set())
  const [showToolFilter, setShowToolFilter] = useState(false)

  const games = useGameLogs()
  const effectiveGame = selectedGame ?? (games.length > 0 ? games[0].game : null)

  // Get sessions for the selected game
  const selectedGameInfo = useMemo(
    () => games.find((g) => g.game === effectiveGame),
    [games, effectiveGame]
  )

  const { entries, connected } = useGameLog(live, effectiveGame, selectedSession)

  // Compute tool counts for the filter panel
  const toolCounts = useMemo(() => {
    const counts = new Map<string, number>()
    for (const e of entries) {
      const t = e.tool ?? "unknown"
      counts.set(t, (counts.get(t) ?? 0) + 1)
    }
    return counts
  }, [entries])

  // Get category for an entry (use pre-computed field, fallback for safety)
  const entryCategory = (e: LogEntry): ToolCategory => {
    if (e.category) return e.category
    if (e.type === "error") return "error"
    return getToolCategory(e.tool)
  }

  // Filter entries by category and specific tools
  const filtered = useMemo(() => {
    if (hiddenCategories.size === 0 && hiddenTools.size === 0) return entries
    return entries.filter((e) => {
      const cat = entryCategory(e)
      if (hiddenCategories.has(cat)) return false
      if (e.tool && hiddenTools.has(e.tool)) return false
      return true
    })
  }, [entries, hiddenCategories, hiddenTools])

  const currentTurn = filtered.length > 0 ? filtered[filtered.length - 1].turn : null

  const toggleCategory = (cat: ToolCategory) => {
    setHiddenCategories((prev) => {
      const next = new Set(prev)
      if (next.has(cat)) next.delete(cat)
      else next.add(cat)
      return next
    })
  }

  const toggleTool = (tool: string) => {
    setHiddenTools((prev) => {
      const next = new Set(prev)
      if (next.has(tool)) next.delete(tool)
      else next.add(tool)
      return next
    })
  }

  // Group tools by category for the filter panel
  const toolsByCategory = useMemo(() => {
    const groups: Record<ToolCategory, { tool: string; count: number }[]> = {
      query: [],
      action: [],
      turn: [],
      error: [],
    }
    for (const [tool, count] of toolCounts) {
      const cat = tool === "unknown" ? "error" : getToolCategory(tool)
      groups[cat].push({ tool, count })
    }
    for (const cat of Object.keys(groups) as ToolCategory[]) {
      groups[cat].sort((a, b) => b.count - a.count)
    }
    return groups
  }, [toolCounts])

  return (
    <div className="flex h-screen flex-col">
      <NavBar active="timeline" turn={currentTurn} />

      {/* Sub-header with filters */}
      <div className="shrink-0 border-b border-marble-300 bg-marble-50/50 px-6 py-2">
        <div className="mx-auto flex max-w-4xl items-center gap-4">
          {/* Game picker */}
          <select
            value={effectiveGame ?? ""}
            onChange={(e) => {
              setSelectedGame(e.target.value || null)
              setSelectedSession(null)
            }}
            className="rounded-sm border border-marble-300 bg-marble-100 px-2 py-1 font-mono text-xs text-marble-700"
          >
            <option value="">Select game...</option>
            {games.map((g) => (
              <option key={g.game} value={g.game}>
                {formatGameLabel(g)}
              </option>
            ))}
          </select>

          {/* Session sub-filter (within selected game) */}
          {selectedGameInfo && selectedGameInfo.sessions.length > 1 && (
            <select
              value={selectedSession ?? ""}
              onChange={(e) => setSelectedSession(e.target.value || null)}
              className="rounded-sm border border-marble-300 bg-marble-100 px-2 py-1 font-mono text-xs text-marble-700"
            >
              <option value="">All sessions</option>
              {selectedGameInfo.sessions.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          )}

          {/* Category toggles */}
          <div className="flex items-center gap-1">
            {(Object.keys(CATEGORY_LABELS) as ToolCategory[]).map((cat) => {
              const active = !hiddenCategories.has(cat)
              return (
                <button
                  key={cat}
                  onClick={() => toggleCategory(cat)}
                  className={`rounded-sm border px-2 py-0.5 font-mono text-[10px] transition-colors ${
                    active ? CATEGORY_STYLES[cat].on : CATEGORY_STYLES[cat].off
                  }`}
                >
                  {CATEGORY_LABELS[cat]}
                </button>
              )
            })}
          </div>

          {/* Tool-level filter toggle */}
          <button
            onClick={() => setShowToolFilter((v) => !v)}
            className={`rounded-sm border px-2 py-0.5 font-mono text-[10px] transition-colors ${
              hiddenTools.size > 0
                ? "border-terracotta/30 bg-terracotta/10 text-terracotta"
                : "border-marble-300 text-marble-500 hover:bg-marble-100"
            }`}
          >
            {hiddenTools.size > 0 ? `${hiddenTools.size} hidden` : "Tools..."}
          </button>

          <div className="flex-1" />

          {/* Event count + live toggle */}
          <span className="font-mono text-xs tabular-nums text-marble-500">
            {filtered.length === entries.length
              ? `${entries.length} events`
              : `${filtered.length} / ${entries.length}`}
          </span>
          <LiveIndicator
            live={live}
            connected={connected}
            onToggle={() => setLive(!live)}
          />
        </div>
      </div>

      {/* Tool filter panel (collapsible) */}
      {showToolFilter && (
        <div className="shrink-0 border-b border-marble-300 bg-marble-50 px-6 py-3">
          <div className="mx-auto max-w-4xl">
            <div className="flex items-center justify-between">
              <span className="font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
                Filter Tools
              </span>
              {hiddenTools.size > 0 && (
                <button
                  onClick={() => setHiddenTools(new Set())}
                  className="font-mono text-[10px] text-terracotta hover:underline"
                >
                  Clear all
                </button>
              )}
            </div>
            <div className="mt-2 space-y-2">
              {(Object.keys(CATEGORY_LABELS) as ToolCategory[]).map((cat) => {
                const tools = toolsByCategory[cat]
                if (tools.length === 0) return null
                return (
                  <div key={cat}>
                    <span className="font-mono text-[10px] text-marble-500">{CATEGORY_LABELS[cat]}</span>
                    <div className="mt-0.5 flex flex-wrap gap-1">
                      {tools.map(({ tool, count }) => {
                        const hidden = hiddenTools.has(tool)
                        return (
                          <button
                            key={tool}
                            onClick={() => toggleTool(tool)}
                            className={`rounded-sm border px-1.5 py-0.5 font-mono text-[10px] transition-colors ${
                              hidden
                                ? "border-marble-200 bg-marble-50 text-marble-400 line-through"
                                : "border-marble-300 bg-marble-100 text-marble-700"
                            }`}
                          >
                            {tool} <span className="text-marble-400">{count}</span>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Timeline */}
      <Timeline entries={filtered} live={live} />
    </div>
  )
}
