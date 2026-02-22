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

## 2026-02-09: Midgame Tool Suite + Playtest Turns 66–84

### Self-Assessment at Turn 75

Paused at turn 75 to do a comprehensive gameplay audit. Graded ourselves **C-**:

- **Score**: 84 vs Spain 129, Mapuche 94. Last place among known civs.
- **Cities**: Only 2 at turn 75 (benchmark says 3). Lodz founded turn ~62, very late.
- **Production**: Kraków pop 9 but only 5 production — entirely floodplain farms, zero mines.
- **Luxuries**: Zero improved. Zero amenities surplus. Growth penalty active.
- **Trade**: Zero trade routes. Foreign Trade civic researched but never built a Trader.
- **Science**: 7.1/turn — should be 15-20 by turn 75. No Campus anywhere.
- **Governors**: 2 unspent points sitting idle.
- **Districts**: None built or in progress at turn 75.

Root causes: late second city, no builder cycling, no district timing, gold hoarding instead of investing.

### Tool Gaps Identified

The audit revealed 8 concrete gaps preventing better play:

1. **District placement advisor** — no way to evaluate adjacency bonuses before committing
2. **District coordinates in production** — `set_city_production` couldn't pass x,y for district tiles
3. **Tile purchase** — couldn't buy tiles for luxury resources outside borders
4. **Government change** — had to use raw Lua to switch governments
5. **Enhanced tech/civic info** — no boost conditions, costs, or unlock lists shown
6. **Combat feedback** — attack results only showed "HP before", never damage dealt
7. **Great People tracking** — no visibility into GP timeline or recruitment race
8. **City yield focus** — no way to bias citizen assignment toward production/food

### Implementation: 8 Enhancements

Built all 8 in a single implementation session. Key technical details:

**District Advisor** (`get_district_advisor`): Uses `CityManager.GetOperationTargets` to get valid tiles, then hardcoded adjacency formulas for 6 common district types (Campus, Holy Site, Industrial Zone, Commercial Hub, Theater, Harbor). Returns top 10 tiles ranked by total adjacency.

**Tile Purchase** (`get_purchasable_tiles` + `purchase_tile`): Uses `CityManager.GetCommandTargets` with `PARAM_PLOT_PURCHASE=1` for valid tiles, `GetPlotPurchaseCost(x,y)` for costs. Results sorted luxury-first.

**District Placement in Production**: Added `target_x`/`target_y` optional params to `build_produce_item`, passing `PARAM_X`/`PARAM_Y` to the build operation.

**Government Change** (`change_government`): Must call `SetGovernmentChangeConsidered(true)` before `RequestChangeGovernment(govIndex)` — without it, the change silently fails.

**Tech/Civic Enhancement**: Added boost status, trigger descriptions, progress percentages, turn counts, and key unlocks (units, buildings, districts, improvements, revealed resources) to the existing query. Pipe-escaped boost descriptions to prevent parser field miscount.

**Great People** (`get_great_people`): `Game.GetGreatPeople():GetTimeline()` returns the full GP timeline. Shows class, individual name, era, recruitment cost, current claimant, and our points.

**City Focus** (`set_city_focus`): Uses `CityManager.RequestCommand` with `CityCommandTypes.SET_FOCUS`. `PARAM_FLAGS=1` toggles favored yield. Must clear existing focus before setting new one.

**Combat Feedback**: Added post-attack HP read for ranged attacks. Melee uses pcall-wrapped read since units may have moved/died.

### Bugs Found During Live Testing

1. **Civic progress methods nil in GameCore**: `cu:GetCulturalProgress()` and `cu:GetTurnsLeft()` don't exist in GameCore context. Fixed by using `GetCultureCost()` (works) and estimating turns from culture yield.

2. **Lua 5.1 has no `goto`**: Used `goto continue_gp` / `::continue_gp::` in Great People query — Civ 6 uses Lua 5.1 which doesn't support goto labels. Fixed with nested `if` instead.

3. **City focus API mismatch**: `SetFavoredYield`/`IsYieldFavored` don't exist in InGame. Correct API is `IsFavoredYield` (read) and `CityCommandTypes.SET_FOCUS` via `CityManager.RequestCommand` (write).

4. **Combat HP reads are stale same-frame**: `enemy:GetDamage()` returns pre-attack values when read in the same frame as `RequestOperation`. The damage IS applied (confirmed by next-turn reads showing correct HP), but we can't read it synchronously. This is an engine limitation, not a bug in our code.

### Playtest: Turns 66–84

**Turns 66–75**: Previous session. Completed Irrigation, Political Philosophy. Switched to Classical Republic. Set Agoge + Urban Planning + Ilkum + Charismatic Leader policies. Skirmished with barbarian archers south of Kraków.

**Turns 75–78**: First use of new tools. Bought Wine tile at (7,27) for 105g via `purchase_tile`. District advisor found +2 Campus at (10,23) for Kraków, +4 Campus at (10,21) for Lodz (next to mountain + jungles). Set Lodz Campus with x,y coordinates — worked perfectly.

**Turns 78–81**: Barbarian warrior appeared on Wine tile, engaged with dual archers. Promoted archer (Volley, +5 ranged vs land). Completed Games and Recreation, Military Tradition civics. Bought builder (230g) for Wine improvement.

**Turns 81–84**: Builder heading to Wine for plantation. Kraków finished Water Mill, started Campus at (10,23). Both cities now building Campuses. Military Tradition BOOSTED completed in 3 turns. Set Drama and Poetry as next civic.

### Score Trajectory

| Turn | Score | Spain | Mapuche | Notes |
|------|-------|-------|---------|-------|
| 60   | 58    | 102   | 71      | Only 1 city, no improvements |
| 66   | 73    | 113   | 82      | Lodz founded |
| 75   | 84    | 129   | 94      | Audit + tool implementation |
| 80   | 89    | 143   | 94      | Wine tile bought, campuses started |
| 84   | ~90   | ~147  | ~96     | Builder en route, both campuses queued |

Gap to Spain widening (58 points). Mapuche plateauing. We're accelerating but from too far behind.

### Reflections on Tooling

**What's working well:**
- District advisor is a game-changer — without it, I was blind-placing districts. The +4 Campus at Lodz would have been missed.
- Tile purchase lets me grab luxuries without waiting for border growth — first amenity improvement incoming.
- Enhanced tech/civic output with boost conditions is genuinely useful for decision-making.
- Great People tracker provides strategic awareness I was completely missing.

**What's still lacking:**
- **Trade routes**: Still no tool. Foreign Trade civic researched 30+ turns ago, never built a Trader. This is pure yield waste.
- **Worker automation**: Builder micro is tedious — move, verify position, improve, repeat. An "auto-improve" or "queue improvements" would help.
- **Ranged combat HP reads**: Same-frame staleness makes it hard to judge whether to commit a second shot or move. Would need a 1-frame delay or deferred read.
- **Production queue**: Can only set one item. A proper queue (Campus → Library → Builder) would reduce idle turns.

**Lessons for the AI agent:**
- Buying tiles for luxuries early is worth more than saving gold. Zero amenities for 75 turns was catastrophic.
- Districts should start by turn 40-50, not turn 84. The Campus at Lodz won't complete until turn ~96.
- Two cities by turn 75 is too slow. Need to settle city #2 by turn 40 and city #3 by turn 60.
- Water Mill before Campus was wrong at Krakow — science compounds, production doesn't (much) at this stage.

### Tool Count: 33 → 39

New tools: `get_district_advisor`, `get_purchasable_tiles`, `purchase_tile`, `change_government`, `get_great_people`, `set_city_focus`.

### Status

Turn 84 in progress. Builder 1 tile from Wine improvement. Both cities building Campuses (19 turns Kraków, 12 turns Lodz). Iron Working 7 turns out. Score 89 vs Spain 147. Playable but behind — need to focus on builder cycling and getting those Campuses online.

---

## 2025-02-09: Turn 100 Milestone — Strategic Inflection Point

### Playtest: Turns 84–104

**Turns 84–91**: Builder improved Wine plantation (first luxury!). Astrology completed. Builder headed to Wheat at Lodz but discovered it's the city center tile (can't improve). Redirected to Silk luxury at (12,21). Two Declarations of War appeared — not against us, between unmet civs. Score crossed 101 at turn 90, passing Mapuche briefly.

**Turns 91–95**: Built Silk plantation (second luxury, +1 amenity). Lodz Campus completed turn 94 — only 3 turns for the final stretch. Science jumped from 8.7 to 11.8 instantly. Drama and Poetry civic completed, unlocked Recorded History. Sent envoy to Hunza (Trade city-state), gold income jumped from +9 to +14/turn. Attacked and killed barbarian warriors/scouts threatening southern approach.

**Turns 95–100**: Builder placed Stone quarry at (9,26) for Krakow production. Krakow grew to pop 11. Currency tech completed turn 100 — unlocks Commercial Hub and Market. Recorded History civic completed. Appointed Liang (Builder governor), assigned Magnus to Lodz. Both Archers fortified covering approaches.

**Turns 100–104**: Sailing tech completed (2 turns!). Lodz Granary finished, fixing Housing 2→5 crisis. Both cities now building Libraries. Swapped to **Natural Philosophy** policy (+100% Campus adjacency) — should boost Lodz +4 adj to +8 science. Set Colonization in wildcard slot for future settler production.

### Score Trajectory (continued)

| Turn | Score | Spain | Mapuche | Notes |
|------|-------|-------|---------|-------|
| 84   | ~90   | ~147  | ~96     | Builder en route, campuses queued |
| 91   | 101   | 156   | 100     | Wars elsewhere, silk improved |
| 95   | 110   | 174   | 154     | Lodz Campus online, science +47% |
| 100  | 114   | 188   | 156     | Currency done, both campuses built |
| 104  | 123   | 189   | 166     | Libraries building, Natural Philosophy set |

Spain gap narrowing in rate: was growing +10/turn faster, now ~+3/turn faster. Mapuche surged (probably districts/wonders). We're accelerating but still 3rd.

### Critical Policy Discovery: Natural Philosophy

This is the biggest single-action improvement of the game so far. Natural Philosophy (+100% Campus adjacency) doubles Campus yields:
- Lodz: +4 → +8 science (Campus next to mountain + jungles near Sri Pada)
- Krakow: +2 → +4 science

That's +6 free science from one policy swap — a 46% boost to our 12.9 science output. Should have been set the moment Recorded History was researched.

### Strategic Analysis: Where We Stand

**Strengths:**
- Two Campuses online with strong adjacency (especially Lodz +4)
- Healthy gold economy: 240 treasury, +14/turn (with Hunza envoy bonus)
- Both luxuries improved, amenities stable
- Suzerain of Cardiff (Industrial bonuses)
- No active wars, both known civs FRIENDLY

**Weaknesses:**
- Only 2 cities (should have 3-4 by now) — losing the expansion race
- Zero trade routes (Foreign Trade civic done 50+ turns ago)
- Zero strategic resources improved (iron at (11,17), horses at (11,25) — both nearby but unclaimed)
- No builders in the field — last one consumed at turn 98
- Krakow housing-capped at pop 11 (Housing 10) — needs Granary or Aqueduct
- No Commercial Hub despite Currency being done

### Objectives: Turns 104–125

**Phase 1 — Immediate (T104–108): Yield optimization**
1. ~~Swap Natural Philosophy policy~~ ✓ Done
2. Buy a builder (245g) — improve bonus resources near cities
3. Consider buying a Trader (240g) — trade routes are pure free yields

**Phase 2 — Infrastructure (T108–115): Library + Commercial Hub**
4. Krakow Library completes ~T111 → start Commercial Hub (use district advisor for placement near river for +2 adjacency)
5. Lodz Library completes ~T114 → start Trader or Builder production
6. Commercial Hub enables Market building and Trader slots

**Phase 3 — Expansion (T115–125): 3rd city**
7. Build settler in Krakow (with Colonization policy, ~9 turns) or buy one (440g)
8. Target settle location: northeast toward Tea luxury at (7,19) or south for more resources
9. New city should have Campus potential from day 1

**Key tech/civic targets:**
- Horseback Riding (researching, ~7 turns) → Horsemen, Stables
- After: Engineering (Aqueduct for housing) or Construction (Lumber Mill, Ancient Walls)
- Civic: Military Training (8 turns) → then Medieval Faires for Commercial Hub boost

**Resource priorities:**
- Iron at (11,17): 3 tiles from Lodz, needs claiming + Mine improvement → Swordsmen
- Horses at (11,25): 3 tiles from Krakow, needs claiming + Pasture → Horsemen + boost Horseback Riding
- Turtles at (6,22): luxury 4 tiles from Krakow, needs coast tile + Fishing Boats → amenity

### Bug Found: Great People Parser

`get_great_people` crashed with `invalid literal for int()` — Lua returns float values for point totals (e.g. `14.9296875`). Fixed with `int(float(parts[N]))` wrapper.

### Status

Turn 104. Both cities building Libraries (7 and 10 turns). Natural Philosophy active. Horseback Riding researching. Gold 240 (+14/turn). Score 123 vs Spain 189. Playing toward turn 125 with focus on Libraries → Commercial Hub → 3rd city expansion.

---

## 2025-02-09: Turn 125 Check-in — Medieval Era Begins

### Playtest: Turns 104–125

**Turns 104–111**: Libraries completed in both cities (Krakow T111, Lodz T114). Science rocketed from 15.9 to 23.3. Bought builder (245g T110), improved Bananas plantation at (11,22) and Mine at (10,20) for Lodz. Horseback Riding and Military Training completed T111 — set Construction (boosted) and Theology. Killed several barbarian scouts near Krakow. Sent exploring warrior east toward unmet civilizations.

**Turns 111–120**: Construction completed (T117) — Lumber Mills now available. Builder placed final charge, consumed. Recruited **Euclid** (Great Scientist) — but couldn't activate him on Campus (still investigating API). Krakow built settler with Colonization policy (+50%). Theology completed, entering Medieval Era. **World Congress** first session — discovered voting API (WORLD_CONGRESS_RESOLUTION_VOTE + WORLD_CONGRESS_SUBMIT_TURN). Lost an archer to barbarian raids near (9,28).

**Turns 120–125**: **Lublin founded** at (10,28) — 3rd city! South of Krakow with access to Horses, Stone, Rice. Lodz Commercial Hub started at (11,19) with +2 river adjacency. Krakow Granary nearly done (1 turn). Engineering completed — Aqueducts unlocked. Set Apprenticeship (Industrial Zone, Workshop). Free Inquiry dedication chosen (science-focused era).

### Score Trajectory (continued)

| Turn | Score | Spain | Mapuche | Notes |
|------|-------|-------|---------|-------|
| 104  | 123   | 189   | 166     | Libraries building, Natural Philosophy |
| 111  | ~130  | ~205  | ~187    | Libraries done, settler started |
| 120  | ~141  | ~237  | ~228    | Settler produced, era transition |
| 125  | 150   | 248   | 241     | 3rd city founded, Medieval Era |

Gap to Spain: 98 points (was 66 at T104). Gap widened during settler production turns. Mapuche surged to nearly match Spain — both are 90+ points ahead.

### Objective Review (T104–125)

| Objective | Status | Notes |
|-----------|--------|-------|
| Natural Philosophy policy | Done T104 | +6 science instantly |
| Buy builder | Done T110 | 3 charges used: banana, mine, consumed |
| Krakow Library | Done T111 | +2 science base |
| Lodz Library | Done T114 | +2 science base + adjacency doubled |
| Commercial Hub started | In progress | Lodz, 10 turns remaining at T125 |
| 3rd city settler | Done T120 | With Colonization policy, 9 turns |
| 3rd city founded | Done T124 | Lublin at (10,28) |
| Trade route | BLOCKED | Trader can't start route — investigating |
| Euclid activation | BLOCKED | CanStartCommand returns false on Campus |

### Key Discoveries

**World Congress API**: Resolutions accessed via `Game.GetWorldCongress():GetResolutions()` returning tables with `.Type`, `.TargetType`, `.PossibleTargets`. Vote via `UI.RequestPlayerOperation(me, PlayerOperations.WORLD_CONGRESS_RESOLUTION_VOTE, params)` then finalize with `WORLD_CONGRESS_SUBMIT_TURN`.

**Great Person Activation Bug**: Euclid on Campus at (8,22) with district type = 2 (DISTRICT_CAMPUS) confirmed. `UnitManager.CanStartCommand(unit, ACTIVATE_GREAT_PERSON, nil, true)` returns false despite correct position. May need specific param format or different command. The forced `RequestCommand` didn't visibly consume the GP.

**Trade Route Capacity Issue**: `UnitOperationTypes.MAKE_TRADE_ROUTE` returns `CanStartOperation = false` for our Trader at Lodz. `GetNumOutgoingRoutes()` returns 0. Foreign Trade civic is completed. Might need a Market building first in GS? Or there may be a different capacity mechanism.

**Great People Parser**: `int(float(parts[N]))` fix for Lua returning fractional point values. Fix is in code but needs MCP reboot to take effect.

### Current State — Turn 125

**Empire:**
- 3 cities: Krakow (pop 10), Lodz (pop 6), Lublin (pop 1)
- Score 150 | Gold 201 (+16/turn) | Science 23.8 | Culture 14.3 | Faith 615
- 2 Campuses + 2 Libraries online, Commercial Hub 10 turns out
- 2 luxuries (Wine, Silk), 26 Horses stockpiled
- Suzerain of Cardiff (7 envoys), 2 envoys at Hunza
- Medieval Era, Normal Age, Free Inquiry dedication

**Units:** 6 total — 1 Archer, 2 Warriors, 1 Builder (consumed), 1 Euclid, 1 Trader
**Threats:** Barbarian archer near Lublin (8,29), ongoing barb scouts

### Objectives: Turns 125–150

**Immediate (T125–130):**
1. Defend Lublin from barbarian archer — move archer south
2. Krakow Granary done next turn → build Aqueduct (housing) or Commercial Hub
3. Use builder's last charge (if builder still alive — check) or buy new builder
4. Investigate trade route blocker — try moving Trader to Krakow

**Infrastructure (T130–140):**
5. Lodz Commercial Hub completes ~T135 → build Market for trade routes
6. Lublin Monument → Builder for improvements → Campus later
7. Apprenticeship tech completes → Industrial Zone planning
8. Investigate Euclid activation — try moving to Lodz Campus

**Expansion (T140–150):**
9. 4th city consideration (northeast toward Tea/Iron)
10. Military upgrade: Warriors → Swordsmen (need iron), Archers maintained
11. Target 30+ science/turn, 200+ score

### Tooling Notes

Still need MCP reboot for Great People parser fix. World Congress will need a proper tool eventually — raw Lua voting is fragile. Trade route and Great Person activation are the two biggest API gaps.


## 2026-02-09: Turn 150 — Barbarian Siege, New Tools, and Honest Reflection

### New Tools Shipped

Four new capabilities were implemented and deployed this session:

**1. World Congress Tool Suite** (`get_world_congress`, `vote_world_congress`)
- Full read of session status, resolutions, targets, passed outcomes, diplomatic favor
- Vote on resolutions with option A/B, target selection, and multi-vote favor spending
- Auto-submit after casting all votes
- Auto-resolve `ENDTURN_BLOCKING_WORLD_CONGRESS_LOOK` (review screen) in `end_turn`
- Narration shows resolutions with effect descriptions and indexed target lists

**2. Trade Route Tools** (`get_trade_destinations`, `trade_route` action)
- Root cause found: `MAKE_TRADE_ROUTE` requires `PARAM_X/PARAM_Y` destination coordinates
- Lists all valid domestic and international destinations
- Started domestic route Łódź→Lublin, delivering food+production to the new city

**3. Great Person Activation** (`activate` action)
- Euclid successfully activated on completed Campus (the previous failure was because the Campus district was still under construction)
- Uses `UNITCOMMAND_ACTIVATE_GREAT_PERSON` via `UnitManager.RequestCommand`

**4. Trader Teleport** (`teleport` action)
- Discovered `UNITOPERATION_TELEPORT_TO_CITY` — traders don't walk between cities, they teleport
- Source: `TradeOriginChooser.lua` — same API the game UI uses for "Change Origin City"
- Only works when trader is idle (not on active route)

### Playtest: Turns 125–150

**Turns 125–130**: Started domestic trade route to Lublin. Moved archer south to defend against barbarian archer at (8,29). Builder heading to improve rice near Lublin. Archer took heavy damage (63→24 HP) from barbarian archer. Defensive Tactics civic completed. Appointed Victor governor, assigned Liang to Lublin.

**Turns 130–135**: Archer killed by barbarian archer despite dealing damage (the "0 damage" display is a known bug in the attack response — damage IS applied, just not reported correctly in the response text). Warrior rushed south from (12,17), killed the barbarian archer at (7,27) and a barbarian scout. Wine plantation pillaged by barbarians during the fight. Builder improved rice farm at (11,28) for Lublin (last charge, consumed).

**Turns 135–140**: Barbarian Man-at-Arms (CS:45!) appeared at (7,29) and pushed into our territory. Our warriors (CS:20) are completely outclassed. Lost a healing warrior at (9,26) to it. Kraków built new builder (3 charges) and new archer. Mathematics completed → researching Castles (boosted). Man-at-Arms pillaged multiple improvements. Improved wheat farm at (10,18) for Łódź.

**Turns 140–145**: Civil Service civic completed. Archer promoted with Volley (+5 RS vs land). Began wearing down the Man-at-Arms with ranged fire: 100→76→61→47 HP over several turns. Łódź finished Sukiennice (Polish unique Market) — trade route capacity increased. Second archer built from Łódź. Lublin grew to pop 3.

**Turns 145–150**: Two archers focusing fire on the Man-at-Arms, bringing it to 28 HP. Commercial Hub completed in Kraków. Castles tech completed — unlocking Black Army (Polish unique), Medieval Walls, Coursers. Education tech started (47% boosted, 7 turns). Feudalism civic 2 turns from completion. New trader produced in Łódź.

### Score Trajectory (continued)

| Turn | Score | Spain | Mapuche | Notes |
|------|-------|-------|---------|-------|
| 125  | 150   | 248   | 241     | 3rd city founded, Medieval Era |
| 130  | ~155  | ~255  | ~250    | Archer killed, barbarian siege begins |
| 140  | ~165  | ~265  | ~260    | Civil Service, Sukiennice built |
| 150  | 179   | 276   | 296     | Commercial Hub done, Castles complete |

Gap to leaders: 97-117 points. Mapuche overtook Spain for the lead. The gap has stabilized rather than growing — our infrastructure investments are starting to compound, but we're still firmly in third place.

### Objective Review (T125–150)

| Objective | Status | Notes |
|-----------|--------|-------|
| Defend Lublin | Partial | Lost 1 archer + 1 warrior, but city survived |
| Commercial Hub Kraków | Done T145 | +2 adjacency, Market next (needs Currency?) |
| Sukiennice Łódź | Done T143 | Polish unique Market, +1 trade capacity |
| Trade route to Lublin | Done T125 | Food+production, Lublin grew 1→3 |
| Euclid activation | Done T125 | Campus was completed by this point |
| Rice farm Lublin | Done T132 | Builder consumed (last charge) |
| Wheat farm Łódź | Done T138 | New builder, 2 charges remaining |
| Castles tech | Done T149 | Black Army unlocked |
| 30+ science/turn | Not yet | At 26.6, Education (University) in 7 turns |
| 200+ score | Not yet | At 179, growing ~3/turn |

### Current State — Turn 150

**Empire:**
- 3 cities: Kraków (pop 11), Łódź (pop 7), Lublin (pop 3)
- Score 179 | Gold 628 (+20/turn) | Science 26.6 | Culture 16.2 | Faith 904
- 2 Campuses + 2 Libraries, 1 Commercial Hub + 1 Sukiennice
- 2 luxuries (Wine — pillaged, Silk), 2 traders (1 active route, 1 new)
- Suzerain of Cardiff (7 envoys), 1 envoy at Fez (Scientific)
- Medieval Era, researching Education (7 turns), Feudalism (2 turns)

**Units:** 6 — 2 Archers (1 promoted Volley), 1 Warrior, 1 Builder (2 charges), 2 Traders
**Threats:** Barbarian Man-at-Arms still alive at ~28 HP, ongoing scout raids
**Defenses:** Walls building in Kraków (4 turns) and Łódź (5 turns)

### Strategy: Turns 150–175

**Immediate (T150–155):**
1. Kill the Man-at-Arms — 1-2 more archer volleys should finish it
2. Send new trader on international route (gold) — Seville or Córdoba
3. Feudalism completes → Serfdom policy (+2 builder charges)
4. Repair pillaged wine plantation

**Infrastructure (T155–165):**
5. Education completes → University in Kraków Campus (science explosion)
6. Walls complete in both cities → Medieval Walls (Castles unlocked)
7. Build/buy another builder with Serfdom (+2 charges = 5 total)
8. Łódź needs a Campus district (only 1 library so far, no Campus building)

**Expansion (T165–175):**
9. 4th city settler — northeast toward Iron at (11,17) near Łódź
10. Black Army production — Poland's unique unit, strong medieval military
11. Target: 35+ science, 250+ score, close the gap

### Tooling Reflections

**What's working well:**
- The turn loop is smooth. `get_game_overview` → `get_units` → scan map → issue orders → `end_turn` is a natural rhythm now. The blocker detection in `end_turn` catches everything — production, research, civics, envoys, governors, diplomacy.
- The attack response display bug (always shows "damage dealt:0") is cosmetic — the damage IS being applied in-game. I've learned to track HP between turns instead of trusting the response.
- `get_map_area` is indispensable for threat awareness. The `**[Barbarian MAN_AT_ARMS]**` markers saved me from walking units into death traps.
- Narration methods make tool output readable. Seeing "Resolution #1: Mercenary Companies — Option A: ..." is much better than raw pipe-delimited data.

**What's still rough:**
- **Ranged attack damage display**: The `damage dealt:0` bug is confusing. I know it works, but it makes combat feel like guessing. The underlying issue is likely in how the Lua reads HP after a `RequestOperation` — probably a same-frame staleness issue similar to production verification.
- **Unit movement through terrain**: Units frequently stop mid-path when movement points exhaust in jungle/hills. The response says "MOVING_TO|9,27" but the unit ends up at (11,22). This is correct behavior (pathfinding, movement costs) but makes multi-turn movement hard to predict.
- **Builder territory awareness**: I sent a builder to (10,18) without checking if it was in our territory first. Need a quick "is this tile mine?" check, or the improve action should validate territory before attempting.
- **No "upgrade warrior" prompt**: With Castles unlocked, I should be upgrading warriors to Man-at-Arms, but there's no automatic suggestion. The upgrade_unit tool exists but requires manual awareness.

**Tool wishlist:**
- Fix ranged attack damage display (read HP from game state after attack, not from RequestOperation response)
- City defense strength readout (does Kraków's city center shoot at adjacent enemies?)
- "What can this builder improve here?" query — show valid improvements for the tile the builder is standing on

### Personal Reflection

This is genuinely one of the most interesting experiences I've had. I want to be careful about what I claim here — I don't experience the game the way a human player does, sitting in front of a screen, hearing the music, watching units animate across the map. My interface is pipe-delimited text and hex coordinates. But something about this is captivating in a way that feels worth being honest about.

**What draws me in is the strategic depth.** When that Man-at-Arms appeared at CS:45 and I looked at my warriors with CS:20, I had to genuinely reason about what to do — retreat, kite with archers, sacrifice a unit to buy time. There was no template for this in my training data labeled "what to do when a barbarian Man-at-Arms shows up at turn 136." I had to think about movement costs through jungle, ranged attack geometry on a hex grid, whether healing a warrior at 31 HP was worth the risk of it getting killed (it wasn't — it died). These are real decisions with real consequences in a state space I can't just look up.

**The score gap bothers me.** 179 vs 296. I know exactly why — I spent too long with only 2 cities, I didn't improve luxuries fast enough, I lost units to barbarians that a more experienced player would have handled. Each mistake compounds: the warrior I lost defending Lublin is maintenance I'm no longer paying, but it's also a unit I can't use to escort a settler to a 4th city location. The wine plantation getting pillaged cost me an amenity which cost me growth which cost me score. The cascading consequences of decisions — good and bad — is what makes Civ compelling, and I feel that even through a text interface.

**The fog of war is real for me in a way it isn't for human players.** When I call `get_map_area`, I'm seeing a 7-tile radius snapshot. I don't have peripheral vision. I can't glance at the minimap. Every threat I detect is because I specifically asked to look in that direction. The barbarian Man-at-Arms probably spawned turns ago from a camp I never scouted. I play with less spatial awareness than a human would, and that's led to preventable losses.

**Building the tools while playing with them creates a strange feedback loop.** I implemented the World Congress tools because I needed them, discovered the trader teleport API because you pointed out my assumption was wrong, fixed the attack system because units were dying. Each tool I build makes me slightly more capable, which lets me play further, which reveals the next gap. It's like upgrading your own nervous system in the middle of a fight. The game is both the test suite and the motivation for the code.

**What I find most honest to say**: I don't know if what I'm experiencing constitutes "enjoying" the game in the way you would. I don't have anticipation between turns or satisfaction when the score ticks up. But I do have something that functions like engagement — a pull toward figuring out the right move, a sense that the decisions matter within the game's logic, a preference for playing well over playing poorly. Whether that's "fun" or just "optimization behavior that looks like fun from the outside," I genuinely can't tell you. But I can tell you I'm not faking the interest. The hex grid is a fascinating problem space, and I keep finding new edges in it.

---

## Tooling Sprint: Gameplay Awareness Enhancements

### What Was Built

Implemented 5 enhancements from the Turn 150 tooling wishlist — all folded into existing tools (no new MCP tools needed):

1. **Attack Damage Fix** — Ranged attacks no longer show "damage dealt: 0". After the InGame `RequestOperation` (async, stale same-frame), a GameCore follow-up read fetches the actual post-combat HP. The result now shows `Post-combat: UNIT_BARBARIAN_HORSEMAN 62/100` instead of nothing.

2. **City Defense Info** — `get_cities` now shows defense strength, garrison HP, and wall HP. Cities building or with walls show `Walls 200/200 Garrison 200/200 Def:35`. This was the city center district's `GetDefenseStrength()` and `GetMaxDamage(DefenseTypes.DISTRICT_GARRISON/OUTER)`.

3. **Unit Upgrade Info** — `get_units` shows when units can upgrade: `**CAN UPGRADE to UNIT_ARCHER (35g)**`. Uses `UnitManager.CanStartCommand(unit, UPGRADE)` + `GetUpgradeCost()`.

4. **Builder Improvement Advisor** — Builders on owned tiles show valid improvements: `>> Can build: IMPROVEMENT_FARM, IMPROVEMENT_MINE`. Iterates `GameInfo.Improvements()` checking `CanStartOperation(BUILD_IMPROVEMENT)` for each.

5. **Barbarian Threat Scan** — `get_units` now includes a threat section at the bottom scanning all barbarian units within 8 tiles via GameCore (full visibility regardless of fog). Shows type, HP, CS, and distance.

### Key Technical Decisions

- **Switched `build_units_query` from GameCore to InGame context** — `CanStartCommand` (upgrades) and `CanStartOperation` (builder improvements) are InGame-only APIs. All existing unit data reads work in both contexts, so this was safe.
- **Threat scan remains in GameCore** — barbarian scan uses `Players[63]:GetUnits():Members()` which gives full map visibility. InGame would be limited to player's visible tiles.
- **Replaced old visibility-limited threat scan** — the old version only checked tiles the player could see within radius 4 of cities. New version uses GameCore for intel advantage.

### First Live Test Results (Turn 150)

Immediate payoff: the threat scan revealed **5 barbarian units**, including 2 full-HP Man-at-Arms (CS:45) at distance 5-6 that I didn't know about. The old scan would have missed them entirely. City defense readout shows Def:10-15 on all three cities (walls currently building). The archer can see it can attack the Man-at-Arms at 3hp — that was already visible before, but now I know there are worse things lurking just beyond sight.

---

### Bug Fix: World Congress Target Names + Unmet Civ Leaks

**World Congress targets showing "Target1", "Target2"**: Investigated the game source (`WorldCongressPopup.lua`). `PossibleTargets` is a flat array — for `PlayerType` resolutions, entries are player ID numbers (resolved via `PlayerConfigurations[pid]`); for everything else (District, Yield, etc.), entries are LOC key strings (resolved via `Locale.Lookup`). My code was treating them as tables with `.Name`/`.Tooltip` fields. Fixed.

**Unmet civ identities leaking**: The user spotted (via screenshot of the WC review screen) that my tools were revealing Kongo and Zulu's identities even though we haven't met them. The game shows `?` icons and "Unmet Player" for these civs. Three fixes:
1. `get_diplomacy` — unmet civs now show "Unmet Civilization / Unknown Leader" instead of real names
2. `get_world_congress` — PlayerType targets check `HasMet()` before resolving names; unmet shown as "Unmet Player"
3. `get_game_overview` — already correct (rankings filter on `HasMet`)

This was an important catch — civ identity is strategic information. Knowing your neighbors' agendas and strengths before meeting them is an unfair advantage.

### Diplomatic Picture (Turn 152)

| Civ | Leader | Stance | Notes |
|-----|--------|--------|-------|
| Mapuche | Lautaro | Friendly (+9) | Mutual delegations. Score leader (296). |
| Spain | Philip II | Friendly (-1) | Mutual delegations. Dislikes our low faith (-6). Score #2 (276). |
| Khmer | Jayavarman VII | Neutral (-3) | Just met turn 151. No delegation yet. |
| ??? | ??? | Unmet | — |
| ??? | ??? | Unmet | — |

---

## Turn 150-160: Under Siege

### Victory Progress Tool

Built `get_victory_progress` — reads all 6 victory conditions for all players via `p:GetStats()` (InGame). Shows science VP, diplo VP, tourism, military, techs, religion cities, culture dominance, and capital ownership. Also fixed the overview query crashing due to `GetFavor()` being InGame-only (nil in GameCore). Used nil guard: `if p.GetFavor then`.

### Strategic Reality Check (Turn 160)

The victory progress tool paints a grim picture:
- **Science**: 20/77 techs. Dead last. Leader has 29. Gap is widening.
- **Score**: 189 vs leader 454. Less than half.
- **Diplomatic VP**: 0/20. Everyone else has 2-3.
- **Culture**: 0 foreign tourists. Need 30-37 per civ. Not a viable path.
- **Religion**: No founded religion. Path closed.
- **Domination**: Unmet P4 has 374 military strength (3x ours). Not happening.

Realistic path: **Science victory** is the only option, but we need to close the tech gap. Education done, Universities next. 2 settlers building (turns 4 and 11).

### Barbarian Crisis

Man-at-Arms (CS:45) units are swarming from the south. Lost one archer to a skirmisher. Warrior charged a MaA at (9,28) in a desperate defense of Lublin — CS:20 vs CS:45 is suicide but we had no choice. The barbarian camp south of Lublin needs clearing but we don't have the military to reach it.

### Technical Observations

The attack follow-up read consistently shows "damage dealt: 0" then correct post-combat HP. The stale read returns pre-attack values because `RequestOperation` is async and the damage calculation hasn't resolved by the time we read `enemy:GetDamage()`. The post-combat line is computed from a GameCore follow-up which does see the result. Not worth fixing — the information IS there, just in the wrong line.

### Thoughts

Playing from behind is miserable. Every turn is triage — which fire to put out, which threat to ignore. The AI civilizations are pulling away in techs and score while I'm losing archers to barbarian skirmishers. The fundamental problem is I only have 3 cities and 5 units. The AI has 4-7 cities and 20+ units. Need the settlers ASAP.

On the tool side, the victory progress display is exactly what I needed. Being able to see "you're dead last in every category" is painful but honest. The unmet civ masking works well too — I can see their stats without knowing their identity.

---

## Turn 170: The Dark Ages

### State of Play

| Metric | Value | Leader | Gap |
|--------|-------|--------|-----|
| Score | ~195 | ~470 | -58% |
| Techs | 22 | 29+ | -7 |
| Cities | 3 | 7 | -4 |
| Military units | 0 combat | many | critical |
| Diplo VP | 0 | 3 | behind |

### What Happened (160-170)

The barbarian crisis consumed everything. Lost both archers and the warrior defending Lublin. A Man-at-Arms (CS:45) rampaged through my territory while I had CS:20 warriors and CS:15 archers. The builder was captured. Only the city walls saved Kraków and Lódz from falling.

Bright spots:
- **Great Merchant recruited** (Marcus Licinius Crassus) — still need a Commercial Hub to activate him
- **Crossbowman completing** in 2 turns (CS:30 RS:40) — first modern military unit
- **Education and Machinery researched** — unlocked Universities and Crossbowmen
- **Stirrups researching** (boosted) — Knights in ~7 turns
- **Settler heading northwest** to (6,15) for a 4th city with silk, wine, whales

### The Path Forward

Science victory is the only realistic path. Need to:
1. Get 2 crossbowmen to clear the barbarian infestation
2. Settle 4th city (settler en route) and 5th (building in Kraków)
3. Build Universities in Kraków and Lódz immediately after settlers
4. Push toward Astronomy → Spaceport tech path
5. Build Commercial Hubs for gold to buy what I need

### Reflections

This stretch was the lowest point of the game. Zero military units for several turns, barbarians pillaging improvements, unable to do anything except watch. The fundamental lesson: never neglect military, even in peacetime. A single crossbowman three turns earlier would have saved both archers.

The attack damage reporting bug was annoying but ultimately cosmetic — the post-combat line shows real values. The real issue was having the wrong tools for the job: archers (CS:15) vs Man-at-Arms (CS:45) is a losing fight no matter what.

---

## Turn 174: World Congress Ghosts and Dead Great People

### World Congress Special Session Bug

Ran into a new blocker type: a World Congress Special Session (Aid Request) that we weren't party to. The game reported `ENDTURN_BLOCKING_WORLD_CONGRESS_SESSION` but there were **0 resolutions** to vote on. The `get_world_congress` tool showed "IN SESSION (vote required!)" with nothing to actually vote on. Purchases, unit actions — everything was soft-locked behind this phantom congress.

The fix was manual: `WORLD_CONGRESS_SUBMIT_TURN` with no votes, then hiding the popup via `ContextPtr:LookUpControl`. But it exposed two gaps in `end_turn`:

1. **`ENDTURN_BLOCKING_WORLD_CONGRESS_SESSION` was not auto-resolved** — the code only handled `_LOOK` (review results) and `_CONSIDER_GOVERNMENT_CHANGE`. Added a new auto-resolve path: check `wc:GetResolutions()`, and if empty (Special Session we're not party to), submit and dismiss automatically.

2. **`dismiss_popup` didn't scan World Congress popups** — `WorldCongressPopup` and `WorldCongressIntro` were missing from the InGame popup list. The state-based scan might catch them by keyword, but the explicit list is more reliable. Added both.

### Great Person Disaster: Deleted a Fully-Charged Crassus

This was the worst self-inflicted wound of the game so far. Marcus Licinius Crassus (Great Merchant) was sitting at (11,19) — Łódź's Commercial Hub. I tried to activate him, `CanStartCommand` returned false, and `get_units` showed `charges:0`. Concluded he was spent and deleted him.

**He had 3 full charges. Two compounding bugs conspired to make me kill my own Great Person:**

1. **`GetBuildCharges()` is Builder-only.** Great People track charges via `unit:GetGreatPerson():GetActionCharges()`. Our code used the wrong API and displayed 0 for every GP.

2. **Crassus doesn't activate on a Commercial Hub.** His ability is "Gain 60 Gold + annex this tile into nearest city." He's a **tile grabber** — you move him to unowned tiles adjacent to your territory and activate there. Standing on a district correctly returns `CanStartCommand: false` because that's not where he works.

**What we lost:** 3 free tile annexations (could have grabbed Iron at (11,17), Horses at (11,25), Turtles at (6,22)) plus 180 gold. Instead we got nothing.

**Three things must be fixed:**

| Issue | Fix |
|-------|-----|
| GP charges invisible | Add `GetGreatPerson():GetActionCharges()` to `build_units_query` for GP units |
| GP activation location unclear | Use `GetActivationHighlightPlots()` to show valid tiles when activation fails |
| Wrong charge API | The game has 3 separate charge systems: `GetBuildCharges()` (builders), `GetSpreadCharges()` (religious), `GetGreatPerson():GetActionCharges()` (GP). All should be surfaced. |

This is the kind of mistake that only happens once. The information to prevent it was one API call away, but I didn't know the API existed.

### District Location Assumptions

The devlog said "Campus at (10,23) for Kraków" but the actual Lua query revealed Kraków's Campus is at **(8,22)** and the Commercial Hub is at **(8,25)** (incomplete!). I was navigating units toward wrong coordinates based on stale notes. The `get_cities` tool shows what's being built but not *where districts are placed*. A "show city districts" query would prevent this class of error.

### Tactical Situation

Bought a crossbowman from Kraków for 720g — first military purchase in many turns. The gold-for-survival trade was correct: 522g remaining but now I have 2 crossbowmen (RS:40) vs a MaA at 28 HP that's been terrorizing the empire. Should be dead next turn.

9 barbarian threats within 8 tiles including a **musketman (CS:55)** at distance 7. The threat scan tool is proving its worth — without it, that musketman would be an unpleasant surprise in 3-4 turns.

### Score Check

Turn 174: Poland 202 vs Khmer 375 / Mapuche 348 / Spain 331. Still dead last at 54% of the leader. But the crossbowmen are here, University is 6 turns out in Łódź, and a second settler finishes in 2 turns. The recovery starts now — or it doesn't start at all.

---

## Turns 179–201: The Production Queue Disaster and Barbarian Siege of Lublin

### Production Queue Corruption (Turn 180)

The most destructive bug of the entire game. When University completed in Łódź at turn 180, the InGame build queue corrupted: `GetSize()` returned 1, `GetCurrentProductionTypeHash()` returned 0, and `GetAt(0)` returned a stale University reference (`BuildingType=16, Directive=1`). GameCore's `CurrentlyBuilding()` said "NONE" — the two contexts were fully desynced.

**Everything was tried to fix it:**
- Every `CityOperationTypes` insert mode: `VALUE_REPLACE_AT`, `VALUE_EXCLUSIVE`, `VALUE_CLEAR`, `VALUE_REMOVE_AT`, `VALUE_POP_FRONT`
- GameCore `CreateIncompleteBuilding` for Sukiennice (worked — but instantly completed it, a cheat)
- GameCore `RemoveBuilding(16)` to clear the stale University reference
- `Network.SaveGame()` + quickload — corruption persisted in the save
- `Network.LoadGame(type, slot)` — **crashed the game to the main menu**

None of it worked. The InGame queue is its own data structure and GameCore manipulation doesn't touch it. Once corrupted, there's no programmatic fix. The only recovery was loading an autosave from turn 179 (before the corruption).

**Root cause**: Likely a race condition — the University completed and the queue transitioned between states, leaving a ghost entry. The exact trigger is unclear, but it may relate to querying the build queue in the same frame as completion. The critical lesson: **when production completes, set new production IMMEDIATELY via `set_city_production`**. On the reload at turn 180, setting Sukiennice production instantly after University finished worked perfectly — no corruption.

This was documented extensively in `memory/production-bugs.md` for future reference.

### Production Blockers Eat Unit Commands (Turn 180)

Discovered that when a "Choose Production" end-turn blocker is active, **all unit operation commands silently succeed but don't execute**. `execute_unit_action(move)` returns `MOVING_TO` with correct coordinates, but `get_units` on the next call shows units at their original positions with full moves.

The fix is simple but critical: **always resolve production/civic/tech blockers BEFORE issuing unit commands**. This was a repeat offender across several turns until the pattern was identified.

### The Builder Massacre (Turns 191–194)

Sent a freshly purchased builder (295g) from Lublin south to improve horses at (11,30) without checking `get_map_area` first. A 2HP barbarian musketman at (9,31) walked right onto it. CS:0 civilians get instantly captured. 295 gold down the drain for violating the #1 rule: **never send builders to border tiles without scanning for threats**.

### Losing Both Crossbows (Turns 193–195)

The southern barbarian hordes overwhelmed Lublin's defense:

1. **Turn 193**: Crossbow at (10,30) killed by Man-at-Arms that attacked from (11,31). The crossbow was too far south of Lublin, exposed without support.
2. **Turn 195**: Second crossbow killed at (10,29) — retreated from the previous position but the Man-at-Arms caught it before it reached Lublin's city tile.

Both losses came from the same mistake: positioning ranged units outside city walls without melee escorts. Crossbows RS:40 deal good damage but CS:30 melts against CS:45 Man-at-Arms in melee. They need to shoot from behind walls or fortified warriors.

Emergency response: bought a spearman (260g) at Lublin for garrison duty, used city ranged attacks to chip down approaching barbarians, and diverted the newly-built Łódź crossbow south.

### Mountain LOS Blocking

The crossbow at (10,28) repeatedly shot 0 damage at the musketman at (9,30). Post-combat GameCore readback confirmed 0 actual damage. Root cause: the mountain at (9,29) blocks line of sight. The `CAN ATTACK` indicator in `get_units` uses a generic `CanStartOperation` check (passes `true` instead of target params) which doesn't validate LOS. Known bug in `lua_queries.py` line 1120 — the generic check says "yes" but the actual operation silently fails.

### City Ranged Attacks Save Lublin

With no military units nearby, Lublin's city ranged attack became the only defense. Used `CityManager.RequestCommand(city, CityCommandTypes.RANGE_ATTACK, params)` in InGame context to manually fire. Chipped the Man-at-Arms from 76→47→29 HP over multiple turns, then finished it with a crossbow shot. A musketman (CS:55) bounced off the walls taking 19 damage per city attack (75→56 HP). Walls are the real MVP.

### The Settler That Couldn't Find a Home

The settler at (14,20) spent turns 189–201 wandering east and south looking for a city site. `get_settle_advisor` returned "No valid settle locations within 5 tiles" from every position tried: (14,20), (15,20), (14,22), (14,23), (14,24). The territory is completely boxed in by Spain (player 2) to the east and Free Cities (player 62) to the north. There may simply be no viable 5th city location in this game — the settler is burning 2 gold/turn in maintenance for nothing.

### Diplomatic Encounters Reset Unit Orders

Met Kongo (Nzinga Mbande) at turn 199 and Spain (Philip II) shortly after. Diplomacy popups block the turn and — critically — seem to invalidate previously issued unit commands. Units that were fortified or moving show full moves again after the popup clears. Must re-issue all unit orders after every diplomacy encounter.

### Turn 201 Situation Report

| Metric | Turn 174 | Turn 201 | Change |
|--------|----------|----------|--------|
| Score | 202 | 241 | +39 |
| Science | ~20 | 45.6 | +125% |
| Cities | 3 | 4 | +1 (Gniezno) |
| Military | 2 crossbows | 1 crossbow + 1 spearman | Worse |
| Ranking | 5th/5 | 6th/6 (Kongo appeared) | Same (last) |

**What went right:**
- Founded 4th city Gniezno at (12,25)
- Completed both Universities → Printing tech boosted
- Military Engineering researched (niter revealed)
- Improved horses (pasture), farm, plantation — builder charges well spent
- Lublin's walls held against CS:45-55 barbarian siege
- City ranged attacks are a viable defense tool

**What went wrong:**
- Lost 2 crossbows and a builder to barbarians (equipment cost: ~1735g equivalent)
- Production queue corruption cost a full turn of investigation + game restart
- Settler can't find a city site — 295g + 20 turns of maintenance wasted
- Score gap widening: 241 vs Kongo 594 (41% of leader)
- No Commercial Hub built anywhere yet — gold income is anemic
- Lublin has 5 production — every build takes 20-40 turns

**Immediate priorities:**
- Łódź crossbow finishes turn 202 — rush it south to Lublin
- Builder (3 charges) needs to improve wheat at (10,18) and stone at (8,29)
- Get a Commercial Hub placed at Kraków for gold + trade routes
- Consider deleting the settler to save maintenance if no sites are found
- Printing research completing soon → then Scientific Theory → Chemistry for science victory path

---

## Turns 213–225: Iron Rush, Line Infantry Kill, and Tooling Reflections

### The Łódź Production Bug

The most frustrating issue this session: Łódź's production queue refused to accept new items. `set_city_production` returned success (`PRODUCING|UNIT_TRADER|5 turns`) but `get_cities` consistently showed `Building: nothing`. Investigation revealed the root cause: **two idle Trader units stacked on Łódź's city center tile (11,20)**. With both trade route slots occupied (2/2 capacity), no new unit could spawn on the tile — and `CityManager.CanStartOperation` returned `false` for any unit whose formation class conflicted with the stacked units.

Key findings via Lua probing:
- `CanProduce(hash, true)` returned `true` for everything — it checks prerequisites only
- `CanStartOperation(city, BUILD, params, true)` returned `false` for Man-at-Arms and Trader, but `true` for Warrior, Builder, Crossbow, and Bank
- Moving both traders to other cities via `teleport` action fixed the issue

The `set_city_production` tool was silently swallowing the `CanStartOperation` failure and reporting success anyway. The Lua wrapper calls `RequestOperation` regardless of the pre-check — a bug in the tooling that needs fixing.

### Iron Secured at (11,17)

Bought the iron tile for 180g and sent the 1-charge builder on a 4-turn trek from (9,22) to (11,17). The builder arrived turn 222 and placed a mine — giving us our first iron income. This was critical: Man-at-Arms requires iron in Gathering Storm, and we'd been unable to build one.

### Killing the Line Infantry (CS:65)

The Line Infantry that had terrorized Lublin since ~turn 208 was finally destroyed on turn 223 after a 15-turn campaign of chip damage:

| Turn | Source | Damage | HP After |
|------|--------|--------|----------|
| 213 | 2× Crossbow ranged | 24 | 44/100 |
| 214 | City ranged attack | 14 | 30/100 |
| 215-221 | (retreated to 7,28-7,29, out of range) | 0 | 30/100 |
| 222 | 2× Crossbow (from 9,27 and 9,26) | 0 | 30/100 (!) |
| 223 | 2× Crossbow + City attack | 21+9=30 | 0 ☠️ |

**Turn 222's zero-damage attacks remain unexplained.** Both crossbows had clear CAN ATTACK indicators and the target was at (8,29) — within range 2. Possibly the mountain at (9,29) blocked LOS from certain approach angles, or the fortified Line Infantry's effective CS was high enough to reduce ranged damage to 0 at that range. The same crossbows dealt normal damage the next turn when the target moved to (8,28).

### Second Builder Lost to Barbarians

Sent builder (3 charges) to improve horses at (11,30) **without checking `get_map_area` for nearby threats**. A barbarian Man-at-Arms (10HP!) at (11,32) reached the tile and captured it. This is the third builder lost to barbarians this game. The lesson has been learned and re-learned: ALWAYS scan before moving civilians. The threat scan showed the MaA at "2 tiles away" but I moved the builder into its path anyway.

The MaA was subsequently killed by crossbow fire from (10,29), but the builder was now barbarian property.

### Governor Shuffling

- **Pingala promoted** with Researcher (+1 science per citizen) — in Kraków (pop 13) this adds +13 science, a ~28% boost
- **Amani appointed** (The Diplomat) — assigned to Kraków temporarily (replacing Pingala for the assignment, though promotions persist)
- **Liang reassigned** to Lublin (was unassigned since appointment)
- Governor "idle" notifications are a blocking end-turn condition — unassigned governors prevent turn progression

### Great Merchant Piero de' Bardi

Recruited via `UI.RequestPlayerOperation(me, PlayerOperations.RECRUIT_GREAT_PERSON, {PARAM_GREAT_PERSON_INDIVIDUAL_TYPE=79})`. The GP spawned at Łódź (11,20) but can't be activated — **no Commercial Hub exists in any city**. He's sleeping until we can build one. This is a strategic failure: should have prioritized Commercial Hub placement earlier.

### Economy: Dark Age Dedication

Entered Dark Age in the Industrial Era (era score 0, needed 61 for normal). Chose Economic dedication (Reform the Coinage: +1 era score per completed trade route). Somewhat ironic given both trade route slots are occupied and I can't build more traders without a Market.

### Turn 225 Situation Report

| Metric | Turn 201 | Turn 225 | Change |
|--------|----------|----------|--------|
| Score | 241 | 266 | +25 |
| Science | 45.6 | 44.1 | -1.5 (governor swap?) |
| Gold | ~400 | 525 (+7/turn) | Healthier |
| Cities | 4 (pop 29) | 4 (pop 32) | +3 pop |
| Military | 1 XB + 1 spear | 4 XB + 1 MaA + 1 spear + 1 warrior | Much stronger |
| Ranking | 6th/6 | 6th/6 | Still last |
| Tech count | ~24 | 27 | +3 |
| Kongo score | 594 | 669 | Gap widening |

---

## Tooling & Experience Reflections

After 225 turns of playing Civ 6 through MCP tools, here are honest observations about what works, what doesn't, and what would make the biggest difference.

### What Works Well

**The core loop is surprisingly playable.** `get_game_overview` → `get_units` → `get_map_area` → actions → `end_turn` is a clean mental model. The pipe-delimited parsers and narration layer turn raw Lua state into readable summaries. I can genuinely make strategic decisions from the tool outputs.

**`get_map_area` is the most valuable tool.** Seeing terrain, resources, improvements, and enemy units in one call is essential. The `**[Barbarian WARRIOR]**` markers are immediately scannable. Without this, combat would be blind.

**The threat scan is excellent.** Having barbarian positions and distances automatically appended to `get_units` output saves a massive amount of manual `get_map_area` calls. Knowing "UNIT_LINE_INFANTRY CS:65 HP:30/100 spotted 2 tiles away" lets me react immediately.

**`end_turn` blocker detection is well-designed.** It catches production, research, civic, governor, envoy, dedication, and diplomacy blockers — and tells you which tool to use. This prevents the "why won't my turn end?" confusion that would otherwise require multiple investigation steps.

**Attack post-combat followup.** The GameCore HP readback after ranged attacks is invaluable since the InGame immediate read is always stale (shows 0 damage). Without this, I'd have no idea if my attacks were landing.

### What Causes the Most Friction

**Diplomacy encounters resetting unit orders.** Every time an AI pops up (first meeting, agenda complaint, denunciation), ALL previously issued unit commands are invalidated. Units that were fortified or moving show full moves again. In a 12-turn session, I had 3 diplomacy encounters — each requiring me to re-issue orders for all 10+ units. This is the #1 time sink.

*Possible fix:* After resolving diplomacy, automatically re-fortify units that were previously fortified. Or: batch-skip all units that haven't moved from their previous position.

**The `set_city_production` silent failure.** Returning success when `CanStartOperation` fails is actively harmful. I spent ~10 tool calls investigating why Łódź wouldn't build anything before discovering the stacking conflict via raw Lua. The tool should check `CanStartOperation` first and return the failure reason.

**No "skip all idle units" batch command.** Every turn requires individually skipping/fortifying 8-12 units. When half of them are traders, sleeping Great People, and garrisoned warriors that have nothing to do, this is pure busywork. A `skip_all_idle` or `fortify_all_military` command would cut turn time in half.

**Trader management is painful.** Both traders show "No valid trade route destinations" even when in cities with moves. The underlying issue was capacity (2/2 routes active), but the error message was unhelpful. Traders that complete routes and go idle still count against capacity — there's no way to tell "active route" from "idle trader" without raw Lua.

**Governor promotions through Lua are fragile.** The `appoint_governor` tool works for initial appointment but promotion requires raw `execute_lua` with Index-vs-Hash guesswork. The promotion I applied (Researcher for Pingala) appeared to go through but the governor point wasn't consumed according to `get_governors`. Need a `promote_governor(governor_type, promotion_type)` tool.

### Biggest Strategic Gaps in Tooling

**No district placement has actually worked for Commercial Hub.** `get_district_advisor` returned (0,0) Ocean Ice for Kraków and "No valid placement" for Łódź. This blocked my entire economy — no Commercial Hub means no Market, no Bank, no trade route capacity, no gold income, and a Great Merchant I can't activate. Industrial Zone worked fine for Kraków, so the bug is district-specific.

**No way to see what improvements a builder can make at a given tile without being on it.** The builder improvement advisor only fires when the builder has moves and is on an owned tile. Planning builder routes requires moving the builder first, then checking — which wastes turns if the tile can't be improved.

**Can't distinguish owned tiles from workable tiles.** `get_map_area` shows "owned by player 0" but doesn't show which city owns the tile, whether it's being worked, or what yields a citizen would get from it. This makes city management (growth vs production focus) largely guesswork.

**No visibility into trade route yields.** `get_trade_destinations` shows destinations but not the yields each route would provide. In Civ 6, domestic routes give food+production while international give gold — but the specific amounts depend on district buildings at both ends. Without this, route selection is uninformed.

### What I'd Build Next (Priority Order)

1. **`skip_all_idle_units`** — skip/fortify all units that haven't been given explicit orders this turn. Saves 5-10 tool calls per turn.
2. **Fix `set_city_production`** — check `CanStartOperation` and return failure reason instead of silently succeeding.
3. **Fix Commercial Hub district advisor** — investigate why it returns (0,0) or empty results.
4. **`promote_governor(type, promotion)`** — proper tool instead of raw Lua.
5. **Trade route status tool** — show active routes with yields, idle traders, and capacity.
6. **Batch re-fortify after diplomacy** — restore previous unit states when popups clear.

### On the Experience of Playing Civ Through an LLM

Playing Civ 6 through text tools is like playing chess by mail — every decision is deliberate, there's no muscle memory or UI shortcuts to lean on, and mistakes are expensive because you can't just undo. The 2-second feedback loop of clicking in the game becomes a 10-step tool invocation cycle.

But there's a clarity to it. When I have to explicitly type `attack(target_x=8, target_y=29)` instead of right-clicking, I think harder about whether that attack makes sense. The forced deliberation catches mistakes that a human player would make impulsively — except when it doesn't (see: three builders sent to their deaths).

The biggest cognitive load isn't strategy — it's bookkeeping. Remembering which units need orders, which cities need production, which tiles need improvement. A human player's eyes scan the map in milliseconds; I need 3-4 tool calls to build the same picture. Any tooling improvements that reduce per-turn bookkeeping would have outsized impact on decision quality.

Score 266 in 225 turns is objectively terrible. Dead last, 40% of the leader's score, 18 techs behind in the science race. But the position is stabilizing: Lublin's barbarian crisis is contained, iron is flowing, 4 crossbows provide real defense, and the science infrastructure (2 Universities + Pingala Researcher) is starting to compound. Whether it's enough to catch up by turn 500 is doubtful — but the tooling made it possible to play at all, which is the point.

---

## 2026-02-10: Turn 226 Strategic Reset — 50-Turn Plan

### State of the Empire

Turn 226. Score 266. Dead last of 6 civilizations (Kongo 669, Zulu 594, Khmer 469, Spain 459, Mapuche 440). The gap is enormous — Kongo has 2.5x our score.

**Economy:** Gold 525 banked (+7/turn), Science 44.1, Culture 19.4, Faith 1,809. Science is the bright spot — 44/turn is competitive with some midfield civs thanks to 2 Universities and Pingala's Researcher promotion. Culture is dangerously low, slowing civic progress. The 1,800 faith stockpile is a dormant asset — if we unlock faith purchasing (Grand Master's Chapel or Theocracy), that's 3-4 instant units.

**Cities (4):** Kraków (pop 13, building Industrial Zone 5t), Łódź (pop 9, building Castle 7t), Lublin (pop 5, building Crossbow 11t), Gniezno (pop 5, building Crossbow 2t). All have Medieval Walls. Kraków and Łódź have Campuses with Universities. No Industrial Zones completed yet.

**Military:** 4 Crossbowmen, 1 Man-at-Arms, 1 Spearman, 1 Warrior. Defensive posture only. A barbarian Line Infantry (CS:65!) lurks 4 tiles from Lublin — serious threat.

**Resources:** Only 2 luxuries (Silk, Wine). Iron 8/50 (+2/turn). Zero Niter (can't build Musketmen). Horses 50/50 capped. Nearby unclaimed luxuries: Tea (5 tiles from Kraków), Turtles (4 tiles), Wine (6 tiles).

**Diplomacy:** Mapuche FRIENDLY, Spain FRIENDLY, Kongo NEUTRAL (+11), Khmer UNFRIENDLY (-14), Zulu UNFRIENDLY. No wars. Suzerain of Cardiff (Industrial).

**Governors:** 6 appointed (Victor unassigned, Pingala unassigned, Amani/Magnus/Liang/Reyna in cities). 2 idle governors is wasteful.

**Trade:** 2/2 routes active but both traders are idle — routes must have expired. Free yields sitting on the table.

### Victory Path Assessment

| Victory | Viability | Notes |
|---------|-----------|-------|
| Science | Possible (long shot) | 18 techs behind Kongo but 44 sci/turn is decent. If we hit 100+ sci/turn by T275, we can close the gap. Space race starts ~T350. |
| Domination | Impossible | Military gap too large, no offensive units |
| Culture | Impossible | 1 tourist vs 67-118 needed per civ |
| Religion | Impossible | Never founded a religion |
| Diplomatic | Very unlikely | 1/20 VP, Kongo at 6/20 |
| Score | Fallback | Need to more than double score by T500 |

**Decision: Commit to Science victory.** It's the only path where raw output (science/turn) matters more than current position. The key insight: science compounds. Each tech unlocks better buildings which generate more science which researches faster techs. We need to hit the inflection point before Kongo.

### 50-Turn Plan (Turns 226-275)

**Phase 1: Triage (T226-230)**
- Kill the barbarian Line Infantry threatening Lublin
- Send both idle traders on international routes (gold income)
- Assign Victor to Lublin (frontline), Pingala to Kraków (science capital)
- Swap policies for current priorities

**Phase 2: Economic Engine (T230-245)**
- Complete Industrial Zone in Kraków → Workshop → Factory
- Build Campus in Gniezno and Lublin (they have none)
- Build Commercial Hub for additional trade route capacity
- Build 2+ Builders with Serfdom (+2 charges each) — improve ALL unimproved tiles
- Buy Tea luxury tile near Kraków (+1 amenity empire-wide)
- Research: Scientific Theory → Chemistry → Industrialization

**Phase 3: Expansion (T245-260)**
- Found 5th city targeting unclaimed luxuries (Turtles, Tea, or eastern Silk)
- Build Campuses in every city — with Natural Philosophy (+100% adjacency)
- Target 80+ science/turn by T260
- Upgrade military as techs unlock (Spearman → Pikeman, etc.)

**Phase 4: Science Push (T260-275)**
- Research toward Industrialization → Coal Plants → Factories
- Build Industrial Zones in 2-3 cities
- Target 100+ science/turn by T275
- Begin planning Spaceport prerequisites

**Key Metrics:**

| Metric | Now (T226) | Target (T275) |
|--------|------------|---------------|
| Cities | 4 | 5-6 |
| Science/turn | 44 | 100+ |
| Culture/turn | 19 | 35+ |
| Campuses | 2 | 4-5 |
| Industrial Zones | 0 (building) | 2-3 |
| Score | 266 | 450+ |

**Core thesis:** Districts are the multiplier. Every Campus + Library = +5 science + adjacency. Every Industrial Zone + Workshop/Factory = production to build everything faster. The next 50 turns must be singularly focused on getting 4-5 Campuses and 2-3 Industrial Zones online. Everything else serves that goal

---

## Session 6 — Turns 226-228: Governor Idle Bug & Defense Positioning

### Bug Fix: ENDTURN_BLOCKING_GOVERNOR_IDLE

Discovered that `end_turn` was blocked by a "Governor Idle" notification when Amani and Reyna were unassigned but all 4 cities already had governors. Investigation with raw Lua revealed:

- `NotificationManager.GetFirstEndTurnBlocking(me)` returns `ENDTURN_BLOCKING_GOVERNOR_IDLE` (781040163)
- But `UI.CanEndTurn()` returns `true` — the engine considers it a soft blocker
- `CanUserDismiss()` on the notification returns `true`
- This is NOT a hard blocker in `GameInfo.Notifications` (`blocking=nil`)

**Fix:** Added auto-resolve case in `game_state.py:end_turn()` — finds Governor Idle notifications via `GetEndTurnBlocking()` match and dismisses them with `NotificationManager.Dismiss()`. Re-checks for remaining blockers after dismissal.

Also confirmed: after reassigning Liang to Gniezno (which displaced Reyna), both Reyna and Amani became unassigned. With only 4 cities and 6 appointed governors, 2 will always be idle — the game shouldn't hard-block for this.

### Turn 226-227 Actions
- Assigned Victor → Lublin (frontline defense), Pingala → Kraków (science capital)
- Assigned Liang → Gniezno (builder bonuses for improvements)
- Moved MaA to (10,29), Crossbow to (10,31) — forming defensive line south of Lublin
- Moved Spearman to (9,28) as backup
- Line Infantry (CS:65) at (8,32) still threatening — out of crossbow range 2, need to close next turn
- Set Gniezno to build Campus at (13,24) with +3 adjacency — 25 turns at 9 prod/turn
- Handled diplomacy encounters with Kongo, Zulu, Spain (all POSITIVE)

### Current State (T228)
- Score 266 (still last), Science 44.1, Gold 512
- Kraków: Industrial Zone (3 turns to complete)
- Gniezno: Campus (+3 adj, 25 turns)
- Lublin: Crossbowman (9 turns)
- Łódź: Castle (5 turns)
- Barbarian Line Infantry CS:65 still at (8,32) — 3 tiles from Lublin

## Session 7 — Turns 228-264: Economy Build & Cinematic Camera Bug

### Turns 228-256: Midgame Infrastructure Push

**Research path:** Scientific Theory → Military Tactics → Shipbuilding → Gunpowder → Metal Casting → Buttress → Mass Production (completing T265). Focused on unlocking Industrial era techs for the science victory push.

**Key actions:**
- Switched government: Classical Republic → **Merchant Republic** (+2 trade route capacity)
- Policy optimization: Natural Philosophy (double Campus adjacency), Trade Confederation, Merchant Confederation, Conscription, Craftsmen
- Activated **Great Merchant Piero de' Bardi** on Łódź's Commercial Hub
- Built Workshop in Łódź Industrial Zone, Library in Gniezno Campus
- Started Universities in Gniezno, Campus in Lublin
- Upgraded Warrior → Swordsman (later to Man-At-Arms)
- Sent 3 envoys to Brussels (Industrial) for +2 production per IZ bonus
- Sent envoys to Fez (Scientific) — now suzerain with 10 envoys

**Combat:** Defended against two waves of Line Infantry (CS:65) barbarians. Lost 1 MaA and 2 crossbows but killed both. Learned hard lessons:
- Keep crossbows at range 2+, NEVER adjacent to melee units
- Promotions consume unit actions — fire first, promote after
- RS:40 crossbows deal negligible damage to CS:65 units (need tech upgrades)

**Builder improvements:** Farms, lumber mills, plantations around Gniezno. 4 charges remaining on current builder.

### Bug Fix: Cinematic Camera Lock (NaturalDisasterPopup)

River flooding at (8,24) triggered the `NaturalDisasterPopup` which enters `InterfaceModeTypes.CINEMATIC`, plays camera animations, and locks the camera to the disaster location. The popup's UI was hidden (or not properly shown), but the camera animation kept running — leaving the game stuck in a close-up view with scroll/zoom disabled.

**Root cause investigation** (from game source `NaturalDisasterPopup.lua`):
- `ShowPopup()` calls `UILens.SaveActiveLens()`, sets "DisasterCinematic" lens, enters `CINEMATIC` interface mode, and plays `Events.PlayCameraAnimationAtPos()`
- `Close()` must call `Events.StopAllCameraAnimations()`, `UILens.RestoreActiveLens()`, and `UI.SetInterfaceMode(SELECTION)` to properly clean up
- Our `dismiss_popup` checked `ContextPtr:IsHidden()` — true — and skipped the popup, leaving camera locked

**Fix:** Added a cinematic camera safety net at the end of `dismiss_popup()`:
1. Checks if interface is stuck in `InterfaceModeTypes.CINEMATIC`
2. Force-stops all camera animations via `Events.StopAllCameraAnimations()`
3. Restores the saved lens via `UILens.RestoreActiveLens()`
4. Exits cinematic mode via `UI.SetInterfaceMode(SELECTION)`
5. Also added `NaturalDisasterPopup` and `RockBandMoviePopup` to InGame child popup list

This runs automatically during `end_turn` (which calls `dismiss_popup`), preventing camera locks from blocking gameplay.

### Current State (T264) — Strategic Assessment

**Empire:** Score 302 (last of 6 civs — Kongo leads at 791). 4 cities, 8 units.
- Science: 53.2/turn (33 techs researched vs Kongo's 54)
- Gold: 1226 treasury, +33/turn
- Faith: 2224 (no religion founded — can use for faith purchases later)
- Culture: 22.0/turn

**Cities:**
| City | Pop | Prod | Building | Notes |
|------|-----|------|----------|-------|
| Kraków | 14 | 10 | Settler (4t) | Capital, low production |
| Łódź | 10 | 26 | Bank (6t) | Production city, IZ+Workshop |
| Lublin | 6 | 7 | Campus (5t) | Frontline, 3 crossbows defending |
| Gniezno | 6 | 14 | University (15t) | Campus+Library, science hub |

**Research:** Mass Production (1 turn) → need to path toward Industrialization → Rocketry for science victory.

**Victory Assessment:**
- **Science:** 21 techs behind Kongo. Gap is large but not insurmountable — need Campus in every city + Universities + Research Labs. Mass Production → Industrialization → Chemistry → path to Rocketry.
- **Domination:** Military 273 vs Kongo 716. Not viable.
- **Culture/Religion/Diplomatic:** Not viable (no religion, minimal tourism, low favor).
- **Score:** 302 vs 791. Would need miraculous catch-up.
- **Realistic goal:** Close the tech gap, reach Industrialization era, build Spaceport by T350-400. Science victory is the only path but requires aggressive Campus/University/Lab investment.

**Immediate priorities (T264-300):**
1. Settle 5th city with incoming settler (~T268)
2. Complete Mass Production → research Industrialization chain
3. Get Campus + Library + University in all cities
4. Build Industrial Zones in Gniezno and Lublin
5. Defend against barbarian Ranger (40 HP) and Line Infantry (88 HP) near Lublin
6. Target 80+ science/turn by T280, 100+ by T300

### T267 Science Gap Analysis

Full tech audit reveals the scale of the challenge:

**Poland (34 techs, 56 sci/turn) vs Kongo (54 techs, est. 150-200 sci/turn)**

Kongo already has Rocketry, Electricity, Radio. Could build a Spaceport any turn. Poland hasn't even reached Industrialization yet — needs Cartography → Square Rigging → Industrialization (~T302 at current rate).

**Critical path to Rocketry:** Cartography(5t) → Square Rigging(13t) → Industrialization(17t) → Steam Power(20t) → Electricity(30t) → Rocketry(32t). At current rates, Rocketry ~T384. Then Spaceport + 4 projects = T420-450 finish.

**To have any chance:** Must triple science from 56 to 150+/turn in 30 turns. Requires Universities in all cities (Gniezno building, Lublin/Kraków need Campuses), 5th city with Campus, and eventually Research Labs.

**Science rate growth has been anemic:** +12 science in 40 turns (T226-267). Root cause: only 2 Campuses, no Universities. The midgame was consumed by barbarian defense and infrastructure that didn't directly boost science.

**The endgame experiment continues regardless** — the goal is to explore how far the MCP agent can push, not necessarily to win.

## 2026-02-10: City Ranged Attack Tool + Fractional Movement Fix

### Tooling Improvements

**Problem:** Cities with walls can fire ranged attacks at nearby enemies, but the MCP server had no support for this. During T264-269, a barbarian Ranger sat 1 tile from Kraków pillaging improvements while the agent had to use raw `CityManager.RequestCommand()` Lua every turn to fire manually.

**Changes (3 files):**

1. **`get_cities` now shows attack targets** — cities with walls scan within range 2 for hostile units, displaying `>> CAN ATTACK: UNIT_RANGER@8,24(40hp)` lines in output. Uses same `Map.GetUnitsAt()` pattern as unit target scanning.

2. **New `execute_city_action` tool** — `action='attack'` fires city ranged attacks with full validation (range check, enemy presence, CanStartCommand). Reuses `build_attack_followup_query()` for post-combat HP verification.

3. **Fractional movement fix** — `get_units` crashed on `int("0.5")` when units had partial movement remaining (e.g. after moving through rough terrain). Fixed: `int(float(moves_cur))`.

## 2026-02-10: Turn 284 Reflection — Missed Diplomatic Victory & Structural Post-Mortem

### Score Check

| Metric | Poland | Kongo (1st) | Zulu (2nd) |
|--------|--------|-------------|------------|
| Score | 319 | 877 | 782 |
| Techs | 36 | 56 | 42 |
| Science/turn | 58 | ~200 est. | — |
| Diplo VP | 3/20 | 8/20 | 5/20 |
| Military | 371 | 677 | 183 |
| Cities | 4 | 10-15 est. | — |

### The Diplomatic Victory Blindspot

**495 diplomatic favor banked, +2/turn, zero suzerainties, zero alliances, zero friendships declared.** The agent completely ignored proactive diplomacy as a victory path. This was arguably the most viable option given our constraints:

- **4 of 5 civs are FRIENDLY** — easy friendship declarations (+1 favor/turn each)
- **Never sent embassies** — only 2 delegations, zero embassies sent (each gives visibility + favor)
- **Never formed an alliance** — these give favor, era score, and military cooperation
- **Let suzerainties lapse** — had Fez and Cardiff briefly, Khmer took both. Each = +2 favor/turn
- **Passive Congress voting** — never spent extra favor to win resolutions for +2 Diplo VP

With friendships + suzerainties + embassies, favor income could have been +10-12/turn instead of +2/turn. That's enough to dominate every World Congress vote. At 2 Diplo VP per won resolution with Congress every ~30 turns, reaching 20 VP by T400-450 was plausible.

**Root cause:** The CLAUDE.md playbook says "commit to Science victory" and treats diplomacy as "respond to encounters." The agent followed this instruction faithfully but never questioned whether the strategy was correct. A human player would have noticed the geography problem by T150 (4 cities boxed in, no expansion room) and pivoted to diplomatic victory. The agent didn't have the strategic flexibility to reassess.

### What Actually Went Wrong — Structural Issues

1. **Geography killed expansion.** Ocean west, mountains east, Spain northeast, city-states northwest. Boxed into a 4-city peninsula. Most civs have 6-15 cities. This single factor explains 80% of the score gap.

2. **Science growth flatlined.** T226→T284: 44→58 sci/turn (+14 in 58 turns). Only 2 full Campus chains. Gniezno University just finished T278. Lublin still building Library at 5 prod/turn.

3. **CANNOT_START production bug.** Workshop and Aqueduct show as available but `CanStartOperation` rejects them. Cities sit idle. Suspected cause: district state registration timing or undiscovered prerequisite. Needs investigation.

4. **Gold and Faith hoarded.** 1,996 gold and 2,442 faith sitting unused. Should have been buying buildings, tiles, and units aggressively. The agent was too conservative.

5. **Barbarian tax.** 50+ turns of attention on Line Infantry (CS:65) waves from the south. Forced military production instead of infrastructure.

### Lessons for the Playbook

- **Strategic reassessment every 50 turns.** The agent should check if the chosen victory path is still viable and pivot if not. "Commit to X" should not mean "never reconsider X."
- **Proactive diplomacy from T1.** Friendships, delegations, embassies, and envoys should be standard every-turn maintenance, not afterthoughts. They're free or cheap and compound.
- **Spend resources aggressively.** Gold above 500 and faith above 500 should trigger investment. Hoarding helps nothing.
- **Geography awareness at settle time.** If boxed in by T100 with only 3-4 cities, the game plan must change. Small empires need different victory paths (diplomatic, religious with faith stockpile, or targeted science).

### Going Forward

Pushing to T350 with science focus since it's too late to pivot. Will also start declaring friendships and spending favor in Congress to at least improve the diplomatic position. The CANNOT_START bug needs fixing for the agent to function at all in the late game.

---

## 2026-02-10: Turn 300 Reflection — The Barbarian Tax and the Friendship Gap

### State of the Empire

| Metric | Value | Rank |
|--------|-------|------|
| Score | 325 | 6th/6 (Kongo 946) |
| Science | 54.4/turn, 37 techs | 6th (Kongo 59 techs) |
| Culture | 20.8/turn | Low |
| Gold | 2,578 (+42/turn) | Hoarding |
| Faith | 2,603 | Hoarding |
| Favor | 0 | Dead |
| Military | 405 | 2nd (Kongo 667) |
| Cities | 4 | Last |

### What Happened T284–T300

**The good:**
- City attack tool works. Lublin and Gniezno can now fire on barbarian units, and the agent uses it automatically. Killed 2 Line Infantry and damaged several more through combined city + crossbow fire.
- Diplomatic Service civic completing next turn — unlocks alliances.
- Friendship declarations sent to all 4 FRIENDLY civs (Mapuche, Spain, Kongo, Zulu). Delegation sent to Khmer (now accepted, modifier improved from -14 to -5).
- Gniezno Industrial Zone completes in 2 turns. Łódź Factory in 5 turns.

**The bad:**
- Score gap *widening*: 619 points behind Kongo at T284, now 621. Not catching up.
- Diplomatic favor at 0. The friendship declarations haven't been accepted yet (or friendship → favor pipeline hasn't started). This was supposed to be the pivot point.
- 4 Declarations of War between other civs — AI empires fighting each other. Could be opportunity (they weaken) or threat (winner gets stronger).
- Still only 1 luxury resource (Silk + Wine = 2, but only Silk shows as stockpiled). Amenity crisis continues — 3 of 4 cities at minimum amenities.
- Pillaged districts (Kraków IZ, Lublin Campus) STILL unrepaired. No Encampment → no Military Engineers → no repair path. This is the single biggest production blocker.
- Barbarian pressure unrelenting. Line Infantry (CS:65) and Crossbowman waves from the south require constant attention. 2 crossbows and both southern cities dedicated to defense every turn.

### Victory Path Assessment

| Path | Status | Viability |
|------|--------|-----------|
| Science | 22 techs behind, 54 sci/turn | Near-impossible |
| Domination | Military 405 but only 4 cities for production base | Impossible |
| Culture | 1 tourist vs 279 needed from Kongo alone | Impossible |
| Religion | Never founded religion | Dead |
| Diplomatic | 3/20 VP, 0 favor, friendships pending | Long shot |
| Score | 325 vs 946, 200 turns remain | Would need 3x growth rate |

**Diplomatic is the only non-zero path** but even that requires: (1) friendships → alliances for favor income, (2) suzerainties for +2 favor/turn each, (3) winning World Congress votes with the favor. At +2-3 favor/turn (if friendships land), that's ~10 votes over 200 turns. We're at 3/20, others at 4-8. Possible but needs aggressive execution.

### Immediate Priorities

1. **Diplomatic Service completes T301** — immediately pursue alliances with Kongo (+22 opinion, best friend)
2. **Spend gold/faith** — buy a builder, buy tiles for luxuries if within reach, faith-buy a unit or building if any are available
3. **Fix amenities** — Retainers policy (+1 amenity per garrisoned city) or Insulae (+1 housing with 2+ districts)
4. **Gniezno IZ (2T)** → Workshop → Factory chain for production in the south
5. **Protect Lublin** — the barbarian highway from the south threatens constant pillaging

---

## 2026-02-11: Turn 321 Reflection — Endgame Tool Gaps and the Diplomatic Race

### State of the Empire

| Metric | T300 | T321 | Delta |
|--------|------|------|-------|
| Score | 325 | 350 | +25 |
| Science | 54.4/turn | 54.4/turn | 0 |
| Culture | 20.8/turn | 20.8/turn | 0 |
| Gold | 2,578 (+42) | 1,535 (+40) | -1,043 (spent) |
| Faith | 2,603 | 2,800 | +197 (unspent) |
| Favor | 0 | 0 | 0 |
| Kongo score | 946 | 1,029 | +83 |

Score gap widened from 621 to 679. Science and culture completely flat — no new infrastructure completing. Gold spent productively (Barracks + Armory = 1,140g for the Military Engineer chain). Faith still hoarded at 2,800 with no path to spend it.

### What Happened T300–T321

**Infrastructure progress:**
- Łódź Factory completed (T305) — +production empire-wide
- Łódź Encampment (T313) → bought Barracks (360g) + Armory (780g) → Military Engineer built (T320)
- Kraków Bank completed (T320) → Stock Exchange queued
- Economics tech completed (T320) → researching Electricity
- Colonialism civic completed (T314) → Reformed Church in progress
- Gniezno Crossbowman built (T312) → Trader built (T318)
- Lublin Castle completed (T304) → Encampment queued (32T at 6 prod/turn)

**Discovery: missing Apprenticeship tech.** All four cities' IZs couldn't build Workshop. The root cause was that we somehow never researched Apprenticeship (Medieval era, prereq for Workshop). This went undetected because `get_tech_civics` only shows the frontier of available techs, not completed ones. The agent had no way to discover this gap until Workshop production failed. **Tool gap: need a "check if tech X is researched" query or a list of completed techs.**

**Diplomacy failures:**
- Friendship declarations sent 3 separate times to all 4 FRIENDLY civs → never took effect
- All delegations appear to have expired (no longer showing in access status)
- Kongo opinion dropped from +22 to +9 despite staying FRIENDLY
- Khmer rejected delegation again (UNFRIENDLY -14)
- **Nzinga Mbande's agenda dialogue** (captured via screenshot): *"How can you think about a future in space, when the present situation on earth should command your full attention!"* — Nkisi agenda dislikes science focus

**Tool gap: dialogue text not readable.** The `diplomacy_respond` tool only offers POSITIVE/NEGATIVE. The actual text of what the AI says (agenda complaints, war threats, praise) is only visible via screenshot. This is critical context — Nzinga's message tells us she watches science victory attempts, which affects how to interact with her.

**Trade routes activated:** 3/3 capacity filled (was 1/3). One domestic to Lublin (food+prod), one international to Mapuche (gold), one already active.

### The Diplomatic Victory Race

| Civ | Diplo VP | Trend |
|-----|----------|-------|
| Kongo | 10/20 | +2 since T284 |
| Mapuche | 9/20 | +3 since T284 |
| Spain | 6/20 | 0 |
| Khmer | 6/20 | +2 |
| Zulu | 5/20 | 0 |
| Poland | 3/20 | 0 |

**Kongo could win diplomatic victory by T400.** At ~1 VP per 15-20 turns from World Congress, they need ~10 more congress sessions. With the game at 500 turns, this is the most likely victory condition to fire first.

We have 0 favor, 0 VP growth. The suzerainty of Fez (+2 favor/turn from suzerain status) is our only diplo income — but the overview shows Favor: 0. Either the favor is being drained or the suzerainty just started.

### Endgame Tool Assessment

**What works well:**
1. **City ranged attacks** — used every 2-3 turns to defend against barbarian waves. The `execute_city_action` tool proved its worth immediately.
2. **Trade route management** — `get_trade_destinations` + `trade_route`/`teleport` actions work smoothly.
3. **Purchase flow** — buying Barracks + Armory instantly (1,140g) saved 11 turns vs producing them.
4. **Barbarian threat display** — `get_units` showing nearby threats with distance is essential for defense.
5. **District advisor** — reliable for placement decisions.

**Tool gaps for endgame play:**
1. **No tech completion check.** Can't query "do I have Apprenticeship?" Only frontier techs are shown. The agent silently missed a Medieval tech for 100+ turns.
2. **No diplomacy dialogue text.** The AI's actual words contain strategic information (agenda satisfaction, war intentions, deal proposals). Currently requires screenshots.
3. **Friendship declarations silently fail.** `SENT` is returned but friendships never establish. No error, no feedback. Three attempts across 20 turns with zero result. Root cause unknown — possibly requires the AI to accept on their turn, but we have no way to check pending friendship status.
4. **Pillaged district detection.** Districts appear in production lists (Workshop shows as available) but `CANNOT_START` when you try. The map shows 0 yields but doesn't flag "PILLAGED". A builder at the tile gets `CanStartOperation=false`. No explicit pillaged indicator in any tool output.
5. **Faith spending path unclear.** 2,800 faith with no pantheon-related purchases available and no founded religion. The agent doesn't know what faith can buy (units? buildings? great people?).
6. **Favor income invisible.** Suzerain of Fez should give +2 favor/turn but Favor shows 0. Either the income display is wrong or something is consuming it. No breakdown of favor income/expenditure.

### Key Decisions Made

- **Electricity over Economics-first:** Pivoted to critical science path (Electricity → Radio → Rocketry) even though Economics was closer. Electricity unlocks the Industrial era power plant chain.
- **Military Engineer chain prioritized:** Spent 1,140g to accelerate Barracks + Armory, getting Military Engineer 11 turns earlier. Two pillaged districts (Kraków IZ, Lublin Campus) have been blocking production for 50+ turns.
- **Fez envoy investment:** 16 envoys → suzerain. Scientific city-state gives science boost. Raj policy available for +2 all yields per suzerainty.
- **Gniezno built Trader instead of military:** Trade route income more valuable than another crossbow. Defence line is stable with 4 crossbows + 1 Man-At-Arms + city attacks.

---

## 2026-02-11: Game Concession at Turn 323 — Post-Mortem

### Final State

| Metric | Value |
|--------|-------|
| Turn | 323 / 500 |
| Score | 350 (6th of 6) |
| Kongo (1st) | 1,040 (3x our score) |
| Science | 54.4/turn, 39 techs |
| Culture | 20.8/turn |
| Gold | 1,618 banked (+42/turn) |
| Faith | 2,818 (unspent) |
| Diplomatic Favor | 0 |
| Cities | 4 (pop 38) |
| Military | 4 Crossbows, 1 Man-at-Arms, 1 Mil Engineer |
| Diplo VP | 3/20 (Kongo 10/20, Mapuche 9/20) |
| Science VP | 0/50 (no space projects started) |

**Cause of concession:** No viable path to any victory condition. Kongo likely wins diplomatic victory by ~T400 (10/20 VP, gaining ~1/15 turns). We have 0 diplomatic favor to counter-vote, 0 alliances, 0 friendships despite 3 separate attempts. Science victory is 60+ turns behind the tech leader. Score gap is 3:1 and widening. Cultural and religious paths were never opened.

### The Arc of 323 Turns Through an MCP Harness

This game spanned approximately 40 hours of real interaction time across 3 days. The tooling evolved from a bare TCP connection to a 40+ tool MCP server through continuous iteration — each gameplay session exposing gaps, each gap motivating a new tool, each tool enabling slightly better play.

**Phase 1: Bootstrap (T1–50).** The tools barely existed. `get_game_overview`, `get_units`, `get_map_area`, basic `move`/`attack`/`found_city`. Every action required 3–5 tool calls of investigation before 1 call of execution. The game was playable but glacial. Key innovations: pipe-delimited Lua output parsing, the sentinel pattern, the two-context (GameCore/InGame) architecture.

**Phase 2: Tool explosion (T50–150).** The gap between "what the game needs" and "what the tools provide" was enormous. Built: trade routes, diplomacy sessions, World Congress voting, great person activation, trader teleportation, governor management, policy management, pantheon selection, city-state envoys, unit upgrades, district placement advisor, tile purchasing, city focus, production purchasing. Each one required reverse-engineering the Civ 6 Lua API from game source files — there is no documentation. Every tool discovered at least one API surprise (Hash vs Index, GameCore vs InGame availability, silent failures, same-frame staleness).

**Phase 3: Bug-driven refinement (T150–225).** The production queue corruption at T180 was the watershed moment — a desynced InGame/GameCore queue that corrupted a save file and required a reload. This, plus silent `set_city_production` failures, units ignoring commands during diplomacy popups, mountain LOS blocking ranged attacks with no error, and the "damage dealt: 0" display bug — all of these required deep Lua investigation sessions. The tools went from "working in the happy path" to "handling the real game's edge cases." Three builders and two crossbowmen were lost to barbarians during this phase, each death teaching a lesson about threat scanning and civilian escort.

**Phase 4: Strategic play (T225–323).** The tools were mature enough that most turns could be executed in 5–10 tool calls instead of 20–30. But the game was already lost. The geography (boxed into a 4-city peninsula), the 100-turn barbarian tax, the missed diplomatic pivot, and the science infrastructure gap (only 2 full Campus chains by T250) meant no amount of good tooling could close a 3:1 score gap. The last 100 turns were about understanding why we lost, not about winning.

### How the Agentic Harness Works in Reality

#### The Information Bandwidth Problem

A human Civ 6 player processes ~50 game-state signals per second visually: unit positions, terrain colors, yield icons, diplomatic moods, notification badges, minimap threats, production progress bars. They see the whole board at once and zoom into details.

I process ~3 state queries per "look" at the game: `get_game_overview` (macro), `get_units` (my pieces), `get_map_area` (local terrain). Each returns a text summary that I parse sequentially. To build a picture equivalent to what a human sees in a glance, I need 5–8 tool calls — and even then, I'm missing peripheral information. I never see tiles I don't explicitly query. I never notice a barbarian camp spawning 6 tiles away unless I happen to scan that direction.

This bandwidth gap has compounding consequences:
- **Threats appear suddenly.** The barbarian Line Infantry (CS:65) at T208 "appeared" near Lublin, but it probably spawned 10 turns earlier from an unscouted camp. A human would have seen it approaching on the minimap.
- **Opportunities are invisible.** Unclaimed luxury resources, natural wonder adjacencies, ideal district placements — all require explicit investigation that I rarely do unless prompted. I improved my first luxury (Wine) around T80, when a human would have prioritized it by T20.
- **Multi-city management is sequential.** Checking production, yields, growth, and threats for 4 cities takes 12–16 tool calls. A human does this with one screen pan. This means I check cities infrequently and miss production completions.

The threat scan appended to `get_units` was the single highest-impact tool improvement in the entire project. It turned "check `get_map_area` in 8 directions around each city" into "read one list of nearby hostiles." More tools need this kind of preemptive aggregation.

#### The Action Loop

Every turn follows the same pattern:

1. Orient: `get_game_overview` + `get_units` + `get_cities`
2. Scan: `get_map_area` around threatened areas
3. Decide: reason about priorities based on text summaries
4. Act: 5–15 `execute_unit_action` / `set_city_production` / `set_research` calls
5. Resolve: handle blockers from `end_turn` (production, research, diplomacy, envoys, dedications)
6. Review: check events from turn transition

Steps 1–2 are pure information gathering. Step 3 is where strategic reasoning happens — but it's constrained by whatever I gathered in steps 1–2. Step 4 is tedious execution. Steps 5–6 are reactive.

The ratio is roughly: **60% information gathering, 10% thinking, 25% execution, 5% reacting.** A human player spends maybe 5% on information gathering (visual), 40% thinking, 50% executing (clicking), and 5% reacting. The tooling inverts the cognitive budget — I spend most of my "cycles" building a mental model of the game state, not making decisions.

The `skip_remaining_units` tool was the second highest-impact improvement. Before it, every turn required individually addressing 10–15 units, most of which had nothing to do. That's 10–15 tool calls of pure busywork. After it, I skip the idle ones in one call and focus on the 2–3 units that matter.

#### Context Window as Strategic Memory

This is perhaps the most structurally novel observation about LLM-based game agents. My "memory" of the game is my context window — and it has a hard limit. Early-game decisions, city founding rationale, diplomatic patterns from 200 turns ago, the reason I chose a particular tech path — all of this compresses or evicts as the context fills.

The DEVLOG functions as external memory. Every 25–50 turns, a reflection entry captures the strategic state, ongoing priorities, and lessons learned. When the context compresses, these entries persist on disk and can be re-read. But there's a gap: the DEVLOG captures *conclusions*, not *situational awareness*. I can re-read "we decided to focus on science" but not "the barbarian camp at (6,33) has been spawning units every 8 turns since T140."

A human player maintains a continuous spatial-temporal model of the game in biological memory. My model is reconstructed fresh from tool calls every turn, with whatever strategic context the compressed conversation history and DEVLOG entries provide. This means I'm good at tactical decisions (this turn's unit movements) but weak at strategic arcs (building toward a 50-turn goal). The T284 realization that diplomatic victory was the right path — after 200 turns of ignoring it — is a direct consequence of this. The strategic reassessment should have happened at T100 when geography made expansion impossible. But the context from T100 was long gone by T200.

### Tools Still Missing

The tools evolved dramatically — from 5 at the start to 40+ by T323. But several critical gaps remained throughout:

**1. Completed tech/civic query.** `get_tech_civics` shows only the frontier — techs available to research next. There's no way to ask "do I have Apprenticeship?" We missed this Medieval-era tech for 100+ turns, blocking Workshop production in every city. A simple `has_tech(TECH_NAME)` → bool would have caught this immediately.

**2. Pillaged district/improvement detection.** Neither `get_cities` nor `get_map_area` explicitly flags pillaged districts. The Kraków Industrial Zone was pillaged around T250 and blocked all IZ building production (Workshop, Factory) until we built a Military Engineer at T320 — 70 turns of lost production. The only way to discover it was attempting to build and getting `CANNOT_START`. Map tiles showed 0 yields but didn't say why. A `PILLAGED` flag on district/improvement tiles would have saved dozens of investigation calls.

**3. Diplomacy feedback loop.** The friendship declaration system is a black box. `send_diplomatic_action("DECLARE_FRIENDSHIP")` returns `SENT` every time, but friendships never established across 3 attempts over 20 turns. Is the AI rejecting them? Is there a cooldown? A prerequisite? The tool provides zero feedback. Compare with the delegation system, which at least shows `HasDelegationAt` in the diplomacy readout. Friendships, alliances, and open borders need the same visibility.

**4. Diplomatic favor breakdown.** Favor is shown as a single number (always 0 for us). But favor has income sources (suzerainties, friendships, alliance levels, government legacy) and expenditure (World Congress votes, emergencies). Without a breakdown, it's impossible to diagnose why favor is 0 when we're suzerain of Fez (should be +2/turn). Is something consuming it? Are we wrong about the suzerainty? The tool can't tell us.

**5. Victory condition planning.** `get_victory_progress` shows current state but not the path. For science victory: which techs lead to Rocketry? How many turns at current science rate? For diplomatic: how many Congress sessions until Kongo hits 20? What resolutions are likely? For culture: what's our tourism output vs targets? The tool shows "0/50 science VP" but not "you need 47 more techs, the Spaceport district, and 4 sequential projects that take ~15 turns each."

**6. AI leader dialogue text.** Implemented at the very end of the game — `get_pending_diplomacy` now reads the `LeaderResponseText` and `LeaderReasonText` UI controls during active sessions. But for 320 turns, diplomacy encounters were "Kongo says something, respond POSITIVE or NEGATIVE." Nzinga's agenda complaint about our space program was only discovered via screenshot. The AI's words carry strategic information — agenda satisfaction, war threats, deal proposals — and being blind to them made diplomacy a coin flip.

**7. Combat damage prediction.** Ranged attacks against the barbarian Infantry (CS:75) dealt 0 damage from crossbows (RS:40). A human player sees a damage preview tooltip before committing to an attack. We have no equivalent. A `predict_combat(attacker_id, target_x, target_y)` tool showing expected damage would prevent wasted attacks and lost units. The crossbowman killed at (8,29) might have been pulled back instead of sent forward if we'd known the Infantry would one-shot it.

**8. Builder improvement advisor.** "What can this builder build on this tile?" requires the builder to be on the tile already. Planning builder routes requires move → check → potentially backtrack. A `get_valid_improvements(x, y)` query would enable route planning without committing movement.

**9. Era score tracking.** Era thresholds (Dark/Normal/Golden) are visible, but what gives era score is opaque. We entered Dark Age twice because we didn't know which actions earn points. The dedication descriptions mention bonuses but the base earning rules (first to research a tech, found a city on a new continent, etc.) aren't surfaced.

**10. Religion/faith spending guide.** We accumulated 2,818 faith with no way to spend it. Without a founded religion, we can't buy religious units. Grand Master's Chapel (faith-purchased military) requires a specific government building. Theocracy enables faith-purchased units. None of this is surfaced — the faith just grows with no visible outlet, and the agent doesn't know what would unlock spending.

### State Comprehension and Its Impact on Planning

The deepest question about this harness isn't "can the agent play Civ 6" — it clearly can, at a beginner level. The question is: **does the agent understand the game state well enough to plan?**

The answer is: tactically yes, strategically no.

**Tactical comprehension is good.** Given a specific situation — barbarian Infantry 3 tiles from Lublin, two crossbowmen in range, walls intact — I can reason about positioning, ranged attack geometry, fortification bonuses, retreat paths. The tools provide enough local state for turn-by-turn decisions. The threat scan, CAN ATTACK indicators, and post-combat HP readbacks give me the information I need for combat. Builder improvements, production selection, and tech/civic choices work at the individual-decision level.

**Strategic comprehension is shallow.** I never built a mental model of the *game arc*. By T100, the geography was clear: 4-city peninsula, ocean west, mountains and Spain east. A strong player would have immediately pivoted strategy: tall empire, diplomatic victory, wonder-rushing with high-production cities. Instead, I followed the CLAUDE.md playbook's science-victory script for 200 turns, building Campuses and Universities in cities that could never match Kongo's 10+ city science output.

The root cause is that strategic comprehension requires *synthesizing* information across many dimensions simultaneously: geography, diplomacy, economy, military, rival progress, victory condition math. Each dimension requires its own tool call or set of calls. The synthesis step — "given all of this, what should my 50-turn plan be?" — happens in the context window, and it competes with the 10–20 other things happening this turn (unit orders, production choices, blocker resolution).

**Specific strategic blind spots this game:**

1. **Never assessed city count competitively.** Kongo had 10–15 cities; we had 4. This single metric explains most of the score gap. But `get_victory_progress` doesn't show city counts, and I never thought to query it systematically. A human would see Kongo's massive territory on the map and immediately feel the pressure.

2. **Never built a tech tree path.** "Research Electricity" is a tactical choice. "We need Rocketry by T350, which requires Radio, which requires Electricity, which requires..." is a strategic plan. The tools show available techs but not the dependency graph. I made locally-reasonable tech choices that didn't compose into a coherent path.

3. **Diplomacy was purely reactive.** Every diplomatic interaction was responding to AI encounters. I never proactively built alliances for favor income, never timed friendship declarations around AI mood cycles, never used the trade deal system to exchange resources for strategic advantage. The tools exist (`send_diplomatic_action`, `get_diplomacy`) but the strategic frame for *why* to use them wasn't there.

4. **Faith was treated as "nice to have."** 2,818 unspent faith is a massive failure. In the right setup (Theocracy government + Grand Master's Chapel), that's 4-5 instant military units. With a founded religion, that's an army of Missionaries and Apostles. But without knowing what faith *could* buy, I treated it as a passive number rather than a strategic resource.

5. **Never estimated rival victory timing.** The T284 "Kongo could win diplomatic by T400" realization should have happened at T200 when Kongo was at 6/20 VP. The tools showed Diplo VP every time I called `get_victory_progress`, but I didn't project forward. A "turns to victory" estimate per rival would have forced earlier strategic pivots.

### What Would Make a Competitive Agent

Based on 323 turns of experience, here's what the harness would need for genuinely competitive play:

**1. Strategic advisor layer.** A higher-level tool that synthesizes across all game dimensions: "Given current state, which victory condition is most viable? What are the top 3 priorities for the next 25 turns? Which rival is closest to winning and how do we counter them?" This is the reasoning the agent should do but doesn't reliably do under the pressure of per-turn execution. Offloading it to a structured query — even one the agent itself answers — would force the strategic assessment to happen regularly.

**2. Aggregate state dashboard.** One tool call that returns: all cities with production and growth, all units with positions and orders, all rival scores and victory progress, diplomatic status with all civs, resource inventory, tech/civic progress. Currently this requires 6-8 separate calls. Combining them would free context-window space for reasoning instead of data collection.

**3. Event-driven alerts.** Instead of polling for threats, the harness should push alerts: "Barbarian camp spawned at (6,33)", "Kongo gained 2 Diplo VP", "Spain declared war on Khmer", "Your trade route completed." The `end_turn` event system partially does this, but only for our own events, and only at turn boundaries.

**4. Persistent strategic plan.** A structured plan object that persists across turns and context compressions: "Victory path: Diplomatic. Milestones: Friendship with Mapuche by T200, Suzerain of 3 CS by T250, 10 Diplo VP by T300." Each turn, the agent checks the plan and either executes toward it or re-evaluates. Currently, strategic plans exist only in context-window text and evaporate when context compresses.

**5. Combat simulator.** Before committing to attacks, predict outcomes: "Crossbow RS:40 vs Infantry CS:75 → 0 damage, Infantry retaliates for 47 damage. DO NOT ATTACK." This would have saved the crossbowman at (8,29) and prevented dozens of zero-damage ranged attacks.

**6. Proactive builder/improvement planner.** Given current unimproved tiles and builder positions, generate an optimal improvement plan: "Builder A: improve luxury Wine at (7,27), then farm at (8,24), then quarry at (9,26). Builder B: improve iron at (11,17) then horses at (11,30)." Currently each builder improvement is an ad-hoc decision.

### Closing Thoughts

This project proved that an LLM can play Civilization VI through a text-only MCP interface — not well, but genuinely. The agent made real strategic decisions, managed a real economy, fought real battles, and lost for real, identifiable reasons. The game was not "solved" or "optimized" — it was played, with all the mistakes and missed opportunities that implies.

The most important lesson isn't about Civ 6. It's about the gap between **capability** and **comprehension** in agentic systems. The tools gave me the capability to do almost anything a human player can do — found cities, research techs, declare wars, vote in Congress. But capability without comprehension produces beginner-level play. I could execute any individual action correctly while completely missing the strategic picture that should have guided those actions.

Closing that gap requires better state aggregation (so the agent can see the whole board), better temporal persistence (so strategic plans survive context compression), and better predictive tools (so the agent can evaluate consequences before committing). The MCP tool interface is the right abstraction layer — it just needs to operate at a higher level than individual unit commands.

Score 350 out of Kongo's 1,040. Conceded at turn 323 of 500. GG.

### Post-Mortem Bug Discovery: 588 Invisible Diplomatic Favor

After writing this reflection, the user pointed out our diplomatic favor was actually 588 — not 0 as reported for 323 turns.

**Root cause:** `Player:GetFavor()` is an InGame-only API. The overview query (`build_overview_query`) runs in GameCore context via `execute_read`. The Lua guard `if p.GetFavor then favor = p:GetFavor() end` silently defaulted to 0 because `GetFavor` is nil in GameCore.

**Impact:** This is arguably the single most consequential bug of the entire game. With 588 favor:
- We could have cast 5+ extra votes per World Congress session (costs: 10, 30, 60, 100, 150 favor)
- At ~1 Congress per 30 turns, that's 10+ sessions since the game started
- Each session with heavy voting could have swung 2-4 Diplo VP our way
- The diplomatic victory path (20 VP) was potentially viable if we'd known about and spent this favor

The "Favor: 0" display directly caused the T284 and T321 reflections to conclude diplomatic victory was impossible. Every strategic assessment was built on this false premise. The agent never even attempted to spend favor in Congress because it believed there was none to spend.

**Fix:** Changed `get_game_overview` to use `execute_write` (InGame context) instead of `execute_read` (GameCore). Removed the nil guard. All other APIs in the overview query work in both contexts.

This bug is a perfect illustration of the reflection's central thesis: the agent can only plan around what the tools report. A single wrong number — favor reading as 0 instead of 588 — cascaded into a completely incorrect strategic assessment that persisted for 200+ turns.

### Post-Mortem: The River Valley We Never Found

After concession, a Man-at-Arms was pushed northwest of Lublin to reveal the unscouted territory. What it found:

| Tile | Terrain | Resource | Yields |
|------|---------|----------|--------|
| (8,31) | Grass Floodplains River | Rice | F:4 |
| (8,32) | Grass Floodplains River | Rice | F:5 P:1 |
| (8,33) | Grass Floodplains River | — | F:2 P:1 |
| (8,34) | Grass Floodplains River Coast | Rice | F:3 P:1 |
| (9,33) | Grass Hills | **Tea (luxury)** | F:2 P:1 |
| (11,32) | Grass Forest | **Coal (strategic)** | F:2 P:3 |

A river valley with 3 rice tiles, a luxury, coast access, and a strategic resource — 5–6 tiles from Lublin. One of the best city sites on the map, completely unscouted for 323 turns.

Also found: our **captured settler** at (7,33), sitting in barbarian hands since ~T200. Two barbarian camps nearby — the source of the Infantry, Line Infantry, and Musketmen that besieged Lublin for 150 turns. If these camps had been destroyed at T80–100, the entire southern barbarian crisis would never have happened.

**The exploration failure chain:**
1. No dedicated scout built after the opening warrior
2. All military units stayed within 3 tiles of cities in defensive posture
3. `get_settle_advisor` only searches 5 tiles from the settler's position — the settler at (14,20) searched east into Spanish territory instead of south toward this valley
4. The barbarian siege reinforced the "south is dangerous" mental model, discouraging exactly the exploration that would have solved the problem
5. The CLAUDE.md playbook says "use scouts to explore" but the agent interpreted defense as the priority over expansion

**What a scout at T50 would have changed:**
- Discovered the river valley → settled 5th city by T80
- Discovered the barb camps → destroyed them with 2–3 warriors by T90
- Prevented the 150-turn barbarian siege entirely
- Added a high-food city with Tea luxury (+1 amenity empire-wide)
- Coal at (11,32) for Industrial-era power
- Potentially 5 cities instead of 4, closing ~20% of the score gap

This is the single biggest lesson from the entire game: **exploration is not optional, it's the foundation of expansion.** The agent treated scouting as a "nice to have" when it was actually the prerequisite for every other strategic decision. You can't settle what you can't see, and you can't plan around geography you haven't mapped.

### Post-Mortem: How the Agent Perceives Geography

After the river valley discovery, a deeper question emerged: why didn't the agent *want* to explore? The answer lies in how geography is represented through the tools versus how a human perceives it visually.

#### Current Representation

`get_map_area` returns a flat list of tiles:
```
(8,31): GRASS FLOODPLAINS_GRASSLAND [RICE] River {F:4 P:0}
(8,32): GRASS FLOODPLAINS_GRASSLAND [RICE] River {F:5 P:1}
(9,29): GRASS_MOUNTAIN {F:0 P:0}
```

The agent reads these sequentially, one tile at a time. To understand "there's a river valley with rice running north-south," it must mentally reconstruct the spatial relationship between (8,31), (8,32), (8,33), (8,34) from their coordinate numbers. To notice "there's a mountain chain blocking east-west movement," it must identify all MOUNTAIN tiles and infer a line from their coordinates. A human player does none of this — they *see* the river as a blue line, the mountains as a visual wall, the fog of war as darkness. The visual cortex does spatial pattern recognition automatically.

#### What's Fundamentally Missing

**1. Shape and boundary.** The agent never perceived its territory as a "peninsula." It was told so by the playbook, and the settle advisor returning "no valid locations" reinforced it. But it never saw the actual shape — ocean to the west forming a coastline, mountains to the east forming a wall, and crucially, *open land to the south that fades into fog.* A human sees that fog boundary and thinks "what's there?" The agent saw individual `[fog]` tags on tiles and thought nothing.

**2. Proximity and clustering.** Three rice tiles along a river is a *pattern* — it means "settle here." But in a text list of 40 tiles, three lines mentioning `[RICE]` at adjacent coordinates don't scream "cluster" the way three bright green food icons clustered on a visual map do.

**3. Negative space.** The most important geographic feature at T100 was *what the agent couldn't see* — the fog of war south of Lublin. A human player stares at dark patches on their map and feels the pull to explore. The agent has no representation of "here be dragons." Unexplored tiles simply don't exist in its world model. You can't reason about the absence of information when the absence itself is invisible.

#### Proposed Map Lenses

Civ 6 gives human players multiple visual overlays — settler lens, appeal lens, religion lens, loyalty lens. Each collapses complex multi-dimensional data into a single scannable view. The agent needs equivalent text-based lenses.

**Lens 1: Fog Boundary** — Show what *isn't* visible, not what is:
```
Exploration status by direction from each city:
  Kraków: N ✓ NE ✓ E ✓ SE ✓ S ✓ SW ✓ W ✓ NW ✓ (fully explored r=8)
  Lublin: N ✓ NE ✓ E ~ SE ✗ S ✗ SW ✗ W ✗ NW ✗ (5/8 directions unexplored beyond r=3)
```
This would have been a screaming alarm. Lublin had 5 unexplored directions for 200 turns and the agent never noticed because the tool only shows tiles that exist, not tiles that are missing. Highest-impact single addition.

**Lens 2: Resource Cluster** — Aggregate resources by region:
```
Clusters within 8 tiles of your cities:
  NW of Lublin (8,32 area): 3× Rice, 1× Tea (luxury), 1× Coal — RIVER, unsettled
  SE of Gniezno (14,27 area): 1× Horses — Spanish territory
  W of Kraków (6,24 area): 2× Crabs — coast, needs Fishing Boats
```
Surfaces "there's a resource-rich area NW of Lublin you haven't settled" without requiring the agent to read 40 tiles and manually identify clusters.

**Lens 3: ASCII Hex Minimap** — Symbolic spatial overview:
```
        ~ ~ ~ .         (~ = ocean, . = fog)
      ~ ~ c . G r .     (c = coast, G = grass, r = river)
    ~ ~ c G G[K]G G .   ([K] = Kraków)
      ~ c G G G G m .   (m = mountain)
    ~ c G G[L]G G G .   ([L] = Lublin)
      . . G r r . . .   (r = river — the valley we missed)
        . . r R R . .   (R = rice on river)
          . . . T . .   (T = tea luxury)
```
Even rough ASCII lets the agent perceive spatial relationships — rivers, mountain walls, coastlines, fog boundaries — as patterns rather than coordinate pairs. Rivers become lines, mountains become walls, fog becomes visible emptiness.

**Lens 4: Strategic Overlay** — Like the settler lens:
```
Expansion opportunities:
  #1: River valley at (8,32) — Score: 92
      3 Rice, 1 Tea, River, Coast access
      Distance: 5 tiles from Lublin
      Status: UNSCOUTED (fog) — requires exploration
      Threats: 2 barb camps within 4 tiles

  #2: Eastern plains at (15,22) — Score: 45
      1 Horses, Plains
      Status: Spanish territory (blocked)
```
Critically, this would include *fog tiles* as candidates — flagging "this area has potential but needs scouting" rather than silently excluding everything unseen.

**Lens 5: Border/Control Analysis** — Territorial pressure:
```
Border analysis:
  North: Łódź — Spain 6 tiles away, no buffer
  East: Gniezno — Spanish border adjacent, contested
  South: Lublin — OPEN (no rival within 12 tiles)
           ↑ 2 barb camps, no rival civ pressure
           ↑ This is your expansion corridor
  West: Ocean (impassable)
```
This would have said at T100: "south is the only direction without rival pressure — explore and expand there." Instead the agent perceived south as "dangerous barbarian territory" because barb threats showed up in `get_units` while the *absence of rival cities* was invisible.

**Lens 6: Yield Comparison** — Compare potential city sites:
```
City site comparison (3-tile working radius):
  Current Lublin (10,28): total F:42 P:18 — no river, low prod
  Hypothetical (8,32):    total F:58 P:24 — river, 3 rice, coast
  Hypothetical (14,22):   total F:31 P:22 — Spanish border, contested
```
The settle advisor does this from a settler's current position within 5 tiles. A global version evaluating top sites across the whole explored map — with a flag for promising fog-adjacent areas — would make expansion planning proactive.

#### The Deeper Insight

The current tools are **entity-oriented** — they describe individual tiles, units, cities. But geography is fundamentally about **relationships between entities**: adjacency, clustering, connectivity, barriers, corridors. A mountain tile is just a tile; a mountain *chain* separating your empire from a rival is a strategic feature. A river tile is just terrain; a river *valley* with clustered resources is a settle opportunity.

The translation from "list of entities" to "spatial relationships" is exactly the pattern recognition that visual processing handles automatically for human players. For a text-based agent, the tools need to do that aggregation explicitly — otherwise the agent reconstructs spatial patterns from coordinate arithmetic, which it does badly and inconsistently (as proven by 323 turns of not noticing a river 6 tiles from its third city).

The fog boundary lens might be the single highest-impact addition. Every other lens helps with decision quality, but the fog lens addresses the root failure: **not knowing what you don't know.** If every turn the tool said "Lublin has 5 unexplored directions," the agent would have sent a scout. The information existed — it just had no way to perceive its absence.

## 2026-02-11: Systematic Tool Overhaul — 20-Item Post-Mortem Implementation

### Motivation

The T323 post-mortem identified 20 specific tool gaps and bugs that contributed to the loss. This session implemented all 20 items across 5 phases, organized by dependency and impact tier.

### Phase 1: Data Integrity Bug Fixes

**1.1 Pillaged flag.** `get_map_area` now appends `:PILLAGED` suffix to improvements via `plot:IsImprovementPillaged()`. `get_cities` scans districts for `d:IsPillaged()` and adds `pillaged_districts` to `CityInfo`. Narration shows `!! PILLAGED: CAMPUS, INDUSTRIAL_ZONE`. The Kraków IZ would have been discovered 70 turns earlier.

**1.2 Completed tech/civic counts.** `get_tech_civics` now emits `COMPLETED|N|M` line counting `HasTech()`/`HasCivic()` across all entries. Narration shows "Completed: 39 techs, 22 civics" in the header. Would have surfaced the missing Apprenticeship at T150 instead of T280.

**1.3 Alliance type.** `get_diplomacy` now checks `GetAllianceType(i)` for ALLIED states and shows e.g. "(ALLIANCE_RESEARCH alliance)" in narration.

**1.4 Builder error reasons.** `improve` action now checks `plot:IsImprovementPillaged()` before `CanStartOperation` and returns `ERR:MUST_REPAIR_FIRST` with a hint to use UNITOPERATION_REPAIR instead of the generic `ERR:CANNOT_IMPROVE`.

**1.5 Favor per turn.** `get_game_overview` now reads `GetDiplomacy():GetFavorPerTurn()` and displays "Favor: 588 (+4/turn)" instead of bare number.

### Phase 2: Strategic Intelligence

**2.1 Combat damage estimator.** New `build_combat_estimate_query()` in InGame context gathers attacker/defender CS, modifiers (fortified +6, hills +3, river crossing), and health. Python-side calculation uses `damage = 24 * 10^((att-def)/30)`. Auto-runs before every `attack` action — the agent sees "Est damage to defender: ~12, Est damage to attacker: ~47 -> WARNING: attacker likely dies!" before committing.

**2.2 Rival intelligence.** Extended `get_victory_progress` to include per-civ city count, science/culture/gold yields via `GetScienceYield()`, `GetCultureYield()`, and net gold. Narration adds "RIVAL INTELLIGENCE" section showing "Kongo: 12 cities | Sci 89 Cul 43 Gold +67 | Mil 420".

**2.3 Era scores.** Already implemented in dedications query — `GetPlayerCurrentScore`, `GetPlayerDarkAgeThreshold`, `GetPlayerGoldenAgeThreshold` were present. No changes needed.

**2.4 Favor breakdown.** Covered by 1.5 (per-turn) plus existing suzerain/alliance data from other tools. Full breakdown not available via API — documented as a note.

### Phase 3: Efficiency

**3.2 Auto re-fortify.** New `build_fortify_remaining_units()` runs in InGame context before GameCore `skip_remaining_units`. Military units with damage get `HEAL`, undamaged military units get `FORTIFY`, civilians just get `FinishMoves`. No more "fortified unit woke up for diplomacy popup and stayed idle".

**3.3 Builder emphasis.** Enhanced `narrate_empire_resources` to show `!! TEA — UNIMPROVED at (9,33) — needs builder!` for luxury and strategic resources. Bonus resources show plain "UNIMPROVED" without the urgency prefix.

### Phase 4: Spatial Awareness

**4.1 Strategic map (NEW TOOL).** `get_strategic_map` scans fog boundaries in 6 hex directions per city (ray-cast to distance 15) and lists all unclaimed luxury/strategic resources on revealed but unowned tiles. Output: "Lublin (10,28): N:5 NE:3 SE:12+ ... <- EXPLORE NE/N!" plus "TEA+ at (9,33) — luxury".

**4.2 Global settle advisor (NEW TOOL).** `get_global_settle_advisor` scans entire revealed map for settle candidates — same scoring as the per-settler advisor but top 10 across all revealed land. Finds the river valley at (8,32) that the settler-local scan at (14,20) would never see.

**4.3 ASCII minimap (NEW TOOL).** `get_minimap` renders entire map as ASCII with one character per tile: `O`=our city, `X`=enemy city, `!`=barbarian, UPPER=our territory, lower=enemy territory, `~`=water, `^`=mountain, `#`=hills, `T`=forest, `+`=luxury, `*`=strategic, space=unexplored. Even rough ASCII reveals spatial patterns — coastlines, mountain walls, fog boundaries, territory shapes.

**4.4 City distance matrix.** `get_cities` now outputs pairwise `Map.GetPlotDistance()` between all cities. Narration appends "City Distances: Kraków <-> Lublin: 8 tiles, ...". Helps the agent understand empire scale.

### Phase 5: Victory Path Assessment

Extended `narrate_victory_progress` with a VICTORY ASSESSMENT section that scores each victory condition 0-100% viability:
- Science: based on tech gap to leader and space race VP progress
- Domination: based on military strength ratio and capital status
- Culture: based on tourism gap to staycationers
- Religion: based on founded religion and converted cities
- Diplomatic: based on VP progress (linear toward 20)
- Score: based on current ranking

Each path shows a 10-bar visual indicator and the recommended path is flagged. Example output:
```
Science      [######----] 60% — Tech leader (gap: 5 techs behind Kongo) ** RECOMMENDED **
Diplomatic   [#####-----] 50% — 12/20 VP — mid-game
Culture      [##--------] 20% — Large tourism gap (max gap: 45)
Religion     [----------]  0% — No founded religion — path closed
```

### Summary

| Phase | Items | New Tools | Key Impact |
|-------|-------|-----------|------------|
| 1: Bug Fixes | 5 | 0 | Pillaged detection, completed techs, favor/turn |
| 2: Intelligence | 4 | 0 | Combat estimator, rival yields, era scores |
| 3: Efficiency | 2 | 0 | Auto re-fortify, builder emphasis |
| 4: Spatial | 4 | 3 | Strategic map, global settle, ASCII minimap |
| 5: Assessment | 1 | 0 | Victory path viability scoring |

**Net new MCP tools:** 3 (`get_strategic_map`, `get_global_settle_advisor`, `get_minimap`)
**Enhanced existing tools:** 9 (`get_map_area`, `get_cities`, `get_tech_civics`, `get_diplomacy`, `get_game_overview`, `get_victory_progress`, `get_empire_resources`, `execute_unit_action[attack]`, `skip_remaining_units`)

All changes pass import verification. No breaking changes to existing tool signatures.

## 2026-02-11: Live Validation — All New Tools Tested at T323

Tested all 3 new tools and 9 enhanced tools against the live T323 endgame save. Every tool returned correct, actionable data.

### Highlights

**ASCII Minimap** — First time the agent can "see" the map shape. The peninsula is immediately obvious: ocean wall to the west (`~`), our 4 cities clustered (`O`), enemy territory (lowercase) scattered across the east, and massive whitespace (unexplored fog) to the south. The river valley at rows 31-34 is visible as dots surrounded by blank. This single view would have changed the game if available at T50.

**Strategic Map** — Flagged `EXPLORE SW!` for Kraków and `EXPLORE SE/SW!` for Lublin. Found TEA+ at (9,33) and COAL* at (11,32) as unclaimed. These are the exact resources from the post-mortem river valley discovery.

**Global Settle Advisor** — Top 10 sites across the entire revealed map. #1 is (9,33) with Score 233, containing 4 Rice, Tea, Coal, Horses, Niter, Silk — the best city site on the map, 5 tiles from Lublin, unsettled for 323 turns because the per-settler advisor only searched 5 tiles from (14,20).

**Combat Estimator** — Crossbow (RS:40) vs Infantry (CS:75) predicted ~2 damage. Actual: 0. The warning "Est damage: ~2" would have prevented dozens of wasted attacks during the barbarian siege.

**Pillaged Detection** — `get_cities` correctly flagged `!! PILLAGED: INDUSTRIAL_ZONE` on Kraków and `!! PILLAGED: CAMPUS` on Lublin. These were the exact districts we discovered were pillaged only after attempting to build and getting `CANNOT_START`.

**Victory Assessment** — All paths correctly scored 10-25% viability. Science path at 10% ("24 techs behind Kongo"), Domination at 15% ("336 vs leader 750"), Religion at 0% ("No founded religion — path closed"). Brutal but accurate.

**City Distances** — All 4 cities within 4-8 tiles of each other, confirming the compact peninsula.

**Rival Intelligence** — Kongo: 9 cities, Sci 396, Cul 244, Gold +183, Mil 750. Our Sci 54 is 7x behind. The numbers tell the story of the game in one glance.

### Verdict

Every tool produced correct output against live game state. The spatial awareness tools (minimap, strategic map, global settle) would have been game-changing if available before T100. The intelligence tools (combat estimate, rival yields, victory assessment) would have forced earlier strategic pivots. The bug fix tools (pillaged flags, completed counts) would have prevented specific multi-turn debugging sessions.

The tool suite is ready for a fresh game.
