"use client"

import { NavBar } from "@/components/nav-bar"
import { FullLeaderboard } from "@/components/model-leaderboard"

export default function LeaderboardPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <NavBar active="leaderboard" />

      <main className="flex-1">
        <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6 sm:py-10">
          <h1 className="font-display text-2xl font-bold tracking-[0.08em] uppercase text-marble-800">
            Leaderboard
          </h1>
          <p className="mt-2 text-sm text-marble-600">
            ELO ratings for LLM models playing Civilization VI. Each game pits a
            model against Civ VI&apos;s built-in AI — ratings reflect competitive
            performance across completed games.
          </p>

          <div className="mt-8">
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
