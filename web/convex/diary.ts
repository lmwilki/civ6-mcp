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
    // Fetch agent_model from the first agent playerRow per game
    const results = await Promise.all(
      games.map(async (g) => {
        const firstAgent = await ctx.db
          .query("playerRows")
          .withIndex("by_game_turn", (q) => q.eq("gameId", g.gameId))
          .filter((q) => q.eq(q.field("is_agent"), true))
          .first()
        return {
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
          agent_model: firstAgent?.agent_model ?? null,
        }
      })
    )
    return results
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

/** Get completed games with outcomes + last-turn player rows for ELO computation */
export const getEloData = query({
  args: {},
  handler: async (ctx) => {
    const games = await ctx.db
      .query("games")
      .withIndex("by_status", (q) => q.eq("status", "completed"))
      .collect()

    const results = []
    for (const game of games) {
      if (!game.outcome?.winnerCiv) continue

      // Get player rows for the last recorded turn
      const lastTurnRows = await ctx.db
        .query("playerRows")
        .withIndex("by_game_turn", (q) =>
          q.eq("gameId", game.gameId).eq("turn", game.lastTurn)
        )
        .collect()

      if (lastTurnRows.length < 2) continue

      results.push({
        gameId: game.gameId,
        winnerCiv: game.outcome.winnerCiv,
        players: lastTurnRows.map((r) => ({
          pid: r.pid,
          civ: r.civ,
          leader: r.leader,
          is_agent: r.is_agent,
          agent_model: r.agent_model ?? null,
        })),
      })
    }

    return results
  },
})
