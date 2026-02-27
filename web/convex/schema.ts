import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  // One doc per game session — used for listing and lifecycle
  games: defineTable({
    gameId: v.string(),
    civ: v.string(),
    leader: v.string(),
    seed: v.string(),
    status: v.union(v.literal("live"), v.literal("completed")),
    lastTurn: v.number(),
    lastUpdated: v.number(),
    turnCount: v.number(),
    hasCities: v.boolean(),
    hasLogs: v.boolean(),
    hasSpatial: v.optional(v.boolean()),
    agentModelOverride: v.optional(v.string()),
    // Denormalized from playerRows (set at ingest time)
    agentModel: v.optional(v.string()),
    agentScore: v.optional(v.number()),
    eloPlayers: v.optional(
      v.array(
        v.object({
          pid: v.number(),
          civ: v.string(),
          leader: v.string(),
          is_agent: v.boolean(),
          agent_model: v.union(v.string(), v.null()),
        }),
      ),
    ),
    // Precomputed sparkline time-series (set at ingest time)
    turnSeries: v.optional(
      v.object({
        turns: v.array(v.number()),
        players: v.any(), // { [pid]: { civ, leader, is_agent, metrics: { score: number[], ... } } }
      }),
    ),
    // Denormalized from logEntries (set at ingest time)
    logSummary: v.optional(
      v.object({
        count: v.number(),
        firstTs: v.number(),
        lastTs: v.number(),
        minTurn: v.union(v.number(), v.null()),
        maxTurn: v.union(v.number(), v.null()),
        sessions: v.array(v.string()),
      }),
    ),
    outcome: v.optional(
      v.object({
        result: v.union(v.literal("victory"), v.literal("defeat")),
        winnerCiv: v.string(),
        winnerLeader: v.string(),
        victoryType: v.string(),
        turn: v.number(),
        playerAlive: v.boolean(),
      }),
    ),
  })
    .index("by_gameId", ["gameId"])
    .index("by_status", ["status", "lastUpdated"]),

  // One doc per player per turn — mirrors PlayerRow from diary JSONL
  playerRows: defineTable({
    gameId: v.string(),
    // Identity
    turn: v.number(),
    pid: v.number(),
    civ: v.string(),
    leader: v.string(),
    is_agent: v.boolean(),
    timestamp: v.string(),
    game: v.string(),
    v: v.number(),
    // Score & yields
    score: v.number(),
    cities: v.number(),
    pop: v.number(),
    science: v.number(),
    culture: v.number(),
    gold: v.number(),
    gold_per_turn: v.number(),
    faith: v.number(),
    faith_per_turn: v.number(),
    favor: v.number(),
    favor_per_turn: v.number(),
    // Military
    military: v.number(),
    units_total: v.number(),
    units_military: v.number(),
    units_civilian: v.number(),
    units_support: v.number(),
    unit_composition: v.any(),
    // Progress
    techs_completed: v.number(),
    civics_completed: v.number(),
    techs: v.optional(v.array(v.string())),
    civics: v.optional(v.array(v.string())),
    current_research: v.string(),
    current_civic: v.string(),
    // Infrastructure
    districts: v.number(),
    wonders: v.number(),
    great_works: v.number(),
    territory: v.number(),
    improvements: v.number(),
    exploration_pct: v.number(),
    // Governance
    era: v.string(),
    era_score: v.number(),
    age: v.string(),
    government: v.string(),
    policies: v.array(v.string()),
    pantheon: v.string(),
    religion: v.string(),
    religion_beliefs: v.array(v.string()),
    // Victory
    sci_vp: v.number(),
    diplo_vp: v.number(),
    tourism: v.number(),
    staycationers: v.number(),
    religion_cities: v.number(),
    // Resources
    stockpiles: v.any(),
    luxuries: v.any(),
    // Agent-only fields (optional)
    diplo_states: v.optional(v.any()),
    suzerainties: v.optional(v.number()),
    envoys_available: v.optional(v.number()),
    envoys_sent: v.optional(v.any()),
    gp_points: v.optional(v.any()),
    governors: v.optional(v.any()),
    trade_routes: v.optional(v.any()),
    reflections: v.optional(v.any()),
    agent_client: v.optional(v.string()),
    agent_client_ver: v.optional(v.string()),
    agent_model: v.optional(v.string()),
  })
    .index("by_game_turn", ["gameId", "turn"])
    .index("by_game_turn_pid", ["gameId", "turn", "pid"]),

  // One doc per city per turn — mirrors CityRow from diary JSONL
  cityRows: defineTable({
    gameId: v.string(),
    turn: v.number(),
    game: v.string(),
    v: v.number(),
    pid: v.number(),
    city_id: v.number(),
    city: v.string(),
    pop: v.number(),
    food: v.number(),
    production: v.number(),
    gold: v.number(),
    science: v.number(),
    culture: v.number(),
    faith: v.number(),
    housing: v.number(),
    amenities: v.number(),
    amenities_needed: v.number(),
    districts: v.string(),
    producing: v.string(),
    loyalty: v.number(),
    loyalty_per_turn: v.number(),
  }).index("by_game_turn", ["gameId", "turn"]),

  // One doc per tool call log line — mirrors LogEntry from types.ts
  logEntries: defineTable({
    gameId: v.string(),
    line: v.number(),
    game: v.string(),
    civ: v.string(),
    seed: v.number(),
    session: v.string(),
    ts: v.number(),
    turn: v.union(v.number(), v.null()),
    seq: v.number(),
    type: v.string(),
    tool: v.string(),
    category: v.string(),
    params: v.union(v.any(), v.null()),
    result_summary: v.union(v.string(), v.null()),
    result: v.union(v.string(), v.null()),
    duration_ms: v.union(v.number(), v.null()),
    success: v.boolean(),
    events: v.optional(v.any()),
    agent_model: v.optional(v.union(v.string(), v.null())),
  })
    .index("by_game_line", ["gameId", "line"])
    .index("by_game_session", ["gameId", "session"]),

  // One doc per turn — pre-aggregated spatial attention data
  spatialTurns: defineTable({
    gameId: v.string(),
    turn: v.number(),
    tiles_observed: v.number(),
    tool_calls: v.number(),
    cumulative_tiles: v.number(),
    total_ms: v.number(),
    by_type: v.object({
      deliberate_scan: v.number(),
      deliberate_action: v.number(),
      survey: v.number(),
      peripheral: v.number(),
      reactive: v.number(),
    }),
  }).index("by_game_turn", ["gameId", "turn"]),
});
