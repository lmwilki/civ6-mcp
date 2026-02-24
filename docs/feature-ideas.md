# Feature Ideas

## ELO Leaderboard: Add Difficulty Level Tracking

**Status:** Blocked — needs live game to test Lua API

**Problem:** The ELO leaderboard currently ranks individual AI leaders (Trajan, Cleopatra, etc.) against LLM models. But AI leaders don't have inherent difficulty — difficulty is a game-wide setting (Settler → Deity) that applies equally to all AI players. The leaderboard should rank **difficulty levels** (e.g. "Deity AI", "Emperor AI") instead of individual leaders.

**What's needed:**

1. **Lua query** — Call `GameDifficulty.GetCurrentDifficulty()` (or equivalent) in `src/civ_mcp/lua/overview.py` inside `build_overview_query()`
2. **GameOverview model** — Add `difficulty` field to the dataclass in `src/civ_mcp/lua/models.py`
3. **Narration** — Include difficulty in `src/civ_mcp/narrate.py` output
4. **Diary JSONL** — Add `difficulty` field to PlayerRow entries (both agent and rival rows)
5. **Web types** — Add `difficulty` to `PlayerRow` in `web/src/lib/diary-types.ts`
6. **ELO API** — Update `web/src/app/api/elo/route.ts` to use `"difficulty:<level>"` as the AI participant ID instead of `"ai:<leader>"`
7. **Leaderboard component** — Update display in `web/src/components/model-leaderboard.tsx`
8. **Dummy data** — Update `~/.civ6-mcp/diary_demo_elo*.jsonl` files with difficulty field

**Civ 6 difficulty levels:** Settler, Chieftain, Warlord, Prince, King, Emperor, Immortal, Deity

---

## N-Player LLM Arena (Agent vs Agent)

**Status:** Design complete — see `docs/agent-vs-agent.md`

**Problem:** The MCP server currently supports a single LLM agent playing against Civ 6's built-in AI. The goal is N LLM agents playing against each other in the same game with fog-of-war fairness.

**Key constraint:** FireTuner is hard-disabled in Civ 6's multiplayer/hotseat modes (anti-cheat). The approach is **single-player puppeteering** — a Lua gameplay mod intercepts AI players' turns and hands control to LLM agents.

**Architecture:**
```
Agent 0 (Player 0)  Agent 1 (Player 1)  Agent N (Player N)
        \                 |                  /
         └────── Coordinator ──────────┘
                      |
                 GameState(player_id=X)   ← per-player instances
                      |
                 GameConnection           ← shared, serialized
                      |  TCP :4318
                 Civ 6 + PuppeteerMod     ← single-player game
```

**Implementation phases:**

### Phase 1: PuppeteerMod (Lua Gameplay Mod)
- Create `PuppeteerMod/` — Lua mod that intercepts N configurable AI players' turns
- Hook `GameEvents.PlayerTurnStartComplete`: freeze units via `FinishMoves`, restore movement, set ready flag
- Coordinator polls `__puppet_turn_active[playerID]` to detect whose turn it is

### Phase 2: Lua Builder Parameterization
- Add `player_id: int | None = None` to all 106 `build_*` functions across 12 Lua modules
- Replace 72 hardcoded `Game.GetLocalPlayer()` calls with `_lua_player_expr(player_id)`
- Backward compatible: `player_id=None` preserves existing single-agent behavior

### Phase 3: Fog-of-War Enforcement
- Existing `PlayersVisibility[me]` checks automatically scope to correct player after Phase 2
- Add visibility checks to threat scan (enemy units) and diplomacy (enemy cities)
- Create `fog_filter.py` for defense-in-depth auditing

### Phase 4: Local-Player Switching
- Add `_with_player_context(player_id, lua_code)` to `game_state.py`
- Wraps InGame operations in `PlayerManager.SetLocalPlayerAndObserver()` + pcall + restore
- Required for: move, attack, found city, production, purchases, diplomacy

### Phase 5: Coordinator + Puppet End-Turn
- Create `coordinator.py` — turn detection, N-agent dispatch, timeout handling
- Create `puppet_end_turn.py` — simplified end-turn (`FinishMoves` instead of `ACTION_ENDTURN`)
- Turn sequence: Player 0 ends turn → puppet players intercepted sequentially → AI processes → repeat

### Phase 6: Agent Interface + CLI
- Create `agent.py` — Claude conversation loop via Anthropic API with tool-use
- Create `tool_schemas.py` — tool definitions mirroring `server.py`
- Create `arena.py` — CLI entry point: `civ-arena --players 0:model-a,1:model-b --max-turns 200`
- Per-player diary, context window management (sliding window + diary summaries)

**Files:** 8 new, 16 modified

---

## Live Gameplay Streaming to Web Dashboard

**Status:** Not started

**Problem:** The web dashboard currently shows post-game data (diary replays, ELO ratings). There's no way to watch a game live as the agent plays.

**Approach:** Add WebSocket streaming from the MCP server's FastAPI backend (port 8000) to push real-time game state updates to the Next.js dashboard.

**Why WebSockets over video capture:** The MCP server already has structured game state (overview, units, cities, map tiles, diplomacy) and the `GameLogger` captures every tool call with timing. Streaming this data is low-bandwidth, works remotely, and gives viewers the agent's perspective — what it queried, what it decided, and why. Video capture (OBS/FFmpeg) could be layered on later as a complement.

**What's needed:**

1. **WebSocket endpoint** — Add `/ws/game` to `src/civ_mcp/web_api.py` using FastAPI's WebSocket support. Broadcast game state diffs after each tool call or turn.
2. **Event bus** — Hook into `GameLogger` or create a lightweight pub/sub so tool calls, turn transitions, and end-turn snapshots emit events to connected WebSocket clients.
3. **Live dashboard page** — New `/live` page in `web/` that connects to the WebSocket and renders:
   - Game overview (turn, yields, score) updating in real-time
   - Simplified hex map with unit positions and city locations
   - Agent action feed (tool calls streaming in with timing)
   - Current diary entry / agent reasoning
4. **Map rendering** — Render a simplified hex grid in the browser using Canvas or SVG, showing terrain, units, cities, and fog of war from `get_map_area` data.
5. **Reconnection handling** — WebSocket auto-reconnect with full state sync on connect (not just diffs).
6. **Optional: video stream embed** — Add a video player component that can embed an HLS/WebRTC stream of the game window alongside the data visualization.
