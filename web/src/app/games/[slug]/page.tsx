"use client"

import { useParams, useSearchParams, useRouter } from "next/navigation"
import { NavBar } from "@/components/nav-bar"
import { GameDiaryView } from "@/components/game-diary-view"
import { GameLogView } from "@/components/game-log-view"

type Tab = "diary" | "log"

export default function GameDetailPage() {
  const params = useParams<{ slug: string }>()
  const searchParams = useSearchParams()
  const router = useRouter()

  const slug = params.slug
  const filename = `diary_${slug}.jsonl`
  const tab: Tab = searchParams.get("tab") === "log" ? "log" : "diary"

  const setTab = (t: Tab) => {
    const url = t === "log" ? `/games/${slug}?tab=log` : `/games/${slug}`
    router.replace(url)
  }

  return (
    <div className="flex min-h-screen flex-col">
      <NavBar active="games" />

      {/* Tab bar */}
      <div className="shrink-0 border-b border-marble-300 bg-marble-50 px-3 sm:px-6">
        <div className="mx-auto flex max-w-4xl">
          <button
            onClick={() => setTab("diary")}
            className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
              tab === "diary"
                ? "border-gold-dark text-gold-dark"
                : "border-transparent text-marble-500 hover:text-marble-700"
            }`}
          >
            Diary
          </button>
          <button
            onClick={() => setTab("log")}
            className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
              tab === "log"
                ? "border-gold-dark text-gold-dark"
                : "border-transparent text-marble-500 hover:text-marble-700"
            }`}
          >
            Turn Log
          </button>
        </div>
      </div>

      {/* Tab content */}
      {tab === "diary" ? (
        <GameDiaryView filename={filename} />
      ) : (
        <GameLogView gameSlug={slug} />
      )}
    </div>
  )
}
