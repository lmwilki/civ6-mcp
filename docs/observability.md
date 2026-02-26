# Observability: Diary, Logging, and Spatial Tracking

The MCP server records three parallel data streams during gameplay, all written to `~/.civ6-mcp/` as JSONL (one JSON object per line). Together they capture *what the game looked like*, *what the agent did*, and *where the agent looked*.

```
~/.civ6-mcp/
  diary_korea_-879712000.jsonl           # per-turn game state + agent reflections
  diary_korea_-879712000_cities.jsonl    # per-turn per-city detail
  log_korea_-879712000.jsonl             # every tool call with timing and results
  spatial_korea_-879712000.jsonl         # tile-level attention tracking
```

All files are keyed by `{civ}_{seed}` (e.g. `korea_-879712000`), derived from the civilization type and the game's random seed. Multiple concurrent games produce independent file sets.

---

## Diary

**Files:** `diary_{civ}_{seed}.jsonl` + `diary_{civ}_{seed}_cities.jsonl`

The diary is the agent's persistent memory. It captures a full game-state snapshot plus the agent's own reflections once per turn, written just before the turn advances. When context compacts or the agent resumes a game in a new session, `get_diary` reconstructs strategic context from these entries.

### What's recorded

**Per-player row** (one per alive civilization per turn):
- Score, population, city count
- Yields: science, culture, gold, faith, favor (with per-turn rates)
- Military strength and unit composition
- Tech/civic completion lists and current research
- District, wonder, and great work counts
- Territory size, improvement count, exploration percentage
- Government, policies, era, era score, age
- Pantheon, religion, and religion beliefs
- Victory progress (science VP, diplomatic VP, tourism, domestic tourists)
- Resource stockpiles and luxury counts

**Agent row** (additional fields for the local player):
- Diplomatic states with all known civs (state index, alliance type/level, grievances)
- City-state envoys and suzerainties
- Governor assignments and promotions
- Trade route utilization
- Great Person point accumulation
- Five reflection fields (see below)
- MCP client identity and model ID

**City rows** (separate file, one per city per turn):
- Population, all six yields, housing, amenities
- District list, current production
- Loyalty and loyalty per-turn

### Reflections

The agent writes five required fields on every `end_turn` call:

| Field | Purpose |
|-------|---------|
| `tactical` | What happened this turn: specific units, tiles, combat outcomes |
| `strategic` | Standing vs rivals: yields, city count, victory path viability |
| `tooling` | Tool issues observed, or "No issues" |
| `planning` | Concrete actions for the next 5-10 turns |
| `hypothesis` | Predictions: attack timing, milestones, risks |

Reflections are recorded *before* AI processing begins. Events that surface after `end_turn` (diplomacy proposals, AI movements) belong in the next turn's diary.

If `end_turn` is blocked (diplomacy, World Congress) and retried, the new reflections are merged into the existing turn's entry with `" | "` separators rather than creating a duplicate.

### Retrieval

The `get_diary` tool reads back diary entries filtered to agent rows:

```
get_diary(last_n=5)           # most recent 5 entries
get_diary(turn=100)           # single turn
get_diary(from_turn=80, to_turn=120)  # range
```

Output is formatted as readable markdown with yields, resources, and all five reflection fields.

### Format

```json
{
  "v": 1,
  "turn": 145,
  "game": "korea_-879712000",
  "timestamp": "2026-02-26T18:30:45.123456+00:00",
  "is_agent": true,
  "pid": 0,
  "civ": "CIVILIZATION_KOREA",
  "leader": "Seondeok",
  "score": 742,
  "cities": 5,
  "science": 89.5,
  "gold_per_turn": 18.5,
  "reflections": {
    "tactical": "Established Campus in Seoul...",
    "strategic": "Currently 2nd in science...",
    "tooling": "No issues.",
    "planning": "Build Library in Busan...",
    "hypothesis": "Poland likely to declare friendship..."
  },
  "agent_model": "claude-opus-4-6"
}
```

(Many fields omitted for brevity — full schema has 95+ fields per player row.)

---

## Tool Log

**File:** `log_{civ}_{seed}.jsonl`

Every MCP tool call is logged with full timing, parameters, and results. This is the authoritative record of what the agent did and how long it took.

### What's recorded

Each entry:
- Tool name and category (`query` / `action` / `turn`)
- Input parameters
- Full narrated result text
- Result summary (first 200 chars, for quick analysis)
- Success/failure flag
- Wall-clock duration in milliseconds
- Turn number, timestamp, per-game sequence number
- Session ID (unique per MCP server process)
- Agent model ID

Game-over entries include an `outcome` object with winner, victory type, and whether the agent survived.

### Format

```json
{
  "game": "korea_-879712000",
  "session": "a1b2c3d4",
  "ts": 1708981845.123,
  "turn": 145,
  "seq": 2847,
  "type": "tool_call",
  "tool": "get_units",
  "category": "query",
  "params": {},
  "result_summary": "4 units:\n  Crossbowman (UNIT_CROSSBOW...",
  "result": "4 units:\n  Crossbowman (UNIT_CROSSBOWMAN) at (43,6)...",
  "duration_ms": 342,
  "success": true,
  "agent_model": "claude-opus-4-6"
}
```

### Typical size

10-50 MB per full game (400 turns). The `result` field stores complete narrated text, which dominates file size.

---

## Spatial Attention Tracker

**File:** `spatial_{civ}_{seed}.jsonl`

Research instrumentation that records which map tiles the agent observes through each tool call. This does not feed back to the agent — it exists to measure the "Sensorium Effect" (the gap between what a human player passively sees and what the agent explicitly queries).

### Motivation

A human player glances at the minimap and notices territory changing color. They see the score ribbon tick up. They spot a unit health bar drop. The agent gets none of this passively — every piece of spatial information must be explicitly queried. The spatial tracker measures *where* and *when* the agent's attention falls, enabling analysis of blind spots and attention decay.

### How tiles are extracted

Two sources per tool call:

1. **Result text** — A regex `\((\d+),(\d+)\)` extracts all coordinate pairs from the narrated output. This format is used consistently by every narration function.
2. **Input parameters** — `target_x`/`target_y`, `x`/`y`, or computed from `center_x`/`center_y`/`radius` for `get_map_area`.

### Attention types

Each observation is classified by how the agent came to see those tiles:

| Type | Tools | What it means |
|------|-------|---------------|
| `deliberate_scan` | `get_map_area`, `get_settle_advisor`, `get_district_advisor`, `get_wonder_advisor`, `get_purchasable_tiles`, `get_pathing_estimate` | Agent chose to look at a specific area |
| `deliberate_action` | `unit_action`, `city_action`, `spy_action`, `set_city_production`, `purchase_tile` | Agent acted on a specific tile |
| `survey` | `get_strategic_map`, `get_global_settle_advisor`, `get_empire_resources` | Broad scan across the map or empire |
| `peripheral` | `get_units`, `get_cities`, `get_spies`, `get_diplomacy`, `get_trade_routes`, `get_trade_destinations` | Coordinates seen as a side effect of status queries |
| `reactive` | `get_notifications` | Coordinates from game-pushed alerts |

Tools with no spatial data (research, policies, governors, etc.) are silently skipped.

### Format

```json
{
  "game": "korea_-879712000",
  "turn": 208,
  "tool": "get_map_area",
  "type": "deliberate_scan",
  "tiles": [[42,5],[42,6],[42,7],[43,5],[43,6],[43,7],[44,5],[44,6],[44,7]],
  "n_tiles": 9,
  "ts": 1772134312.095,
  "ms": 364
}
```

### Typical size

~1 MB per full game (400 turns on a standard map). Roughly 2-5% of the tool log size.

### Analysis ideas

The data supports several kinds of post-hoc analysis:

- **Attention heatmap**: For each tile, when was it last observed? Which tiles are never observed?
- **Attention decay**: How quickly does observation frequency drop for a region after the agent moves on?
- **Reactive vs proactive**: Does the agent survey systematically, or only look where threats already appeared?
- **Blind spot correlation**: When the agent loses a unit or misses a rival's victory, was the relevant region unobserved?
- **Tool utility**: Which tools expand spatial coverage vs redundantly re-observe known tiles?
- **Coverage rate**: What fraction of revealed map tiles does the agent observe per turn? Per 10 turns?

---

## Shared patterns

All three systems share the same architecture:

**Unbounded buffer pattern.** Each tracker starts unbound (no game identity). Tool calls are buffered in memory. When `get_game_overview` first runs, it calls `get_game_identity()` to determine the civ and seed, then binds all three trackers. Buffered entries are flushed to disk with the now-known identity.

**Game identity.** Determined by a Lua query that reads `PlayerConfigurations[me]:GetCivilizationTypeName()` and `GameConfiguration.GetValue("GAME_SYNC_RANDOM_SEED")`. The civ name is lowercased and stripped of the `CIVILIZATION_` prefix.

**Turn tracking.** All trackers maintain a `_turn` field updated at four points:
1. `get_game_overview` — primary entry point each turn
2. `end_turn` diary capture — keeps turn in sync if overview was skipped
3. `end_turn` result parsing — advances to the new turn number after `"Turn X -> Y"`
4. `concede_game` — ensures final entries have the correct turn

**JSONL format.** One JSON object per line, compact separators (`(",":")`), no array wrapper. Files can be tailed, grepped, or streamed without parsing the entire file.

**Hook point.** All tool calls pass through `_logged()` in `server.py`, which:
1. Times the execution
2. Catches errors
3. Calls `logger.log_tool_call()` — writes to tool log
4. Calls `spatial.record()` — writes to spatial log (try/except, never breaks gameplay)
5. Returns the narrated result to the agent

```
Agent ─── MCP Tool Call ──→ _logged() ──→ fn() ──→ narrated result
                               │                        │
                               ├─ logger.log_tool_call() ← result + timing
                               └─ spatial.record()       ← result + params
                                                          ↓
                               Diary written separately by end_turn()
```

---

## File size estimates (400 turns, standard map)

| File | Typical size | Driven by |
|------|-------------|-----------|
| `diary_*.jsonl` | 2-5 MB | Player count, field count |
| `diary_*_cities.jsonl` | 1-3 MB | City count, turns played |
| `log_*.jsonl` | 10-50 MB | Tool calls per turn, result text length |
| `spatial_*.jsonl` | 0.5-1.5 MB | Spatial tool calls per turn, tile counts |
| **Total per game** | **~15-60 MB** | |
