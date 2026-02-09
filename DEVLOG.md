# Civ 6 MCP — Development Log

## 2025-02-08: Research Spike — FireTuner Protocol

### Goal

Determine whether we can programmatically communicate with Civ 6 on macOS to read game state and send commands. This is the critical-path risk for the entire project.

### Findings

#### 1. macOS File Paths

| What | Path |
|------|------|
| Config + Logs | `~/Library/Application Support/Sid Meier's Civilization VI/Firaxis Games/Sid Meier's Civilization VI/` |
| Save Games | `~/Library/Application Support/Sid Meier's Civilization VI/Sid Meier's Civilization VI/Saves/` |
| Custom Mods | `~/Library/Application Support/Sid Meier's Civilization VI/Sid Meier's Civilization VI/Mods/` |
| Game Install | `~/Library/Application Support/Steam/steamapps/common/Sid Meier's Civilization VI/Civ6.app/` |
| Debug/Tuner | `.../Civ6.app/Contents/Assets/Debug/` |
| Tuner Lua Scripts | `.../Civ6.app/Contents/Assets/Base/Assets/UI/Tuner/` |
| Log Files (70+) | `.../Firaxis Games/Sid Meier's Civilization VI/Logs/` |

#### 2. FireTuner Infrastructure on macOS

The game ships with full **server-side** tuner infrastructure despite Aspyr removing the client GUI:

- **`Civ6TunerPlugin.dll`** — .NET assembly, the game-side plugin (loaded via Mono)
- **35 `.ltp` panel files** — XML definitions for FireTuner UI panels containing embedded Lua
- **12 `TunerXxxPanel.lua` scripts** — game-side Lua for each panel
- **`TunerUtilities.lua`** — UI control tree inspector

The `EnableTuner` toggle was removed from the macOS options UI by Aspyr, but the `AppOptions.txt` setting still works. We set `EnableTuner 1`.

#### 3. FireTuner Wire Protocol (Confirmed)

The protocol was independently reverse-engineered by two projects:
- [sourcehut civ-firetuner-client](https://git.sr.ht/~max1truc/civ-firetuner-client) — clean asyncio implementation
- [Archipelago civilization_vi_apworld](https://github.com/hesto2/civilization_vi_apworld) — production-tested with Civ 6

**Wire format:**
```
[4 bytes: payload_length, little-endian uint32]
[4 bytes: tag, little-endian int32]
[N bytes: null-terminated payload string]
```

**Tags and command prefixes:**

| Tag | Prefix | Direction | Purpose |
|-----|--------|-----------|---------|
| 4 | `APP:` | Client -> Game | Request game identity |
| 4 | `LSQ:` | Client -> Game | List all Lua states |
| 3 | `CMD:N:code` | Client -> Game | Execute Lua in state N |
| 1 | `HELP:N:prefix` | Client -> Game | Autocomplete |
| — | `ERR:` | Game -> Client | Lua error + stacktrace |
| — | `O` | Game -> Client | Unsolicited debug output |

**Handshake:**
1. TCP connect to `127.0.0.1:4318`
2. Send `APP:\x00` with tag=4 — receive game identity ("Civ6" + install path)
3. Send `LSQ:\x00` with tag=4 — receive numbered list of ~31 Lua states
4. Ready to send `CMD:N:lua_code\x00` with tag=3

**Port: 4318** (not 15555 as Civ 5 community suggested). Game is TCP server, our client connects to it.

#### 4. Two Lua Execution Contexts

The game runs two Lua VMs accessible via tuner:

| Context | `CompatibleStates` | Access Level |
|---------|--------------------|-------------|
| **GameCore** | `GameCore_Tuner` | Full simulation read/write — `Players[]`, `Game`, `Map`, `GameInfo` |
| **UI** | `InGame`, `TunerMapPanel`, etc. | Display layer — `UI`, builders (`UnitManager`, `ResourceBuilder`, etc.) |

For our MCP server, **GameCore** context gives us everything: player resources, unit positions, city data, tech/civic trees, diplomacy. The **UI** context gives us `UnitManager.RequestOperation()` for commanding units.

#### 5. Lua API Surface (from .ltp analysis)

**Reading (GameCore context):**
- `Players[id]:GetTreasury():GetGoldBalance()` — gold
- `Players[id]:GetTechs()` — tech tree, research progress
- `Players[id]:GetCulture()` — civics, cultural progress
- `Players[id]:GetCities():Members()` — all cities, yields, build queues
- `Players[id]:GetUnits():Members()` — all units, positions, health, moves
- `Players[id]:GetDiplomacy()` — relationships, war/peace
- `Map.GetPlot(x,y)` — terrain, features, resources, improvements

**Writing (GameCore context via tuner):**
- `Players[id]:GetTreasury():ChangeGoldBalance(n)` / `SetGoldBalance(n)`
- `Players[id]:GetTechs():SetResearchProgress(techIdx, cost)` — grant tech
- `Players[id]:GetCulture():SetCivic(idx, bool)` — grant civic
- `Players[id]:GetUnits():Create(unitType, x, y)` — spawn unit
- `Players[id]:GetCities():Create(x, y)` — found city

**Writing (UI context):**
- `UnitManager.RequestOperation(unit, op, params)` — move/attack/etc. (local player only)
- `UI.RequestPlayerOperation(playerID, op, params)` — research, civic, diplomacy

#### 6. Civ6TunerPlugin.dll Internals

Decompiled via `monodis`. Key findings:
- Depends on `NexusConnection.dll` and `FireTuner3Panel.dll` (ship with Windows SDK, not macOS)
- 3 panel classes: `AudioPanel`, `ConsolePanel`, `GraphicsPanel`
- `ConsolePanel` is the key class — has `OnConsoleOutput` (NexusMessage handler) and `SendMessage` (sends Lua to game)
- `[NexusMessage]` attribute marks methods called when game sends data to client
- The method name IS the message name, parameters define the payload

### Connection Test Results (macOS, Main Menu)

Ran `scripts/test_connection.py` with Civ 6 at the main menu:

```
1. TCP connect to 127.0.0.1:4318 — SUCCESS
2. APP: handshake — "Civ6 Sid Meier's Civilization 6 C:\Emu\AppAssets\Base\Binaries\Debug"
3. LSQ: — 31 Lua states returned (numbered 0-30)
4. CMD:0:print('hello from civ-mcp') — SUCCESS, response: "O hello from civ-mcp"
5. CMD:0:return tostring(Game.GetCurrentGameTurn()) — ERR (expected: Game is nil at main menu)
```

**Lua states at main menu** (31 states, alternating index/name pairs in response):
`Main State`, `DebugHotloadCache`, `Options`, `CreditsScreen`, `My2K`, `LoadGameMenu`,
`PBCNotifyRemind`, `Lobby`, `Mods`, `LoadGameMenu`, `SaveGameMenu`, `MultiSelectWindow`,
`CityStatePicker`, `LeaderPicker`, `HostGame`, `ConfirmKick`, `EditHotseatPlayer`,
`StagingRoom`, `LoadGameMenu`, `SaveGameMenu`, `FrontEndPopup`, `CivRoyaleIntro`,
`PiratesIntro`, `CrossPlayLogin`, `MainMenu`, `StateTransition`, `JoiningRoom`,
`UserSetupWarning`, `SwitchLayoutPopup`, `Test`, `FrontEnd`

**Key observations:**
- LSQ response format: alternating lines of `[number]` then `[state_name]`. The number is the state index to use in `CMD:N:`.
- `print()` output comes back with `O ` prefix (the "Output" message type)
- Errors come back with `ERR:` prefix and full Lua stacktrace
- `Game` object is only available in-game states (`InGame`, `GameCore_Tuner`)
- The game identity path says `C:\Emu\AppAssets\...` — this is the Wine/CrossOver emulation path used by Aspyr's macOS port

### In-Game State Reading (Turn 1)

Loaded a game (England/Victoria vs Australia, Gran Colombia, Aztec) and queried `GameCore_Tuner` (state index `8`):

```
Turn: 1 | Player: 0 (England, Victoria Age of Empire) | Gold: 10

Units:
  65536  | Settler  | 56,21 | moves: 2
  131073 | Warrior  | 55,21 | moves: 2
  196610 | Builder  | 55,21 | moves: 2
  262147 | Scout    | 56,22 | moves: 3

Opponents:
  1 | Australia    | John Curtin
  2 | Gran Colombia | Simón Bolívar
  3 | Aztec        | Montezuma
```

**Key protocol details learned:**
- `return` statements produce empty responses — must use `print()` for output
- `print()` output comes back as `O GameCore_Tuner: <value>` (context name is prepended)
- State index `8` is `GameCore_Tuner` when in-game (index may shift with mods/DLC loaded)
- Unit IDs are large (65536, 131073, etc.) — these are composite IDs encoding player + unit index
- `Locale.Lookup()` resolves localized strings (unit names, civ names, leader names)
- `PlayerConfigurations[i]` gives civ/leader info; `Players[i]` gives gameplay state
- Map queries work: `Map.GetPlot(x,y)` returns terrain, features, resources

### Write Path: Founded a City (Turn 1)

Successfully founded London at 56,21 using `UnitManager.RequestOperation` from the `InGame` context (state 153):

```lua
-- Must run in InGame context (state 153), NOT GameCore
local pUnit = UnitManager.GetUnit(0, 0)  -- playerID=0, unitIndex=0
local tParameters = {}
tParameters[UnitOperationTypes.PARAM_X] = 56
tParameters[UnitOperationTypes.PARAM_Y] = 21
UnitManager.RequestOperation(pUnit, UnitOperationTypes.FOUND_CITY, tParameters)
```

**Key findings:**
- `UnitManager.RequestOperation` is in the **InGame/UI** context, not GameCore
- `UnitManager.GetUnit(playerID, unitIndex)` retrieves a unit (separate from the composite ID)
- After founding, the settler moves to `-9999,-9999` (consumed, disappears next turn)
- `UnitManager.CanStartOperation(unit, op, nil, true)` checks if an operation is valid
- Unsolicited debug output (`TETHYS OCEAN ...` coordinate dumps) comes through after map-changing operations

**City state after founding:**
```
London | 56,21 | pop:1 | housing:6 | amenities:2
food:4 | production:5 | gold:5 | science:2.5 | culture:1.3 | faith:0
food surplus:2 | turns to grow:8
Can build: UNIT_SETTLER, BUILDING_MONUMENT, DISTRICT_CITY_CENTER
```

### UI Popup Dismissal

Founding a city triggers popups (Historic Moments, Boost Unlocked, etc.) that cover the screen. These can be dismissed programmatically:

```lua
-- Each popup Lua context has an OnClose() global function
-- Call it from the popup's own state index
-- e.g. for HistoricMoments (state 137):
OnClose()  -- CMD:137:OnClose()

-- Fallback: force-hide via ContextPtr
ContextPtr:SetHide(true)
```

**To detect visible popups**, check `ContextPtr:IsHidden()` in each popup state. Popup-like states include: `EraCompletePopup`, `NaturalWonderPopup`, `WonderBuiltPopup`, `BoostUnlockedPopup`, `TechCivicCompletedPopup`, `EventPopup`, `InGamePopup`, `DedicationPopup`, etc. `NewTurnPanel` being visible is normal (it's the HUD).

### Game State API Reference

**Two execution contexts:**

| Context | State index | API available | Use for |
|---------|------------|---------------|---------|
| `GameCore_Tuner` | `8` | `Players[]`, `Game`, `Map`, `GameInfo`, `Locale` | Reading all game state |
| `InGame` | `153` | `UnitManager`, `UI`, `UIManager`, `Input`, `LuaEvents`, `ContextPtr` | Issuing commands, UI interaction |

State indexes may vary with mods/DLC loaded. Always use `LSQ:` to discover them.

**Reading state (GameCore_Tuner, state 8):**

| What | Lua | Notes |
|------|-----|-------|
| Turn number | `Game.GetCurrentGameTurn()` | |
| Local player ID | `Game.GetLocalPlayer()` | Usually 0 |
| Gold balance | `Players[id]:GetTreasury():GetGoldBalance()` | |
| Gold yield/expense | `:GetGoldYield()` / `:GetTotalMaintenance()` | |
| Science yield | `Players[id]:GetTechs():GetScienceYield()` | |
| Current research | `Players[id]:GetTechs():GetResearchingTech()` | -1 if none |
| Culture yield | `Players[id]:GetCulture():GetCultureYield()` | |
| Current civic | `Players[id]:GetCulture():GetProgressingCivic()` | |
| Faith balance | `Players[id]:GetReligion():GetFaithBalance()` | |
| Unit iteration | `Players[id]:GetUnits():Members()` | Returns iterator |
| Unit by ID | `Players[id]:GetUnits():FindID(unitID)` | |
| Unit type | `GameInfo.Units[unit:GetType()].UnitType` | e.g. `UNIT_SETTLER` (GameCore uses `GetType()`, not `GetUnitType()`) |
| Unit name | `Locale.Lookup(unit:GetName())` | Localized |
| Unit position | `unit:GetX(), unit:GetY()` | |
| Unit HP | `unit:GetMaxDamage() - unit:GetDamage()` | Max is typically 100 |
| Unit moves | `unit:GetMovesRemaining()` / `unit:GetMaxMoves()` | |
| City iteration | `Players[id]:GetCities():Members()` | |
| City by ID | `Players[id]:GetCities():FindID(cityID)` | |
| City yields | `city:GetYield(0..5)` | 0=food, 1=prod, 2=gold, 3=sci, 4=cul, 5=faith |
| City population | `city:GetPopulation()` | |
| City growth | `city:GetGrowth():GetTurnsUntilGrowth()` | |
| City housing | `city:GetGrowth():GetHousing()` | |
| City amenities | `city:GetGrowth():GetAmenities()` | |
| City production | `city:GetBuildQueue():CurrentlyBuilding()` | |
| Can produce | `city:GetBuildQueue():CanProduce(itemIndex, true)` | In InGame context |
| Map tile | `Map.GetPlot(x, y)` | |
| Terrain | `GameInfo.Terrains[plot:GetTerrainType()].TerrainType` | e.g. `TERRAIN_GRASS` |
| Feature | `GameInfo.Features[plot:GetFeatureType()].FeatureType` | e.g. `FEATURE_JUNGLE` |
| Resource | `GameInfo.Resources[plot:GetResourceType()].ResourceType` | |
| Hills? | `plot:IsHills()` | |
| River? | `plot:IsRiver()` | |
| Fresh water? | `plot:IsFreshWater()` | |
| Coastal? | `plot:IsCoastalLand()` | |
| Tile yields | `plot:GetYield(0..5)` | Same index as city yields |
| Player is alive | `Players[id]:IsAlive()` | |
| Player is major | `Players[id]:IsMajor()` | false for city-states |
| Civ name | `Locale.Lookup(PlayerConfigurations[id]:GetCivilizationShortDescription())` | |
| Leader name | `Locale.Lookup(PlayerConfigurations[id]:GetLeaderName())` | |
| Has met | `Players[id]:GetDiplomacy():HasMet(otherID)` | |
| At war | `Players[id]:GetDiplomacy():IsAtWarWith(otherID)` | |
| Map dimensions | `Map.GetGridSize()` | Returns single number (width?) |

**Writing/commanding (InGame, state 153):**

| What | Lua |
|------|-----|
| Get unit ref | `UnitManager.GetUnit(playerID, unitIndex)` |
| Check operation | `UnitManager.CanStartOperation(unit, op, nil, true)` |
| Request operation | `UnitManager.RequestOperation(unit, op, {PARAM_X=x, PARAM_Y=y})` |
| Found city | `UnitManager.RequestOperation(unit, UnitOperationTypes.FOUND_CITY, params)` |
| Move unit | `UnitManager.RequestOperation(unit, UnitOperationTypes.MOVE_TO, params)` |
| Attack | `UnitManager.RequestOperation(unit, UnitOperationTypes.RANGE_ATTACK, params)` |
| Set research | `UI.RequestPlayerOperation(playerID, PlayerOperations.RESEARCH, {PARAM_TECH_TYPE=idx})` |

### Map Data (Around Settler Start, 56,21)

```
54,19 PLAINS_HILLS  jungle          | 55,19 GRASS_HILLS                  | 56,19 GRASS     stone    coastal
54,20 PLAINS        floodplains     | 55,20 GRASS     floodplains maize  | 56,20 GRASS_HILLS stone
54,21 PLAINS        floodplains     | 55,21 GRASS     floodplains river  | 56,21 GRASS     floodplains river coastal [LONDON]
54,22 PLAINS                        | 55,22 GRASS     floodplains river  | 56,22 GRASS     floodplains river coastal
54,23 PLAINS        jungle   amber  | 55,23 GRASS     forest    coastal  | 56,23 COAST     pearls
```

River, floodplains, coastal, maize, stone, pearls — a solid city location.

### Diplomacy (Turn 1)

| ID | Civ | Leader | Met? |
|----|-----|--------|------|
| 0 | England | Victoria (Age of Empire) | — |
| 1 | Australia | John Curtin | No |
| 2 | Gran Colombia | Simón Bolívar | No |
| 3 | Aztec | Montezuma | No |

**City-States:** Valletta (4), Mitla (5), Lahore (6), Akkad (7), Venice (8), Brussels (9). Free Cities (62).

### Status

- **Full read+write loop confirmed working on macOS**
- Can read: units, cities, map, yields, diplomacy, tech, civics, game info
- Can write: found cities, (move/attack untested but API confirmed)
- Can dismiss UI popups programmatically
- **Next: build the MCP server exposing these capabilities as tools**

---

## 2026-02-08: MCP Server MVP Complete

### Architecture

Built a 5-layer architecture with clean separation of concerns:

```
Claude / MCP Client
    │  stdio (JSON-RPC)
    ▼
server.py         ← 12 MCP tools (FastMCP + lifespan pattern)
    │
game_state.py     ← Business logic + narration (ZERO MCP dependency)
    │
connection.py     ← Persistent TCP connection, lock, state discovery
    │
tuner_client.py   ← Wire protocol (unchanged from spike)
    │
lua_queries.py    ← Lua code builders + response parsers + dataclasses
```

Key design decision: `game_state.py` has no MCP dependency, enabling future multi-agent architectures where specialist servers (military, economic, diplomatic) import the same `GameState` class but expose different tool subsets.

### 12 Tools

**Query (read-only, 6 tools):**
- `get_game_overview` — turn, yields, research, civic, city/unit counts
- `get_units` — all units with position, type, moves, health
- `get_cities` — all cities with yields, population, production, growth
- `get_map_area(x, y, radius)` — terrain, features, resources, improvements
- `get_diplomacy` — known civs, met status, war status
- `get_tech_civics` — current research/civic, turns remaining, available options

**Action (mutating, 4 tools):**
- `execute_unit_action(unit_id, action, target_x, target_y)` — move/attack/fortify/skip/found_city
- `set_city_production(city_id, item_type, item_name)` — queue units/buildings/districts
- `set_research(tech_or_civic, category)` — choose tech or civic
- `end_turn` — end the current turn

**Utility (2 tools):**
- `dismiss_popup` — scan and dismiss blocking UI popups
- `execute_lua(code, context)` — escape hatch for arbitrary Lua

### Bugs Fixed During Implementation

1. **`GetUnitType()` doesn't exist in GameCore context** — must use `GetType()` instead. `GameInfo.Units[u:GetType()]` then gives the `.UnitType` string.
2. **Consumed units crash iteration** — units at position (-9999,-9999) return nil from `GetType()`. Fixed by checking position BEFORE accessing type.
3. **`GetCulturalProgress()` doesn't exist in GameCore** — replaced with `GetTurnsLeftOnCurrentCivic()`.
4. **Cities parser off-by-one** — expected 15 fields but output has 14. Fixed field count check.
5. **FastMCP API differences** — no `description` param (use `instructions`), no `tags` on tools.

### Server-Side Narration

All tools return human-readable text, not raw JSON. Example `get_game_overview` output:
```
Turn 1 | England (Victoria (Age of Empire))
Gold: 10 (+5/turn) | Science: 2.5 | Culture: 1.3 | Faith: 0
Research: None | Civic: Code of Laws
Cities: 1 | Units: 4
```

### Configuration

`.mcp.json` in project root for Claude Code:
```json
{
  "mcpServers": {
    "civ6": {
      "command": "uv",
      "args": ["run", "--directory", "/Users/liam/Code/civ-mcp", "civ-mcp"]
    }
  }
}
```

### Status

- All 12 tools implemented and tested against live game
- All 6 query tools verified working with correct narration
- Action tools implemented (need live testing with MCP client)
- **Next: test with Claude Code as MCP client**

---

## 2026-02-08: First Playtest — Bugs & Design Reflections

### What happened

Attempted to play Turn 1 as England through the MCP tools. Got a full read of the game state (overview, units, cities, map, diplomacy, tech/civics) — all 6 query tools worked perfectly through the MCP protocol. Then tried to act on what I saw.

### Bugs Found

**1. `from __future__ import annotations` breaks FastMCP context injection**

FastMCP uses runtime type inspection to detect `Context`-typed parameters and auto-inject them. The `from __future__ import annotations` import makes all annotations lazy strings, so FastMCP couldn't detect `ctx: Context` and treated it as a regular parameter. Fix: removed the future import, used `typing.Optional` instead of `X | None`.

**2. Unit ID → player/index extraction is wrong (CRITICAL)**

The `execute_unit_action` tool extracted player_id and unit_index from the composite unit ID using `unit_id >> 16` and `unit_id & 0xFFFF`. This is **wrong** — unit IDs are sequential game-wide entity IDs, not player-encoded. For player 0's units (IDs 65536, 131073, 196610, 262147), `uid >> 16` gives 1, 2, 3, 4 — which are OTHER players' IDs. This meant move commands silently moved **opponent units** instead of our own.

The `uid % 65536` trick does give the correct per-player index (0, 1, 2, 3), but there's no player ID encoded in the composite ID at all.

**Fix needed:** Action Lua builders should determine the player ID themselves via `Game.GetLocalPlayer()` in Lua, not accept it from Python. The tool should only need the unit index (which is already shown in `get_units` output as `idx`).

**3. `set_city_production` routes to wrong Lua context**

The tool called `execute_write()` (InGame context) but used `bq:CreateIncompleteBuilding()` which only exists in GameCore context. The InGame build queue has no `Create*` methods.

But even worse: `CreateIncompleteBuilding` is a **debug/cheat function** — it completes the building instantly. It gave London a free Monument on Turn 1.

**Fix needed:** Production must use `CityManager.RequestOperation(pCity, CityOperationTypes.BUILD, params)` in InGame context. Key details:
- Use `.Hash` not `.Index` for item references
- PARAM key varies by type: `PARAM_UNIT_TYPE`, `PARAM_BUILDING_TYPE`, `PARAM_DISTRICT_TYPE`
- `PARAM_INSERT_MODE = VALUE_EXCLUSIVE` replaces current production
- Get city via `CityManager.GetCity(playerID, cityIndex)` where cityIndex = `cityID % 65536`

### Design Reflections

**GameCore vs InGame is the central API challenge.** Every action needs careful routing:
- GameCore has full read access but its write methods are debug cheats (instant effects, no validation)
- InGame has the proper game-rule-respecting API (`UnitManager.RequestOperation`, `CityManager.RequestOperation`, `UI.RequestPlayerOperation`) but lacks some read methods

The rule of thumb: **read from GameCore, write through InGame**. But even this isn't clean — `CanProduce` works in InGame but throws "Not Implemented" in GameCore.

**The cheat problem is real and needs architectural attention.** The GameCore context exposes debug functions that bypass game rules entirely: instant buildings, free techs, spawning units, setting gold. An agent with `execute_lua` access to GameCore can trivially cheat. This is fine for us debugging, but player-facing agents must NOT have raw Lua access. The `execute_lua` tool should be developer-only. The proper action tools (move, produce, research, end turn) that go through InGame context are safe — they respect the same game rules as a human player clicking the UI.

**Unit identification needs rethinking.** Showing both `id` and `idx` in unit output is confusing. The composite `id` is only useful internally; agents should work with `idx` (per-player index) which is what `UnitManager.GetUnit(playerID, unitIndex)` expects. Consider dropping the composite ID from narration entirely, or making the tool accept `idx` directly.

**The civics list is too long.** Without `CanProgress()` in GameCore, we list all unresearched civics (60+). An agent doesn't need to see Nuclear Program on Turn 1. Options:
- Filter by era (only show current + next era)
- Run `CanProgress` in InGame context instead
- Accept the noise and trust the agent to focus on relevant options

**Production setting is a two-step dance.** You need to know what's available before you can queue it. Currently there's no "list available production" tool — agents have to guess item names. Should either:
- Fold available production into `get_cities` output (might be verbose)
- Keep `list_city_production` as a separate query tool
- Just document common items in tool descriptions

### Immediate Fixes Needed

1. **Action builders:** Use `Game.GetLocalPlayer()` in Lua, accept only `unit_index` not `player_id`
2. **Production tool:** Rewrite to use `CityManager.RequestOperation` in InGame context
3. **Tool API:** Accept `unit_index` (from `idx` in output) directly, not composite ID
4. **execute_lua:** Keep for development, but flag as debug-only — not for player agents

### Status

- Query tools: all 6 working through MCP
- Action tools: `set_research` works, unit moves work (with correct player), production and unit ID routing need fixes
- **Next: fix action tools, then resume playtest**

---

## 2026-02-08: Second Playtest — Fixes Validated, New Issues Found

### Fixes Applied & Verified

All three critical bugs from the first playtest were fixed and verified working:

1. **Unit actions use `Game.GetLocalPlayer()`** — Warrior moved from (55,21) to (54,21), Builder to (55,20). Positions confirmed via `get_units`. No more silent opponent-unit moves.
2. **Production uses `CityManager.RequestOperation`** — Successfully queued Slinger, then switched to Warrior. Verified via `get_cities` showing "Building: UNIT_WARRIOR". No instant cheat.
3. **`execute_lua` now supports numeric state indices** — `context="42"` routes to state 42 via `execute_in_state`. Needed for popup dismissal.

### Playtest Progress

Played Turn 1 → Turn 2 as England:
- Set Pottery research, queued Warrior in London
- Moved Warrior west to explore, Builder onto Maize at (55,20)
- Scout explored south to (54,23) — discovered a Natural Wonder
- Builder improvements work via `UnitOperationTypes.BUILD_IMPROVEMENT` with `PARAM_IMPROVEMENT_TYPE` (tested farm on Maize)
- Successfully ended Turn 1 → Turn 2

### New Issues Found

**1. Popup dismissal is fragile — NaturalWonderPopup blocked turn progression**

The Scout discovering a Natural Wonder triggered `NaturalWonderPopup` which blocked `end_turn` from advancing to Turn 3. The `dismiss_popup` tool only checked two hardcoded states (85, 137) and missed it entirely.

Attempted workarounds from InGame context:
- `LuaEvents.NaturalWonderPopupClosed()` — wrong event name (missing underscores)
- `LuaEvents.NaturalWonderPopup_Closed()` — correct name, dismissed the zoomed art but left the window frame
- `ContextPtr:LookUpControl("/InGame/NaturalWonderPopup"):SetHide(true)` — hid the visual but didn't release the `ExclusivePopupManager` lock
- `Events.LocalPlayerTurnEnd()` — fired but popup in broken half-dismissed state by this point

**Root cause:** The popup's `Close()` function runs cleanup code (`ExclusivePopupManager:Unlock()`, `UILens.RestoreActiveLens()`, etc.) that only works from WITHIN the popup's own Lua state. Hiding the UI control or firing events from InGame doesn't release the lock. Must call `OnClose()` in the popup's own state index.

**Fix applied:** Rewrote `dismiss_popup` to dynamically scan ALL states from `conn.lua_states` whose names contain "Popup", "Wonder", or "Moment". Calls `OnClose()` in each visible one. No more hardcoded state indices.

**2. Builder improvements not exposed as an action**

`execute_unit_action` supports move/attack/fortify/skip/found_city but NOT build_improvement. Builders are a core unit type and need a dedicated improvement action. Required params: `PARAM_IMPROVEMENT_TYPE` (the `.Hash` of the improvement entry). Tested working via raw Lua.

**3. `end_turn` doesn't detect or report popup blocks**

`end_turn` returns "TURN_ENDED" even when a popup prevents the turn from actually advancing. The tool should verify the turn actually incremented (check `Game.GetCurrentGameTurn()` before and after) or at minimum auto-dismiss popups before ending.

### Observations for Agent Design

**Builder actions are a significant gap.** Builders are one of the most important early-game units and the agent currently can't use them without raw Lua. Need to add a `build_improvement` action or extend `execute_unit_action` with an improvement parameter.

**Popup handling needs to be proactive, not reactive.** Rather than having the agent call `dismiss_popup` when things seem stuck, the server should auto-dismiss popups before executing any action. Or `end_turn` should dismiss all popups first, then end the turn, then verify advancement.

**The turn loop pattern emerging:**
1. `get_game_overview` (orient)
2. `get_units` + `get_cities` (what do I have?)
3. For each unit: decide action → `execute_unit_action`
4. For each city: check production → `set_city_production` if needed
5. `get_tech_civics` → `set_research` if needed
6. `end_turn`

This matches the progressive disclosure design from the research — overview first, then drill down.

### Status

- All query tools: working
- Unit move/fortify/skip: working
- Production: working (non-cheat)
- Research/civic: working
- End turn: works but doesn't handle popup blocks
- **Missing:** builder improvements, robust popup dismissal
- **Stuck on Turn 2** due to half-dismissed NaturalWonderPopup — need server restart with new dismiss_popup code to clear it
- **Next:** restart server, clear popup, continue playtest

---

## 2026-02-08: Third Playtest — Resilience, Diplomacy, and Skip

### New Game: Persia (Nader Shah) on small island map

Started fresh after the previous game soft-crashed from the half-dismissed NaturalWonderPopup. New opponents: Arabia, China, Poland, Khmer, Russia.

### Infrastructure Fixes Applied Before Playtest

**1. Lazy connection (server starts without game running)**

The MCP server previously called `await conn.connect()` in the lifespan, blocking the server from even starting if the game wasn't running. Now the connection is deferred — `ensure_connected()` is called on first tool use. This also uncovered a stale-state bug: the server would connect at the main menu, discover main-menu Lua states, then fail when the user loaded a game because `GameCore_Tuner` and `InGame` weren't in the stale state list.

**Fix:** Added `_ensure_game_states()` which auto-reconnects if `gamecore_index` or `ingame_index` is None. TCP connect also has a 5-second timeout now instead of hanging indefinitely.

**2. Builder improvements added to `execute_unit_action`**

New `"improve"` action with `improvement` parameter (e.g. `IMPROVEMENT_FARM`). Uses `UnitOperationTypes.BUILD_IMPROVEMENT` with `PARAM_IMPROVEMENT_TYPE` hash.

**3. Robust `end_turn`**

Now auto-dismisses popups before ending, checks `Game.GetCurrentGameTurn()` before and after, and retries dismiss+end up to 2 times. Reports `"Turn N -> N+1"` on success.

### Playtest: Turns 1–5

**Turn 1:** Founded Mashhad at (23,27), set Animal Husbandry research, queued Scout. Sent warrior north, scout south, skipped builder. `dismiss_popup` caught the HistoricMoments popup automatically — dynamic state scanning works.

**Turn 2–3:** Moved builder toward maize tile at (22,25). Attempted `improve` action — got `"IMPROVING|IMPROVEMENT_FARM|22,25"` response. But the farm never appeared on the map. **Root cause: the tile wasn't in city territory.** The `CanStartOperation` check with `nil` params passed (it only checks if the unit type can use BUILD_IMPROVEMENT in general), but the game silently rejected the operation because you can't improve unowned tiles. This is a validation gap.

**Turn 3–4:** Scout discovered goody hut at (23,31) — 20 gold bonus. Tried to move builder to owned tile (22,27), but it only reached (23,26) after 2 moves. **Move response bug confirmed:** the tool reports the *target* coordinates, not where the unit actually ended up. Fixed the Lua to print `unit:GetX(), unit:GetY()` after `RequestOperation` instead of the target. (Fix needs server restart to take effect.)

**Turn 4:** Attempted `end_turn` — reported "turn is still 4, popup may be blocking". `dismiss_popup` found nothing. **Actual blocker: a first-meeting diplomacy encounter with Kublai Khan (China).** The DiplomacyActionView was visible, blocking all game progression, but it's not a "popup" by our keyword filter.

### Deep Dive: Diplomacy Encounters

The diplomacy system is entirely data-driven:

**Session tracking:** `DiplomacyManager.FindOpenSessionID(myPlayerID, otherPlayerID)` returns the active session. `GetSessionInfo(sid)` gives `{FromPlayer, ToPlayer}`.

**Response choices** come from `GameInfo.DiplomacySelections` table, keyed by `Type` (e.g. `FIRST_MEET_NEAR_RECIPIENT`):

| Type | Key | Text |
|------|-----|------|
| FIRST_MEET_NEAR_RECIPIENT | CHOICE_POSITIVE | "It is an honor to meet you." |
| FIRST_MEET_NEAR_RECIPIENT | CHOICE_EXIT | "Well met stranger, but I'm afraid we are too busy..." |
| FIRST_MEET_VISIT_RECIPIENT | CHOICE_POSITIVE | "We would love to sample your hospitality." |
| FIRST_MEET_VISIT_RECIPIENT | CHOICE_EXIT | "Sorry but not at this time." |
| FIRST_MEET_NO_MANS_INFO_EXCHANGE | CHOICE_POSITIVE | "Exchanging information on our capitals is a great idea..." |

**Responding:** `DiplomacyManager.AddResponse(sessionID, playerID, "POSITIVE"/"NEGATIVE")` selects a response. Multiple rounds may be needed — a first meeting has 2–3 dialogue stages. After the last response, the session closes and `DiplomacyActionView` hides.

**Other DiplomacyManager API:** `CloseSession(sid)`, `HasQueuedSession()`, `IsSessionIDOpen(sid)`, `SendAction()`, `TestAction()`, `RequestSession()`.

**DiplomacyActionTypes enum:** `SET_EMBASSY`, `DECLARE_FRIEND`, `DENOUNCE`, `ALLY`, `MAKE_DEAL`, `SET_DELEGATION`, `SET_OPEN_BORDERS`, `SET_WAR_STATE`.

Successfully responded POSITIVE twice to Kublai Khan and the session closed properly.

### Skip Action is Broken

`UnitOperationTypes.SKIP_TURN` is **nil** — the enum constant doesn't exist. The skip Lua code was calling `RequestOperation` with nil, which silently does nothing. The unit stays "ready to select" and blocks turn end.

The hash exists in the database: `GameInfo.UnitOperations["UNITOPERATION_SKIP_TURN"].Hash = 745019656`. Using the hash with `RequestOperation` appears to work (the unit stops blocking turn progression) even though `GetMovesRemaining()` still reports the same value. The fix is to look up the hash from `GameInfo.UnitOperations` instead of using the non-existent enum.

Also discovered: `FORTIFY` works via the enum (confirmed for warriors), `SLEEP` enum is nil (same issue as SKIP_TURN — need to use `GameInfo.UnitOperations["UNITOPERATION_SLEEP"].Hash`).

### `end_turn` Verification Timing Issue

The robust `end_turn` sleeps 1 second then checks the turn number. But AI turns can take longer than 1 second, so it falsely reports "turn is still N" when the turn did actually advance. The diplomacy encounter made this worse — the turn was blocked by diplomacy, we resolved it, the turn advanced during AI processing, but our check happened too early.

**Possible fixes:**
- Increase sleep duration (blunt, wasteful)
- Poll turn number in a loop with shorter intervals
- Check `UI.CanEndTurn()` state instead of just turn number
- Accept that "turn is still N" is sometimes a false negative and let the caller retry

### What's Needed Next

**1. Diplomacy tool** — Most critical gap. Diplomatic encounters block game progression and require meaningful choices. Need a tool that:
- Detects open diplomacy sessions (`DiplomacyManager.FindOpenSessionID`)
- Reports who we're meeting and what choices are available (from `GameInfo.DiplomacySelections`)
- Lets the agent choose a response (`DiplomacyManager.AddResponse`)
- Handles multi-round dialogues (first meetings have 2–3 stages)
- Also needs to handle later-game diplomacy: deals, friendship, denouncement, war declarations

**2. Fix move response** — Report actual position after move, not target. Code change made but needs server restart.

**3. Fix skip/sleep** — Use `GameInfo.UnitOperations` hash lookup instead of non-existent enum constants. Code change made for skip, sleep still needs fixing.

**4. Improve builder validation** — `CanStartOperation` with nil params doesn't validate tile ownership. Should check `Map.GetPlot(x,y):GetOwner() == Game.GetLocalPlayer()` before attempting improvement.

**5. `end_turn` timing** — Replace fixed 1-second sleep with a polling loop, or increase tolerance.

**6. `dismiss_popup` should also catch diplomacy** — Add "Diplomacy" to the keyword filter, or better yet, `end_turn` should check for open diplomacy sessions before attempting to end.

### Updated Turn Loop Pattern

```
1. get_game_overview (orient)
2. get_units + get_cities (what do I have?)
3. Check for diplomacy sessions → handle_diplomacy if needed
4. For each unit: decide action → execute_unit_action
5. For each city: check production → set_city_production if needed
6. get_tech_civics → set_research if needed
7. end_turn (auto-dismisses popups, verifies advancement)
```

### Status

- Lazy connection + auto-reconnect: working
- All query tools: working
- Unit move: working (response reports target not actual position — fix pending restart)
- Builder improve: partially working (needs tile ownership validation)
- Skip: broken (fix applied, needs restart)
- Production/research/civic: working
- End turn: mostly working (timing false negatives)
- Popup dismissal: working for standard popups
- Diplomacy: manually handled via raw Lua — needs proper tool
- **On Turn 5**, game is playable
- **Next:** build diplomacy tool, restart server with accumulated fixes, continue playtest

---

## 2026-02-08: Fourth Playtest — Diplomacy Tools, Farm Validation, Polling

### Fixes Applied Since Last Playtest

All five issues from the third playtest were fixed and server restarted:

1. **Diplomacy tools** — `get_pending_diplomacy` detects open sessions (scans all players), `diplomacy_respond` sends POSITIVE/NEGATIVE via `DiplomacyManager.AddResponse`. Multi-round sessions handled by calling repeatedly until session closes.
2. **Move response** — Now prints `unit:GetX(), unit:GetY()` after `RequestOperation`. Reports *current* position, not target. (Position is pre-move due to async pathfinding — the move queues but position updates next frame.)
3. **Skip action** — Uses `GameInfo.UnitOperations["UNITOPERATION_SKIP_TURN"].Hash` (745019656) instead of the non-existent `UnitOperationTypes.SKIP_TURN` enum. Confirmed working.
4. **Builder territory validation** — Checks `plot:GetOwner() == pid` before attempting improvement. Returns clear error "NOT_YOUR_TERRITORY" for unowned tiles.
5. **`end_turn` polling** — Replaced fixed 1-second sleep with 8×0.5s polling loop. Also checks for diplomacy sessions before attempting end (returns informative error if blocked). Retries dismiss+end twice if turn doesn't advance.

### Playtest: Turns 5–10 (Persia, Nader Shah)

**Turn 5:** Server reconnected after restart. All query tools worked immediately — lazy connection + `_ensure_game_states()` auto-reconnect functioning as designed. 1 city (Mashhad, pop 1, building Scout), 3 units.

**Turn 6:** Farm successfully placed at (22,27) — builder improve action confirmed working on owned territory. Warrior moved toward goody hut at (19,25). Scout explored south. All moves verified next turn at correct positions.

**Turn 7:** Warrior grabbed the goody hut — **free Builder** spawned at city center + gold jumped +20. Now have 2 builders. Second farm placed at (23,28). Switched city production from Scout to Monument for faster border expansion. Skip action confirmed working on idle builders.

**Turn 8:** `end_turn` blocked — **second diplomacy encounter with Kublai Khan (China)**. `get_pending_diplomacy` correctly detected the session. Responded POSITIVE 3 times but session persisted. **Root cause: the final dialogue stage is a "Goodbye" button which requires `CloseSession()`, not another `AddResponse()`.** The POSITIVE response was accepted but didn't advance past the exit screen. Had to use raw Lua `DiplomacyManager.CloseSession(sid)` to close it.

**Turn 10:** City grew to pop 2. Both farms working (food 6). Gold accumulated to 170. Building Monument.

### Bug Found: Diplomacy "Goodbye" Phase

The diplomacy dialogue has distinct phases:
1. **Greeting** — POSITIVE/NEGATIVE choices (2-3 rounds)
2. **Goodbye** — Only an EXIT/Goodbye button, no POSITIVE/NEGATIVE

`DiplomacyManager.AddResponse(sid, me, "POSITIVE")` during the goodbye phase is accepted but doesn't close the session. The session stays open, blocking turn end. Must use `DiplomacyManager.CloseSession(sid)` for the goodbye phase.

**Fix needed:** `diplomacy_respond` should detect when `AddResponse` doesn't close the session after repeated attempts, and fall back to `CloseSession()`. Or add explicit session close logic after a reasonable number of responses.

### Bug Found: Async Move Position Reporting

`RequestOperation(unit, MOVE_TO, ...)` queues pathfinding asynchronously. Reading `unit:GetX(), unit:GetY()` immediately after returns the *pre-move* position, not the destination. This means the MOVED response always shows where the unit was, not where it's going.

This isn't wrong — it's reporting ground truth — but it's confusing. The agent sees "MOVED|19,24" and thinks the unit is at (19,24) when it's actually en route to (19,25). Next turn's `get_units` confirms the correct final position.

**Options:**
- Accept it — the agent will see correct positions at turn start
- Print the target as "MOVING_TO|target_x,target_y" instead
- Add a brief delay and re-read (unreliable, game tick timing varies)

### Bug Found: Civic List Too Long

`get_tech_civics` returns ALL civics in the game database (60+), not just researachable ones. Seeing "Nuclear Program" and "Globalization" on Turn 5 is noise. The GameCore context has no `CanProgress()` filter — that only works in InGame. Need to either run the civic check in InGame context, or filter by era/prerequisites.

### Validated Working

- Farm building on owned tiles (builder consume a charge, improvement appears same turn)
- Skip action with hash-based operation
- Territory validation for builder improvements
- `end_turn` polling loop (turn 5→6, 6→7, 7→8 all worked first try)
- Diplomacy detection blocking `end_turn` (correct error message returned)
- `get_pending_diplomacy` detecting open sessions
- `diplomacy_respond` for POSITIVE/NEGATIVE rounds
- Goody hut rewards tracked through state changes
- City production switching (Scout → Monument)
- Monument building confirmed in progress

### What's Needed Next

1. **Fix diplomacy goodbye phase** — `diplomacy_respond` should auto-close sessions after AddResponse stops advancing dialogue
2. **Fix civic list filtering** — Only show current/next era civics, or run availability check in InGame context
3. **Move response clarity** — Either accept async position or switch to reporting target coordinates
4. **Continue playtest** — Push to Turn 20+ to test mid-game tools (combat, districts, tech completion)
5. **Production list query** — Agent currently guesses item names. Need a way to query available production for a city

### Status

- 14 tools total (12 original + get_pending_diplomacy + diplomacy_respond)
- All query tools: working
- Unit actions (move/fortify/skip/improve/found_city): all working
- Production/research/civic: working
- End turn with polling: working
- Diplomacy: mostly working (goodbye phase bug)
- **On Turn 10**, Mashhad pop 2, building Monument, 2 farms, met China
- **Next:** fix diplomacy goodbye, filter civics, continue playtest to Turn 20+

---

## 2026-02-08: Fifth Playtest — Threat Visibility, Score Rankings, Turn 34

### Enrichments Implemented

Two major game state enrichments added after reflecting on the lack of threat awareness during combat:

1. **Score + rankings in `get_game_overview`** — `Player:GetScore()` works for all met civs. Overview now shows "Rankings: Russia 60 > China 30 > Persia 22". Gives the agent a sense of how it's performing relative to competitors.

2. **Visible enemy units in `get_map_area`** — Scans all 64 players' units for each tile in the radius, checks `PlayersVisibility[me]:IsVisible(plotIndex)`, and appends unit labels to tile output. Example: `(13,26): PLAINS_HILLS Hills JUNGLE **[Barbarian WARRIOR]**`. Player 63 = Barbarians. City-state and civ units also shown with their civ name.

Both confirmed working immediately after server restart.

### Diplomacy Auto-Close Fix Validated

The "goodbye phase" bug from the fourth playtest was fixed: after `AddResponse`, if the session persists, the tool auto-calls `CloseSession()`. Tested against two Russia encounters — both closed cleanly. The pattern is now: first `diplomacy_respond(POSITIVE)` sends the response and auto-closes the goodbye, then a second call correctly returns `NO_SESSION`.

### Playtest: Turns 18–34 (Persia, Nader Shah)

**Turn 18–20:** Warrior at (12,25) was healing near the barbarian camp. The new map enrichment immediately proved its value — I could see `[Barbarian WARRIOR]` at (13,26) and `[Chinguetti WARRIOR]` at (13,25) right on the map output. Previously I was completely blind to these threats.

**Turn 20:** Met Russia (Peter). Score: Russia 51, China 25, Persia 17. Russia was already dominant. Diplomacy encounter handled smoothly via the auto-close fix.

**Turn 22:** Warrior dropped to 53 HP — barbarians attacked it while fortified/sleeping! The threat was visible on the map but there was no proactive notification. I only discovered the damage by checking `get_units` and noticing the HP change.

**Turn 25:** Scout killed by barbarians near (27,22). A barbarian camp at (27,20) with a Spearman and roaming Warrior caught it at 54 HP. The map had shown the threats — I just didn't retreat fast enough.

**Turn 27:** Slinger built. Monument completed (culture jumped to 3.9). Queued Settler + set Early Empire civic for expansion.

**Turn 34:** Archery completed, Irrigation researching. City pop 4, settler building. Score: Russia 72, China 42, Persia 26. Falling behind significantly.

### Reflections on the Play Experience

**What's working well:**
- The query → decide → act → end_turn loop is smooth. I can read game state, reason about it, and execute commands fluently.
- Map enrichment with enemy units is a game-changer. Before it, I was walking blind into combat. Now I can see threats before engaging.
- Score rankings give strategic context — I know I'm losing to Russia and need to expand.
- Diplomacy auto-close makes first meetings seamless. No more getting stuck.
- Builder improve with territory validation prevents wasted charges.

**What's frustrating / slowing me down:**

1. **No notification system.** I don't know when things happen unless I poll. My warrior took 30 damage and I only noticed by checking HP. My scout died and I only learned from the unit count dropping. A human player gets attack animations, notification banners, and the combat log. I get nothing. This is the single biggest gap in the play experience.

2. **`end_turn` false negatives are confusing.** About 30% of end_turn calls report "turn is still N" when the turn actually did advance. The polling window (8×0.5s = 4 seconds) isn't the issue — it's that turns can advance during diplomacy resolution or AI processing before the polling starts. I end up calling `get_game_overview` to check the real turn number. This should just work.

3. **Move response is misleading.** Every MOVED response shows the pre-move position because pathfinding is async. I've learned to ignore it and check `get_units` next turn, but it's still a paper cut. Should either report the target ("MOVING_TO|x,y") or just say "OK" without coordinates.

4. **Civic list is absurdly long.** 60+ civics on Turn 5. Nuclear Program, Globalization, Space Race — all listed as "available" because the GameCore query can't filter by prerequisites. This is pure noise. The tech list is fine (5-7 options) because it seems to filter correctly.

5. **No combat preview.** When I'm deciding whether to attack the barbarian camp, I have no way to estimate the outcome. A human sees combat strength comparison and predicted HP loss. I'm guessing blind. Need a way to query combat odds or at least see unit combat strength.

6. **Unit movement is slow and tedious.** Every turn I'm issuing skip/fortify for idle builders. The game keeps waking up fortified/sleeping units and demanding fresh orders. Ideally, sleeping units should stay asleep unless a threat appears. The `fortify` → `SLEEPING` response inconsistency is also confusing.

7. **No available production list.** When a city finishes building, I have to guess what I can build next. I knew UNIT_SLINGER existed but couldn't confirm it was available. A `list_city_production` query would eliminate guesswork.

### Tools / Info I Want Most (prioritised)

1. **Notification/event log** — "Your Scout was killed", "Barbarian Warrior attacked your Warrior for 30 damage", "Mining research completed", "Mashhad's borders expanded". Even a simple per-turn event summary would transform the experience.

2. **Combat strength on units** — Add combat/ranged strength to `get_units` output. Currently I see HP but not strength, so I can't evaluate matchups.

3. **Combat preview** — Given attacker unit + defender position, estimate damage outcome. The game has `Combat.PredictCombat()` or similar.

4. **Available production query** — What can this city build right now? Units, buildings, districts, wonders — with production cost and turns.

5. **Civic list filtering** — Only show civics the player can actually research (has prerequisites for).

6. **`end_turn` reliability** — Fix the false negative polling. Maybe read the turn number AFTER sending ACTION_ENDTURN with a longer initial delay, or detect "waiting for unit orders" state.

7. **Move response fix** — Report target coordinates instead of stale position, or just "OK".

### Status

- 14 tools, all working
- Map + overview enriched with threat/score data
- Diplomacy auto-close validated
- **On Turn 34**: Mashhad pop 4, settler building, Archery done, Irrigation researching
- Score: Russia 72 > China 42 > Persia 26 (falling behind — need second city ASAP)
- **Next:** implement notification log, add combat strength to units, fix end_turn reliability, filter civics

---

## 2026-02-08: Notification System — Snapshot-Diff Architecture

### Problem

The single biggest gap in the play experience: no awareness of what happened between turns. A human player gets attack animations, combat logs, notification banners, city growth popups, and research complete sounds. The agent gets silence — it only discovers events by manually polling and comparing state.

The Civ 6 `NotificationManager` API exists and works (confirmed via live Lua test), but many notifications (combat, unit killed) are **ephemeral** — they have `ExpiresEndOfTurn: true` in the XML and are gone from `GetList()` by the time we query after `end_turn` advances. We can't rely on NotificationManager alone for combat events.

### Design: Hybrid Snapshot-Diff + NotificationManager

Rather than trying to capture ephemeral notifications mid-turn-processing, we snapshot the full game state **before** and **after** ending the turn, then diff the two snapshots to detect events.

**Snapshot contents** (`TurnSnapshot` dataclass):
- All units: id, type, position, HP
- All cities: id, name, population, currently_building
- Current research + current civic

**Events detected by diff** (`TurnEvent` dataclass with priority 1-3):
- Priority 1 (critical): Unit killed, city lost
- Priority 2 (important): Unit took damage, production completed, tech/civic completed
- Priority 3 (info): Unit healed, city grew, new unit built

**NotificationManager** supplements the diff with non-ephemeral notifications that survive the turn: tech boosts (Eureka/Inspiration), governor available, pantheon available, policy slots, barbarian camp discovered, etc. These are split into "Action Required" (needs player decision) vs informational.

### Implementation

**New dataclasses in `lua_queries.py`:**
- `CitySnapshot` — minimal city state for diffing (id, name, population, building)
- `TurnSnapshot` — full state: turn number, units dict, cities dict, research, civic
- `TurnEvent` — priority, category, message
- `GameNotification` — type_name, message, turn, x, y

**New queries:**
- `build_notifications_query()` — queries `NotificationManager.GetList(me)` + `Find(me, nID)` in InGame context. Sanitizes pipe chars from messages, wraps `GetLocation()` in pcall for safety.
- `parse_notifications_response()` — parses `NOTIF|type|message|turn|x,y` lines

**GameState changes:**
- `_last_snapshot` field — cached for next diff
- `_take_snapshot()` — queries overview + units + cities, builds `TurnSnapshot`
- `_diff_snapshots(before, after)` — compares units (killed/damaged/healed/new), cities (lost/grew/production done/new), research/civic completion
- `_build_turn_report()` — formats events + notifications with priority icons (`!!!`/`>>`/`--`) and action-required vs info split
- `end_turn()` rewritten: snapshot → end turn → poll → snapshot → diff → notifications → report
- `get_game_overview()` bootstraps the first snapshot silently

**Combat strength enrichment:**
- `build_units_query()` now outputs `entry.Combat` and `entry.RangedCombat`
- `parse_units_response()` populates `combat_strength` and `ranged_strength`
- `narrate_units()` shows `CS:20 RS:15` for combat/ranged units

### Expected Turn Report Format

```
Turn 34 -> 35

== Events ==
  !!! Your Scout (UNIT_SCOUT) was killed! Last seen at (27,22).
  >> Your Warrior (UNIT_WARRIOR) took 15 damage! HP: 38/100 at (12,25).
  >> Mashhad finished building UNIT_SETTLER. Now: nothing (queue empty).
  -- Mashhad grew to population 5.

== Action Required ==
  * Choose a new technology to research.

== Notifications ==
  - Eureka! Irrigation research boosted.
```

### Status

- All code implemented and compiles clean
- **Needs server restart + playtest validation**
- Key risks: NotificationManager API may behave differently for some notification types; snapshot queries add 3 Lua round-trips to each end_turn

---

## 2026-02-08: Rich Diplomacy — From Blind to Informed

### Problem

Playing as Persia on Turn 38, both China and Russia are **Unfriendly** toward us and we had no idea. The agent was blindly reacting to first-meeting dialogues with no awareness of relationship state, no ability to take proactive diplomatic actions, and no feedback when actions were rejected.

The screenshot from the player showed Kublai Khan's tooltip: Unfriendly (-17), with modifiers like "-10 Kublai Khan heaps scorn on the weak and the poor" and "-6 Unknown Reason". The agent couldn't see any of this — `get_diplomacy` only showed "met" and "at war" booleans.

### API Discovery

**What doesn't work:**
- `DiplomacyManager.TestAction(me, other, hash)` — returns false for everything, even valid actions. The game's own UI doesn't use this for checking action validity.
- `DiplomacyManager.SendAction(me, other, hash)` — completes without error but does nothing. Not the right API path.
- `GetDiplomaticState`, `IsDeclaredFriendWith`, `IsAlliedWith`, `IsDenouncing` — all **nil** in both GameCore and InGame on the `Diplomacy` object.
- `HasOpenBordersFrom` — nil in GameCore, exists in InGame.

**What works (InGame context only):**
- `Players[i]:GetDiplomaticAI():GetDiplomaticStateIndex(me)` — returns 0-6 index mapping to Allied/Declared Friend/Friendly/Neutral/Unfriendly/Denounced/War.
- `Players[i]:GetDiplomaticAI():GetDiplomaticModifiers(me)` — returns table of `{Score=int, Text=string}`. This is exactly what the tooltip shows.
- `pDiplo:IsDiplomaticActionValid(actionType, targetID, showReasons)` — the **correct** way to check if an action is possible. Returns `(bool, {FailureReasons=[]})`. Action types are full strings like `"DIPLOACTION_DIPLOMATIC_DELEGATION"`.
- `DiplomacyManager.RequestSession(me, target, "DIPLOMATIC_DELEGATION")` — the **correct** way to initiate proactive actions. Opens a dialogue session where the AI responds.
- `pDiplo:GetGrievancesAgainst(i)`, `GetVisibilityOn(i)`, `HasDelegationAt(i)`, `HasEmbassyAt(i)`, `GetMetTurn(i)` — all work in InGame.

**Critical finding:** `GetDiplomaticAI()` and `IsDiplomaticActionValid()` are **nil in GameCore**. The diplomacy query HAD to move to InGame context.

### Rejection Detection

Sending a delegation via `RequestSession` opens a dialogue session. The AI responds — and may reject if Unfriendly. The key insight: **check `HasDelegationAt()` and gold balance before and after** to detect acceptance vs rejection. If `HasDelegationAt` is still false and gold unchanged, the AI rejected it.

During playtesting, we sent delegations to both China (Unfriendly, -17) and Russia (Unfriendly, -4). Both were rejected — sessions opened, we responded POSITIVE to the dialogue, sessions closed, but `HasDelegationAt` remained false and gold unchanged. Without the rejection detection, this was completely silent.

### GameInfo.DiplomaticActions Database

42 diplomatic actions in the database. Key ones for early game:

| Action | Cost | RequiresCapitalPath | Notes |
|--------|------|-------------------|-------|
| `DIPLOACTION_DIPLOMATIC_DELEGATION` | 25 gold | true | Obsoleted by Diplomatic Service civic |
| `DIPLOACTION_RESIDENT_EMBASSY` | 50 gold | false | Needs Writing tech |
| `DIPLOACTION_DECLARE_FRIENDSHIP` | 0 | false | Both sides must agree |
| `DIPLOACTION_DENOUNCE` | 0 | false | |
| `DIPLOACTION_OPEN_BORDERS` | 0 | false | |

### Implementation

**Enriched `CivInfo` dataclass** — added 10 new fields:
- `diplomatic_state` (str): FRIENDLY/NEUTRAL/UNFRIENDLY/etc.
- `relationship_score` (int): sum of all modifiers
- `modifiers` (list[DiplomacyModifier]): each with score and text reason
- `grievances`, `access_level`, `has_delegation`, `has_embassy`, `they_have_delegation`, `they_have_embassy`
- `available_actions` (list[str]): validated actions we can take right now

**Rewrote `build_diplomacy_query()`** — now runs in InGame context. For each met civ: reads diplomatic state index, all modifiers, grievances, visibility, delegation/embassy status both directions, and validates 5 common diplomatic actions via `IsDiplomaticActionValid`.

**New `build_send_diplo_action()` Lua builder** — validates with `IsDiplomaticActionValid` (returns failure reasons), sends via `RequestSession`, auto-navigates the AI dialogue (up to 5 rounds of AddResponse + CloseSession), then checks post-state to detect acceptance/rejection.

**New `send_diplomatic_action` MCP tool** — takes player_id and action name (DIPLOMATIC_DELEGATION, DECLARE_FRIENDSHIP, DENOUNCE, RESIDENT_EMBASSY, OPEN_BORDERS).

**Updated narration** — `narrate_diplomacy()` now shows:
```
2 civilizations:
  China (Kublai Khan (China)) — UNFRIENDLY (-17) [player 2]
    Access: they have delegation
    -1 Unknown Reason
    -6 Unknown Reason
    -10 Kublai Khan heaps scorn on the weak and the poor
    Can: Diplomatic Delegation, Declare Friendship, Denounce
  Russia (Peter) — UNFRIENDLY (-4) [player 5]
    -7 Peter is disappointed you have little science and culture
    +1 Unknown Reason
    +2 Unknown Reason
    Can: Diplomatic Delegation, Declare Friendship, Denounce
```

### Playtest Observations (Turn 36-38)

- **Notification system validated**: First `end_turn` with snapshot-diff returned: `"Turn 36 -> 37 == Action Required == Fill Policy Slot, Choose a Civic, Choose a Technology"`. The system works.
- **Diplomacy blocked end_turn again** on Turn 34 — China warrior at (21,26) triggered another encounter. Auto-close handled it.
- **Barbarian scout spotted by player** heading toward our capital but agent couldn't see it — it was outside unit visibility range and moved away before next scan. Highlights need for better perimeter awareness.
- **False negative on end_turn** persists (~30% rate) — Turn 34→36 jumped because diplomacy caused the turn to advance mid-resolution and polling started too late.

### Strategic Picture (Turn 38)

Russia (-4) is almost fixable — their main complaint is low science/culture. Expanding to a second city and building a Campus would help. China (-17) is harder — Kublai Khan's agenda ("Pax Mongolica") penalises weak civs heavily. Both rejected our delegation attempts.

### What's Needed Next

1. **Playtest the rich diplomacy** — restart server, verify narration looks right, attempt delegation/friendship with the new tool
2. **Policy management** — "Fill Policy Slot" notification appeared but we have no tool for setting policies
3. **Barbarian perimeter awareness** — scout sighted near capital but outside visibility. Need broader scan or alert system
4. **end_turn false negatives** — still ~30% failure rate on polling

### Status

- 16 tools total (added `send_diplomatic_action`, enriched `get_diplomacy`)
- Rich diplomacy: state, modifiers, grievances, access, available actions
- Proactive diplomacy: send delegation/friendship/denounce with rejection detection
- Notification system validated (first turn report generated)
- **Needs server restart for all changes**

---

## 2026-02-08: Batch 1 Improvements — Production, Civics, Bug Fixes

### Improvements Implemented

**1. Civic List Filtering (P0)**

Reduced civic list from 60+ to 3-8 relevant options. Used `GameInfo.CivicPrereqs()` (NOT `Civic_Prerequisites` — that's nil) to build a prerequisite lookup table, then filter to only show civics whose prerequisites are all completed. Also added era cap (current + 2 eras) to exclude `ERA_FUTURE` repeatable civics that have no prerequisites.

**Before:** Turn 38 showed 60+ civics including Nuclear Program, Globalization, Space Race.
**After:** Turn 38 shows Foreign Trade, Military Tradition, State Workforce.

**2. Available Production Query (P0)**

Exposed `get_city_production(city_id)` as a new MCP tool. Fixed two critical bugs:
- **Context bug:** `list_city_production()` called `execute_read` (GameCore) but `bq:CanProduce()` throws "Not Implemented" in GameCore. Changed to `execute_write` (InGame).
- **Hash vs Index bug (CRITICAL):** `bq:CanProduce(item.Index, true)` in InGame context gives **completely wrong results**. Only `.Hash` works correctly. With `.Index`, we got 1 producible unit (UNIT_MODERN_AT — a modern era anti-tank for a Turn 38 ancient civ). With `.Hash`, we correctly get Settler, Builder, Scout, Warrior, Archer. This is the same `.Hash` vs `.Index` gotcha documented for `CityManager.RequestOperation` params.

Added `ProductionOption` dataclass and `parse_city_production_response()` parser.

**3. Move Response Fix (P2)**

Changed `build_move_unit()` to report target coordinates instead of stale pre-move position:
```
Before: OK:MOVED|21,25     (shows where unit IS, not where it's going)
After:  OK:MOVING_TO|20,26|from:21,25  (shows target + origin)
```

**4. end_turn Reliability (P1)**

Improved polling: longer initial delay (1.0s), plus a final 2.0s verification check before declaring failure. Also added `advanced` flag to avoid confusing control flow.

**5. InGame Child Popup Dismissal**

`dismiss_popup` previously only scanned standalone Lua states. The "Unit Captured" popup (`InGamePopup`) is a child UI element within the InGame context, not its own state. Added a second pass that checks `ContextPtr:LookUpControl("/InGame/InGamePopup")` (and GenericPopup, PopupDialog) from InGame context and hides them.

### Bugs Discovered During Playtest (Turns 38–45)

**1. `CanProduce` requires `.Hash` not `.Index` in InGame context**

This was already known for `CityManager.RequestOperation` params, but `CanProduce` has the same requirement. Using `.Index` makes it interpret the integer as something else entirely — it returns true for random items whose Hash coincidentally matches. This produced absurd results: UNIT_MODERN_AT, UNIT_SUBMARINE, UNIT_AIRCRAFT_CARRIER, UNIT_ENGLISH_REDCOAT (for Persia!) were listed as producible.

**2. `found_city` silently fails on invalid tiles**

The agent attempted to found a city at (22,30), which is within Mashhad's existing borders. The Lua returned `FOUNDED|22,30` (success) but the city was never created. `UnitManager.CanStartOperation(unit, FOUND_CITY, nil, true)` returns true generically (the unit CAN found cities) but doesn't validate the specific tile when params aren't passed for the check. The agent had no way to know the tile was invalid.

**Fix needed:** Either:
- Check `CanStartOperation` with the actual tile params before founding
- Verify city count increased after `RequestOperation`
- Add a settle validity tool that shows legal settle locations

**3. Builders captured by barbarians — twice**

Builder at (21,27) was captured while building a plantation on an owned tile near the city border. Builder at (25,26) was captured while building a plantation on a tile that may have been at the edge of territory. Both times the agent sent builders to work without military escort and without checking for nearby threats.

**Lessons:**
- Builders should never be sent to border tiles without checking `get_map_area` for nearby hostile units first
- The barbarian perimeter scan (Batch 2, item 8) would have prevented this
- Agent needs better threat awareness in its decision-making

**4. Russia denounced us**

Peter denounced Persia on Turn 41. The denouncement came as a diplomacy session — `get_pending_diplomacy` correctly detected it and we responded NEGATIVE. Russia's relationship modifiers: -7 for low science/culture.

### Validated Working

- Civic filter: 3 options instead of 60+ ✓
- Production query: Correct list (Settler, Builder, Scout, Warrior, Archer) ✓
- Move response: Shows target + origin ✓
- Notification system: "Settler completed", "Research complete: Irrigation", action required items ✓
- InGamePopup dismissal: "Unit Captured" popup caught ✓ (after fix)
- Turn advancement: Turns 38→39→40→41→42→44 (skipped 43 due to polling)

### What's Needed Next (Updated Batch 2)

1. **Settle validity** — Tool or validation to check where a settler can legally found. The game has `CanStartOperation` with tile-specific params, or a `GetBestSettleArea()` API.
2. **Policy management** — "Fill Policy Slot" has been an action-required item since Turn 37, still unresolvable.
3. **Barbarian perimeter scan** — Two builders lost because we didn't check for threats.
4. **Combat preview** — Agent needs to evaluate fight outcomes before committing.
5. **City-state diplomacy** — 9 city-states invisible to the agent.
6. **`found_city` post-validation** — Verify the city actually exists after the founding operation.

### Status

- 17 tools total (added `get_city_production`)
- Civic filter, production query, move response, popup dismissal all working
- **Turn 45**: Mashhad pop 3, building Archer. Settler still alive but failed to found. 2 builders lost to barbarians. Warrior at 30 HP. Score still last place.
- **Next:** Fix found_city validation, research settle validity API, implement Batch 2 items

---

## 2026-02-08: Information Parity — Fog of War, Yields, Settle Validation, Threats

### Problem: Agent Sees Both Too Much and Too Little

A human-player parity audit revealed two-directional problems:

**Agent sees MORE than human:**
- `build_map_area_query()` returned resources, improvements, and features for ALL tiles regardless of visibility. Only unit scanning was gated by `vis:IsVisible()`. A human cannot see resources on unexplored tiles or improvements in fog of war.

**Agent sees LESS than human:**
- No tile yields (food/prod/gold/science/culture/faith) — human sees yield icons on every tile
- No fresh water indicator — human sees this in the settler lens (+3 housing)
- No settle validity feedback — human sees green/red tiles via settler lens
- No passive threat awareness — human sees ALL enemy units in their visibility range at all times
- Silent settle failures — `found_city` reported success even when the city wasn't created

### Changes Implemented

#### 1. Fog of War Gating (Fairness Fix)

Rewrote `build_map_area_query()` with three-tier visibility:
- **Unexplored** (`vis:IsRevealed(plotIdx)` = false): tile omitted entirely
- **Revealed/Fog** (revealed but not visible): terrain, features, resources shown; NO improvements, units, or yields. Tagged `[fog]` in narration.
- **Visible** (`vis:IsVisible(plotIdx)` = true): everything shown including yields and fresh water.

Added `visibility: str` field to `TileInfo` dataclass ("visible", "revealed", "unexplored").

**Tested:** Tile at (25,29) correctly shows `[fog]` tag — terrain/features visible but no improvements or units.

#### 2. Tile Yields + Fresh Water (Parity)

Added `plot:GetYield(0..5)` and `plot:IsFreshWater()` to visible tiles in the map query.

- `TileInfo` gained `yields: tuple[int,...]` (food, prod, gold, science, culture, faith) and `is_fresh_water: bool`
- `narrate_map()` shows yields as `{F:2 P:1 G:0}` and `[freshwater]` indicator
- Only shown for visible tiles (yields on fog tiles may be stale due to improvements)

#### 3. Settle Pre-Validation (Fix Silent Failures)

Rewrote `build_found_city()` with comprehensive pre-checks:
- Water tile check (`plot:IsWater()`)
- Mountain check (`TERRAIN_GRASS_MOUNTAIN` etc.)
- Minimum city distance from ALL alive players' cities (`Map.GetPlotDistance > 3`)
- Returns clear error: `ERR:CANNOT_FOUND|Too close to Mashhad (distance 3, need > 3)`

**Tested:** Settle attempt at (22,30) correctly returned "Too close to Mashhad" with 5 recommended alternatives.

#### 4. Settle Advisor on Failure

When `found_city` fails, automatically scans radius 5 around the settler for valid candidates, scores them by summing workable-radius yields + water bonus, and returns top 5 recommendations.

New dataclasses: `SettleCandidate(x, y, score, total_food, total_prod, water_type, resources)`.

#### 5. Threat Scanning in `end_turn`

After each turn, scans visible tiles around each city (radius 4) for hostile military units. Appended to turn report as priority-2 events.

**Tested:** Turn report showed "China WARRIOR (CS:20) spotted 3 tiles from Mashhad" and "Barbarian HORSEMAN (CS:20) spotted 1 tiles from Mashhad".

New dataclass: `ThreatInfo(city_name, unit_desc, x, y, distance)`.

### Bug Found: `found_city` Async Race Condition

`UnitManager.RequestOperation` for FOUND_CITY is **async** — the city appears next frame. Post-verification checking city count immediately after `RequestOperation` returned false negative. The settler at (20,28) successfully founded "Hagmatana" but the count check said it failed.

**Fix:** Removed post-verification entirely. Pre-validation is thorough enough (water, mountain, city distance from ALL cities). The async nature of `RequestOperation` makes same-frame verification unreliable.

### API Discovery: Pantheon Selection

`UI.RequestPlayerOperation(me, PlayerOperations.FOUND_PANTHEON, {[PlayerOperations.PARAM_BELIEF_TYPE] = belief.Hash})`

Successfully selected Fertility Rites (free builder + 10% growth). This was a blocking notification ("Choose a Pantheon") that the agent needs proper tooling for.

### API Discovery: Policy Management (InGame Only)

Long investigation into the government/policy API. Key findings:

- `GetCurrentGovernment()`, `GetNumPolicySlots()`, `GetSlotPolicy(s)`, `GetSlotType(s)` — **InGame only** (nil in GameCore)
- `PlayerOperations.POLICY_SLOT` is **nil** — the enum constant doesn't exist
- Found the mechanism in game source: `Base/Assets/UI/Screens/GovernmentScreen.lua` line 1570

**The correct pattern:**
1. `UI.RequestPlayerOperation(me, PlayerOperations.UNLOCK_POLICIES, {})` — MUST call first
2. `pCulture:RequestPolicyChanges(clearList, addList)` — then set policies
- `clearList` = sequential array of slot indices to clear, e.g. `{0, 1}`
- `addList` = table keyed by slot index → policy Hash, e.g. `addList[0] = agoge.Hash`
- Without UNLOCK_POLICIES first, RequestPolicyChanges **silently fails**

**Slot types are counterintuitive:** 0=economic, 1=military (reversed from what you'd expect).

Successfully set Agoge (military, +50% melee/ranged XP) + Urban Planning (economic, +1 production).

### API Discovery: Trade Deal Reading

China offered a trade deal — first time this scenario appeared. Discovered the API:

- `DealManager.GetWorkingDeal(DealDirection.INCOMING, me, otherPlayerID)` → deal object
- `deal:GetItemCount()`, `deal:Items()` → iterate items
- `pItem:GetFromPlayerID()`, `GetType()`, `GetSubType()`, `GetAmount()`, `GetDuration()`, `GetValueType()`
- `DealItemTypes.GOLD`, `RESOURCES`, `AGREEMENTS`, `CITIES`, `TECHNOLOGY`, `FAVOR`
- `DealAgreementTypes.OPEN_BORDERS`, `JOINT_WAR`
- Resources: `GameInfo.Resources[valueType].ResourceType`

**Trade valuation lesson:** China offered 2 GPT + Open Borders for our Tobacco (luxury). Research showed luxury resources are worth 5-10 GPT in standard play — China's offer was 60-75% below market. Open borders with their military nearby was also risky. Agent needs to evaluate deals against market rates and consider other buyers before accepting.

### API Discovery: Dialogue Text

The agent responds POSITIVE/NEGATIVE to diplomacy sessions without knowing what the AI leader is saying. Russia declared their agenda ("Leave the exploring to me") but the agent couldn't read the text. AI dialogue text reading needs tooling.

### User Feedback Themes

1. **"you have completely ignored the religion creation dialogue"** — Pantheon/religion/governor selection dialogues need to be prominently surfaced as action-required notifications, not silently handled
2. **"Fill policy slot is what I see"** — Policy slot screen is blocking and needs proper tooling
3. **"this will be a key scenario we need tooling for"** — Trade deals need a proper read+evaluate+respond tool
4. **"might be worth using a subtask to research trade deal value"** — Don't accept first offer; evaluate against market rate and consider other buyers
5. **"i think its something to do with their ambition"** — Agent can't read AI dialogue text, missing important strategic info about leader agendas

### Playtest Progress (Turns 45-52)

- Founded second city "Hagmatana" at (20,28) — pop 2, building Scout
- Mashhad pop 3, building Monument (then Archer)
- Warrior fully healed to 100 HP
- Archer built and positioned at (22,27)
- Builder improving tobacco at (21,27)
- Slinger fortified at (20,28)
- Set Agoge + Urban Planning policies
- Selected Fertility Rites pantheon
- Score: Russia > China > Persia (still last place)

### Tooling Gaps Identified

**No MCP tool yet (API discovered):**
- Trade deal reading + evaluation + response
- Policy management (set/swap policies)
- Pantheon/religion selection
- AI dialogue text reading

**Not yet researched:**
- Governor selection
- Unit promotion
- Combat preview
- Proactive trade offers to other civs
- Citizen management / city focus

### Status

- 17 tools, all working
- Fog of war gating: working (3-tier visibility)
- Tile yields + fresh water: working
- Settle validation + advisor: working
- Threat scanning: working
- **Turn 52**: 2 cities, Archery done, score still last
- **Next:** Build proper MCP tools for trade deals, policy management, and action-required notification surfacing

---

## 2026-02-08: Information Parity Batch 2 — Trade Deals, Policies, Notifications

### Implementation

Built 5 new MCP tools to close the biggest interaction gaps:

**Trade Deals:**
- `get_pending_deals` — scans all met players for incoming trade offers, gated on `DiplomacyManager.FindOpenSessionID` (not `DealManager.GetWorkingDeal` alone, which returns stale cached deals)
- `respond_to_deal(player_id, accept)` — accepts/rejects via `DealManager.SendWorkingDeal`, then closes the diplomacy session with AddResponse+CloseSession loop

**Policy Management:**
- `get_policies` — reads government, slot types (with integer→string mapping: 0=economic, 1=military, 2=diplomatic, 3/4=wildcard), current policies, and all unlocked policies grouped by type
- `set_policies(assignments)` — two-step: `UI.RequestPlayerOperation(UNLOCK_POLICIES)` then `pCulture:RequestPolicyChanges(clearList, addList)`. Simple string format for LLMs: `"0=POLICY_AGOGE,1=POLICY_URBAN_PLANNING"`

**Enhanced Notifications:**
- `get_notifications` — standalone tool with `NOTIFICATION_TOOL_MAP` mapping each notification type to the MCP tool that resolves it (e.g. `NOTIFICATION_FILL_CIVIC_SLOT → get_policies() then set_policies()`)
- Enriched `GameNotification` with `is_action_required` and `resolution_hint` fields
- Turn reports now show tool hints on action-required items

### Bugs Fixed During Testing

1. **`GetSlotType()` returns integers, not strings** — 0=economic, 1=military (counterintuitive). Added `slotNames` mapping table in Lua.
2. **Lua table literal `{[0]=...}` in f-strings** — Python f-string `{}` conflicts. Fixed with `{{}}` double-brace escaping.
3. **`DealManager.GetWorkingDeal()` returns stale cached deals** — After rejecting a deal, `GetWorkingDeal` still returns the old deal object. Gated on `DiplomacyManager.FindOpenSessionID()` — only report deals with an active diplomacy session.
4. **`respond_to_deal` didn't close diplomacy session** — `SendWorkingDeal(REJECTED)` alone doesn't clear the blocking session. Added AddResponse NEGATIVE + CloseSession loop.
5. **`set_policies` readback is stale same-frame** — `GetSlotPolicy()` immediately after `RequestPolicyChanges` returns pre-change values. Simplified to success message instead.

### Status

- 22 tools total (5 new: get_pending_deals, respond_to_deal, get_policies, set_policies, get_notifications)
- All verified working against live game
- **Next:** Playtest to find remaining gaps

---

## 2026-02-08: Sixth Playtest — Turn Stuck, Blocking Notifications, New Gaps

### What Happened

Playtested Turn 52 as Persia. Moved units, set production, attempted to end turn. The turn got permanently stuck — Russia's AI turn never completed, eventually requiring a game reload to Turn 38.

### Root Cause: `EndTurnBlockingTypes`

The game has a **mandatory notification system** (`EndTurnBlockingTypes`) that MUST be resolved before the turn advances. Our `end_turn` tool was completely unaware of this. `NotificationManager.GetFirstEndTurnBlocking(me)` returns the specific blocking type.

Blocking types discovered:
- `ENDTURN_BLOCKING_GOVERNOR_APPOINTMENT` (934074454) — **must** appoint a governor
- `ENDTURN_BLOCKING_UNIT_PROMOTION` (1706768628) — **must** promote a unit
- `ENDTURN_BLOCKING_UNITS` (23669119) — unmoved units
- `ENDTURN_BLOCKING_FILL_CIVIC_SLOT` — must set policies
- `ENDTURN_BLOCKING_PRODUCTION` — must choose production
- Plus ~20 more types (research, civic, pantheon, religion, etc.)

The turn appeared to end (`IsTurnActive=false`) but blocking notifications prevented actual advancement. Russia's AI got stuck in a processing loop because our blocking notifications were unresolved. Dismissing notifications via `NotificationManager.Dismiss()` eventually cleared the blocks, but the damage was done — the game state was corrupted.

### Promotion API Discovery

- `CanPromote(index)` in GameCore returns ALL 145 promotions without class filtering — must filter by `row.PromotionClass == info.PromotionClass` (e.g. `PROMOTION_CLASS_MELEE` → 7 valid options for Warrior)
- `UnitManager.RequestCommand(unit, UnitCommandTypes.PROMOTE, {[PARAM_PROMOTION_TYPE]=hash})` — correct API, but `CanStartCommand(PROMOTE)` returned false during the stuck state
- `UnitCommandTypes.PARAM_PROMOTION_TYPE` exists in InGame (value -927495623)

### Governor API Discovery

- `Players[me]:GetGovernors()` — exists in InGame only (nil in GameCore)
- `GetGovernorPoints()`, `GetGovernorPointsSpent()`, `CanAppoint()` — all work
- `PlayerOperations.APPOINT_GOVERNOR` with `PARAM_GOVERNOR_TYPE = governor.Hash` — the correct appointment API
- `PlayerOperations.ASSIGN_GOVERNOR` + `PROMOTE_GOVERNOR` also exist
- `GetGovernorList()` returns boolean (false) when no governors appointed, not a table
- 8 governors available: Victor, Amani, Moksha, Magnus, Liang, Pingala, Reyna, Ibrahim
- `UI.CanStartPlayerOperation(APPOINT_GOVERNOR)` returned false during stuck state — possibly because turn wasn't truly active

### Other Gaps Found

1. **Builder charges not in `get_units` output** — Builder had 2 charges remaining but narration only shows type/position/moves. Critical for decision-making.
2. **Fortify on ranged units returns "SLEEPING"** — Slingers/archers can't fortify, they sleep. The tool should explain this or handle it transparently.
3. **`IsTurnActive=false` doesn't mean turn was accepted** — Can mean the game is in a blocked state where blocking notifications prevent advancement.

### Game State Corruption Sequence

1. Turn 52: end_turn requested
2. Governor appointment blocking (unknown to tool)
3. `IsTurnActive` went false, but turn counter stayed at 52
4. Russia's AI marked as "active" but couldn't complete
5. Attempted to appoint governor — `CanStartPlayerOperation` returned false
6. Dismissed all notifications via `NotificationManager.Dismiss()`
7. Blocking cleared to 0, but Russia AI still stuck (`IsTurnActiveComplete=true` but still "active")
8. No recovery possible — game state permanently stuck
9. Used `Game.RetirePlayer(5)` (killed Russia) — still stuck
10. Used `Game.SetCurrentGameTurn(53)` — desync'd GameCore vs InGame
11. **Reloaded save to Turn 38**

### Lessons Learned

1. **end_turn MUST check `GetFirstEndTurnBlocking()` BEFORE attempting to end** — report the specific blocking type and how to resolve it
2. **Governor appointment is MANDATORY** — the game literally won't advance without it
3. **Unit promotions are MANDATORY** — same as governors
4. **Don't dismiss blocking notifications** — resolve them properly (appoint the governor, promote the unit)
5. **FireTuner Lua commands block the game thread** — sending commands while AI is processing interrupts their turn. Wait longer without sending commands.

### Priority Fixes Needed

1. **end_turn blocking detection** — check `GetFirstEndTurnBlocking()` and map to MCP tool resolution
2. **Governor tool** — appoint/assign/promote governors
3. **Promotion tool** — list valid promotions (class-filtered) and apply them
4. **Builder charges in `get_units`** — add `build_charges` field
5. **Fortify/sleep transparency** — don't confuse the agent

### Status

- Game reloaded to Turn 38
- All 22 tools working but 3 critical gaps: governors, promotions, end_turn blocking
- **Next:** Implement end_turn blocking detection, governor tool, promotion tool, builder charges

## 2025-02-09: Information Parity Batch 3 — Blocking Detection, Governors, Promotions

### Implemented

5 new MCP tools + 1 critical end_turn fix:

1. **`end_turn` blocking detection** — Before requesting end turn, queries `NotificationManager.GetFirstEndTurnBlocking()` to detect mandatory blockers (governor appointment, unit promotion, policy slots, production, etc.). Returns actionable error with resolution hint instead of silently failing. Maps ~9 `EndTurnBlockingTypes` to tool suggestions via `BLOCKING_TOOL_MAP`.

2. **`get_governors`** — Shows governor points (available/spent), appointed governors with city assignments and establishment status, and all available governor types. Handles `GetGovernorList()` returning boolean `false` when empty.

3. **`appoint_governor(governor_type)`** — Appoints a governor via `PlayerOperations.APPOINT_GOVERNOR` with hash-based params. Pre-checks `CanAppoint()`.

4. **`assign_governor(governor_type, city_id)`** — Assigns appointed governor to a city via `PlayerOperations.ASSIGN_GOVERNOR`.

5. **`get_unit_promotions(unit_id)`** — Lists valid promotions filtered by unit's `PromotionClass` (e.g. melee warrior gets 7 melee promos, not all 145). Uses GameCore context with `exp:CanPromote()`.

6. **`promote_unit(unit_id, promotion_type)`** — Applies promotion via `UnitManager.RequestCommand(PROMOTE)` with `PARAM_PROMOTION_TYPE` hash. Pre-checks `CanStartCommand`.

7. **Builder charges in `get_units`** — Added `build_charges` field to UnitInfo, shows `charges:N` in narration for builders.

8. **Fortify/sleep clarity** — When fortify falls back to sleep (for non-melee units), response now says "Unit is sleeping (non-melee units cannot fortify)" instead of just "SLEEPING".

9. **`screenshot` tool** — Captures the Civ 6 game window as an image for visual reasoning. Uses Swift/CoreGraphics to find window ID, then `screencapture -l` to capture just the game window. Returns MCP `Image` type inline.

### Bugfixes

- **`build_end_turn_blocking_query` fix** — `GetFirstEndTurnBlocking()` returns the blocking TYPE VALUE directly (e.g. 23669119), not a notification ID. Original code tried to use it as a notification ID with `NotificationManager.Find()`, which returned nil. Fixed to match value directly against `EndTurnBlockingTypes` enum, and scan notification list separately for the message.

### Architecture

- `lua_queries.py`: 5 new dataclasses, `BLOCKING_TOOL_MAP`, 4 new query/action builders, 3 new parsers, updated units query/parser
- `game_state.py`: 5 new methods, 2 new narrations, blocking check in `end_turn()`, updated fortify and units narration
- `server.py`: 6 new MCP tools (28 total, including screenshot)

### Testing

- Fresh game: Poland (Jadwiga), Turn 3
- `get_governors` — 0 points, 8 available types
- `get_unit_promotions` — correctly shows nothing for fresh warrior (no XP)
- `get_units` — builder shows `charges:2` after building farm
- `end_turn` blocking — detected ENDTURN_BLOCKING_UNITS but type was "UNKNOWN" (fixed)
- `screenshot` — successfully captured game window via Swift/CoreGraphics + screencapture

---

## 2026-02-09: Playtest Bugfixes — Skip, Stacking, Attack Validation

### Critical Bug: Skip Was Never Working

During sustained playtesting (Turn 30–41, Poland/Jadwiga), discovered that `execute_unit_action(skip)` **silently did nothing** for all unit types. The Lua returned "OK:SKIPPED" but `GetMovesRemaining()` stayed at max.

**Root cause:** `UNITOPERATION_SKIP_TURN` exists in `GameInfo.UnitOperations` (hash 745019656) but `CanStartOperation()` returns **false for ALL units** — builders, warriors, scouts, slingers. The `RequestOperation` call doesn't error; it simply does nothing.

**Fix:** Rewrote `build_skip_unit()` to use **GameCore** context with `UnitManager.FinishMoves(unit)` instead of InGame `RequestOperation`. Changed `game_state.py` to call `execute_read` (GameCore) instead of `execute_write` (InGame) for skip. Confirmed: moves go from 2 → 0 immediately.

**Key API difference documented:**
- GameCore `UnitManager`: `FinishMoves`, `WakeUnit`, `MoveUnit`, `Kill`, `PlaceUnit`
- InGame `UnitManager`: `RequestOperation`, `CanStartOperation`, `RequestCommand`
- Unit lookup differs too: GameCore uses `Players[me]:GetUnits():FindID(idx)`, InGame uses `UnitManager.GetUnit(me, idx)`

### Bug: Move Stacking Conflict (Warrior Killed)

Moved warrior to (9,24) where slinger was already stationed. Both are military (FORMATION_CLASS_LAND_COMBAT) — Civ 6 doesn't allow stacking same formation class. The move command returned "MOVING_TO|9,24" (success), but the warrior never actually moved. It stayed at (9,25) exposed to 3 barbarians and died next turn.

**Fix:** Added pre-validation stacking check to `build_move_unit()`. Uses `Map.GetUnitsAt(x,y):Units()` iterator to scan target tile for friendly units of the same formation class. Returns `ERR:STACKING_CONFLICT|Friendly UNIT_SLINGER already on (9,24)`.

### Bug: Attack Validation Crash

The initial attack validation used `tgtPlot:GetUnit(i)` which is **nil in InGame context**. Only `Map.GetUnitsAt(x,y)` with `:Units()` iterator works for accessing units on a tile in InGame.

**Fix:** Rewrote enemy presence check in `build_attack_unit()` to use `Map.GetUnitsAt():Units()`. Also added `ERR:NO_ENEMY` pre-check and melee attack warning about unit displacement.

### Bug: Governor Appointment Crashes Game

`appoint_governor` with `PlayerOperations.APPOINT_GOVERNOR` caused a full game crash (process terminated). The Lua code passed the operation to `UI.RequestPlayerOperation` without verifying the PlayerOperations constants exist.

**Fix:** Added nil-safety checks for `PlayerOperations.APPOINT_GOVERNOR` and `PARAM_GOVERNOR_TYPE` before calling engine. Returns `ERR:API_MISSING` instead of crashing. Full governor API investigation still pending — the correct appointment mechanism may differ from what we assumed.

### Plot Unit Access API (Critical Discovery)

- `Plot:GetUnit(i)` does **NOT** exist in InGame — causes nil crash
- `Map.GetUnitsAt(x, y)` returns a collection with `:Units()` iterator and `:GetCount()`
- Iterator: `for u in Map.GetUnitsAt(x,y):Units() do ... end`
- Unit has `:GetOwner()`, `:GetType()` in InGame context
- Barbarian owner ID = 63

### end_turn Flow Ordering

Three ordering bugs discovered and fixed in `end_turn()`:
1. **Popups must be dismissed first** — Eureka popups block unit skip commands from taking effect
2. **Diplomacy sessions before blocking check** — Spain diplomacy was the real blocker but ENDTURN_BLOCKING_UNITS was reported
3. **Fortify already-fortified** — Warrior auto-woke from barb proximity, `GetFortifyTurns()=2` but `CanStartOperation(FORTIFY)` returned false. Added check for already-fortified state.

### Status

- 28 tools total
- Skip fix: confirmed working (GameCore FinishMoves)
- Stacking pre-check: code ready (needs reboot to test)
- Attack validation: code ready (needs reboot to test)
- Governor appointment: safely gated but untested (game crashed)
- **Loaded Turn 33 save**, continuing playtest

## 2025-02-09: Source Code Spelunking — Purchase API & Governor Crash Root Cause

### Governor Crash Root Cause: `.Hash` vs `.Index`

Reading the game's own UI source (`GovernorPanel.lua` in Expansion2 DLC) revealed the crash cause:

```lua
-- GovernorPanel.lua:223 — what the game actually does:
governorInstance.AppointButton:SetVoid1( governorDef.Index );  -- INDEX, not Hash!

-- GovernorPanel.lua:556-557 — the appointment call:
kParameters[PlayerOperations.PARAM_GOVERNOR_TYPE] = eGovernor;  -- eGovernor is .Index
UI.RequestPlayerOperation(Game.GetLocalPlayer(), PlayerOperations.APPOINT_GOVERNOR, kParameters);
```

Our code was passing `governor.Hash` — a large number like `-1352788443`. The engine expected `.Index` (small int like 0-6). Passing Hash caused an out-of-bounds access in C++ → hard crash that `pcall` can't catch.

**Fix:** Change `PARAM_GOVERNOR_TYPE` to use `.Index`. Same applies to `ASSIGN_GOVERNOR` and `PROMOTE_GOVERNOR`.

### Gold/Faith Purchase API (from `ProductionPanel.lua`)

Purchasing units/buildings uses `CityManager.RequestCommand` (not `RequestOperation`):

```lua
-- Purchase a unit with gold:
local tParameters = {}
tParameters[CityCommandTypes.PARAM_UNIT_TYPE] = row.Hash           -- Hash for units!
tParameters[CityCommandTypes.PARAM_MILITARY_FORMATION_TYPE] = MilitaryFormationTypes.STANDARD_MILITARY_FORMATION
tParameters[CityCommandTypes.PARAM_YIELD_TYPE] = GameInfo.Yields["YIELD_GOLD"].Index  -- Index for yield!
CityManager.RequestCommand(city, CityCommandTypes.PURCHASE, tParameters)

-- Purchase a building with gold:
tParameters[CityCommandTypes.PARAM_BUILDING_TYPE] = row.Hash
tParameters[CityCommandTypes.PARAM_YIELD_TYPE] = GameInfo.Yields["YIELD_GOLD"].Index
CityManager.RequestCommand(city, CityCommandTypes.PURCHASE, tParameters)

-- Check if purchaseable:
CityManager.CanStartCommand(city, CityCommandTypes.PURCHASE, true, tParameters, false)

-- Get cost:
city:GetGold():GetPurchaseCost(YIELD_TYPE_INDEX, unitHash, formationType)
```

Key pattern differences from production:
- Production: `CityManager.RequestOperation(city, CityOperationTypes.BUILD, params)` with `CityOperationTypes.PARAM_*`
- Purchase: `CityManager.RequestCommand(city, CityCommandTypes.PURCHASE, params)` with `CityCommandTypes.PARAM_*`
- Yield type uses `.Index`, unit/building type uses `.Hash`

### Auto-Reconnect on Dead Socket

After game crashes, the MCP server's TCP socket goes dead but `is_connected` still returns true (socket not marked as closing). Added retry logic in `_execute_and_collect`: catches `IncompleteReadError`/`ConnectionError`/`OSError`, calls `reconnect()`, and retries once. Lock is held across both attempts to prevent interleaving.

### Hash vs Index Summary (CRITICAL reference)

| API | Parameter | Uses |
|-----|-----------|------|
| Production `PARAM_UNIT_TYPE` | `CityOperationTypes.PARAM_UNIT_TYPE` | `.Hash` |
| Purchase `PARAM_UNIT_TYPE` | `CityCommandTypes.PARAM_UNIT_TYPE` | `.Hash` |
| Purchase `PARAM_YIELD_TYPE` | `CityCommandTypes.PARAM_YIELD_TYPE` | `.Index` |
| Governor `PARAM_GOVERNOR_TYPE` | `PlayerOperations.PARAM_GOVERNOR_TYPE` | `.Index` |
| Governor `PARAM_CITY_DEST` | `PlayerOperations.PARAM_CITY_DEST` | city ID |

### Status

- Governor crash understood — fix pending (`.Index` not `.Hash`)
- Purchase API mapped — implementation pending
- Auto-reconnect added to connection layer
- Turn 33 save loaded, ready to playtest

## 2026-02-09: Playtest Session 7 — Melee Attacks, Diplomacy Blocking, Governor Validation

### Melee Attack Root Cause (FINALLY!)

Two separate issues conspired to make melee attacks silently fail:

**Issue 1: `MOVE_IGNORE_UNEXPLORED_DESTINATION` breaks visible-tile attacks**

The game source (`Civ6Common.lua`) has two movement functions:
- `MoveUnitToPlot()` — uses `PARAM_MODIFIERS = UnitOperationMoveModifiers.ATTACK` (just ATTACK, value=16)
- `RequestMoveOperation()` — uses `ATTACK + MOVE_IGNORE_UNEXPLORED_DESTINATION` (value=16400)

We were using the second pattern. But `MOVE_IGNORE_UNEXPLORED_DESTINATION` (value=16384) causes `CanStartOperation` to return `false` for visible tiles with enemies. The first pattern (ATTACK only) works correctly for adjacent melee attacks.

**Issue 2: Diplomacy popups block ALL game operations silently**

When Philip II's agenda popup was active, `UnitManager.RequestOperation()` silently does nothing — no error, no movement, no damage. `CanStartOperation()` returns `false` for every tile. Even `CityManager.RequestOperation()` for production fails silently. This is the game's way of forcing you to handle diplomacy first.

**Fix applied:**
```lua
-- Use ATTACK only (not ATTACK + MOVE_IGNORE_UNEXPLORED_DESTINATION)
params[UnitOperationTypes.PARAM_MODIFIERS] = UnitOperationMoveModifiers.ATTACK
-- Pre-check with CanStartOperation (4th arg is params, not 3rd!)
if not UnitManager.CanStartOperation(unit, UnitOperationTypes.MOVE_TO, nil, params) then
    print("ERR:ATTACK_BLOCKED")
end
UnitManager.RequestOperation(unit, UnitOperationTypes.MOVE_TO, params)
```

**Key API detail:** `CanStartOperation(unit, operation, mapOrNil, paramsTable)` — the params table is the 4th argument, NOT the 3rd. The game source confirms this pattern.

### Governor API — `GetGovernorList()` Returns Boolean

The `GetGovernorList()` method returns `false` when empty and `true` when non-empty — never a Lua table. This broke our governor listing code.

**Working pattern:** Iterate `GameInfo.Governors()`, check `pGovs:HasGovernor(row.Hash)`, then `pGovs:GetGovernor(row.Hash)` to get the governor object.

Governor object methods: `GetName()`, `GetAssignedCity()`, `IsEstablished()`, `GetTurnsToEstablish()`, `GetType()`, `GetOwner()`.

### Enemy Target Selection Fix

When multiple units share a tile (e.g., captured barb builder + barb warrior), the attack code now prefers military targets (Combat > 0) over civilians. Previously it picked the first unit found, which could be a builder.

### Playtest Results (Turn 33→41)

- **Turn 38:** First successful melee kill (barb warrior 21hp) + captured barb builder
- **Turn 39:** User saved for governor testing. Killed 1hp barb warrior, attacked barb slinger.
- **Turn 40:** Ranged-killed barb slinger (28hp). Lost builder #1 to barb slinger at (9,25).
- **Turn 41:** Early Empire completed → governor point. Appointed Pingala, assigned to Kraków (5 turns to establish). Set Mysticism as next civic.

### Lessons Learned

1. **Always dismiss diplomacy before attempting ANY game operation** — popups silently block everything
2. **`end_turn` should auto-detect pending diplomacy** and resolve it or report it before units/production fail
3. **`RequestOperation` returns nil for both success AND failure** — always pre-check with `CanStartOperation`
4. **`CanStartOperation` arg order matters**: `(unit, opType, nil, paramsTable)` not `(unit, opType, paramsTable, showReasons)`
5. **Builders are tissue paper** — barbarian slingers captured two of our builders this session. Need escort or keep deep in territory

### Code Changes

| File | Change |
|------|--------|
| `lua_queries.py` | Fixed melee: ATTACK only (not +IGNORE), added CanStartOperation pre-check |
| `lua_queries.py` | Fixed enemy targeting: prefer military over civilian units |
| `lua_queries.py` | Fixed governor query: HasGovernor/GetGovernor instead of GetGovernorList |
| `lua_queries.py` | Added turns_to_establish to AppointedGovernor dataclass |
| `game_state.py` | Updated governor narration to show establishment turns |
| `MEMORY.md` | Added melee attack, governor iteration patterns |

## 2026-02-09: Playtest Session 8 — Turns 41→51, Economy Gaps, Envoy Hack

### Gameplay Progress (Turn 41→51)

- **Turn 41→48:** Steady growth. Granary built, warrior healed to full. Kraków growing well with 4 farms but only 4 production — painfully slow builds.
- **Turn 49:** Archer set as production (17 turns at 4 prod). Attempted to gold-purchase a builder (190g treasury) but builder costs 215g — can't afford it. Production and purchase both returned cryptic errors initially due to diplomacy popup blocking, then production worked after popup resolution.
- **Turn 50:** Kraków grew to pop 7. Scout retreated north from 2 barbarian warriors near (13,17) and (15,16). Put home garrison (slinger + 2 warriors) on alert.
- **Turn 51:** Mysticism civic completed. Chose Craftsmanship next (unlocks Agoge/Ilkum policy cards for faster unit+builder production). Sent envoy to Cardiff (Industrial CS) for production bonus. Scout set to auto-explore.

### Key Discoveries

**Purchase cost != production cost.** `get_city_production` shows production cost (builder = 50 hammers) but gold purchase cost is much higher (215g). The `purchase_item` tool gives `CANNOT_PURCHASE|unknown` with no reason — should report "not enough gold" and the actual cost.

**Envoy sending requires raw Lua.** The `GIVE_INFLUENCE_TOKEN` player operation needs `PARAM_PLAYER_ONE` set to the city-state player ID. First call returned tokens=1 still (async?), second call with `PARAM_FLAGS=0` worked and reduced tokens to 0. No dedicated tool exists.

**`set_city_production` false error.** The tool reported `PRODUCTION_FAILED|UNIT_ARCHER was not added to queue` but the archer WAS actually added (confirmed by `get_cities`). The post-verification reads queue size too early (same-frame stale read). This is a known async issue.

**Alert vs fortify for idle garrison.** Fortified units still trigger "Command Units" blocker every turn, requiring manual skip. Alert units sleep until enemies approach — better for garrison duty since they don't block end-turn.

### Current Game State (Turn 51)

| Metric | Value |
|--------|-------|
| Score | 39 (Spain: 70) |
| Gold | 195 (+4/turn) |
| Science | 5.8 |
| Culture | 5.4 |
| Research | Writing (2 turns) |
| Civic | Craftsmanship (just started) |
| City | Kraków pop 7, building Archer (17 turns) |
| Military | 2 warriors (alert), 1 slinger (alert), 1 scout (auto-explore) |
| Envoys | 1 in Cardiff |

### Tools That Need To Be Built

| Priority | Tool | Why |
|----------|------|-----|
| **HIGH** | `send_envoy(city_state_id)` | Currently requires raw Lua. Envoy allocation is a blocking notification when tokens are available. Need to enumerate known city-states with their types and current envoy counts. |
| **HIGH** | `choose_pantheon(belief_type)` | Pantheon selection is a blocking notification. Currently requires `execute_lua` with `PlayerOperations.FOUND_PANTHEON`. Should list available beliefs with descriptions. |
| **HIGH** | Better purchase error messages | `purchase_item` returns `CANNOT_PURCHASE|unknown` — should report actual cost vs treasury balance so the agent knows *why* it can't afford something. |
| **MEDIUM** | `get_great_people()` | No visibility into great person progress or recruitment options. |
| **MEDIUM** | `manage_trade_routes()` | Trader unit exists but no tool for setting trade route destinations. |
| **MEDIUM** | `get_city_details(city_id)` | Detailed per-city view: tile yields, worked tiles, amenity breakdown, housing sources. Current `get_cities` is summary-only. |
| **LOW** | `upgrade_unit(unit_id)` | Unit upgrade (e.g. slinger→archer) requires gold + tech. Currently no tool. |
| **LOW** | `swap_tiles(city_id, x, y)` | Citizen tile management between cities. |
| **LOW** | `rename_city(city_id, name)` | Cosmetic but useful. |

### Existing Tool Issues (now resolved — see next entry)

| Tool | Issue | Status |
|------|-------|--------|
| `set_city_production` | False-negative error — reports failure when production actually set (async verification reads stale queue) | **FIXED** |
| `purchase_item` | No cost information in error — "CANNOT_PURCHASE\|unknown" instead of "costs 215g, you have 190g" | **FIXED** |
| `get_city_production` | Shows production cost but not purchase cost — agent can't evaluate gold-buy decisions | **FIXED** |
| `execute_unit_action(fortify)` | Fortified units still block end-turn — agent must skip them each turn or use alert instead | Known (use alert) |
| `end_turn` | "Command Units" blocker fires for fortified units that didn't move — confusing since they have standing orders | Known (use alert) |

## 2026-02-09: Tool Expansion — 5 New Tools, 3 Bug Fixes, Full Envoy/Pantheon/Upgrade Support

### Bug Fixes

**1. `purchase_item` — informative error messages**

Previously returned `CANNOT_PURCHASE|unknown`. Now computes cost and balance BEFORE the `CanStartCommand` check, so the error reads: `"costs 215g but you only have 199g"`. On success, also reports actual gold spent.

**2. `set_city_production` — eliminated false-negative**

Removed same-frame `GetSize()` post-verification (always returned stale 0). Now pre-checks with `bq:CanProduce(item.Hash, true)` and trusts the async `RequestOperation`. Reports success with turn estimate: `"PRODUCING|UNIT_ARCHER|15 turns"`.

**3. `get_city_production` — shows gold purchase costs**

Added `GetPurchaseCost()` call for every producible item. Output now includes buy price: `"UNIT_BUILDER (cost 50, 15 turns, buy: 215g)"`. Districts show `-1` (not purchasable). Uses `MilitaryFormationTypes.STANDARD_MILITARY_FORMATION` for units, `-1` for buildings.

### New Tools (5)

**4. `get_city_states` — city-state & envoy visibility**

Lists all known city-states with:
- Type (Scientific, Industrial, Trade, Cultural, Religious, Militaristic)
- Envoys sent by us (via `Players[csID]:GetInfluence():GetTokensReceived(myID)`)
- Current suzerain (via `Players[csID]:GetInfluence():GetSuzerain()`)
- Available envoy tokens and whether we can send to each CS

**Key API discovery:** `GetTokensReceived` and `GetSuzerain` must be called on the **city-state's** `GetInfluence()` object, not the player's. Calling on our own influence always returned 0.

**5. `send_envoy(city_state_player_id)` — assign envoy tokens**

Sends an envoy via `UI.RequestPlayerOperation(GIVE_INFLUENCE_TOKEN)`. Pre-checks `GetTokensToGive() > 0` and `CanGiveTokensToPlayer()`. Reports remaining tokens after send.

**6. `get_available_beliefs` — pantheon belief listing**

Shows current pantheon status (or "no pantheon"), faith balance, and all available beliefs with descriptions. Filters out beliefs already taken by other players by checking each alive player's `GetReligion():GetPantheon()`.

**7. `choose_pantheon(belief_type)` — found a pantheon**

Founds a pantheon via `UI.RequestPlayerOperation(FOUND_PANTHEON, {PARAM_BELIEF_TYPE=belief.Hash})`. Pre-checks that no pantheon exists and the belief type is valid.

**8. `upgrade_unit(unit_id)` — unit upgrades**

Upgrades a unit (e.g. slinger → archer) via `UnitManager.RequestCommand(UPGRADE)`. Pre-checks with `CanStartCommand`. Uses `UpgradeUnitCollection[1].UpgradeUnit` to resolve the target type (not a direct field — it's a collection from a many-to-many relationship).

**Live-tested:** Slinger → Archer upgrade confirmed working in-game during Turn 51.

### API Discoveries

| Pattern | Detail |
|---------|--------|
| CS envoy count | `Players[csID]:GetInfluence():GetTokensReceived(myID)` — call on CS, not player |
| CS suzerain | `Players[csID]:GetInfluence():GetSuzerain()` — no args, returns player ID or -1 |
| CS type | `GameInfo.Leaders[cfg:GetLeaderTypeName()].InheritFrom` → `"LEADER_MINOR_CIV_INDUSTRIAL"` etc. |
| Pantheon check | `GetPantheon() >= 0` (no `HasPantheon()` method) |
| Belief hash | `belief.Hash` for `PARAM_BELIEF_TYPE` (not Index) |
| Unit upgrade path | `GameInfo.Units[type].UpgradeUnitCollection[1].UpgradeUnit` (not `.UpgradeUnit` directly) |
| Purchase cost | `city:GetGold():GetPurchaseCost(yieldIdx, hash, formationType)` — buildings use `-1` for formation |

### Code Changes

| File | Change |
|------|--------|
| `lua_queries.py` | Fixed `build_purchase_item`: compute cost/balance before CanStartCommand, include in error |
| `lua_queries.py` | Fixed `build_produce_item`: pre-check CanProduce, removed stale GetSize post-verify |
| `lua_queries.py` | Added gold purchase cost to `build_set_city_production` via GetPurchaseCost |
| `lua_queries.py` | Added `gold_cost` field to `ProductionOption` dataclass |
| `lua_queries.py` | Added 6 new dataclasses: CityStateInfo, EnvoyStatus, BeliefInfo, PantheonStatus, UnitUpgradeInfo |
| `lua_queries.py` | Added 6 query builders: city_states, send_envoy, pantheon_status, choose_pantheon, unit_upgrade, upgrade_unit |
| `lua_queries.py` | Added 2 parsers: parse_city_states_response, parse_pantheon_status_response |
| `lua_queries.py` | Updated NOTIFICATION_TOOL_MAP and BLOCKING_TOOL_MAP for pantheon/envoy tools |
| `game_state.py` | Added 6 GameState methods for envoys, pantheon, and upgrades |
| `game_state.py` | Added 2 narration methods: narrate_city_states, narrate_pantheon_status |
| `game_state.py` | Updated narrate_city_production to show gold purchase cost |
| `server.py` | Added 5 new MCP tools: get_city_states, send_envoy, get_available_beliefs, choose_pantheon, upgrade_unit |
| `CLAUDE.md` | Added City-States & Envoys, Pantheon & Religion, Unit Upgrades sections |
| `MEMORY.md` | Added envoy, pantheon, upgrade API patterns |

### Tool Count: 28 → 33

---

## 2026-02-09: Tech Debt Refactor + Extended Playtest — Turn 55→100

### Refactor: `lua_queries.py` Deduplication

Read the entire 2583-line file end-to-end looking for tech debt. Found significant copy-paste duplication across 20+ Lua code builders — the same unit lookup, city lookup, and error-bail patterns repeated verbatim everywhere. Extracted:

- **`_bail(msg)`** — Python helper returning `print("ERR:..."); print("---END---"); return`. Deduplicates ~40 bail sites at the Python string level (Lua output unchanged, zero runtime risk).
- **`_lua_get_unit(unit_index)`** — 3-line InGame unit lookup snippet (GetLocalPlayer + UnitManager.GetUnit + nil check). Used by 11 action builders.
- **`_lua_get_unit_gamecore(unit_index)`** — Same but for GameCore context (Players[me]:GetUnits():FindID). Used by 2 builders.
- **`_lua_get_city(city_id)`** — 3-line city lookup snippet. Used by 4 builders.
- **`_ITEM_TABLE_MAP` / `_ITEM_PARAM_MAP`** — Module-level constants extracted from duplicate local dicts in `build_produce_item` and `build_purchase_item`.

Also renamed misleading `build_set_city_production` → `build_city_production_query` (it lists available production, doesn't set it), and removed dead `build_dismiss_popups` (raised NotImplementedError, never called). Added Code Architecture section to CLAUDE.md.

All syntax checks passed. Live-tested against running game — every affected tool works.

### Playtest: Poland (Jadwiga) — Turns 55→100

**The big picture:** Started at Turn 55 with 1 city (Kraków), Score 48 vs Spain 72. By Turn 100: 3 cities, Score 92 vs Spain 160. Still behind, but expanding. The game is getting interesting.

**Key milestones:**
- **Turn 66:** Settler completed (Colonization policy cut build time from 19→8 turns). Founded Wroclaw at (14,25) on horses + river. Appointed Magnus.
- **Turn 76:** Political Philosophy completed → switched to Classical Republic (4 policy slots vs Chiefdom's 2). This was a big power spike — diplomatic + wildcard slots opened up envoy generation and military flexibility.
- **Turn 81:** Games & Recreation → first envoy token. Reinforced Cardiff (Industrial) suzerainty to 4 envoys.
- **Turn 88–91:** Barbarian two-front attack. Warrior at (8,25) threatening Kraków, archer at (13,23) hitting Wroclaw. My archer killed the warrior in 3 ranged shots (100→58→dead). My warrior attacked the archer and got a Battlecry promotion (+7 vs ranged) — the heal-on-promote saved it from 16 HP.
- **Turn 92:** Settler #2 built, Currency tech done. Routed settler south through a goody hut.
- **Turn 99:** Founded Gdansk at (11,28) on rice. Fertility Rites pantheon gave a free builder with 3 charges. God King policy slowly generated the 25 faith needed.
- **Turn 100:** 3 cities, 2 archers, 2 warriors, 1 scout, 2 builders. Researching Horseback Riding, civic Drama & Poetry.

### Reflections on Playing to Win

**What's working:**
- The turn loop is smooth now. Query → reason → act → end turn. The notification system makes events visible. I know when units take damage, cities finish building, techs complete.
- Policy management is genuinely strategic. Swapping Colonization → Agoge → Ilkum at the right moments made a real difference. Classical Republic's wildcard slot accepting military policies is powerful.
- Promotion timing matters. Saving the warrior's promotion until it was at 16 HP, then promoting (which heals to full) was a clutch play. This is the kind of tactical decision that makes combat interesting.
- The builder purchase option (230g) as an alternative to building is a real strategic choice. I accumulated 368 gold — enough to purchase units instantly when needed.

**What's frustrating:**
1. **Builder improve action is unreliable on forest tiles.** I spent 5 turns trying to build a farm on a forest tile at (10,25). Each turn it said "IMPROVING" but the charge never consumed and the improvement never appeared. The forest was never removed. Eventually I gave up. Needs investigation — might be a missing tech requirement for forest removal, or the BUILD_IMPROVEMENT operation isn't handling feature removal correctly.
2. **Movement through difficult terrain is tedious.** Moving a builder from (8,22) to (10,25) took 4 turns due to marsh and forest movement costs. Each turn is: check position, realize it didn't arrive, issue same move command. Would be nice if `get_units` showed "en route to (x,y)" for multi-turn moves.
3. **Two units stacked at city center blocks purchases.** When the settler spawned at Kraków alongside the new archer, I couldn't purchase a builder (stacking conflict). Had to move the settler out first. The error message "Too many units of the same class" is correct but surprising when you're trying to buy, not build.
4. **Government change notification lingers.** After switching to Classical Republic via `RequestChangeGovernment`, the "Consider Changing Governments" notification still blocked end_turn. Had to manually call `SetGovernmentChangeConsidered(true)` via raw Lua. Should be handled automatically.
5. **Score gap is alarming.** Spain is at 160 vs my 92 on Turn 100. That's a 70% lead. They likely have 4-5 cities, better tech, more military. I need to expand faster and get districts online. Three cities with no specialty districts is not competitive at this stage.

**Strategic assessment:**
- **Economy:** Gold is fine (368 banked, +3/turn) but science (9.6) and culture (9.5) are low for Turn 100. Need Campus districts ASAP.
- **Military:** 2 archers + 2 warriors is adequate defense but can't project power. Horseback Riding will unlock horsemen for offense.
- **Expansion:** 3 cities is the minimum. Should push for a 4th city around Turn 120. The area south of Gdansk is mostly unexplored.
- **Biggest risk:** Spain declaring war while I'm mid-expansion with no walls and minimal military.

### Status

- **Turn 100**, Poland, Score 92 vs Spain 160
- 3 cities: Kraków (pop 10), Wroclaw (pop 4), Gdansk (pop 1)
- 33 tools, all working
- Refactor complete: ~150 lines of duplication eliminated
- **Next:** Campus districts in Kraków/Wroclaw, Horseback Riding for cavalry, scout south for 4th city site, investigate builder forest-improve bug

## 2026-02-09: Strategic Awareness Tools + Playtest Rewind

### Retrospective: What Went Wrong in Turns 55–100

After reflecting on the first playtest, the core problem became clear: **I never scouted properly.** The scout was sent out early but I didn't use map intelligence to inform city placement. All three cities were founded reactively — wherever the settler happened to be — rather than strategically targeting fresh water, luxury resources, or defensible terrain. The empire resources tool confirmed the damage: only 1 luxury (Wine), most tiles unimproved, no iron income.

The tooling gap was real too. `get_map_area` showed resources but didn't classify them (strategic/luxury/bonus), so I couldn't distinguish between critical iron and throwaway stone at a glance. There was no way to survey the whole empire's resource picture. And the settle advisor only triggered on settle *failure* — by then you've already committed the settler.

### New Tools: 3 Strategic Awareness Enhancements

**Enhancement 1: Resource classification in `get_map_area`**
- Resources now show class markers: `[IRON*]` (strategic), `[DIAMONDS+]` (luxury), `[WHEAT]` (bonus)
- Added `resource_class` field to `TileInfo` dataclass
- Tech-gated: only shows resources you've researched the prerequisite tech for (e.g. coal hidden until Industrialization)

**Enhancement 2: Standalone settle site advisor**
- New `get_settle_advisor` tool — callable proactively with any settler, not just on settle failure
- Improved scoring formula: `food×2 + prod×2 + gold + water_bonus + defense_bonus + luxury×4 + strategic×3`
- Defense scoring: hills center (+2), adjacent hills (+1 each), river (+1)
- Resources classified in output: `[S] IRON`, `[L] DIAMONDS`, `[B] WHEAT`
- Reused narration in the `found_city` fallback path

**Enhancement 3: Empire resource summary**
- New `get_empire_resources` tool — birds-eye view of all resources
- **Strategic stockpiles**: amount/cap, net income per turn, import/demand breakdown (e.g. `HORSES: 50/50 (+2/turn) [income 2, import 2]`)
- **Luxury counts**: how many you own + tradeable surplus
- **Owned tile resources**: grouped by class, improved/UNIMPROVED status with coordinates
- **Nearby unclaimed**: resources within 5 tiles of cities with distance and nearest city name
- Runs in InGame context for `GetResourceStockpileCap` / `GetResourceAccumulationPerTurn` access
- All sections tech-gated via `pRes:IsResourceVisible(rIdx)`

**Tech visibility fix (critical)**
- Initial implementation leaked hidden resources — showing COAL, URANIUM, ALUMINUM before the player had the required tech
- Fixed all three queries: `build_map_area_query` (GameCore — uses `PrereqTech` + `HasTech` check), `build_settle_advisor_query` (same pattern), `build_empire_resources_query` (InGame — uses `IsResourceVisible` directly)
- Key finding: `IsResourceVisible` only exists in InGame context. GameCore needs manual `PrereqTech` lookup against `GetTechs():HasTech()`

**Promotion detection in `get_units`**
- Units with pending promotions now show `**NEEDS PROMOTION**` flag
- Detection: `GetExperience():GetExperiencePoints() >= GetExperienceForNextLevel()`
- This was triggered by a bug where the scout had an unnoticed pending promotion that blocked both auto-explore and end-turn for multiple turns

### Tool Bug Fixes (from previous session, now validated)

Four fixes from the earlier plan, all confirmed working:
1. **Builder improve on forest**: `CanStartOperation` now gets real params, feature detection on failure
2. **Government change auto-resolve**: `end_turn()` retry loop auto-dismisses the notification
3. **Policy slot validation**: `CanSlotPolicy` check prevents silent slot clearing
4. **Purchase stacking pre-check**: `Map.GetUnitsAt()` identifies blocking unit by name

### Playtest Rewind: Turn 33 Fresh Start

Loaded save from Turn 33 to replay with the new strategic tools. Initial state: 1 city (Kraków), 251 gold, 5 units, Score 30 vs Spain 47.

**Early moves (Turns 33–39):**
- Dealt with 3-barbarian incursion south of Kraków (2 warriors + 1 slinger)
- Promoted warrior with Battlecry (+7 CS vs melee/ranged) — heal-on-promote from 46→100 HP was clutch
- Upgraded slinger to archer (Archery already researched)
- Promoted archer with Volley (+5 RS vs land)
- Started settler production, researching Bronze Working to reveal iron
- Builder improving floodplains farm at (8,24), second builder heading to rice at (9,22)
- Scout auto-exploring far east, discovered a civ (player 12) near (26,22)

**Target:** Beat the previous Turn 100 score of 92. Key differences this time:
- Use `get_settle_advisor` before committing settlers
- Use `get_empire_resources` to track resource gaps
- Scout aggressively to find luxury resources for amenities
- Prioritize fresh water + luxury access for city placement

### Status

- **Turn 39**, Poland, Score ~32
- 1 city (Kraków, pop 6), settler in production
- 35 tools (2 new: `get_settle_advisor`, `get_empire_resources`)
- All 4 bug fixes validated
- **Next:** Clear remaining barbarians, found 2nd city with settle advisor guidance, improve tiles for production, push to Turn 100

## 2026-02-09: Playtest Turns 41–60 — Policy Fix, Popup Handling, Settlement Misadventure

### Bug Fix: `CanSlotPolicy` Validation

The `CanSlotPolicy` validation added in Fix 3 was rejecting valid policy assignments — "POLICY_COLONIZATION (SLOT_ECONOMIC) cannot go in slot 0 (Economic)" is obviously wrong. Root cause: `CanSlotPolicy` likely requires the `UNLOCK_POLICIES` async operation to complete first, but the check runs in the same frame before the unlock is processed.

**Fix:** Replaced `CanSlotPolicy` with manual slot-type compatibility check using a `slotTypeMap` lookup. Economic/Military slots must match exactly; Diplomatic/Wildcard slots accept any policy type. Simple and reliable.

### Bug Fix: Stubborn Popup Dismissal

`BoostUnlockedPopup` and `GreatWorkShowcase` weren't being dismissed by `dismiss_popup`. The tool scans Lua states with "Popup"/"Wonder"/"Moment" keywords, but `GreatWorkShowcase` doesn't contain any of those. And InGame child popup list only had 3 generic entries.

**Fix:** Added `BoostUnlockedPopup` and `GreatWorkShowcase` to the InGame child popup list in `dismiss_popup`. Both respond to `SetHide(true)` via `ContextPtr:LookUpControl`.

### Bug Fix: `found_city` Position Confusion

The `found_city` error "Too close to Kraków (distance 3, need > 3)" was confusing because I thought the settler was at (8,20) which is actually distance 4. **Root cause:** async movement. The `MOVING_TO` response shows the target destination, but through jungle/hills terrain the settler ran out of moves at an intermediate tile (8,21, distance 3). The error message didn't report the settler's actual position.

**Fix:** Error now includes `"settler at X,Y"` so the actual position is visible when the distance check fails.

**Lesson:** `MOVING_TO` means "path queued toward target" not "arrived at target". Always verify unit position with `get_units` before attempting actions that depend on location.

### Gameplay: Turns 41–60

**Turns 41–46: Exploration & Improvement**
- Set Colonization (+50% settlers) + Discipline (+5 vs barbs) policies
- Sent warriors in 3 directions to explore fog of war — discovered Silk at (12,21), Wine at (7,27), Sri Pada natural wonder, 2 goody huts, lots of banana/rice land
- Improved 3 tiles (farm on Rice 8,22, farm on floodplains 9,25 and 10,24)
- Met Mapuche (Lautaro) — first meeting, exchanged delegations (both rejected ours)
- Completed Craftsmanship civic → unlocked Agoge (+50% military production)

**Turns 47–54: Barbarian Pressure & Losses**
- Completed Bronze Working → revealed iron (none near Kraków!)
- Pantheon founded: Fertility Rites (free builder + 10% growth)
- Completed Mysticism → 2 envoy tokens, sent to Cardiff (Industrial, 3 envoys)
- Lost scout to 3 barbarian warriors (ZOC-locked at 11,17, killed)
- Lost warrior to barbarian slinger pursuit (2 HP, couldn't escape)
- Settler completed turn 54 with Magnus (no pop loss)

**Turns 54–60: Settlement Misadventure**
- Settle advisor recommended (8,20) initially, then (10,20) with better vision
- Both turned out to be distance ≤ 3 from Kraków — wasted 5 turns moving settler back and forth
- Final target: (12,20), advisor #1 with score 240 — IRON, Silk, Bananas, defense 4
- Bought warrior for defense (160g), set archer production, started Writing research
- Currently moving settler to (12,20), ETA ~2 turns

**Score at Turn 60:** Poland 58 vs Spain 102, Mapuche 71. Behind schedule — delayed city founding is the #1 problem.
