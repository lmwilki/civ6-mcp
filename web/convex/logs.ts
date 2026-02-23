import { query } from "./_generated/server"
import { v } from "convex/values"

/** List games that have log data — returns shape compatible with GameLogInfo[] */
export const listGameLogs = query({
  args: {},
  handler: async (ctx) => {
    const games = await ctx.db
      .query("games")
      .withIndex("by_status")
      .order("desc")
      .collect()
    const result = []
    for (const g of games) {
      if (!g.hasLogs) continue
      // Get first and last log entry for timestamps
      const first = await ctx.db
        .query("logEntries")
        .withIndex("by_game_line", (q) => q.eq("gameId", g.gameId))
        .first()
      const last = await ctx.db
        .query("logEntries")
        .withIndex("by_game_line", (q) => q.eq("gameId", g.gameId))
        .order("desc")
        .first()
      // Collect unique sessions (scan first 50 entries)
      const sample = await ctx.db
        .query("logEntries")
        .withIndex("by_game_line", (q) => q.eq("gameId", g.gameId))
        .take(50)
      const sessions = [...new Set(sample.map((e) => e.session))]
      const turns = sample
        .map((e) => e.turn)
        .filter((t): t is number => t != null)
      result.push({
        game: g.gameId,
        civ: g.civ,
        seed: g.seed,
        count: last ? last.line : 0,
        first_ts: first?.ts ?? 0,
        last_ts: last?.ts ?? 0,
        min_turn: turns.length > 0 ? Math.min(...turns) : null,
        max_turn: turns.length > 0 ? Math.max(...turns) : null,
        sessions,
      })
    }
    return result
  },
})

/** Get log entries for a game, optionally filtered by session and after a line */
export const getLogEntries = query({
  args: {
    gameId: v.string(),
    afterLine: v.optional(v.number()),
    session: v.optional(v.string()),
  },
  handler: async (ctx, { gameId, afterLine, session }) => {
    let entries
    if (session) {
      entries = await ctx.db
        .query("logEntries")
        .withIndex("by_game_session", (q) =>
          q.eq("gameId", gameId).eq("session", session)
        )
        .collect()
      if (afterLine) {
        entries = entries.filter((e) => e.line > afterLine)
      }
    } else {
      // Use line index for efficient range query
      const q = ctx.db
        .query("logEntries")
        .withIndex("by_game_line", (q) => q.eq("gameId", gameId))
      entries = await q.collect()
      if (afterLine) {
        entries = entries.filter((e) => e.line > afterLine)
      }
    }
    return entries
  },
})
