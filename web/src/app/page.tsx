"use client"

import Link from "next/link"
import { NavBar } from "@/components/nav-bar"
import { RecentGames } from "@/components/recent-games"
import { CivIcon } from "@/components/civ-icon"
import { CIV6_COLORS } from "@/lib/civ-colors"
import { LeaderboardPreview } from "@/components/model-leaderboard"
import {
  Github,
  Swords,
  Building2,
  Handshake,
  FlaskConical,
  Flame,
  Trophy,
  ScrollText,
} from "lucide-react"

const CAPABILITIES = [
  {
    title: "Units & Combat",
    description: "Move, attack, fortify, found cities, promote, upgrade",
    icon: Swords,
    color: CIV6_COLORS.military,
  },
  {
    title: "Cities & Production",
    description: "Inspect yields, set builds, purchase with gold, manage citizen focus",
    icon: Building2,
    color: CIV6_COLORS.production,
  },
  {
    title: "Diplomacy & Trade",
    description: "Friendships, alliances, peace deals, trade routes, World Congress",
    icon: Handshake,
    color: CIV6_COLORS.favor,
  },
  {
    title: "Research & Civics",
    description: "Tech and civic trees, eureka tracking, policy cards, governments",
    icon: FlaskConical,
    color: CIV6_COLORS.science,
  },
  {
    title: "Religion & Culture",
    description: "Pantheons, beliefs, missionaries, Great People, wonders",
    icon: Flame,
    color: CIV6_COLORS.culture,
  },
  {
    title: "Strategy & Victory",
    description: "All six victory conditions tracked, advisors, strategic overview",
    icon: Trophy,
    color: CIV6_COLORS.goldMetal,
  },
]

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <NavBar active="home" />

      <main className="flex-1">
        <div className="mx-auto grid max-w-5xl gap-10 px-4 py-6 sm:px-6 sm:py-10 lg:grid-cols-[1fr_280px]">
          {/* Left column */}
          <div>
            {/* Hero */}
            <section>
              <h2 className="font-display text-3xl font-bold tracking-[0.08em] uppercase text-marble-800">
                civ6-mcp
              </h2>
              <p className="mt-3 text-xl leading-relaxed text-marble-600">
                An MCP server that connects LLM agents to live games of
                Civilization VI. The agent reads full game state, moves units,
                manages cities, conducts diplomacy, and plays complete games
                through the engine&apos;s own rule-enforcing APIs.
              </p>
              <div className="mt-5">
                <a
                  href="https://github.com/lmwilki/civ6-mcp"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-sm border border-marble-400 bg-marble-100 px-4 py-2 text-sm font-medium text-marble-700 transition-colors hover:border-marble-500 hover:bg-marble-200"
                >
                  <Github className="h-4 w-4" />
                  GitHub
                </a>
              </div>
            </section>

            {/* Divider */}
            <div className="my-8 border-t border-marble-300/50" />

            {/* Leaderboard Preview */}
            <LeaderboardPreview />

            {/* Divider */}
            <div className="my-8 border-t border-marble-300/50" />

            {/* Capabilities */}
            <section>
              <h3 className="mb-4 font-display text-xs font-bold uppercase tracking-[0.12em] text-marble-500">
                70+ Tools
              </h3>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {CAPABILITIES.map((cap) => (
                  <div
                    key={cap.title}
                    className="rounded-sm border border-marble-300/50 bg-marble-50 p-3"
                  >
                    <div className="flex items-center gap-2">
                      <CivIcon icon={cap.icon} color={cap.color} size="sm" />
                      <h4 className="font-display text-xs font-bold uppercase tracking-[0.1em] text-marble-700">
                        {cap.title}
                      </h4>
                    </div>
                    <p className="mt-1.5 text-sm leading-relaxed text-marble-600">
                      {cap.description}
                    </p>
                  </div>
                ))}
              </div>
            </section>

            {/* Divider */}
            <div className="my-8 border-t border-marble-300/50" />

            {/* Archive */}
            <section>
              <h3 className="font-display text-xs font-bold uppercase tracking-[0.12em] text-marble-500">
                Game Archive
              </h3>
              <p className="mt-2 text-sm text-marble-600">
                Browse game diaries — turn-by-turn state, agent reflections, and
                rival comparisons.
              </p>
              <div className="mt-3 flex items-center gap-3">
                <Link
                  href="/diary"
                  className="inline-flex items-center gap-2 rounded-sm border border-gold/40 bg-gold/10 px-4 py-2 text-sm font-medium text-gold-dark transition-colors hover:bg-gold/20"
                >
                  Browse Diaries
                </Link>
                <Link
                  href="/timeline"
                  className="inline-flex items-center gap-2 rounded-sm border border-marble-300 bg-marble-100 px-4 py-2 text-sm font-medium text-marble-700 transition-colors hover:bg-marble-200"
                >
                  Tool Timeline
                </Link>
              </div>
            </section>
          </div>

          {/* Right column — Recent Games */}
          <aside className="lg:sticky lg:top-6 lg:self-start">
            <h3 className="mb-3 flex items-center gap-1.5 font-display text-xs font-bold uppercase tracking-[0.12em] text-marble-500">
              <CivIcon icon={ScrollText} color={CIV6_COLORS.goldMetal} size="sm" />
              Recent Games
            </h3>
            <RecentGames />
          </aside>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-marble-300 px-6 py-4 text-center">
        <p className="font-mono text-xs text-marble-500">MIT License</p>
      </footer>
    </div>
  )
}
