"use client"

import Link from "next/link"
import { useQuery } from "convex/react"
import { api } from "../../convex/_generated/api"
import { CONVEX_MODE } from "./convex-provider"

interface LiveGame {
  gameId: string
  civ: string
  leader: string
  lastTurn: number
}

export function LiveGameBanner() {
  if (!CONVEX_MODE) return null

  // eslint-disable-next-line react-hooks/rules-of-hooks
  const liveGame: LiveGame | null | undefined = useQuery(api.diary.getLiveGame)

  if (!liveGame) return null

  return (
    <Link
      href="/diary"
      className="group flex items-center justify-center gap-3 rounded-sm border border-patina/30 bg-patina/10 px-6 py-3 transition-colors hover:bg-patina/20"
    >
      <span className="relative flex h-2.5 w-2.5">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-patina opacity-75" />
        <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-patina" />
      </span>
      <span className="text-sm text-marble-700">
        <span className="font-semibold">{liveGame.civ}</span> is playing now
        <span className="ml-2 font-mono text-xs text-marble-500">
          Turn {liveGame.lastTurn}
        </span>
      </span>
      <span className="text-xs text-patina group-hover:underline">Watch live</span>
    </Link>
  )
}
