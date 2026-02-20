# civ6-mcp

An MCP server that lets LLM agents play Civilization VI.

Connects to a running Civ 6 game via the [FireTuner](https://civilization.fandom.com/wiki/Modding_(Civ6)#FireTuner) debug protocol and exposes 73 tools for reading game state and issuing commands — all through the game's rule-respecting UI APIs, no cheats.

## How it works

```
Claude / Any MCP Client
    |  stdio (JSON-RPC)
    v
server.py          <- 73 MCP tools
    |
game_state.py      <- Game logic + human-readable narration
    |
lua/               <- Lua code builders + response parsers (by domain)
    |
connection.py      <- Persistent TCP connection + state discovery
    |
tuner_client.py    <- FireTuner wire protocol
    |  TCP :4318
    v
Civilization VI    <- Game is the TCP server
```

The server generates Lua code at runtime, executes it inside the game's two Lua VMs (GameCore for reading state, InGame for issuing commands), parses the pipe-delimited output, and returns narrated text to the LLM.

## What it can do

**73 tools** covering the full gameplay loop:

| Category | Tools | What they do |
|----------|-------|-------------|
| **Overview** | `get_game_overview`, `get_diary` | Turn, yields, research, score, rankings, game diary |
| **Units** | `get_units`, `unit_action`, `upgrade_unit`, `skip_remaining_units` | List units, move/attack/fortify/skip/found city/improve, upgrade, bulk skip |
| **Cities** | `get_cities`, `get_city_production`, `set_city_production`, `purchase_item`, `set_city_focus`, `city_action` | City state, production, purchases, focus, raze/keep/liberate |
| **Map** | `get_map_area`, `get_minimap`, `get_strategic_map`, `get_settle_advisor`, `get_global_settle_advisor`, `get_district_advisor`, `get_empire_resources`, `get_purchasable_tiles`, `purchase_tile` | Terrain, fog of war, settle/district scoring, resources, tile purchase |
| **Research** | `get_tech_civics`, `set_research` | Tech/civic trees, set research target |
| **Diplomacy** | `get_diplomacy`, `get_pending_diplomacy`, `respond_to_diplomacy`, `send_diplomatic_action`, `form_alliance`, `propose_peace` | Relationships, modifiers, delegations, alliances, peace deals |
| **Trade** | `get_pending_trades`, `respond_to_trade`, `get_trade_routes`, `get_trade_destinations`, `get_trade_options`, `propose_trade` | Trade deals, active routes, destinations, proposals |
| **Government** | `get_policies`, `set_policies`, `change_government`, `get_dedications`, `choose_dedication` | Policy cards, government changes, era dedications |
| **Governors** | `get_governors`, `appoint_governor`, `assign_governor`, `promote_governor` | Governor appointment, assignment, promotion |
| **Promotions** | `get_unit_promotions`, `promote_unit` | Unit promotion selection |
| **City-States** | `get_city_states`, `send_envoy` | Envoy allocation |
| **Religion** | `get_pantheon_beliefs`, `choose_pantheon`, `get_religion_beliefs`, `found_religion`, `get_religion_spread` | Pantheon, religion founding, belief selection, spread tracking |
| **Great People** | `get_great_people`, `recruit_great_person`, `patronize_great_person`, `reject_great_person` | Great person recruitment, patronage, rejection |
| **World Congress** | `get_world_congress`, `vote_world_congress`, `queue_wc_votes` | Resolution voting, favor management |
| **Victory** | `get_victory_progress` | Victory condition tracking |
| **Notifications** | `get_notifications` | Action-required items with resolution hints |
| **Turn** | `end_turn` | End turn with blocking detection, snapshot-diff event report |
| **Game Lifecycle** | `quicksave`, `list_saves`, `load_save`, `launch_game`, `load_save_from_menu`, `restart_and_load`, `kill_game` | Save/load, game launch, restart |
| **Utility** | `dismiss_popup`, `run_lua`, `screenshot` | Popup dismissal, raw Lua escape hatch, visual capture |

Every turn, `end_turn` takes before/after snapshots and reports what happened: units damaged, cities grew, production completed, threats spotted near your cities.

## Requirements

- **macOS** with Civilization VI (Steam version with Gathering Storm DLC)
- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** for package management
- An **MCP client** (Claude Code, Claude Desktop, or any MCP-compatible client)

> **Note:** The FireTuner debug protocol is available on macOS via Aspyr's port. Windows support with the official FireTuner client should also work but is untested.

## Setup

### 1. Enable FireTuner in Civ 6

Edit `AppOptions.txt` to enable the tuner server:

```
# macOS path:
~/Library/Application Support/Sid Meier's Civilization VI/Firaxis Games/Sid Meier's Civilization VI/AppOptions.txt
```

Find the `EnableTuner` setting and change it to `1`:

```
EnableTuner 1
```

Restart Civ 6. The game will now listen on TCP port 4318 for tuner connections.

### 2. Install

```bash
git clone https://github.com/lmwilki/civ6-mcp.git
cd civ6-mcp
uv sync
```

### 3. Test the connection

With Civ 6 running (at least at the main menu):

```bash
uv run python scripts/test_connection.py
```

You should see a successful handshake and list of Lua states.

### 4. Configure your MCP client

#### Claude Code

The repo includes `.mcp.json` which Claude Code will detect automatically. Just open the project directory:

```bash
cd civ6-mcp
claude
```

#### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "civ6": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/civ6-mcp", "civ-mcp"]
    }
  }
}
```

#### Other MCP clients

The server runs over stdio. Start it with:

```bash
uv run civ-mcp
```

## Usage

1. Start Civ 6 and load a game (or start a new one)
2. Connect your MCP client
3. Ask the agent to play:

```
Play my Civ 6 game. Start by getting an overview, then check units and cities,
and play through the turn.
```

The agent will follow a turn loop: orient with `get_game_overview`, check units and cities, scan the map for threats, issue orders, set production and research, and end the turn. See [CLAUDE.md](CLAUDE.md) for the full agent playbook.

## Agent playbook

[CLAUDE.md](CLAUDE.md) contains detailed instructions for LLM agents playing Civ 6:

- Turn loop pattern
- Combat and threat awareness
- Unit stacking rules
- Builder management
- End-turn blocker resolution
- Diplomacy handling
- Common mistakes to avoid

This file is automatically loaded by Claude Code and serves as the agent's strategy guide.

## As a benchmark

This project can serve as a harness for evaluating LLM performance in long-horizon strategic decision-making. Civilization VI is a compelling benchmark environment because it requires:

- **Multi-turn planning** — decisions compound over 100+ turns with delayed payoffs
- **Incomplete information** — fog of war, hidden AI intentions, unexplored map
- **Resource management** — balancing gold, production, science, culture, faith, and military
- **Opponent modeling** — reading diplomatic signals, anticipating AI behavior
- **Strategic adaptation** — responding to threats, shifting priorities based on game state

The MCP interface provides a clean abstraction: the model receives narrated game state as text and responds with tool calls. No vision required (though `screenshot` is available). All game rules are enforced by the engine — the model can't cheat.

Potential evaluation dimensions:
- Score relative to AI opponents at fixed turn counts
- Time to key milestones (second city, first district, first military victory)
- Resource efficiency (gold/science/culture per turn curves)
- Threat response (how quickly the agent detects and handles barbarian incursions)
- Diplomatic effectiveness (relationship scores, trade deal valuations)

## Development story

[DEVLOG.md](DEVLOG.md) is a detailed chronicle of building this project — every bug, API discovery, and playtest session. Highlights:

- Reverse-engineering the FireTuner binary protocol on macOS
- Discovering that `GameCore` and `InGame` Lua contexts have completely different APIs
- The `.Hash` vs `.Index` saga (wrong one crashes the game or produces nonsense)
- Governor appointment using `.Hash` causing a hard game crash (should be `.Index`)
- Building a snapshot-diff notification system because the game's own notifications are ephemeral
- Melee attacks silently failing due to a move modifier flag (`MOVE_IGNORE_UNEXPLORED_DESTINATION`)

## Project structure

```
src/civ_mcp/
  server.py         # MCP tool definitions (73 tools)
  game_state.py     # High-level async API + narration
  narrate.py        # Human-readable output formatting
  end_turn.py       # Turn execution + snapshot-diff event reporting
  connection.py     # FireTuner TCP connection management
  tuner_client.py   # Wire protocol implementation
  diary.py          # Game diary / turn log
  game_launcher.py  # macOS game launch automation
  game_lifecycle.py # Save/load/restart management
  lua/              # Lua code builders + response parsers (by domain)
    _helpers.py     #   Shared boilerplate macros
    models.py       #   Dataclasses for all game state
    overview.py     #   Game overview, rivals, demographics
    units.py        #   Unit queries and actions
    cities.py       #   City state, production, purchase
    map.py          #   Terrain, resources, settle scoring
    tech.py         #   Tech/civic research
    diplomacy.py    #   Diplomacy, trade, alliances
    economy.py      #   Resources, gold, maintenance
    governance.py   #   Governors, policies, promotions
    religion.py     #   Religion, beliefs, faith
    victory.py      #   Victory conditions
    notifications.py #  Notifications and blockers
scripts/
  test_connection.py  # FireTuner protocol smoke test
  test_game_state.py  # GameState integration test
  launch_save.py      # Launch game and load a save
CLAUDE.md           # Agent playbook (auto-loaded by Claude Code)
DEVLOG.md           # Development log
```

## License

MIT
