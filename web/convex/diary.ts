import { query } from "./_generated/server"
import { v } from "convex/values"

/** List all games — returns shape compatible with DiaryFile[] */
export const listGames = query({
  args: {},
  handler: async (ctx) => {
    const games = await ctx.db
      .query("games")
      .withIndex("by_status")
      .order("desc")
      .collect()
    return games.map((g) => ({
      gameId: g.gameId,
      filename: `diary_${g.gameId}.jsonl`,
      label: g.civ,
      count: g.turnCount,
      hasCities: g.hasCities,
      hasLogs: g.hasLogs,
      status: g.status,
      leader: g.leader,
      lastUpdated: g.lastUpdated,
      outcome: g.outcome ?? null,
    }))
  },
})

/** Get the most recently updated live game (if any) */
export const getLiveGame = query({
  args: {},
  handler: async (ctx) => {
    const live = await ctx.db
      .query("games")
      .withIndex("by_status", (q) => q.eq("status", "live"))
      .order("desc")
      .first()
    if (!live) return null
    return {
      gameId: live.gameId,
      civ: live.civ,
      leader: live.leader,
      lastTurn: live.lastTurn,
    }
  },
})

/** Get all player + city rows for a game */
export const getGameTurns = query({
  args: { gameId: v.string() },
  handler: async (ctx, { gameId }) => {
    const playerRows = await ctx.db
      .query("playerRows")
      .withIndex("by_game_turn", (q) => q.eq("gameId", gameId))
      .collect()
    const cityRows = await ctx.db
      .query("cityRows")
      .withIndex("by_game_turn", (q) => q.eq("gameId", gameId))
      .collect()
    return { playerRows, cityRows }
  },
})
