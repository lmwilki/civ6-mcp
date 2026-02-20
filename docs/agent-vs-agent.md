# Agent vs Agent: Multi-Agent Play via Single-Player Puppeteering

> **Status: Proposal** — Design document. Not yet implemented.

## Overview

This document describes how to make two (or more) AI agents play Civilization VI against each other using a single game instance in single-player mode. One agent plays normally as the human player; the other agent "puppeteers" an AI player by intercepting its turn and issuing commands through GameCore and temporary local-player switching.

No multiplayer is needed. No binary patching. Works on macOS and Windows.

```
┌─────────────┐     ┌─────────────┐
│   Agent A   │     │   Agent B   │
│ (Player 0)  │     │ (Player 1)  │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └───────┬───────────┘
               │
        ┌──────▼──────┐
        │ Coordinator  │  ← detects whose turn it is, dispatches
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │  MCP Server  │  ← single instance, parametrized by player_id
        └──────┬──────┘
               │ TCP :4318
        ┌──────▼──────┐
        │   Civ 6     │  ← single-player, EnableTuner=1
        │  + Lua Mod   │  ← intercepts AI turns
        └─────────────┘
```

## Why Not Multiplayer?

FireTuner's TCP listener (port 4318) is **hard-disabled at the C++ engine level** for all multiplayer modes — LAN, Internet, and Hot-Seat. This is an intentional anti-cheat measure with no known config override. The Archipelago mod developers independently confirmed there is no workaround.

The only path to agent-vs-agent is single-player puppeteering.

---

## Architecture

### Component 1: Turn Interception Mod (Lua)

A Civ 6 gameplay mod installed in the Mods folder. Its job:

1. **Neutralize built-in AI** — On `GameEvents.PlayerTurnStartComplete`, call `UnitManager.FinishMoves()` on all target player's units before the AI can act
2. **Signal readiness** — Set a global flag that the MCP server can poll to know the puppet player's turn has started
3. **Restore movement** — Give units back their movement points so our agent can command them
4. **Handle turn end** — Call `FinishMoves()` again when the agent signals it's done

#### Turn Event Sequence (per player)

```
GameEvents.PlayerTurnStarted(playerID)
    └─ Movement points NOT yet restored

GameEvents.PlayerTurnStartComplete(playerID)    ← HOOK HERE
    └─ Movement points restored
    └─ *** Built-in AI executes between here and next event ***

Events.PlayerTurnActivated(playerID, isFirstTime)
    └─ AI has finished acting

Events.PlayerTurnDeactivated(playerID)
    └─ Player's turn is over
```

The critical window is between `PlayerTurnStartComplete` and `PlayerTurnActivated`. The mod must call `FinishMoves()` on all units in `PlayerTurnStartComplete` to prevent the AI from acting.

#### Mod Implementation

```lua
-- PuppeteerMod/Scripts/Puppeteer.lua (GameplayScript context)

local PUPPET_PLAYER = 1  -- Which player the agent controls

-- Global state readable by FireTuner
__puppet_turn_active = false
__puppet_player_id = PUPPET_PLAYER

function OnPlayerTurnStartComplete(playerID)
    if playerID == PUPPET_PLAYER then
        -- Step 1: Freeze all units (prevents built-in AI from acting)
        local pUnits = Players[playerID]:GetUnits()
        for _, unit in pUnits:Members() do
            UnitManager.FinishMoves(unit)
        end

        -- Step 2: Restore movement (gives our agent control)
        for _, unit in pUnits:Members() do
            UnitManager.RestoreMovement(unit)
        end

        -- Step 3: Signal that puppet turn is ready
        __puppet_turn_active = true
    end
end

function OnPlayerTurnDeactivated(playerID)
    if playerID == PUPPET_PLAYER then
        __puppet_turn_active = false
    end
end

GameEvents.PlayerTurnStartComplete.Add(OnPlayerTurnStartComplete)
Events.PlayerTurnDeactivated.Add(OnPlayerTurnDeactivated)
```

#### Mod Descriptor

```xml
<!-- PuppeteerMod/PuppeteerMod.modinfo -->
<?xml version="1.0" encoding="utf-8"?>
<Mod id="PUPPET_AGENT_MOD" version="1">
  <Properties>
    <Name>Agent Puppeteer</Name>
    <Description>Intercepts AI turns for external agent control</Description>
    <EnabledByDefault>1</EnabledByDefault>
  </Properties>
  <Components>
    <AddGameplayScripts>
      <File>Scripts/Puppeteer.lua</File>
    </AddGameplayScripts>
  </Components>
</Mod>
```

> **Open question:** `AddGameplayScripts` runs in GameCore context. The `Events.PlayerTurnDeactivated` hook is a UI event — it may need to be in an `AddInGameActions` component instead. Testing required.

---

### Component 2: MCP Server Changes

#### 2a. Parametrize Lua Builders

Every Lua query currently hardcodes `Game.GetLocalPlayer()`. For puppet control, queries need to accept an explicit player ID.

**Strategy:** Add a helper that generates the player expression:

```python
# In _helpers.py
def _lua_player_expr(player_id: int | None = None) -> str:
    """Return Lua expression for the target player.

    None → Game.GetLocalPlayer() (normal play)
    int  → literal player ID (puppet mode)
    """
    if player_id is None:
        return "Game.GetLocalPlayer()"
    return str(player_id)
```

Update `_lua_get_unit` and `_lua_get_city`:

```python
def _lua_get_unit(unit_index: int, player_id: int | None = None) -> str:
    return f"""
local me = {_lua_player_expr(player_id)}
local unit = UnitManager.GetUnit(me, {unit_index})
if unit == nil then {_bail("ERR:UNIT_NOT_FOUND")} end
"""
```

Then propagate `player_id: int | None = None` through:
- All `build_*` functions (66 call sites across 11 modules)
- All `GameState` methods
- All MCP tool definitions in `server.py`

**Scope:** This is a large but mechanical refactor. Each builder gets `player_id=None` as a parameter, and replaces `Game.GetLocalPlayer()` with `{_lua_player_expr(player_id)}`.

#### 2b. Write Operations — GameCore vs InGame

For the puppet player, some operations work in GameCore (any player) and others require temporarily switching the local player.

**GameCore (works for any player — no switching needed):**

| Operation | API | Notes |
|-----------|-----|-------|
| Move (1 tile) | `UnitManager.MoveUnit(unit, plot)` | Unreliable pathfinding; move 1 tile at a time |
| Skip/finish | `UnitManager.FinishMoves(unit)` | |
| Restore moves | `UnitManager.RestoreMovement(unit)` | |
| Kill unit | `UnitManager.Kill(unit)` | |
| Create unit | `UnitManager.InitUnit(playerID, type, x, y)` | |
| Set research | `pTechs:SetResearchingTech(techID)` | |
| Set research progress | `pTechs:SetResearchProgress(techID, val)` | |
| Trigger eureka | `pTechs:TriggerBoost(techID)` | |
| Set civic progress | `pCulture:SetCulturalProgress(civicID, val)` | Do NOT use `SetCivic()` — breaks AI permanently |
| Instant building | `bq:CreateIncompleteBuilding(id, plot, 100)` | Cheat-level; instant completion |

**InGame (requires local-player switch):**

| Operation | API | Why switch needed |
|-----------|-----|-------------------|
| Multi-tile move | `UnitManager.RequestOperation(MOVE_TO)` | Pathfinding only works for local player |
| Ranged attack | `UnitManager.RequestOperation(RANGE_ATTACK)` | |
| Melee attack | `UnitManager.RequestOperation(MOVE_TO + ATTACK)` | |
| Found city | `UnitManager.RequestOperation(FOUND_CITY)` | |
| Build improvement | `UnitManager.RequestOperation(BUILD_IMPROVEMENT)` | |
| Set production | `CityManager.RequestOperation(BUILD)` | |
| Purchase item | `CityManager.RequestCommand(PURCHASE)` | |
| Diplomacy | `DiplomacyManager.RequestSession()` | |
| Promote unit | `UnitManager.RequestCommand(PROMOTE)` | Broken in InGame; use GameCore `SetPromotion` instead |
| Upgrade unit | `UnitManager.RequestCommand(UPGRADE)` | |

#### 2c. Local Player Switching

For InGame operations on the puppet player, temporarily switch who the game considers "local":

```python
async def _with_player_context(self, player_id: int, lua_code: str) -> list[str]:
    """Execute InGame Lua as if player_id were the local player."""
    if player_id is None:
        # Normal path — no switching needed
        return await self.conn.execute_write(lua_code)

    switch_lua = f"""
local origPlayer = Game.GetLocalPlayer()
PlayerManager.SetLocalPlayerAndObserver({player_id})
"""
    restore_lua = f"""
PlayerManager.SetLocalPlayerAndObserver(origPlayer)
"""
    wrapped = switch_lua + lua_code + restore_lua
    return await self.conn.execute_write(wrapped)
```

**Caveats:**
- Causes a visible frame freeze each time
- Must be atomic — if the Lua errors mid-execution, the player stays switched (need pcall wrapping)
- Should restore as quickly as possible to avoid visual artifacts

**Safer version with pcall:**

```python
async def _with_player_context(self, player_id: int, lua_code: str) -> list[str]:
    if player_id is None:
        return await self.conn.execute_write(lua_code)

    wrapped = f"""
local origPlayer = Game.GetLocalPlayer()
PlayerManager.SetLocalPlayerAndObserver({player_id})
local ok, err = pcall(function()
{lua_code}
end)
PlayerManager.SetLocalPlayerAndObserver(origPlayer)
if not ok then print("ERR:PUPPET_ERROR|" .. tostring(err)); print("---END---"); return end
"""
    return await self.conn.execute_write(wrapped)
```

#### 2d. GameCore Movement (1-Tile Pathfinding)

`UnitManager.MoveUnit()` in GameCore has unreliable multi-tile pathfinding. For robust puppet movement, implement 1-tile-at-a-time stepping:

```lua
-- Move unit one tile toward target using adjacency
local unit = Players[pid]:GetUnits():FindID(unitIdx)
local ux, uy = unit:GetX(), unit:GetY()
local tx, ty = targetX, targetY

-- Find best adjacent tile (closest to target)
local bestPlot, bestDist = nil, 999
for dir = 0, 5 do
    local adj = Map.GetAdjacentPlot(ux, uy, dir)
    if adj and not adj:IsImpassable() then
        local dx = adj:GetX() - tx
        local dy = adj:GetY() - ty
        local dist = dx*dx + dy*dy
        if dist < bestDist then
            bestDist = dist
            bestPlot = adj
        end
    end
end
if bestPlot then
    UnitManager.MoveUnit(unit, bestPlot)
end
```

This is naive (no terrain cost weighting, no ZOC handling). A proper implementation would need A* over the hex grid with terrain costs. Alternatively, use the local-player-switch to access `RequestOperation(MOVE_TO)` which has full pathfinding.

**Recommendation:** Use local-player-switch for movement. The frame freeze is acceptable since the human isn't watching the puppet player's turn.

---

### Component 3: Coordinator

The coordinator manages turn sequencing between agents. It runs as a separate process (or coroutine) that:

1. **Polls for turn changes** — Periodically queries `Game.GetLocalPlayer()` and `__puppet_turn_active`
2. **Dispatches to agents** — Tells Agent A or Agent B it's their turn
3. **Waits for completion** — Agent signals done, coordinator triggers turn end

#### State Machine

```
                    ┌──────────────┐
                    │  WAITING     │
                    │  (polling)   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼                         ▼
    ┌─────────────────┐      ┌──────────────────┐
    │ AGENT_A_TURN    │      │ AGENT_B_TURN     │
    │ (player 0)      │      │ (player 1)       │
    │ normal MCP ops  │      │ puppet MCP ops   │
    └────────┬────────┘      └────────┬─────────┘
             │                        │
             ▼                        ▼
    ┌─────────────────┐      ┌──────────────────┐
    │ AGENT_A_END     │      │ AGENT_B_END      │
    │ end_turn()      │      │ finish_moves()   │
    └────────┬────────┘      └────────┬─────────┘
             │                        │
             └────────────┬───────────┘
                          ▼
                    ┌──────────────┐
                    │  WAITING     │
                    └──────────────┘
```

#### Turn Detection

```python
async def poll_turn_state(conn: GameConnection) -> tuple[int, bool]:
    """Returns (current_player_turn, is_puppet_ready)."""
    lines = await conn.execute_read("""
local me = Game.GetLocalPlayer()
print("TURN_STATE|" .. Game.GetCurrentGameTurn())
print("LOCAL|" .. me)
print("PUPPET_ACTIVE|" .. tostring(__puppet_turn_active or false))
print("---END---")
""")
    # Parse and return state
    ...
```

#### Coordinator Loop

```python
async def coordinator_loop(conn, agent_a, agent_b):
    while True:
        turn, puppet_ready = await poll_turn_state(conn)

        if puppet_ready:
            # It's the puppet player's turn — dispatch to Agent B
            await agent_b.play_turn(player_id=PUPPET_PLAYER)
            # Signal done — finish all moves
            await conn.execute_read(f"""
local pUnits = Players[{PUPPET_PLAYER}]:GetUnits()
for _, unit in pUnits:Members() do
    UnitManager.FinishMoves(unit)
end
print("---END---")
""")
        else:
            # Check if it's the human player's turn
            # Agent A plays normally via standard MCP tools
            await agent_a.play_turn(player_id=None)

        await asyncio.sleep(0.5)
```

---

### Component 4: Agent Interface

Each agent needs to know:
- Which player it controls
- When it's their turn
- What tools are available (puppet player has restricted operations)

#### Option A: Two MCP Clients, One Server

Run two Claude Code sessions (or two API-driven agents), both connecting to the same MCP server. Each passes `player_id` to every tool call.

```
Agent A (Claude session 1) ──► MCP Server ──► Civ 6
Agent B (Claude session 2) ──► MCP Server ──► Civ 6
```

**Problem:** MCP servers are per-client. Two Claude sessions = two MCP server processes = two TCP connections fighting over port 4318.

#### Option B: Single Orchestrator Process

One Python process runs both agents sequentially:

```python
async def main():
    conn = GameConnection()
    await conn.connect()

    agent_a = Agent(conn, player_id=0, model="claude-sonnet-4-5-20250929")
    agent_b = Agent(conn, player_id=1, model="claude-sonnet-4-5-20250929")

    while True:
        turn_state = await poll_turn_state(conn)

        if turn_state.is_human_turn:
            await agent_a.play_turn()
        elif turn_state.is_puppet_ready:
            await agent_b.play_turn()
        else:
            await asyncio.sleep(0.5)
```

Each `Agent` uses the Anthropic API directly (not MCP) and calls game functions through the shared `GameState`:

```python
class Agent:
    def __init__(self, conn, player_id, model):
        self.gs = GameState(conn)
        self.player_id = player_id
        self.client = anthropic.AsyncAnthropic()
        self.model = model
        self.messages = []

    async def play_turn(self):
        # Build tool definitions from GameState methods
        # Run agentic loop: observe → decide → act → observe
        overview = await self.gs.get_game_overview(player_id=self.player_id)
        units = await self.gs.get_units(player_id=self.player_id)
        # ... Claude decides actions ...
        # ... execute actions ...
        # ... end turn ...
```

**This is the recommended approach.** Single process, single connection, sequential turns, clean separation.

#### Option C: Agent SDK

Use the [Claude Agent SDK](https://github.com/anthropics/agent-sdk) to define each agent with game tools:

```python
from agent_sdk import Agent, tool

@tool
async def get_units(player_id: int) -> str:
    """Get all units for the specified player."""
    return await shared_gs.get_units(player_id=player_id)

agent_a = Agent(
    model="claude-sonnet-4-5-20250929",
    tools=[get_units, move_unit, attack, ...],
    system="You are playing Civ 6 as player 0. Play to win.",
)

agent_b = Agent(
    model="claude-sonnet-4-5-20250929",
    tools=[get_units, move_unit, attack, ...],
    system="You are playing Civ 6 as player 1. Play to win.",
)
```

---

## GameCore API Reference (Any Player)

### Unit Management

| Method | Signature | Notes |
|--------|-----------|-------|
| Move | `UnitManager.MoveUnit(unit, plot)` | 1-tile reliable; multi-tile unreliable |
| Finish | `UnitManager.FinishMoves(unit)` | Zeros movement |
| Restore | `UnitManager.RestoreMovement(unit)` | Full movement restore |
| Restore attacks | `UnitManager.RestoreUnitAttacks(unit)` | |
| Kill | `UnitManager.Kill(unit)` | Removes unit |
| Place | `UnitManager.PlaceUnit(unit, plot)` | Teleport |
| Create | `UnitManager.InitUnit(playerID, unitType, x, y)` | Spawn new unit |
| Wake | `UnitManager.WakeUnit(unit)` | |

### Research (PlayerTechs)

| Method | Notes |
|--------|-------|
| `SetResearchingTech(techID)` | Set active research |
| `SetResearchProgress(techID, progress)` | Set progress value |
| `ChangeCurrentResearchProgress(delta)` | Increment |
| `TriggerBoost(techID)` | Eureka |
| `SetTech(techID, true)` | Instantly grant (cheat) |

### Culture (PlayerCulture)

| Method | Notes |
|--------|-------|
| `SetCulturalProgress(civicID, progress)` | Safe — set progress |
| `SetCivic(civicID, true)` | **DANGEROUS** — permanently breaks AI civic research |

### Buildings (CityBuildQueue)

| Method | Notes |
|--------|-------|
| `CreateIncompleteBuilding(buildingID, plotIdx, percentComplete)` | Cheat; 100 = instant |

### Scripted Military Operations (from Gedemon's GCO)

| Method | Notes |
|--------|-------|
| `pAiMil:StartScriptedOperationWithTargetAndRally(...)` | Create military operations for any player |
| `pAiMil:AddUnitToScriptedOperation(opID, unitID)` | Assign units to operations |

---

## Limitations and Tradeoffs

### What Works Well
- **Unit movement** (via local-player switch or 1-tile GameCore)
- **Research/civic selection** (GameCore setters)
- **Reading any player's state** (all `Players[N]:Get*()` queries work)
- **Turn interception** (proven by modders)

### What's Fragile
- **Local-player switching** — causes frame freezes, must pcall-wrap
- **Production queue** — no GameCore setter; need switch or instant-build cheat
- **Diplomacy** — `DiplomacyManager` is local-player-only; AI-to-AI diplomacy has no API
- **City founding** — needs `RequestOperation` which needs switch

### What Doesn't Work
- **AI-to-AI diplomacy** — no known API to make two AI players negotiate
- **`SetCivic()` for AI** — permanently breaks their civic research; use `SetCulturalProgress()` instead
- **True simultaneous play** — turns are sequential; agents alternate

### Fairness Considerations
- Agent A (human player) has full InGame API access — normal play
- Agent B (puppet player) has GameCore access to ALL players — could cheat by reading fog-of-war, enemy positions, etc.
- **Enforce fairness:** The coordinator should only allow Agent B to read its own player's visible tiles. This requires wrapping queries with visibility checks.
- **Production asymmetry:** Agent A uses the normal queue; Agent B either uses local-player-switch (fair) or instant-build (unfair). Use the switch for fairness.

---

## Implementation Phases

### Phase 1: Lua Mod + Turn Detection
- Build the `PuppeteerMod` (Lua gameplay script)
- Test that `FinishMoves` + `RestoreMovement` successfully neutralizes and re-enables AI units
- Verify `__puppet_turn_active` is readable from FireTuner
- Test `PlayerManager.SetLocalPlayerAndObserver()` switching
- **Deliverable:** Can manually issue commands for player 1 via FireTuner during their turn

### Phase 2: Parametrize MCP Server
- Add `player_id: int | None = None` to `_lua_player_expr()`, `_lua_get_unit()`, `_lua_get_city()`
- Propagate through all 66 `build_*` call sites
- Add `_with_player_context()` wrapper for InGame operations
- Propagate `player_id` through `GameState` methods
- **Deliverable:** Can call `get_units(player_id=1)` and get player 1's units

### Phase 3: Coordinator + Agent Loop
- Build the turn-polling coordinator
- Integrate with Anthropic API for agent decision-making
- Define tool schemas for agent tool use
- Implement the sequential turn loop
- **Deliverable:** Two agents playing alternating turns in a single game

### Phase 4: Fairness + Polish
- Add visibility checks to puppet player queries
- Use local-player-switch for production/attacks (not cheats)
- Add game logging/replay for analysis
- Run test games and iterate on agent prompts
- **Deliverable:** Fair agent-vs-agent games with replay logs

---

## Open Questions

1. **Does `GameEvents.PlayerTurnStartComplete` fire fast enough?** The AI may start acting before our hook runs if there are multiple mods competing for the event. Testing needed.

2. **Does `PlayerManager.SetLocalPlayerAndObserver()` work in GameCore context?** It may be InGame-only. If so, need to use InGame context for the switch + command + restore sequence.

3. **Can we suppress AI city production/research decisions?** `FinishMoves` only blocks unit actions. The AI may still choose production and research during its turn. We may need to override those post-hoc with GameCore setters.

4. **What happens to AI diplomacy?** The built-in AI may still send delegation requests, declare friendships, or denounce during its turn processing. These happen at the C++ level and can't be intercepted from Lua.

5. **How many puppet players can we support?** In theory, all AI players. In practice, each puppet turn adds latency (polling + agent thinking + command execution). With 7 puppet players, turns could take minutes.

6. **Can we use `AutoplayManager` for Agent A too?** Instead of having Agent A play as the human, we could use AutoPlay for all players and puppet all of them. This would make both agents equally constrained. But AutoPlay hands control to the built-in AI, which defeats the purpose — we'd need to intercept ALL players.
