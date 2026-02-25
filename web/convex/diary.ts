import { query } from "./_generated/server";
import { v } from "convex/values";

/** List all games — returns shape compatible with DiaryFile[] */
export const listGames = query({
  args: {},
  handler: async (ctx) => {
    const games = await ctx.db
      .query("games")
      .withIndex("by_status")
      .order("desc")
      .collect();

    // Batch-fetch agent_model for each game from its latest agent playerRow
    const results = await Promise.all(
      games.map(async (g) => {
        let agentModel: string | null = null;
        let score: number | null = null;
        const agentRow = await ctx.db
          .query("playerRows")
          .withIndex("by_game_turn", (q) =>
            q.eq("gameId", g.gameId).eq("turn", g.lastTurn),
          )
          .filter((q) => q.eq(q.field("is_agent"), true))
          .first();
        if (agentRow) {
          agentModel = agentRow.agent_model ?? null;
          score = agentRow.score;
        }
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
          agentModel,
          score,
        };
      }),
    );
    return results;
  },
});

/** Get the most recently updated live game (if any) */
export const getLiveGame = query({
  args: {},
  handler: async (ctx) => {
    const live = await ctx.db
      .query("games")
      .withIndex("by_status", (q) => q.eq("status", "live"))
      .order("desc")
      .first();
    if (!live) return null;
    return {
      gameId: live.gameId,
      civ: live.civ,
      leader: live.leader,
      lastTurn: live.lastTurn,
    };
  },
});

/** Get ELO data — completed games with winner + player info */
export const getEloData = query({
  args: {},
  handler: async (ctx) => {
    const games = await ctx.db
      .query("games")
      .withIndex("by_status", (q) => q.eq("status", "completed"))
      .collect();

    const results = [];
    for (const game of games) {
      if (!game.outcome?.winnerCiv) continue;

      const playerRows = await ctx.db
        .query("playerRows")
        .withIndex("by_game_turn", (q) =>
          q.eq("gameId", game.gameId).eq("turn", game.lastTurn),
        )
        .order("asc")
        .collect();

      if (playerRows.length < 2) continue;

      results.push({
        gameId: game.gameId,
        winnerCiv: game.outcome.winnerCiv,
        players: playerRows.map((p) => ({
          pid: p.pid,
          civ: p.civ,
          leader: p.leader,
          is_agent: p.is_agent,
          agent_model: p.agent_model ?? null,
        })),
      });
    }
    return results;
  },
});

/** Get all player + city rows for a game, plus game metadata */
export const getGameTurns = query({
  args: { gameId: v.string() },
  handler: async (ctx, { gameId }) => {
    const [game, playerRows, cityRows] = await Promise.all([
      ctx.db
        .query("games")
        .withIndex("by_gameId", (q) => q.eq("gameId", gameId))
        .first(),
      ctx.db
        .query("playerRows")
        .withIndex("by_game_turn", (q) => q.eq("gameId", gameId))
        .collect(),
      ctx.db
        .query("cityRows")
        .withIndex("by_game_turn", (q) => q.eq("gameId", gameId))
        .collect(),
    ]);
    return {
      playerRows,
      cityRows,
      status: game?.status ?? null,
      outcome: game?.outcome ?? null,
    };
  },
});
