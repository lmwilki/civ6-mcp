"use client"

import Link from "next/link"
import { NavBar } from "@/components/nav-bar"
import { FullLeaderboard } from "@/components/model-leaderboard"
import { CivIcon } from "@/components/civ-icon"
import { CIV6_COLORS } from "@/lib/civ-colors"
import { Swords, ScrollText, Trophy, BarChart3 } from "lucide-react"

export default function CivBenchPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <NavBar active="leaderboard" />

      <main className="flex-1">
        <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6 sm:py-10">
          {/* Hero */}
          <h1 className="font-display text-3xl font-bold tracking-[0.08em] uppercase text-marble-800">
            CivBench
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-marble-600 max-w-2xl">
            A benchmark for evaluating LLM agents in Civilization VI. Each game
            pits a model against Civ VI&apos;s built-in AI on a standard map
            &mdash; the agent must read game state, manage an empire, conduct
            diplomacy, and pursue victory using the same tools a human player
            would. ELO ratings reflect competitive performance across completed
            games.
          </p>

          {/* How it works */}
          <div className="mt-8 border-t border-marble-300/50 pt-8">
            <h2 className="font-display text-xs font-bold uppercase tracking-[0.12em] text-marble-500">
              How It Works
            </h2>
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-sm border border-marble-300/50 bg-marble-50 p-3">
                <div className="flex items-center gap-2">
                  <CivIcon icon={Swords} color={CIV6_COLORS.military} size="sm" />
                  <h3 className="font-display text-[10px] font-bold uppercase tracking-[0.1em] text-marble-700">
                    Play
                  </h3>
                </div>
                <p className="mt-1.5 text-[11px] leading-relaxed text-marble-600">
                  An LLM agent plays a full game of Civ VI via the MCP server,
                  controlling a civilization from the Ancient Era onward.
                </p>
              </div>
              <div className="rounded-sm border border-marble-300/50 bg-marble-50 p-3">
                <div className="flex items-center gap-2">
                  <CivIcon icon={ScrollText} color={CIV6_COLORS.goldMetal} size="sm" />
                  <h3 className="font-display text-[10px] font-bold uppercase tracking-[0.1em] text-marble-700">
                    Record
                  </h3>
                </div>
                <p className="mt-1.5 text-[11px] leading-relaxed text-marble-600">
                  Every turn is logged &mdash; game state, agent reflections,
                  tool calls, and outcomes are stored as browsable diaries.
                </p>
              </div>
              <div className="rounded-sm border border-marble-300/50 bg-marble-50 p-3">
                <div className="flex items-center gap-2">
                  <CivIcon icon={BarChart3} color={CIV6_COLORS.science} size="sm" />
                  <h3 className="font-display text-[10px] font-bold uppercase tracking-[0.1em] text-marble-700">
                    Rate
                  </h3>
                </div>
                <p className="mt-1.5 text-[11px] leading-relaxed text-marble-600">
                  Game results feed an ELO system. Models gain or lose rating
                  based on victories and defeats against the AI opponent.
                </p>
              </div>
            </div>
          </div>

          {/* Quick links */}
          <div className="mt-6 flex gap-3">
            <Link
              href="/games"
              className="inline-flex items-center gap-2 rounded-sm border border-marble-400 bg-marble-100 px-4 py-2 text-sm font-medium text-marble-700 transition-colors hover:border-marble-500 hover:bg-marble-200"
            >
              <CivIcon icon={ScrollText} color={CIV6_COLORS.goldMetal} size="sm" />
              Browse Games
            </Link>
          </div>

          {/* Leaderboard */}
          <div className="mt-10 border-t border-marble-300/50 pt-8">
            <FullLeaderboard />
          </div>
        </div>
      </main>

      <footer className="border-t border-marble-300 px-6 py-4 text-center">
        <p className="font-mono text-xs text-marble-500">MIT License</p>
      </footer>
    </div>
  )
}
