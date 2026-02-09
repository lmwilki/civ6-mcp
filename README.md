# civ6-mcp

An MCP server that lets LLM agents play Civilization VI.

Connects to a running Civ 6 game via the [FireTuner](https://civilization.fandom.com/wiki/Modding_(Civ6)#FireTuner) debug protocol and exposes 35 tools for reading game state and issuing commands — all through the game's rule-respecting UI APIs, no cheats.

https://github.com/user-attachments/assets/placeholder-demo-video

## How it works

```
Claude / Any MCP Client
    |  stdio (JSON-RPC)
    v
server.py          <- 35 MCP tools
    |
game_state.py      <- Game logic + human-readable narration
    |
lua_queries.py     <- Lua code builders + response parsers
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

**35 tools** covering the full gameplay loop:

| Category | Tools | What they do |
|----------|-------|-------------|
| **Overview** | `get_game_overview` | Turn, yields, research, score, rankings |
| **Units** | `get_units`, `execute_unit_action`, `upgrade_unit` | List units, move/attack/fortify/skip/found city/improve, upgrade |
| **Cities** | `get_cities`, `get_city_production`, `set_city_production`, `purchase_item` | City state, available production, queue items, buy with gold |
| **Map** | `get_map_area`, `get_settle_advisor`, `get_empire_resources` | Terrain/resources with fog of war, settle site scoring, resource survey |
| **Research** | `get_tech_civics`, `set_research` | Tech/civic trees, set research target |
| **Diplomacy** | `get_diplomacy`, `get_pending_diplomacy`, `diplomacy_respond`, `send_diplomatic_action` | Relationship state, modifiers, meet civs, send delegations |
| **Trade** | `get_pending_deals`, `respond_to_deal` | Read and accept/reject AI trade offers |
| **Government** | `get_policies`, `set_policies` | Policy slots, swap policy cards |
| **Governors** | `get_governors`, `appoint_governor`, `assign_governor` | Governor management |
| **Promotions** | `get_unit_promotions`, `promote_unit` | Unit promotion selection |
| **City-States** | `get_city_states`, `send_envoy` | Envoy allocation |
| **Religion** | `get_available_beliefs`, `choose_pantheon` | Pantheon founding |
| **Notifications** | `get_notifications` | Action-required items with resolution hints |
| **Turn** | `end_turn` | End turn with blocking detection, snapshot-diff event report |
| **Utility** | `dismiss_popup`, `execute_lua`, `screenshot` | Popup dismissal, raw Lua escape hatch, visual capture |

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
  server.py         # MCP tool definitions (35 tools)
  game_state.py     # High-level async API + narration
  lua_queries.py    # Lua code builders + response parsers (49 dataclasses)
  connection.py     # FireTuner TCP connection management
  tuner_client.py   # Wire protocol implementation
scripts/
  test_connection.py  # FireTuner protocol smoke test
  test_game_state.py  # GameState integration test
  test_queries.py     # Lua query builder test
CLAUDE.md           # Agent playbook
DEVLOG.md           # Development log
```

## License

MIT
