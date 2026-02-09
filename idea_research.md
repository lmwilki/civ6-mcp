# Civ 6 MCP Agent: Technical Architecture

## The Idea

Build an MCP server that allows an LLM agent (Claude, GPT-4, etc.) to play Civilization 6 — reading full game state each turn, reasoning about strategy, and issuing commands back into the game. No one has done this. Here's how it could work.

---

## The Core Problem

Civ 6 is a proprietary, closed-source game. Unlike Unciv or Freeciv (which researchers use because they're open-source), Civ 6 has:

- **No external API** — no HTTP endpoints, no sockets, no IPC mechanism
- **Sandboxed Lua** — `io`, `os`, `_G`, and `require` are all disabled in the mod Lua environment. You cannot open files, open sockets, or load external libraries from within a Lua mod.
- **Hardcoded AI** — the core AI decision-making loop is compiled C++ and cannot be replaced via mods
- **Limited unit control for AI players** — `UnitManager.RequestOperation()` only works for the local (human) player. Moving AI-controlled units requires workarounds via `UnitManager.MoveUnit()` (which only works one tile at a time and can't attack).

However, Civ 6 *does* expose:

- **Rich Lua read APIs** — comprehensive game state is readable via the Lua API (players, cities, units, tiles, diplomacy, resources, tech trees, etc.)
- **`print()` writes to Lua.log** — the only "output channel" from the Lua sandbox to the outside world
- **FireTuner** — Firaxis's debug companion app that connects to the running game and can execute arbitrary Lua in any context
- **Detailed log files** — the game writes CSV/log files for AI decisions, unit movements, barbarians, pathfinding, etc.
- **AutoPlay / Cheat Switch Civ** — existing mods that can hand control of the human player's civ to the AI and switch between civs programmatically
- **`ExposedMembers`** — a shared Lua table accessible across different Lua contexts (UI scripts and gameplay scripts), enabling inter-context communication

---

## Architecture: The File-Based Bridge

Since we can't open sockets from inside Civ 6's Lua sandbox, we use the filesystem as a communication bus. The Lua mod writes game state to a file; an external Python process reads it, calls the MCP server (which calls the LLM), and writes commands back; the Lua mod reads the commands and executes them.

```
┌─────────────────────────────────────────────────────┐
│                   Civ 6 Process                     │
│                                                     │
│  ┌─────────────┐    ┌──────────────────────────┐    │
│  │  Lua Mod    │───▶│  Lua.log / state.json     │───┼──▶ (filesystem)
│  │  (in-game)  │◀───│  commands.json            │◀──┼──
│  └─────────────┘    └──────────────────────────┘    │
│                                                     │
└─────────────────────────────────────────────────────┘
                          │ ▲
                          ▼ │
┌─────────────────────────────────────────────────────┐
│               Bridge Process (Python)               │
│                                                     │
│  ┌──────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │ File Watcher │──│ MCP Client  │──│ LLM Agent │  │
│  │ (watchdog)   │  │             │  │           │  │
│  └──────────────┘  └─────────────┘  └───────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
                          │ ▲
                          ▼ │
┌─────────────────────────────────────────────────────┐
│                MCP Server (Python)                   │
│                                                     │
│  Tools:                                             │
│  - get_game_state()     → full game snapshot        │
│  - get_unit_list()      → all units with positions  │
│  - get_city_list()      → all cities with yields    │
│  - move_unit(id, x, y)  → queue unit movement       │
│  - build_in_city(id, item) → queue production       │
│  - research_tech(tech)  → set research target       │
│  - end_turn()           → signal turn complete       │
│  - get_diplomacy_state()→ relationships & deals     │
│                                                     │
│  Resources:                                         │
│  - game://state         → current game state JSON   │
│  - game://map           → visible map data          │
│  - game://history       → turn-by-turn log          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Component 1: The Lua Mod (In-Game)

### What it does

1. **On each turn start** (`Events.PlayerTurnActivated`): serialise the full game state visible to the human player into a structured format and write it to Lua.log via `print()`.
2. **Poll for commands**: On a timer or event hook, check for a command file written by the bridge process. Since `io` is disabled, this requires a creative workaround (see below).
3. **Execute commands**: Parse incoming commands and execute them via the Lua API.

### The File I/O Problem and Workarounds

The biggest technical challenge: **Lua mods cannot read or write files**. Here are the viable workarounds, ranked by feasibility:

#### Option A: Log Output + FireTuner Input (Most Promising)

- **State OUT**: The mod uses `print()` to dump structured game state to `Lua.log`. The bridge process tails this file.
- **Commands IN**: The bridge process sends Lua commands to the game via **FireTuner's socket protocol**. FireTuner connects to Civ 6 over a local TCP connection and can execute arbitrary Lua. We'd need to reverse-engineer or replicate the FireTuner protocol — it's a .NET WinForms app, so decompiling it to understand the wire format is feasible.
- **Pros**: No file reading needed inside Lua. Full Lua API access for commands.
- **Cons**: Requires FireTuner to be running (disables achievements). Need to reverse-engineer the protocol.

#### Option B: Lua.log Output + Save File Manipulation

- **State OUT**: Same `print()` approach as Option A.
- **Commands IN**: Write commands into a save file or config file that the mod reads on reload. The `GameConfiguration` and `PlayerConfiguration` objects in Lua can read/write some custom values that persist across saves. Alternatively, abuse the `ModSettings` database.
- **Pros**: No external tool dependency.
- **Cons**: Requires save/reload cycles to inject commands — very slow loop.

#### Option C: ExposedMembers + UI Script File Watching

- **State OUT**: Gameplay script writes state to `ExposedMembers` table. UI script reads it (UI scripts have slightly different sandbox rules).
- **Commands IN**: A UI script could potentially use `Network` or `ContentManager` functions to check for external state changes. The `UI.PlaySound()` trick has been used to trigger side effects.
- **Pros**: Stays entirely within the game.
- **Cons**: Very hacky, fragile, and the UI sandbox is still restricted.

**Recommendation: Option A** — the FireTuner protocol is the most reliable bidirectional channel.

### Game State Serialisation

The mod would extract and serialise via `print()`:

```lua
-- Example: extracting player state
function SerializeGameState()
    local state = {}
    state.turn = Game.GetCurrentGameTurn()
    state.player = {}

    local pPlayer = Players[Game.GetLocalPlayer()]
    state.player.gold = pPlayer:GetTreasury():GetGoldBalance()
    state.player.science = pPlayer:GetTechs():GetScienceYield()
    state.player.culture = pPlayer:GetCulture():GetCultureYield()

    -- Cities
    state.cities = {}
    local pCities = pPlayer:GetCities()
    for i, pCity in pCities:Members() do
        local city = {}
        city.name = pCity:GetName()
        city.x = pCity:GetX()
        city.y = pCity:GetY()
        city.population = pCity:GetPopulation()
        city.production = pCity:GetBuildQueue():CurrentlyBuilding()
        -- ... yields, districts, buildings, etc.
        table.insert(state.cities, city)
    end

    -- Units
    state.units = {}
    local pUnits = pPlayer:GetUnits()
    for i, pUnit in pUnits:Members() do
        local unit = {}
        unit.id = pUnit:GetID()
        unit.type = UnitManager.GetTypeName(pUnit)
        unit.x = pUnit:GetX()
        unit.y = pUnit:GetY()
        unit.moves = pUnit:GetMovesRemaining()
        unit.health = pUnit:GetMaxDamage() - pUnit:GetDamage()
        table.insert(state.units, unit)
    end

    -- Serialise to a parseable format
    -- (Lua doesn't have JSON built in, but we can write a simple serialiser)
    print("===MCP_STATE_BEGIN===")
    print(TableToJSON(state))
    print("===MCP_STATE_END===")
end

Events.PlayerTurnActivated.Add(function(playerID, isFirstTime)
    if playerID == Game.GetLocalPlayer() then
        SerializeGameState()
    end
end)
```

### Key Lua API Objects Available for Reading

| Category | Objects | Data Available |
|----------|---------|----------------|
| **Game** | `Game.GetCurrentGameTurn()`, `Game.GetEras()` | Turn number, era, victory progress |
| **Player** | `Players[id]:GetTreasury()`, `:GetTechs()`, `:GetCulture()` | Gold, science, culture, faith, era score |
| **Cities** | `PlayerCities:Members()`, `City:GetBuildQueue()` | Population, yields, districts, buildings, production queue |
| **Units** | `PlayerUnits:Members()`, `Unit:GetMovesRemaining()` | Type, position, health, moves, promotions |
| **Diplomacy** | `Players[id]:GetDiplomacy()` | Relationships, war/peace, alliances, grievances |
| **Map** | `Map.GetPlot(x,y)`, `Plot:GetTerrainType()` | Terrain, features, resources, improvements, visibility |
| **AI Info** | `Players[id]:GetAi_Military()`, `:GetAi_Religion()` | Military threat assessment, strategic rivals |

### Executing Commands

For the **local (human) player**, the Lua API provides:

```lua
-- Move a unit (works reliably for local player)
UnitManager.RequestOperation(pUnit, UnitOperationTypes.MOVE_TO, {
    [UnitOperationTypes.PARAM_X] = targetX,
    [UnitOperationTypes.PARAM_Y] = targetY
})

-- Attack with a unit
UnitManager.RequestOperation(pUnit, UnitOperationTypes.RANGE_ATTACK, {
    [UnitOperationTypes.PARAM_X] = targetX,
    [UnitOperationTypes.PARAM_Y] = targetY
})

-- Set city production
local pBuildQueue = pCity:GetBuildQueue()
pBuildQueue:CreateIncompleteBuilding(GameInfo.Buildings["BUILDING_LIBRARY"].Index)

-- Set research
local pTechs = pPlayer:GetTechs()
-- (Research is typically set via UI operations)
UI.RequestPlayerOperation(playerID, PlayerOperations.RESEARCH, {
    [PlayerOperations.PARAM_TECH_TYPE] = GameInfo.Technologies["TECH_WRITING"].Index
})

-- Diplomacy
-- (Limited — some actions require UI.RequestPlayerOperation)
```

**Key limitation**: `UnitManager.RequestOperation()` and `UI.RequestPlayerOperation()` only work for the **local player**. This is fine — we're controlling the human player's civ, not replacing the AI for other civs.

---

## Component 2: The Bridge Process (Python)

A Python process running alongside the game that:

1. **Tails `Lua.log`** for state dumps (between `===MCP_STATE_BEGIN===` and `===MCP_STATE_END===` markers)
2. **Parses the JSON** game state
3. **Exposes it via the MCP server** as tools and resources
4. **Receives LLM decisions** from the MCP server
5. **Translates decisions into Lua commands**
6. **Sends commands to the game** via the FireTuner protocol (or writes to a command file)

```python
# Simplified bridge process
import json
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileModifiedHandler

CIV6_LOG = Path.home() / "Documents/My Games/Sid Meier's Civilization VI/Logs/Lua.log"

class GameStateWatcher(FileModifiedHandler):
    def __init__(self):
        self.current_state = None
        self.buffer = []
        self.capturing = False

    def on_modified(self, event):
        if event.src_path == str(CIV6_LOG):
            # Read new lines, extract state between markers
            with open(CIV6_LOG) as f:
                for line in self._new_lines(f):
                    if "===MCP_STATE_BEGIN===" in line:
                        self.capturing = True
                        self.buffer = []
                    elif "===MCP_STATE_END===" in line:
                        self.capturing = False
                        self.current_state = json.loads("".join(self.buffer))
                        self._notify_mcp_server()
                    elif self.capturing:
                        self.buffer.append(line)
```

---

## Component 3: The MCP Server

A standard MCP server (Python, using the `mcp` SDK) that exposes Civ 6 game state and actions as tools.

### Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_game_state` | Full snapshot of current game state | None |
| `get_visible_map` | Map tiles visible to the player | `center_x`, `center_y`, `radius` |
| `list_units` | All player units with details | `filter_type` (optional) |
| `list_cities` | All player cities with yields and production | None |
| `move_unit` | Move a unit to a target tile | `unit_id`, `target_x`, `target_y` |
| `attack_unit` | Attack with a unit | `unit_id`, `target_x`, `target_y` |
| `set_city_production` | Set what a city is building | `city_id`, `item_type`, `item_name` |
| `set_research` | Set current tech research | `tech_name` |
| `set_civic` | Set current civic research | `civic_name` |
| `end_turn` | End the current turn | None |
| `get_possible_actions` | List valid actions for a unit/city | `entity_id`, `entity_type` |
| `get_diplomacy` | Current diplomatic relationships | None |
| `propose_deal` | Propose a trade deal | `target_player`, `offer`, `demand` |

### Resources

| Resource URI | Description |
|-------------|-------------|
| `game://state/current` | Current game state JSON |
| `game://map/full` | Full visible map data |
| `game://history/turns` | History of all turns played |
| `game://tech_tree` | Full tech tree with research status |
| `game://civic_tree` | Full civic tree with status |

### Prompts

| Prompt | Description |
|--------|-------------|
| `analyze_situation` | Analyse current game state and suggest strategy |
| `plan_turn` | Generate a full turn plan (all moves, production, research) |
| `evaluate_war` | Assess military situation and recommend war/peace |
| `city_planning` | Recommend district and building priorities |

---

## Development Roadmap

### Phase 1: Read-Only Proof of Concept (2-3 weeks)

1. Build the Lua mod that serialises game state to `Lua.log`
2. Build the Python bridge that tails the log and parses state
3. Build a basic MCP server with read-only tools (`get_game_state`, `list_units`, etc.)
4. Connect to Claude and verify it can reason about the game state
5. **Milestone**: Claude can describe what's happening in your Civ 6 game in real-time

### Phase 2: Command Injection via FireTuner (2-4 weeks)

1. Reverse-engineer the FireTuner TCP protocol (decompile the .NET app)
2. Build a Python FireTuner client that can send Lua commands
3. Add action tools to the MCP server (`move_unit`, `set_production`, etc.)
4. Build the command translation layer (MCP tool calls → Lua commands)
5. **Milestone**: Claude can move a unit when asked

### Phase 3: Autonomous Play Loop (2-4 weeks)

1. Implement the full turn loop (state → LLM reasoning → actions → end turn)
2. Add the `plan_turn` prompt that generates a complete turn plan
3. Handle edge cases (combat, diplomacy popups, city state interactions)
4. Add turn history and strategic memory
5. **Milestone**: Claude plays a full game of Civ 6 autonomously

### Phase 4: Polish and Share (1-2 weeks)

1. Package as an installable mod + pip package
2. Documentation and setup guide
3. Add support for multiple MCP clients (not just Claude)
4. Performance optimisation (game state compression, incremental updates)

---

## Key Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **FireTuner protocol is undocumented** | Can't send commands to game | Decompile .NET app; fallback to AutoHotKey input simulation |
| **Lua.log output is too slow** | Laggy turn loop | Use structured markers; only serialise delta between turns |
| **Game state too large for LLM context** | LLM can't process full state | Implement hierarchical summarisation (overview → detail on demand) |
| **`UnitManager.RequestOperation` limitations** | Can't execute all actions | Supplement with `UI.RequestPlayerOperation` and `UnitManager.MoveUnit` workarounds |
| **Game patches break Lua API** | Mod stops working | Pin to a specific game version; abstract API calls behind a compatibility layer |
| **LLM makes bad strategic decisions** | Loses every game | Start on Settler difficulty; add strategy guides as system prompts |
| **Turn processing time** | LLM takes 30s+ per turn | Acceptable for Civ (it's turn-based); add "thinking" indicator in-game UI |

---

## Alternative: The Screen-Reading Fallback

If the FireTuner approach proves too difficult, there's a fallback inspired by the KG-Agent paper (which played Civ V via pure screen reading):

1. Take screenshots each turn using Python (`pyautogui` / `mss`)
2. Send screenshots to a vision-capable LLM
3. LLM outputs keyboard/mouse commands
4. Execute commands via `pyautogui`

This is significantly more fragile and slower, but requires zero modding. It's worth keeping as a Plan B.

---

## Prior Art Summary

| Project | Game | Approach | Status |
|---------|------|----------|--------|
| **CivAgent** (Netease Fuxi) | Unciv (open source) | HTTP API between game and LLM | Active research |
| **CivRealm** (BIGAI) | Freeciv-web (open source) | Python API + Gymnasium interface | Published at ICLR 2024 |
| **KG-Agent** | Civ V (proprietary) | Screen pixels + keyboard/mouse | Recent paper |
| **Sentinel SIEM** | Civ 6 | Read-only log ingestion into Azure | Blog post / demo |
| **This project** | **Civ 6** | **Lua mod + FireTuner + MCP** | **Proposed** |

---

## What Makes This Interesting

1. **First MCP integration with any strategy game** — novel contribution to the MCP ecosystem
2. **First external LLM agent for Civ 6** — researchers have avoided Civ 6 due to its closed nature
3. **Natural language strategy** — unlike RL agents, an LLM agent can explain its reasoning and discuss strategy with the player
4. **Co-play mode** — the agent doesn't have to play alone; it could act as an advisor, executing only the actions the player approves
5. **Transferable pattern** — the Lua.log + FireTuner bridge pattern could work for other Firaxis games (Civ 7 uses the same engine and tooling)
