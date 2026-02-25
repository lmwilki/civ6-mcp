import { query } from "./_generated/server";
import { v } from "convex/values";

/** List games that have log data — returns shape compatible with GameLogInfo[] */
export const listGameLogs = query({
  args: {},
  handler: async (ctx) => {
    const games = await ctx.db
      .query("games")
      .withIndex("by_status")
      .order("desc")
      .collect();

    return games
      .filter((g) => g.hasLogs && g.logSummary)
      .map((g) => {
        const s = g.logSummary!;
        return {
          game: g.gameId,
          civ: g.civ,
          seed: g.seed,
          count: s.count,
          first_ts: s.firstTs,
          last_ts: s.lastTs,
          min_turn: s.minTurn,
          max_turn: s.maxTurn,
          sessions: s.sessions,
        };
      });
  },
});

/** Get log entries for a game, optionally filtered by session and after a line */
export const getLogEntries = query({
  args: {
    gameId: v.string(),
    afterLine: v.optional(v.number()),
    session: v.optional(v.string()),
  },
  handler: async (ctx, { gameId, afterLine, session }) => {
    let entries;
    if (session) {
      entries = await ctx.db
        .query("logEntries")
        .withIndex("by_game_session", (q) =>
          q.eq("gameId", gameId).eq("session", session),
        )
        .collect();
      if (afterLine) {
        entries = entries.filter((e) => e.line > afterLine);
      }
    } else {
      // Use line index for efficient range query
      const q = ctx.db
        .query("logEntries")
        .withIndex("by_game_line", (q) => q.eq("gameId", gameId));
      entries = await q.collect();
      if (afterLine) {
        entries = entries.filter((e) => e.line > afterLine);
      }
    }
    return entries;
  },
});
