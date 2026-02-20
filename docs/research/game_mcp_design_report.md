# Game MCP Design Research Report

Synthesized from three parallel research threads: existing game MCP servers, academic Civ/strategy LLM agents, and MCP design best practices.

---

## Key Design Decisions for Civ 6 MCP

### 1. The LLM Should NOT Micromanage

The strongest signal from academic research: **successful game agents restrict the LLM to strategic decisions and delegate tactics to deterministic code.**

| Project | LLM Controls | Delegated to Code |
|---------|-------------|-------------------|
| **CivAgent** (Netease) | Diplomacy, high-level strategy (every 5 turns) | Unit movement, city production, combat |
| **Vox Deorum** (Civ V) | Grand strategy, victory path, diplomacy persona | All unit-level tactical execution |
| **CivRealm Mastaba** | Advisor sets strategy | Per-unit workers handle movement |
| **TextStarCraft II** | Strategic analysis | Action queue parsed into game commands |

CivAgent is the most extreme: the LLM only picks from ~7 diplomatic "skills" with parameters, max 3 per decision point, every 5 turns. Unit micro stays with rule-based AI.

**Implication for us:** We should support both modes:
- **Advisor mode** — LLM sees state, recommends strategy, human executes
- **Autonomous mode** — LLM makes decisions, but at a higher level than individual unit moves (e.g., "fortify eastern border" → server translates to unit commands)

### 2. Tool Count: Less is More

Every tool definition costs ~250 tokens of context. Research consistently shows agent accuracy degrades with more tools.

| Approach | Example | Risk |
|----------|---------|------|
| 1:1 API mapping (bad) | `move_unit`, `attack_unit`, `fortify_unit`, `get_units`, `get_unit_detail`... | 20+ tools, context bloat, agent confusion |
| Outcome-oriented (good) | `get_game_overview`, `get_details(category)`, `execute_action(type, params)`, `end_turn` | 5-8 tools, clear intent |
| Meta-tool / progressive disclosure (best) | `discover` → `get_details` → `execute` | Minimal base, expand on demand |

**Target: 8-12 tools max.** Group by purpose, not by game entity.

### 3. State Representation: Progressive Disclosure

The #1 anti-pattern is dumping full game state JSON. A mid-game Civ 6 state could be 50-100k tokens.

**The right pattern (from ProDisco, chess-support-mcp, CivRealm):**

```
Level 0: get_game_overview()     → ~500 tokens, always called first
Level 1: get_details(category)   → military/economic/diplomatic/map detail
Level 2: get_specific(entity_id) → one city, one unit, one tile area
```

CivRealm's 5x5 tile window per unit is a concrete example — don't show the whole map, show what's relevant.

**Pre-filter and narrate.** Return:
> "The Aztecs have 5 military units near your eastern border. Your warrior at 55,21 is the only defender."

Not:
> `{"units": [{"id": 131073, "type": "UNIT_WARRIOR", "x": 55, "y": 21, ...}, ...]}`

### 4. Context Window Management Strategies

Every strategy game agent project struggles with this. Solutions that work:

| Strategy | How | Used By |
|----------|-----|---------|
| **Spatial windowing** | Only show nearby tiles, not full map | CivRealm (5x5 per unit) |
| **Temporal compression** | Summarize old turns, keep recent N | CivAgent (20-line window) |
| **Hierarchical delegation** | Global advisor + local workers | CivRealm Mastaba |
| **Scope restriction** | LLM only handles strategy, not tactics | CivAgent, Vox Deorum |
| **Detail-level params** | `detail="brief"` vs `detail="full"` | chess-support-mcp |
| **Server-side filtering** | Server picks what's relevant to return | Anthropic code execution MCP |
| **RAG for past experience** | Retrieve relevant history, don't keep all | CivAgent |

### 5. Tools vs Resources vs Prompts

From the MCP spec and real implementations:

| MCP Primitive | Use For | In Our Server |
|---------------|---------|---------------|
| **Tools** | Everything the LLM calls autonomously | State queries, actions, turn management |
| **Resources** | Static reference data the user/client loads | Tech tree, unit stats, game rules, strategy guides |
| **Prompts** | Reusable prompt templates | `analyze_situation`, `plan_turn`, `evaluate_war` |

Most game MCP servers only use tools. The Minecraft server `mcpmc` is the one exception that properly separates tools (mutable actions) from resources (read-only state). We should follow that pattern.

### 6. Error Handling

MCP has `isError` on tool results. Best practice:
- Return actionable recovery info, not just "failed"
- Include what the agent *can* do: "Unit cannot move to (5,12): tile occupied. Adjacent options: (4,12), (5,11), (6,12)"
- Use tool annotations: `readOnlyHint` for queries, `destructiveHint` for `end_turn`
- Pre-validate when possible (check `CanStartOperation` before executing)

### 7. Turn Flow

Two models observed:

| Model | How | Pros | Cons |
|-------|-----|------|------|
| **Agent-driven** | Agent calls tools in a loop, calls `end_turn` when ready | Simple, agent has full control | Agent might loop forever |
| **Event-driven** | Game notifies MCP on turn start, MCP prompts agent | Natural flow, game-paced | Requires callback mechanism |

For MCP, agent-driven is simpler. The agent calls `get_game_overview()` to start, makes decisions, calls `end_turn()` when done.

---

## Proposed Tool Design

Based on all research, here's the recommended tool set:

### State Query Tools (read-only)

| Tool | Returns | Detail |
|------|---------|--------|
| `get_game_overview` | Turn, score, yields, active threats, pending decisions, notifications | ~500 tokens, always call first |
| `get_units` | All units with position, type, moves, health | Filterable by `status` (idle/fortified/moving) |
| `get_cities` | All cities with yields, population, production, growth | Includes what each city can build |
| `get_map_area` | Tiles in a radius around a point | `center_x, center_y, radius` params |
| `get_diplomacy` | All known civs, relationships, active deals | |
| `get_tech_civics` | Tech/civic trees with research status | Available choices highlighted |

### Action Tools (mutating)

| Tool | Does | Params |
|------|------|--------|
| `execute_unit_action` | Move, attack, fortify, settle, build | `unit_id, action, target_x, target_y` |
| `set_city_production` | Set what a city builds | `city_id, item` |
| `set_research` | Choose tech/civic to research | `tech_or_civic_name` |
| `end_turn` | End the current turn | None |

### Utility Tools

| Tool | Does |
|------|------|
| `dismiss_popup` | Clear any blocking UI popup |
| `execute_lua` | Escape hatch: run arbitrary Lua (advanced) |

**Total: 12 tools.** Under the recommended ceiling. Each has clear purpose and minimal overlap.

### Resources (static reference)

| URI | Content |
|-----|---------|
| `game://rules/units` | All unit types, stats, abilities |
| `game://rules/buildings` | All buildings, costs, effects |
| `game://rules/techs` | Full tech tree |
| `game://rules/civics` | Full civic tree |
| `game://rules/terrains` | Terrain types and yields |
| `game://guides/strategy` | Basic Civ 6 strategy guide |

### Prompts

| Name | Purpose |
|------|---------|
| `analyze_situation` | Structured analysis of current game state |
| `plan_turn` | Generate full turn plan (moves + production + research) |
| `evaluate_threat` | Assess military/diplomatic threat |

---

## Key Anti-Patterns to Avoid

1. **Dumping raw JSON game state** — always summarize server-side
2. **One tool per game action** — leads to 30+ tools, context bloat
3. **LLM micromanaging unit movement** — it's bad at spatial reasoning; keep it strategic
4. **No error recovery info** — always tell the agent what it CAN do after a failure
5. **Synchronous full-state reload every tool call** — cache state, send deltas
6. **Ignoring popup/modal handling** — the game has blocking UI that needs programmatic dismissal

---

## Sources

### Game MCP Servers
- [danilop/chess-support-mcp](https://github.com/danilop/chess-support-mcp) — best state representation design
- [gerred/mcpmc](https://github.com/gerred/mcpmc) — best tools/resources separation
- [jimmcq/Lemonade-Stand-MCP-Server](https://github.com/jimmcq/Lemonade-Stand-MCP-Server) — clean turn-based design
- [thirionlogan/Aurora-4X-MCP](https://github.com/thirionlogan/Aurora-4X-MCP) — strategy game with DB queries
- [jessiqa1118/factorio-mcp](https://github.com/jessiqa1118/factorio-mcp) — RCON command passthrough

### Academic Strategy Game Agents
- [CivRealm](https://github.com/bigai-ai/civrealm) — 5x5 tile windows, hierarchical Mastaba agent
- [CivAgent](https://github.com/fuxiAIlab/CivAgent) — diplomatic skill space, 5-turn decision cycle, RAG memory
- [Vox Deorum](https://github.com/CIVITAS-John/vox-deorum) — LLM strategist + algorithmic tactician for Civ V
- [TextStarCraft II](https://github.com/histmeisah/Large-Language-Models-play-StarCraftII) — Chain of Summarization

### MCP Best Practices
- [Anthropic: Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) — 134K→2K token reduction
- [Phil Schmid: MCP is Not the Problem](https://www.philschmid.de/mcp-best-practices) — outcome-oriented tools
- [Klavis AI: Less is More](https://www.klavis.ai/blog/less-is-more-mcp-design-patterns-for-ai-agents) — progressive disclosure
- [MCP Specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) — tool annotations, isError
