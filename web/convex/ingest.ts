import { mutation } from "./_generated/server"
import { v } from "convex/values"

export const ingestPlayerRows = mutation({
  args: {
    gameId: v.string(),
    civ: v.string(),
    leader: v.string(),
    seed: v.string(),
    rows: v.array(v.any()),
  },
  handler: async (ctx, { gameId, civ, leader, seed, rows }) => {
    for (const row of rows) {
      // Upsert by (gameId, turn, pid) — handles reflection merges
      const existing = await ctx.db
        .query("playerRows")
        .withIndex("by_game_turn_pid", (q) =>
          q.eq("gameId", gameId).eq("turn", row.turn).eq("pid", row.pid)
        )
        .unique()
      if (existing) {
        await ctx.db.replace(existing._id, { gameId, ...row })
      } else {
        await ctx.db.insert("playerRows", { gameId, ...row })
      }
    }

    // Upsert games entry
    const turns = rows.map((r: { turn: number }) => r.turn)
    const maxTurn = Math.max(...turns)
    const game = await ctx.db
      .query("games")
      .withIndex("by_gameId", (q) => q.eq("gameId", gameId))
      .unique()

    if (game) {
      await ctx.db.patch(game._id, {
        lastTurn: Math.max(game.lastTurn, maxTurn),
        lastUpdated: Date.now(),
        turnCount: Math.max(game.turnCount, maxTurn),
        status: "live" as const,
      })
    } else {
      await ctx.db.insert("games", {
        gameId,
        civ,
        leader,
        seed,
        status: "live",
        lastTurn: maxTurn,
        lastUpdated: Date.now(),
        turnCount: maxTurn,
        hasCities: false,
        hasLogs: false,
      })
    }
  },
})

export const ingestCityRows = mutation({
  args: {
    gameId: v.string(),
    rows: v.array(v.any()),
  },
  handler: async (ctx, { gameId, rows }) => {
    for (const row of rows) {
      // Upsert by (gameId, turn, city_id)
      const existing = await ctx.db
        .query("cityRows")
        .withIndex("by_game_turn", (q) =>
          q.eq("gameId", gameId).eq("turn", row.turn)
        )
        .filter((q) => q.eq(q.field("city_id"), row.city_id))
        .unique()
      if (existing) {
        await ctx.db.replace(existing._id, { gameId, ...row })
      } else {
        await ctx.db.insert("cityRows", { gameId, ...row })
      }
    }

    // Mark game as having cities
    const game = await ctx.db
      .query("games")
      .withIndex("by_gameId", (q) => q.eq("gameId", gameId))
      .unique()
    if (game && !game.hasCities) {
      await ctx.db.patch(game._id, { hasCities: true, lastUpdated: Date.now() })
    }
  },
})

export const ingestLogEntries = mutation({
  args: {
    gameId: v.string(),
    civ: v.string(),
    seed: v.string(),
    entries: v.array(v.any()),
  },
  handler: async (ctx, { gameId, civ, seed, entries }) => {
    for (const entry of entries) {
      // Dedup by (gameId, line)
      const existing = await ctx.db
        .query("logEntries")
        .withIndex("by_game_line", (q) =>
          q.eq("gameId", gameId).eq("line", entry.line)
        )
        .unique()
      if (!existing) {
        await ctx.db.insert("logEntries", { gameId, ...entry })
      }
    }

    // Upsert games entry
    const game = await ctx.db
      .query("games")
      .withIndex("by_gameId", (q) => q.eq("gameId", gameId))
      .unique()
    if (game) {
      await ctx.db.patch(game._id, { hasLogs: true, lastUpdated: Date.now() })
    } else {
      await ctx.db.insert("games", {
        gameId,
        civ,
        leader: "",
        seed,
        status: "live",
        lastTurn: 0,
        lastUpdated: Date.now(),
        turnCount: 0,
        hasCities: false,
        hasLogs: true,
      })
    }
  },
})

export const markGameCompleted = mutation({
  args: { gameId: v.string() },
  handler: async (ctx, { gameId }) => {
    const game = await ctx.db
      .query("games")
      .withIndex("by_gameId", (q) => q.eq("gameId", gameId))
      .unique()
    if (game) {
      await ctx.db.patch(game._id, { status: "completed" })
    }
  },
})
