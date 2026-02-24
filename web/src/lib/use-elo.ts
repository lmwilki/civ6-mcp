"use client"

import { useEffect, useState } from "react"
import type { EloEntry } from "./elo"
import { CONVEX_MODE } from "@/components/convex-provider"
import { useEloConvex } from "./use-elo-convex"

interface EloData {
  ratings: EloEntry[]
  gameCount: number
  loading: boolean
}

function useEloFs(): EloData {
  const [ratings, setRatings] = useState<EloEntry[]>([])
  const [gameCount, setGameCount] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let first = true
    const poll = () =>
      fetch("/api/elo")
        .then((r) => r.json())
        .then((data) => {
          setRatings(data.ratings || [])
          setGameCount(data.gameCount || 0)
        })
        .catch(() => {})
        .finally(() => {
          if (first) {
            setLoading(false)
            first = false
          }
        })

    poll()
    const id = setInterval(poll, 30_000)
    return () => clearInterval(id)
  }, [])

  return { ratings, gameCount, loading }
}

export const useElo = CONVEX_MODE ? useEloConvex : useEloFs
