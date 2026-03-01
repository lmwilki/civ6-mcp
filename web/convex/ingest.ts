import { mutation } from "./_generated/server";
import { v } from "convex/values";

// Metrics to precompute for sparkline charts
const SERIES_METRICS = [
  "score", "science", "culture", "gold", "military",
  "faith", "territory", "exploration_pct", "pop", "cities", "tourism",
] as const;

type SeriesPlayer = {
  civ: string;
  leader: string;
  is_agent: boolean;
  metrics: Record<string, number[]>;
};

/** Merge new turn data into existing turnSeries on a games doc. */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function mergeTurnSeries(existing: any | undefined, rows: any[]): { turns: number[]; players: Record<string, SeriesPlayer> } {
  const prev = existing ?? { turns: [], players: {} };
  const turns: number[] = [...prev.turns];
  const players: Record<string, SeriesPlayer> = {};

  // Copy existing player data
  for (const [pid, p] of Object.entries(prev.players as Record<string, SeriesPlayer>)) {
    players[pid] = {
      civ: p.civ,
      leader: p.leader,
      is_agent: p.is_agent,
      metrics: {} as Record<string, number[]>,
    };
    for (const m of SERIES_METRICS) {
      players[pid].metrics[m] = [...(p.metrics[m] ?? [])];
    }
  }

  // Group incoming rows by turn
  const byTurn = new Map<number, typeof rows>();
  for (const r of rows) {
    if (!byTurn.has(r.turn)) byTurn.set(r.turn, []);
    byTurn.get(r.turn)!.push(r);
  }

  for (const [turn, turnRows] of byTurn) {
    let idx = turns.indexOf(turn);
    if (idx === -1) {
      // Insert in sorted position
      idx = turns.findIndex((t) => t > turn);
      if (idx === -1) idx = turns.length;
      turns.splice(idx, 0, turn);
      // Insert placeholder at idx for all existing players
      for (const p of Object.values(players)) {
        for (const m of SERIES_METRICS) {
          p.metrics[m].splice(idx, 0, 0);
        }
      }
    }

    for (const r of turnRows) {
      const pid = String(r.pid);
      if (!players[pid]) {
        players[pid] = {
          civ: r.civ,
          leader: r.leader,
          is_agent: r.is_agent,
          metrics: {} as Record<string, number[]>,
        };
        // Backfill zeros for existing turns
        for (const m of SERIES_METRICS) {
          players[pid].metrics[m] = new Array(turns.length).fill(0);
        }
      }
      for (const m of SERIES_METRICS) {
        players[pid].metrics[m][idx] = typeof r[m] === "number" ? r[m] : 0;
      }
    }
  }

  return { turns, players };
}

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

      // Strip techs/civics arrays — only the _completed counts are displayed
      delete row.techs;
      delete row.civics;

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

    // Denormalize agent model/score and ELO player snapshot
    const agentRow = rows.find(
      (r: { is_agent: boolean }) => r.is_agent,
    );
    const latestRows = rows.filter(
      (r: { turn: number }) => r.turn === maxTurn,
    );

    if (game) {
      const patch: Record<string, unknown> = {
        lastTurn: Math.max(game.lastTurn, maxTurn),
        lastUpdated: Date.now(),
        turnCount: Math.max(game.turnCount, maxTurn),
        // Don't resurrect completed games — lookback re-syncs can re-send old rows
        ...(game.status !== "completed" ? { status: "live" as const } : {}),
      };
      // Backfill leader/civ if game was created by log ingestion with empty values
      if (!game.leader && leader) patch.leader = leader;
      if (!game.civ && civ) patch.civ = civ;
      // Denormalized fields
      if (agentRow) {
        if (agentRow.agent_model) patch.agentModel = agentRow.agent_model;
        if (typeof agentRow.score === "number") patch.agentScore = agentRow.score;
      }
      if (latestRows.length >= 2) {
        patch.eloPlayers = latestRows.map(
          (r: { pid: number; civ: string; leader: string; is_agent: boolean; agent_model?: string }) => ({
            pid: r.pid,
            civ: r.civ,
            leader: r.leader,
            is_agent: r.is_agent,
            agent_model: r.agent_model ?? null,
          }),
        );
      }
      // Update sparkline series
      patch.turnSeries = mergeTurnSeries(game.turnSeries, rows);
      await ctx.db.patch(game._id, patch);
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
        ...(agentRow?.agent_model ? { agentModel: agentRow.agent_model } : {}),
        ...(typeof agentRow?.score === "number" ? { agentScore: agentRow.score } : {}),
        ...(latestRows.length >= 2
          ? {
              eloPlayers: latestRows.map(
                (r: { pid: number; civ: string; leader: string; is_agent: boolean; agent_model?: string }) => ({
                  pid: r.pid,
                  civ: r.civ,
                  leader: r.leader,
                  is_agent: r.is_agent,
                  agent_model: r.agent_model ?? null,
                }),
              ),
            }
          : {}),
        turnSeries: mergeTurnSeries(undefined, rows),
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

    // Compute logSummary from this batch
    const batchTurns = entries
      .map((e: { turn: number | null }) => e.turn)
      .filter((t: number | null): t is number => t != null);
    const batchTs = entries.map((e: { ts: number }) => e.ts);
    const batchSessions = [...new Set(entries.map((e: { session: string }) => e.session))];
    const batchMaxLine = Math.max(...entries.map((e: { line: number }) => e.line));

    if (game) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const patch: Record<string, any> = {
        hasLogs: true,
        lastUpdated: Date.now(),
      };

      // Merge logSummary with existing
      const prev = game.logSummary;
      const allSessions = prev
        ? [...new Set([...prev.sessions, ...batchSessions])]
        : batchSessions;
      patch.logSummary = {
        count: prev ? Math.max(prev.count, batchMaxLine) : batchMaxLine,
        firstTs: prev ? Math.min(prev.firstTs, ...batchTs) : Math.min(...batchTs),
        lastTs: Math.max(prev?.lastTs ?? 0, ...batchTs),
        minTurn:
          batchTurns.length > 0
            ? prev?.minTurn != null
              ? Math.min(prev.minTurn, ...batchTurns)
              : Math.min(...batchTurns)
            : prev?.minTurn ?? null,
        maxTurn:
          batchTurns.length > 0
            ? prev?.maxTurn != null
              ? Math.max(prev.maxTurn, ...batchTurns)
              : Math.max(...batchTurns)
            : prev?.maxTurn ?? null,
        sessions: allSessions,
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
        logSummary: {
          count: batchMaxLine,
          firstTs: Math.min(...batchTs),
          lastTs: Math.max(...batchTs),
          minTurn: batchTurns.length > 0 ? Math.min(...batchTurns) : null,
          maxTurn: batchTurns.length > 0 ? Math.max(...batchTurns) : null,
          sessions: batchSessions,
        },
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

export const setModelOverride = mutation({
  args: { gameId: v.string(), model: v.optional(v.string()) },
  handler: async (ctx, { gameId, model }) => {
    const game = await ctx.db
      .query("games")
      .withIndex("by_gameId", (q) => q.eq("gameId", gameId))
      .unique();
    if (!game) throw new Error(`Game not found: ${gameId}`);
    await ctx.db.patch(game._id, { agentModelOverride: model });
    return { gameId, agentModelOverride: model ?? null };
  },
});

/** Delete up to `limit` rows from a single table for a game.
 *  Returns how many were deleted — call repeatedly until 0. */
export const deleteGameBatch = mutation({
  args: {
    gameId: v.string(),
    table: v.union(
      v.literal("playerRows"),
      v.literal("cityRows"),
      v.literal("logEntries"),
      v.literal("spatialTurns"),
      v.literal("spatialMaps"),
      v.literal("mapData"),
      v.literal("games"),
    ),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, { gameId, table, limit }) => {
    const batchSize = limit ?? 500;

    if (table === "games") {
      const game = await ctx.db
        .query("games")
        .withIndex("by_gameId", (q) => q.eq("gameId", gameId))
        .unique();
      if (game) {
        await ctx.db.delete(game._id);
        return { deleted: 1 };
      }
      return { deleted: 0 };
    }

    // Each table has its own index — query explicitly to satisfy TS
    let deleted = 0;
    if (table === "playerRows") {
      const rows = await ctx.db.query("playerRows")
        .withIndex("by_game_turn", (q) => q.eq("gameId", gameId)).take(batchSize);
      for (const r of rows) await ctx.db.delete(r._id);
      deleted = rows.length;
    } else if (table === "cityRows") {
      const rows = await ctx.db.query("cityRows")
        .withIndex("by_game_turn", (q) => q.eq("gameId", gameId)).take(batchSize);
      for (const r of rows) await ctx.db.delete(r._id);
      deleted = rows.length;
    } else if (table === "logEntries") {
      const rows = await ctx.db.query("logEntries")
        .withIndex("by_game_line", (q) => q.eq("gameId", gameId)).take(batchSize);
      for (const r of rows) await ctx.db.delete(r._id);
      deleted = rows.length;
    } else if (table === "spatialTurns") {
      const rows = await ctx.db.query("spatialTurns")
        .withIndex("by_game_turn", (q) => q.eq("gameId", gameId)).take(batchSize);
      for (const r of rows) await ctx.db.delete(r._id);
      deleted = rows.length;
    } else if (table === "spatialMaps") {
      const rows = await ctx.db.query("spatialMaps")
        .withIndex("by_gameId", (q) => q.eq("gameId", gameId)).take(batchSize);
      for (const r of rows) await ctx.db.delete(r._id);
      deleted = rows.length;
    } else if (table === "mapData") {
      const rows = await ctx.db.query("mapData")
        .withIndex("by_gameId", (q) => q.eq("gameId", gameId)).take(batchSize);
      for (const r of rows) await ctx.db.delete(r._id);
      deleted = rows.length;
    }
    return { deleted };
  },
});

export const backfillDenormalized = mutation({
  args: {},
  handler: async (ctx) => {
    const games = await ctx.db.query("games").collect();
    let patched = 0;
    for (const game of games) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const patch: Record<string, any> = {};

      // Backfill agentModel, agentScore, eloPlayers from playerRows
      const playerRows = await ctx.db
        .query("playerRows")
        .withIndex("by_game_turn", (q) =>
          q.eq("gameId", game.gameId).eq("turn", game.lastTurn),
        )
        .collect();
      if (playerRows.length >= 2) {
        patch.eloPlayers = playerRows.map((r) => ({
          pid: r.pid,
          civ: r.civ,
          leader: r.leader,
          is_agent: r.is_agent,
          agent_model: r.agent_model ?? null,
        }));
      }
      const agentRow = playerRows.find((r) => r.is_agent);
      if (agentRow) {
        if (agentRow.agent_model) patch.agentModel = agentRow.agent_model;
        if (typeof agentRow.score === "number") patch.agentScore = agentRow.score;
      }

      // Backfill logSummary from logEntries
      if (game.hasLogs) {
        const first = await ctx.db
          .query("logEntries")
          .withIndex("by_game_line", (q) => q.eq("gameId", game.gameId))
          .first();
        const last = await ctx.db
          .query("logEntries")
          .withIndex("by_game_line", (q) => q.eq("gameId", game.gameId))
          .order("desc")
          .first();
        // Collect unique sessions from a sample
        const sample = await ctx.db
          .query("logEntries")
          .withIndex("by_game_line", (q) => q.eq("gameId", game.gameId))
          .take(200);
        const sessions = [...new Set(sample.map((e) => e.session))];
        const turns = sample
          .map((e) => e.turn)
          .filter((t): t is number => t != null);
        if (first && last) {
          patch.logSummary = {
            count: last.line,
            firstTs: first.ts,
            lastTs: last.ts,
            minTurn: turns.length > 0 ? Math.min(...turns) : null,
            maxTurn: turns.length > 0 ? Math.max(...turns) : null,
            sessions,
          };
        }
      }

      if (Object.keys(patch).length > 0) {
        await ctx.db.patch(game._id, patch);
        patched++;
      }
    }
    return { patched, total: games.length };
  },
});

/** Backfill one game: strip techs/civics from playerRows + compute turnSeries.
 *  Run per-game to stay within Convex mutation time limits. */
export const backfillStripAndSeries = mutation({
  args: { gameId: v.string() },
  handler: async (ctx, { gameId }) => {
    const game = await ctx.db
      .query("games")
      .withIndex("by_gameId", (q) => q.eq("gameId", gameId))
      .first();
    if (!game) return { error: "game not found" };

    // Read all playerRows for this game
    const allRows = await ctx.db
      .query("playerRows")
      .withIndex("by_game_turn", (q) => q.eq("gameId", gameId))
      .collect();

    // Strip techs/civics from each row
    let stripped = 0;
    for (const row of allRows) {
      if (row.techs || row.civics) {
        await ctx.db.patch(row._id, { techs: undefined, civics: undefined });
        stripped++;
      }
    }

    // Build turnSeries from all rows
    const turnSeries = mergeTurnSeries(undefined, allRows);
    await ctx.db.patch(game._id, { turnSeries });

    return { gameId, stripped, totalRows: allRows.length, seriesTurns: turnSeries.turns.length };
  },
});

/** List all gameIds for batch backfill. */
export const listGameIds = mutation({
  args: {},
  handler: async (ctx) => {
    const games = await ctx.db.query("games").collect();
    return games.map((g) => g.gameId);
  },
});

// Spatial metrics to merge into turnSeries (agent player only)
const SPATIAL_METRICS = ["spatial_tiles", "spatial_actions", "spatial_cumulative"] as const;

export const ingestSpatialTurns = mutation({
  args: {
    gameId: v.string(),
    rows: v.array(v.any()),
  },
  handler: async (ctx, { gameId, rows }) => {
    // 1. Upsert spatialTurns rows
    for (const row of rows) {
      const existing = await ctx.db
        .query("spatialTurns")
        .withIndex("by_game_turn", (q) =>
          q.eq("gameId", gameId).eq("turn", row.turn),
        )
        .unique();
      if (existing) {
        await ctx.db.replace(existing._id, { gameId, ...row });
      } else {
        await ctx.db.insert("spatialTurns", { gameId, ...row });
      }
    }

    // 2. Merge spatial sparkline metrics into games.turnSeries
    const game = await ctx.db
      .query("games")
      .withIndex("by_gameId", (q) => q.eq("gameId", gameId))
      .first();
    if (!game) return;

    const patch: Record<string, unknown> = { hasSpatial: true, lastUpdated: Date.now() };

    if (game.turnSeries) {
      const ts = {
        turns: [...game.turnSeries.turns],
        players: {} as Record<string, SeriesPlayer>,
      };
      // Deep-copy existing players
      for (const [pid, p] of Object.entries(
        game.turnSeries.players as Record<string, SeriesPlayer>,
      )) {
        ts.players[pid] = {
          civ: p.civ,
          leader: p.leader,
          is_agent: p.is_agent,
          metrics: {} as Record<string, number[]>,
        };
        // Copy all existing metrics (diary + any prior spatial)
        for (const [m, arr] of Object.entries(p.metrics)) {
          ts.players[pid].metrics[m] = [...(arr ?? [])];
        }
        // Ensure spatial metric arrays exist with correct length
        if (p.is_agent) {
          for (const m of SPATIAL_METRICS) {
            if (!ts.players[pid].metrics[m]) {
              ts.players[pid].metrics[m] = new Array(ts.turns.length).fill(0);
            }
          }
        }
      }

      // For each incoming row, find the turn index and set spatial values
      for (const row of rows) {
        const idx = ts.turns.indexOf(row.turn);
        if (idx === -1) continue; // Turn not in diary series yet — skip
        for (const [, p] of Object.entries(ts.players)) {
          if (!p.is_agent) continue;
          p.metrics["spatial_tiles"][idx] = row.tiles_observed ?? 0;
          p.metrics["spatial_actions"][idx] = row.tool_calls ?? 0;
          p.metrics["spatial_cumulative"][idx] = row.cumulative_tiles ?? 0;
        }
      }
      patch.turnSeries = ts;
    }

    await ctx.db.patch(game._id, patch);
  },
});

export const ingestSpatialMap = mutation({
  args: {
    gameId: v.string(),
    minX: v.number(),
    maxX: v.number(),
    minY: v.number(),
    maxY: v.number(),
    tileCount: v.number(),
    tiles: v.array(v.number()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("spatialMaps")
      .withIndex("by_gameId", (q) => q.eq("gameId", args.gameId))
      .unique();
    if (existing) {
      await ctx.db.replace(existing._id, args);
    } else {
      await ctx.db.insert("spatialMaps", args);
    }
  },
});

export const ingestMapData = mutation({
  args: {
    gameId: v.string(),
    gridW: v.number(),
    gridH: v.number(),
    // JSON-encoded number[] strings — Convex caps arrays at 8192 elements
    terrain: v.string(),
    initialOwners: v.string(),
    initialRoutes: v.optional(v.string()),
    initialTurn: v.number(),
    ownerFrames: v.string(),
    cityFrames: v.string(),
    roadFrames: v.string(),
    cityNames: v.optional(v.string()),
    players: v.array(v.object({ pid: v.number(), civ: v.string(), csType: v.optional(v.string()) })),
    maxTurn: v.number(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("mapData")
      .withIndex("by_gameId", (q) => q.eq("gameId", args.gameId))
      .first();
    if (existing) {
      await ctx.db.replace(existing._id, args);
    } else {
      await ctx.db.insert("mapData", args);
    }

    // Mark game as having map data
    const game = await ctx.db
      .query("games")
      .withIndex("by_gameId", (q) => q.eq("gameId", args.gameId))
      .unique();
    if (game && !game.hasMap) {
      await ctx.db.patch(game._id, { hasMap: true, lastUpdated: Date.now() });
    }
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
