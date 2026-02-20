# civ6-mcp

An MCP server that lets LLM agents play full games of Civilization VI.

Connect any MCP-compatible client — Claude Code, Codex, Gemini CLI, or your own — to a running Civ 6 game. The agent reads game state, moves units, manages cities, conducts diplomacy, and ends turns, all through the game's own rule-enforcing APIs. No cheats, no vision model required.

<!-- TODO: Add screenshot or GIF of agent playing -->

## Capabilities

70+ tools covering the full gameplay loop:

- **Units** — list, move, attack, fortify, found cities, build improvements, promote, upgrade
- **Cities** — inspect, set production, purchase units/buildings with gold, manage focus
- **Map** — explore terrain, resources, fog of war; get settle and district placement advice
- **Research** — browse tech and civic trees, set research targets
- **Diplomacy** — relationships, modifiers, delegations, embassies, alliances, peace deals
- **Trade** — propose and respond to deals, manage trade routes and destinations
- **Government** — swap policy cards, change governments, choose era dedications
- **Governors** — appoint, assign to cities, promote
- **Religion** — found pantheons and religions, select beliefs, track spread
- **Great People** — recruit, patronize, reject
- **World Congress** — vote on resolutions, manage diplomatic favor
- **Victory** — track progress across all victory conditions
- **Game lifecycle** — save, load, launch, restart, screenshot

Every turn, `end_turn` takes before/after snapshots and reports what happened: units damaged, cities grew, production completed, threats spotted near your cities.

## Quick start

### 1. Enable FireTuner in Civ 6

Edit `AppOptions.txt` and set `EnableTuner 1`:

```
# macOS
~/Library/Application Support/Sid Meier's Civilization VI/Firaxis Games/Sid Meier's Civilization VI/AppOptions.txt

# Windows
%USERPROFILE%\Documents\My Games\Sid Meier's Civilization VI\AppOptions.txt
```

Restart Civ 6. The game will listen on TCP port 4318 for connections.

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

The server runs over stdio. Point your client at it:

<details>
<summary><strong>Claude Code</strong></summary>

The repo includes `.mcp.json` — detected automatically:

```bash
cd civ6-mcp
claude
```
</details>

<details>
<summary><strong>Claude Desktop</strong></summary>

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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
</details>

<details>
<summary><strong>Codex</strong></summary>

Add to `.codex/config.toml` in the project root:

```toml
[mcp_servers.civ6]
command = "uv"
args = ["run", "--directory", "/path/to/civ6-mcp", "civ-mcp"]
```
</details>

<details>
<summary><strong>Gemini CLI</strong></summary>

Add to `.gemini/settings.json` in the project root:

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
</details>

<details>
<summary><strong>Other MCP clients</strong></summary>

The server speaks stdio JSON-RPC:

```bash
uv run civ-mcp
```
</details>

### 5. Play

Load a game in Civ 6, connect your client, and try:

```
Play my Civ 6 game. Start by getting an overview, then check units and
cities, and play through the turn.
```

The agent will orient with `get_game_overview`, scan the map for threats, move units, set production and research, handle diplomacy, and end the turn.

## As a benchmark

Civilization VI is a compelling environment for evaluating LLM strategic reasoning. Games run 300+ turns with compounding decisions, incomplete information, and multiple competing objectives — a significant step up from single-turn or short-horizon tasks.

- **Multi-turn planning** — decisions compound over hundreds of turns with delayed payoffs
- **Incomplete information** — fog of war, hidden AI intentions, unexplored map
- **Resource management** — balancing gold, production, science, culture, faith, and military
- **Opponent modeling** — reading diplomatic signals, anticipating AI behavior
- **Strategic adaptation** — responding to threats, shifting priorities mid-game

The MCP interface provides a clean abstraction: the model receives narrated game state as text and responds with tool calls. All game rules are enforced by the engine. A companion web app lets you replay sessions turn by turn.

## How it works

```
Claude / Any MCP Client
    |  stdio (JSON-RPC)
    v
MCP Server (Python)    <- 70+ tools
    |
    |  Generates Lua code at runtime
    |  TCP :4318
    v
Civilization VI        <- Game is the TCP server
```

The server maintains a persistent TCP connection to Civ 6 via the FireTuner debug protocol. It generates Lua code, executes it inside the game's two Lua VMs (GameCore for reading state, InGame for issuing commands), parses the output, and returns narrated text to the LLM.

The repo includes an [AGENTS.md](AGENTS.md) playbook (symlinked as `CLAUDE.md` for Claude Code) with detailed instructions for agents: turn loop, combat, diplomacy, common pitfalls. See [DEVLOG.md](DEVLOG.md) for the full development story, including reverse-engineering the FireTuner protocol and the many API quirks discovered along the way.

## Requirements

- **macOS or Windows** with Civilization VI (Steam version, Gathering Storm DLC)
- **Python 3.12+** with [uv](https://docs.astral.sh/uv/)
- An **MCP client** (Claude Code, Codex, Gemini CLI, or any MCP-compatible client)

## License

MIT
