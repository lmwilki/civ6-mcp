import { mutation } from "./_generated/server";
import { v } from "convex/values";

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
      // Backfill fields added after early game data was recorded
      if (row.exploration_pct === undefined) row.exploration_pct = 0;

      // Upsert by (gameId, turn, pid) — handles reflection merges
      const existing = await ctx.db
        .query("playerRows")
        .withIndex("by_game_turn_pid", (q) =>
          q.eq("gameId", gameId).eq("turn", row.turn).eq("pid", row.pid),
        )
        .unique();
      if (existing) {
        await ctx.db.replace(existing._id, { gameId, ...row });
      } else {
        await ctx.db.insert("playerRows", { gameId, ...row });
      }
    }

    // Upsert games entry
    const turns = rows.map((r: { turn: number }) => r.turn);
    const maxTurn = Math.max(...turns);
    const game = await ctx.db
      .query("games")
      .withIndex("by_gameId", (q) => q.eq("gameId", gameId))
      .unique();

    if (game) {
      await ctx.db.patch(game._id, {
        lastTurn: Math.max(game.lastTurn, maxTurn),
        lastUpdated: Date.now(),
        turnCount: Math.max(game.turnCount, maxTurn),
        status: "live" as const,
      });
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
      });
    }
  },
});

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
          q.eq("gameId", gameId).eq("turn", row.turn),
        )
        .filter((q) => q.eq(q.field("city_id"), row.city_id))
        .unique();
      if (existing) {
        await ctx.db.replace(existing._id, { gameId, ...row });
      } else {
        await ctx.db.insert("cityRows", { gameId, ...row });
      }
    }

    // Mark game as having cities
    const game = await ctx.db
      .query("games")
      .withIndex("by_gameId", (q) => q.eq("gameId", gameId))
      .unique();
    if (game && !game.hasCities) {
      await ctx.db.patch(game._id, {
        hasCities: true,
        lastUpdated: Date.now(),
      });
    }
  },
});

export const ingestLogEntries = mutation({
  args: {
    gameId: v.string(),
    civ: v.string(),
    seed: v.string(),
    entries: v.array(v.any()),
  },
  handler: async (ctx, { gameId, civ, seed, entries }) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let gameOverOutcome: any = null;

    for (const entry of entries) {
      // Detect game_over entries before stripping for logEntries insert
      if (entry.type === "game_over" && entry.outcome) {
        gameOverOutcome = entry;
      }

      // Strip outcome field — logEntries schema doesn't include it
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { outcome: _outcome, ...logEntry } = entry;

      // Dedup by (gameId, line)
      const existing = await ctx.db
        .query("logEntries")
        .withIndex("by_game_line", (q) =>
          q.eq("gameId", gameId).eq("line", logEntry.line),
        )
        .unique();
      if (!existing) {
        await ctx.db.insert("logEntries", { gameId, ...logEntry });
      }
    }

    // Upsert games entry
    const game = await ctx.db
      .query("games")
      .withIndex("by_gameId", (q) => q.eq("gameId", gameId))
      .unique();

    if (game) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const patch: Record<string, any> = {
        hasLogs: true,
        lastUpdated: Date.now(),
      };
      if (gameOverOutcome) {
        const o = gameOverOutcome.outcome;
        patch.status = "completed";
        const outcomeTurn = gameOverOutcome.turn ?? 0;
        patch.outcome = {
          result: o.is_defeat ? ("defeat" as const) : ("victory" as const),
          winnerCiv: o.winner_civ ?? "Unknown",
          winnerLeader: o.winner_leader ?? "Unknown",
          victoryType: o.victory_type ?? "Unknown",
          turn: outcomeTurn,
          playerAlive: o.player_alive ?? true,
        };
        if (outcomeTurn > 0) {
          patch.lastTurn = Math.max(game.lastTurn, outcomeTurn);
          patch.turnCount = Math.max(game.turnCount, outcomeTurn);
        }
      }
      await ctx.db.patch(game._id, patch);
    } else {
      const outcomeTurn = gameOverOutcome?.turn ?? 0;
      await ctx.db.insert("games", {
        gameId,
        civ,
        leader: "",
        seed,
        status: gameOverOutcome ? "completed" : "live",
        lastTurn: outcomeTurn,
        lastUpdated: Date.now(),
        turnCount: outcomeTurn,
        hasCities: false,
        hasLogs: true,
        ...(gameOverOutcome
          ? {
              outcome: {
                result: gameOverOutcome.outcome.is_defeat
                  ? ("defeat" as const)
                  : ("victory" as const),
                winnerCiv: gameOverOutcome.outcome.winner_civ ?? "Unknown",
                winnerLeader:
                  gameOverOutcome.outcome.winner_leader ?? "Unknown",
                victoryType: gameOverOutcome.outcome.victory_type ?? "Unknown",
                turn: outcomeTurn,
                playerAlive: gameOverOutcome.outcome.player_alive ?? true,
              },
            }
          : {}),
      });
    }
  },
});

export const markGameCompleted = mutation({
  args: { gameId: v.string() },
  handler: async (ctx, { gameId }) => {
    const game = await ctx.db
      .query("games")
      .withIndex("by_gameId", (q) => q.eq("gameId", gameId))
      .unique();
    if (game) {
      await ctx.db.patch(game._id, { status: "completed" });
    }
  },
});

export const patchGameOutcome = mutation({
  args: {
    gameId: v.string(),
    outcome: v.object({
      result: v.union(v.literal("victory"), v.literal("defeat")),
      winnerCiv: v.string(),
      winnerLeader: v.string(),
      victoryType: v.string(),
      turn: v.number(),
      playerAlive: v.boolean(),
    }),
  },
  handler: async (ctx, { gameId, outcome }) => {
    const game = await ctx.db
      .query("games")
      .withIndex("by_gameId", (q) => q.eq("gameId", gameId))
      .unique();
    if (game) {
      await ctx.db.patch(game._id, { status: "completed", outcome });
    }
  },
});

export const deleteGame = mutation({
  args: { gameId: v.string() },
  handler: async (ctx, { gameId }) => {
    const game = await ctx.db
      .query("games")
      .withIndex("by_gameId", (q) => q.eq("gameId", gameId))
      .unique();
    if (game) await ctx.db.delete(game._id);

    const playerRows = await ctx.db
      .query("playerRows")
      .withIndex("by_game_turn", (q) => q.eq("gameId", gameId))
      .collect();
    for (const row of playerRows) await ctx.db.delete(row._id);

    const cityRows = await ctx.db
      .query("cityRows")
      .withIndex("by_game_turn", (q) => q.eq("gameId", gameId))
      .collect();
    for (const row of cityRows) await ctx.db.delete(row._id);

    const logEntries = await ctx.db
      .query("logEntries")
      .withIndex("by_game_line", (q) => q.eq("gameId", gameId))
      .collect();
    for (const row of logEntries) await ctx.db.delete(row._id);

    return {
      deleted: {
        game: game ? 1 : 0,
        playerRows: playerRows.length,
        cityRows: cityRows.length,
        logEntries: logEntries.length,
      },
    };
  },
});

export const backfillAgentModel = mutation({
  args: { model: v.string() },
  handler: async (ctx, { model }) => {
    const rows = await ctx.db
      .query("playerRows")
      .filter((q) => q.eq(q.field("is_agent"), true))
      .collect();
    let patched = 0;
    for (const row of rows) {
      if (!row.agent_model) {
        await ctx.db.patch(row._id, { agent_model: model });
        patched++;
      }
    }
    return { patched, total: rows.length };
  },
});
