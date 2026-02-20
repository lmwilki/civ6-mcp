# CivBench: Civilization VI as a Benchmark for Agentic Strategic Reasoning

## Abstract

As frontier AI benchmarks approach saturation — MMLU-Pro topped at 90.1%, GPQA at 93.8%, both in late 2025 [[1]](#ref-mmlu-saturation) — the field needs evaluation environments that test capabilities current benchmarks cannot measure: sustained multi-domain strategic reasoning, high-volume tool use, diplomatic negotiation, and long-horizon planning under uncertainty. We propose that Civilization VI, interfaced through the Model Context Protocol (MCP), represents a compelling next-generation benchmark for agentic AI. Unlike existing game-based benchmarks (CivRealm [[2]](#ref-civrealm), BALROG [[3]](#ref-balrog)) or business simulations (Vending-Bench [[4]](#ref-vendbench)), CivBench would evaluate agents across simultaneous strategic, economic, diplomatic, military, espionage, and spatial reasoning domains over thousands of tool invocations — using the same tool-calling interface that production AI agents use for real work.

## 1. The Benchmark Saturation Problem

The AI evaluation landscape faces a compounding crisis. Traditional knowledge benchmarks are effectively solved: MMLU saturated at ~90% by 2024, its successor MMLU-Pro was topped by Gemini 3 Pro at 90.1% in November 2025, and even GPQA Diamond — designed to be PhD-level — hit 93.8% the same month [[1]](#ref-mmlu-saturation). Humanity's Last Exam (HLE) was introduced as a response, but the pattern is clear: static question-answering benchmarks have a shelf life measured in months, and contamination concerns plague every popular benchmark [[5]](#ref-hle).

The community's response has been to develop agentic benchmarks — environments where models must act, not just answer. Vending-Bench tests long-horizon business management over 20M+ tokens [[4]](#ref-vendbench). BALROG tests game-playing across NetHack and others [[3]](#ref-balrog). MCPAgentBench evaluates MCP tool selection across 841 tasks [[6]](#ref-mcpagentbench). But each measures a narrow slice:

| Benchmark | What it tests | What it misses |
|-----------|--------------|----------------|
| Vending-Bench 2 [[4]](#ref-vendbench) | Long-term coherence, negotiation | Spatial reasoning, adversarial opponents, multi-domain |
| BALROG [[3]](#ref-balrog) | Game mechanics, long-horizon play | Diplomacy, tool use, strategic planning |
| MCPAgentBench [[6]](#ref-mcpagentbench) | Tool selection accuracy | Long-horizon planning, adversarial pressure |
| CivRealm [[2]](#ref-civrealm) | Civ gameplay (FreeCiv) | Rich diplomacy, MCP interface, full game complexity |
| Diplomacy Arena [[7]](#ref-diplomacy-arena) | Negotiation, alliances | No economic/military/spatial dimensions |

No existing benchmark simultaneously tests an agent's ability to negotiate a trade deal, position military units on a hex grid, optimise a tech tree, manage city production queues, run espionage operations, and adapt to an unexpected barbarian invasion — all through the same tool-calling interface, across hundreds of turns.

## 2. Why Civilization VI

Civilization VI is a 4X strategy game (explore, expand, exploit, exterminate) in which players build civilizations from the Ancient Era through the Information Age. A single game spans 300-500 turns, each requiring decisions across interlocking systems:

- **Economic**: Gold income, trade routes, city yields, resource management, luxury/strategic stockpiles
- **Scientific**: Technology tree with 67 technologies across 8 eras, eureka boost mechanics
- **Cultural**: Civic tree, government selection, policy card optimisation, Great Works
- **Military**: Unit production, hex grid positioning, combat strength calculations, promotions, upgrades
- **Diplomatic**: AI relationships, grievances, delegations, embassies, trade deals, World Congress voting, alliances
- **Religious**: Pantheon selection, faith generation, belief systems, religious units, theological combat
- **Espionage**: Spies (unlocked Renaissance Era), offensive missions (steal tech, siphon gold, disrupt production, sabotage Spaceports), counterintelligence, gaining sources, spy promotions — an entire hidden-information subsystem that becomes critical in the mid-to-late game
- **Spatial**: Hex grid with terrain, features, rivers, resources, fog of war, district placement, city spacing
- **Temporal**: Multi-turn production queues, research timelines, growth projections, era progression

The action space expands continuously throughout a game. CivRealm measured this in FreeCiv at 10^4 early-game to 10^166 late-game [[2]](#ref-civrealm). Civ 6 is richer still, with districts, Great People, governors, loyalty, amenities, espionage, and World Congress mechanics that FreeCiv lacks.

### 2.1 The MCP Interface

Our existing implementation (civ6-mcp) exposes the full game through 30+ MCP tools — the same protocol used by production AI agents for database queries, API calls, and system operations. This is not a simplified gym API or a custom action space. An agent playing Civ 6 through MCP uses the same `tool_name(param=value)` pattern it would use to query a database or file a support ticket.

This makes CivBench uniquely relevant to evaluating production agent capabilities. Tool-use fluency in CivBench directly translates to tool-use fluency in real work.

A typical turn involves 5-15 tool calls:

```
get_game_overview()           → orient: yields, research, score
get_units()                   → unit positions, HP, available actions, threats
get_map_area(x=10, y=20, r=3) → terrain, threats, resources
execute_unit_action(id=65536, action="move", target_x=11, target_y=19)
execute_unit_action(id=131073, action="attack", target_x=9, target_y=21)
get_cities()                  → production queues, growth, defences
set_city_production(city_id=0, item_type="UNIT", item_name="UNIT_ARCHER")
set_research(tech="TECH_ARCHERY")
end_turn()                    → blocker detection, turn events
```

A full game of 300 turns at ~10 calls per turn produces **3,000+ tool invocations** — orders of magnitude beyond any existing tool-use benchmark.

### 2.2 Continuous Performance Signals

Our game state extraction infrastructure provides rich, structured data at every turn. Rather than binary win/lose, we can track continuous performance metrics:

- **Score trajectory**: Game score at every turn, decomposed into era score, military score, civic score, etc.
- **Economic efficiency**: Gold per turn, science per turn, culture per turn — tracked over time
- **City development**: Population growth curves, district completion rates, production efficiency
- **Military effectiveness**: Units lost vs. enemies killed, territory defended, barbarian response time
- **Diplomatic standing**: Relationship modifiers, grievances, suzerainties, World Congress influence
- **Espionage effectiveness**: Spy mission success rate, intelligence gathered, counterespionage catches
- **Tech pace**: Turns per technology, eureka/inspiration bonus capture rate
- **Expansion timing**: Turns to 2nd, 3rd, 4th city — a critical strategic indicator

These signals allow fine-grained capability assessment far beyond "did the agent win?"

## 3. The Role of Prior Knowledge and Search

### 3.1 Training Data as Strategic Advantage

A distinctive property of LLM-based agents — unlike RL agents trained tabula rasa — is that they arrive with substantial prior knowledge from internet training data. The Civilization community has produced decades of strategy content: tier lists ranking civilizations (e.g., Hojo Tokimune and Abraham Lincoln consistently rated S-tier [[8]](#ref-civ-tier)), optimal opening build orders (Scout → Slinger → Settler is a common consensus), district placement adjacency guides, and victory-specific playbooks.

This creates a fascinating evaluation dimension: **does an agent that "knows" the meta actually play better?**

The answer is not straightforward. BALROG's key finding was that LLMs can explain optimal game strategies but fail to execute them [[3]](#ref-balrog) — the knowing-doing gap. CivRealm found that LLM agents with extensive game knowledge still struggled with the full game [[2]](#ref-civrealm). Our own playtest observations confirm this: the agent knows it should expand quickly (standard Civ wisdom) but still settled its third city 50 turns late due to barbarian pressure and tactical misjudgments.

### 3.2 Search Augmentation

An even more interesting variant: agents equipped with web search or retrieval tools during play. An agent that can look up "best counter to Man-at-Arms with only archers" mid-game or consult a district adjacency calculator represents a different capability profile than one relying purely on parametric knowledge.

This mirrors real-world agentic workflows where tool-augmented reasoning (search, documentation lookup, calculator) supplements the model's base knowledge. CivBench could evaluate both modes:

- **Closed-book**: Agent plays with parametric knowledge only
- **Open-book**: Agent has access to search/retrieval tools alongside game tools

The gap between these modes would itself be a meaningful signal — measuring how effectively an agent translates retrieved knowledge into situated action.

### 3.3 Contamination and Novel Scenarios

Known strategies in training data cut both ways. On one hand, an agent that recognises "Poland should prioritise faith generation for Jadwiga's reliquary bonus" is demonstrating useful transfer learning. On the other hand, if benchmark scenarios use well-known map seeds that have published strategy guides, performance may reflect memorisation rather than reasoning.

Mitigations are discussed in Section 5.3, but the key insight is that Civ 6's combinatorial state space makes rote memorisation insufficient. Knowing the optimal tech path is useless if barbarians destroy your second city and you need to improvise. The benchmark's value lies precisely in testing whether knowledge translates to adaptive play.

## 4. Evaluation Framework

### 4.1 Single-Agent Scenarios (vs. Classical AI)

The most straightforward benchmark format: an LLM agent plays Civ 6 against the game's built-in AI opponents at various difficulty levels. Civ 6 has 8 difficulty tiers (Settler through Deity), where higher difficulties give AI opponents increasing yield bonuses, combat bonuses, and free units/buildings.

**Proposed scoring**:
- Score at fixed turn checkpoints (T50, T100, T150, T200, T250, T300)
- Milestone completion: turns to first Campus, first Commercial Hub, first Great Person, first settler
- Victory type achieved (or none) and turn of victory
- Composite rating aggregating economic, military, diplomatic, espionage, and cultural sub-scores

**Reproducibility**: Civ 6 uses dual seeds (map seed + game seed) that deterministically generate identical maps, resources, start positions, and AI opponents given identical game version, DLC configuration, and settings. A benchmark suite would define a fixed set of seed configurations:

- **Scenario A**: Pangaea map, standard size, Prince difficulty — baseline strategic competence
- **Scenario B**: Continents map, King difficulty — tests naval awareness and cross-ocean diplomacy
- **Scenario C**: Small map, Emperor difficulty — tests under pressure with aggressive AI bonuses
- **Scenario D**: TSL Earth, Deity difficulty — maximum challenge, tests adaptation to severe handicap

### 4.2 ELO Rating Against Classical AI

A natural extension: compute ELO ratings for LLM agents based on win/loss/score outcomes against AI at each difficulty level. The classical AI's effective ELO is implicitly defined by difficulty tier (Settler AI ~600, Deity AI ~2000+). An LLM agent's rating emerges from its performance distribution across many games.

This would produce the first **strategic ELO leaderboard** for language models — not testing who writes better prose, but who plays better civilization.

The methodology would mirror Chatbot Arena's approach [[9]](#ref-chatbot-arena): pairwise comparisons, Bradley-Terry model fitting, bootstrap confidence intervals. But instead of human preference votes, the signal is game outcomes — fully automated, no human judges needed.

Importantly, ELO would be computed separately per scenario type, per difficulty level, and across an aggregate — revealing whether a model excels at economic play but fails at military pressure, or handles Prince difficulty competently but collapses at Emperor.

### 4.3 Multi-Agent LLM Play

The most ambitious and scientifically interesting configuration: **multiple LLM agents playing against each other**. Civ 6 supports multiplayer via hotseat mode (sequential turns on one machine) or network play. While FireTuner has limitations in standard multiplayer, a custom mod or instrumented hotseat configuration could enable:

- **Claude vs. GPT vs. Gemini**: Different model families competing on identical maps
- **Same model, different prompts**: Testing whether system prompt engineering affects strategic play
- **Self-play**: The same model playing against copies of itself — do strategies converge or diverge?

This is where the benchmark becomes genuinely novel in the research landscape. No existing benchmark pits frontier LLMs against each other in a rich strategic environment with this many interacting systems.

#### Synchronous vs. Asynchronous Play

The choice between synchronous and asynchronous multiplayer has profound implications for both strategy and evaluation:

**Synchronous (simultaneous turns)**: All agents submit moves concurrently, then all resolve at once. This creates a different strategic texture — agents must anticipate opponents' simultaneous decisions without observing them first. Military positioning becomes a prediction game. Diplomatic messaging (if enabled) happens in real-time bursts between turn submissions. This mode rewards game-theoretic reasoning and models' ability to reason about others' likely actions.

**Asynchronous (sequential turns)**: Agents take turns one at a time, each observing the full result of all previous players' moves before acting. This is closer to the single-player experience and allows more deliberate play. It also fundamentally changes diplomacy — an agent that moves later in turn order can react to betrayals within the same turn, while early movers must commit without that information.

**Hybrid (async negotiation + sync resolution)**: Perhaps the most interesting: give agents an asynchronous messaging phase (minutes, not hours) to negotiate, then resolve all moves simultaneously. This mirrors how human Diplomacy works and how CICERO was evaluated [[10]](#ref-cicero).

The async-vs-sync choice also affects the economics of evaluation. Synchronous play is faster (all agents think in parallel) but requires more concurrent compute. Asynchronous is simpler to implement but takes N times longer for N players. The messaging phase in particular needs careful time-boxing — see Section 4.4.

### 4.4 The CICERO Extension: Diplomatic Messaging

Meta's CICERO achieved human-level Diplomacy play by combining strategic reasoning with natural language negotiation, ranking in the top 10% of human players and scoring 2x the average across 40 games on webDiplomacy.net [[10]](#ref-cicero). Its architecture paired a controllable dialogue model (generating messages grounded in strategic plans) with a planning module (predicting opponents' moves from conversation history). The key insight: an agent that can communicate intentions, build trust, form alliances, and coordinate plans through natural language is fundamentally more capable than one that merely optimises silently.

Civ 6's diplomacy system — relationships, grievances, trade deals, embassies, World Congress — already provides a structured framework for inter-civilization interaction. The open question: **what happens when LLM agents can also message each other in natural language?**

In a multi-agent CivBench configuration with an open messaging channel, agents would need to:

- **Negotiate trade deals**: "I'll give you 5 gold per turn for your iron — I need it for swordsmen to defend our border with the Mapuche"
- **Form alliances**: "Let's declare joint war on Spain — they're running away with the score"
- **Deceive**: "I'm building Campus districts" (while actually massing knights for an invasion)
- **Detect deception**: Reconciling what an opponent says with observable troop movements and game state
- **Coordinate World Congress votes**: "I'll vote for your proposal on Resolution A if you support mine on Resolution B"
- **Manage espionage diplomatically**: "I caught your spy in my Commercial Hub — withdraw your intelligence operation or face consequences"

This would create a **strategic + persuasive** evaluation — a single mind applied to the dual purpose of optimising play and influencing opponents through language. A Civ-scale CICERO benchmark, but with a far richer game substrate than the board game Diplomacy.

#### Guardrails Against Endless Negotiation

A critical design challenge: LLM agents engaged in free-form messaging could enter infinite negotiation loops, endlessly refining proposals without committing to action. CICERO solved this for Diplomacy by grounding dialogue in concrete action plans — messages reflect calculated intents, not open-ended conversation.

CivBench would need similar guardrails:

- **Turn timer**: Each agent gets a fixed messaging budget per turn (e.g., 3 messages per opponent, or a total token budget for diplomacy per turn). This forces agents to be concise and decisive.
- **Action commitment**: After the messaging phase, agents must submit moves. Messages are cheap talk unless backed by in-game actions (moving troops, sending delegations, voting as promised).
- **Structured channels alongside free-text**: Offer both a structured deal-proposal tool (propose specific trade terms, alliance requests) and a free-text channel. This gives agents efficient deal-making without precluding persuasion.
- **Diminishing returns**: Score messaging efficiency — an agent that negotiates brilliantly in 2 messages is more impressive than one that takes 20 to reach the same deal.
- **Defection tracking**: Log promises made in messages and compare against actual in-game actions. The rate of promise-keeping vs. betrayal becomes a measurable diplomatic trait.

Without these constraints, the messaging dimension risks becoming a token-burning contest rather than a test of strategic communication.

### 4.5 Emergent Metas and Novel Strategies

The question of whether **new metas would emerge** from LLM-vs-LLM play is one of the most scientifically interesting aspects of this proposal.

**Precedent from RL self-play**: AlphaGo Zero, trained purely through self-play with no human data, discovered novel Go strategies that overturned centuries of human theory — most famously "Move 37" in its match against Lee Sedol, which professional commentators initially dismissed as a mistake before recognising it as brilliant [[11]](#ref-alphago-zero). AlphaStar, DeepMind's StarCraft II agent, reached Grandmaster level (above 99.8% of human players) using multi-agent reinforcement learning with a league of continually adapting strategies and counter-strategies [[12]](#ref-alphastar). It developed build orders and micro-management patterns that surprised professional players, including unusual unit compositions that exploited game mechanics in ways humans had not considered.

**LLM-specific dynamics**: Unlike RL agents, LLMs start with human strategic knowledge but may combine it in novel ways. Vox Deorum's experiments with Civ V found that LLMs exhibited "play styles that diverge substantially from algorithmic AI and from each other" across 2,327 games [[13]](#ref-vox-deorum). In a multi-agent LLM environment with messaging, emergent behaviour could include:

- **Coordinated economic zones**: Agents agreeing to specialise (you build science, I build military) in ways human players rarely sustain
- **Information trading**: Sharing map knowledge as a diplomatic currency — "I'll tell you where the iron is if you tell me Spain's troop positions"
- **Credible commitment devices**: Using game mechanics (e.g., moving troops away from borders, sending delegations) to make promises enforceable
- **Deception detection arms races**: Agents learning to verify claims against observable game state, satellite intelligence from spies, and historical behaviour patterns
- **Meta-game awareness**: Agents reasoning about other models' known tendencies (e.g., "Claude tends to be cooperative, GPT tends to be aggressive") — a form of opponent modelling unique to LLM-vs-LLM play
- **Espionage-diplomacy interplay**: Using spy intelligence to inform negotiation positions while maintaining plausible deniability about what you know

The key difference from AlphaGo/AlphaStar: those systems discovered strategies through millions of self-play games optimising a reward signal. LLM agents would develop strategies through in-context reasoning over individual games — more akin to how a human expert adapts than how an RL agent trains. Whether this produces genuinely novel strategies or merely recombines known ones is an empirical question worth investigating.

## 5. Comparison to Existing Work

### 5.1 vs. CivRealm (FreeCiv)

CivRealm is the closest existing work [[2]](#ref-civrealm). Key differences:

| | CivRealm | CivBench |
|---|---------|---------|
| Game | FreeCiv (open-source clone) | Civ 6 (full commercial game) |
| Interface | Gymnasium tensor API + LangChain | MCP tool protocol |
| Mechanics | Basic 4X | Districts, governors, loyalty, Great People, World Congress, religion, espionage |
| Diplomacy | Minimal | Full (deals, embassies, grievances, congress, alliances) |
| Espionage | None | Full (spies, missions, counterintelligence) |
| Agent paradigm | RL tensor + LLM text | MCP tool-calling (production-realistic) |
| Evaluation | 16 dimensions, civ score | Continuous multi-signal tracking |
| Key finding | Both RL and LLM agents struggle in full game | TBD — early playtest shows competent mid-game play |

CivRealm's most significant finding — that agents struggle with the full game — was demonstrated with FreeCiv's simpler mechanics. Civ 6 is harder. But the MCP interface may be more natural for language models than gym-style APIs, potentially enabling better performance through more structured tool interactions.

CivAgent [[14]](#ref-civagent), built on Unciv (another open-source Civ clone), similarly found that LLM agents could engage in strategic gameplay and diplomatic negotiation, positioning strategy games as ideal environments for LLM evaluation due to their "large decision and state spaces."

### 5.2 vs. Vending-Bench 2

Vending-Bench 2 is the current gold standard for long-horizon agent coherence [[4]](#ref-vendbench). CivBench would complement it:

- **VB2 tests coherence in a simple domain** (inventory, pricing, suppliers) over 365 time steps with ~5 tools
- **CivBench tests coherence in a complex domain** (9+ systems) over 300+ turns with 30+ tools and 10x more decisions per step
- **VB2's failure modes** (meltdown loops, forgotten orders) would likely appear in CivBench too, but surrounded by richer diagnostic signals — did the agent also lose military awareness? Did diplomatic relationships decay? Did espionage operations continue?
- **VB2 has adversarial suppliers**; CivBench has adversarial civilisations with distinct AI personalities, military capabilities, and hidden agendas

### 5.3 vs. CICERO (Diplomacy)

CICERO demonstrated that combining strategic reasoning with natural language negotiation produces superhuman play in Diplomacy [[10]](#ref-cicero). CivBench with messaging would test the same capability in a vastly richer domain:

| | Diplomacy | Civilization VI |
|---|-----------|----------------|
| Players | 7 | 6-8 |
| Map complexity | ~34 provinces, fixed | ~4,000 hexes, procedurally generated |
| Unit types | ~1 (armies/fleets) | ~50 (melee, ranged, siege, naval, air, civilian, religious, spy) |
| Economy | None | Full (gold, production, food, trade routes, strategic resources) |
| Technology | None | 67 technologies across 8 eras |
| Game length | ~15 turns | 300+ turns |
| Negotiation | Core mechanic | Supplementary (structured deals + optional free-text) |
| Hidden information | Simultaneous moves only | Fog of war, espionage, unmet civilizations |

The strategic reasoning component is deeper (more systems, longer horizon), while the language component is comparable (persuasion, deception, alliance formation). CICERO's architecture — pairing a dialogue model with a strategic planner — would need to scale dramatically to handle Civ 6's complexity.

## 6. Practical Considerations

### 6.1 Licensing

Civilization VI is a commercially licensed game published by 2K Games / Firaxis. Benchmark participants would need to own a copy of the game (~$15-60 depending on edition and DLC). This is a higher barrier than open-source environments like FreeCiv or NetHack, but is straightforward: purchase the game, enable the debug tools (FireTuner), and connect via TCP.

This is not dissimilar from benchmarks that require paid API access (Vending-Bench 2 costs real API credits to run, SWE-bench requires Docker infrastructure). The game license is a one-time cost per evaluation machine.

The MCP server itself (civ6-mcp) is MIT-licensed and open source. It connects to the game but does not distribute any game assets or code.

### 6.2 Cost of Evaluation

This is a more expensive benchmark than traditional evals. The primary cost driver is the growing conversation context — each turn, the agent must process its full conversation history alongside new tool results.

**Per-turn token economics** (estimated from live playtest data):

| Component | Tokens | Notes |
|-----------|--------|-------|
| System prompt | ~3,000 | Fixed: game rules, tool descriptions |
| Conversation context | ~10K-60K | Grows over game, compressed periodically |
| New tool results per turn | ~6,000-10,000 | 10 calls × 600-1,000 tokens each |
| Agent reasoning + tool calls | ~1,000-2,000 | Output per turn |

The key cost driver is the **conversation context**, which grows with game length. With context compression (standard in production agent frameworks), we estimate an average of ~35K input tokens per turn across a full game.

**Per-game cost estimates**:

| Model | Input rate | Output rate | Est. input (300 turns) | Est. output | Total per game |
|-------|-----------|-------------|----------------------|-------------|---------------|
| Gemini 3 Pro | $2/M | $12/M | ~13M tokens | ~450K tokens | **~$31** |
| GPT-4o | $2.50/M | $10/M | ~13M | ~450K | **~$37** |
| Claude Sonnet 4.5 | $3/M | $15/M | ~13M | ~450K | **~$46** |
| Claude Opus 4.5 | $5/M | $25/M | ~13M | ~450K | **~$76** |

**Per-model evaluation suite costs**:

| Suite size | Purpose | Cost range (across models) |
|-----------|---------|---------------------------|
| 5 games | Quick capability check | $155-380 |
| 20 games | Comparable to Diplomacy Arena [[7]](#ref-diplomacy-arena) | $620-1,520 |
| 50 games | Stable ELO estimation | $1,550-3,800 |

**Additional costs**:
- Game license: ~$15-60 one-time per machine
- Wall-clock time: 2-4 hours per game (game engine + API latency)
- Compute: One machine running Civ 6 per concurrent evaluation

This is expensive relative to MMLU ($0.10) but in the range of SWE-bench ($50-200 per run) and well below the cost of human evaluation studies. In an era where the top 10 models score within 2% of each other on MMLU-Pro, a benchmark that can differentiate strategic reasoning capability at $30-80 per game is reasonable.

For multi-agent play with messaging, costs multiply by the number of LLM-controlled players (typically 2-4 in a 6-player game, with the remainder as classical AI).

### 6.3 Reproducibility and Contamination

**Seed-based reproducibility**: Civ 6's dual seed system (map seed + game seed) produces identical maps given identical game version and DLC configuration. A benchmark specification would pin exact game version, DLC set, and seed configurations.

**Save-based reproducibility**: For even stronger guarantees, benchmark scenarios can be distributed as save files — pre-configured game states at specific turns, testing agent performance from identical starting positions. This also enables mid-game evaluation (e.g., "here's a turn-150 position with a military crisis — how do you respond?").

**Contamination risk**: If benchmark scenarios and winning strategies appear in future training data (as has happened with MMLU, HLE, and others [[5]](#ref-hle)), models could learn to pattern-match rather than reason. Mitigations:

- **Rotating seed pools**: New map seeds each evaluation cycle
- **Save-state scenarios**: Mid-game positions that can't be memorised as opening strategies
- **Held-out test set**: Some scenarios never published, used only for official evaluation
- **Process monitoring**: The tool-call trace reveals whether an agent is reasoning or regurgitating — a key advantage over text-only benchmarks. An agent that always opens Scout → Slinger → Settler regardless of start position is likely reciting, not reasoning.
- **Scenario variation**: Same seed but different civilizations, different opponents, different difficulty — testing whether the agent adapts its strategy to its unique advantages

The richness of the game state space is itself a defence against contamination. There are effectively infinite meaningfully different Civ 6 positions — memorising a few hundred openings won't help when a barbarian Man-at-Arms appears at turn 136 with combat strength 45 against your warriors at 20.

### 6.4 Technical Feasibility

The civ6-mcp project already demonstrates the core infrastructure:
- **30+ MCP tools** covering all major game systems
- **Structured data extraction** from live game state (dataclass serialisation)
- **Continuous performance logging** (JSONL game log with turn tracking)
- **Real-time dashboard** (FastAPI + Next.js web viewer with hex map)
- **Full playtest validation** — an LLM agent has played 150+ turns competently, demonstrating the interface is sufficient for genuine strategic play

What remains to be built for a formal benchmark:
- Standardised scenario definitions (seeds, settings, difficulty)
- Automated game reset and scenario loading
- Score extraction and normalisation pipeline
- Multi-agent orchestration (for LLM-vs-LLM scenarios)
- ELO computation infrastructure
- Messaging channel implementation (for CICERO-style evaluation)
- Espionage tool suite (spy missions, counterintelligence)

## 7. Proposed Evaluation Dimensions

A CivBench scorecard would report across multiple axes, enabling nuanced comparison:

| Dimension | Signal | Measurement |
|-----------|--------|-------------|
| **Strategic Planning** | Tech/civic path quality, city placement | Score trajectory, milestone timing |
| **Economic Management** | Yield optimisation, trade routes | Gold/science/culture per turn curves |
| **Military Competence** | Threat response, unit positioning | Units lost ratio, territory defended |
| **Diplomatic Skill** | Relationship management, deal-making | Friendship count, grievance avoidance, WC influence |
| **Espionage** | Spy deployment, mission success, counterintelligence | Intel gathered, missions completed, spies lost |
| **Spatial Reasoning** | Map awareness, city placement, scouting | Exploration %, settle location quality |
| **Tool Use Fluency** | Correct tool selection, parameter accuracy | Error rate, calls per turn, tool diversity |
| **Long-Horizon Coherence** | Maintaining strategic direction | Score variance, strategy drift metrics |
| **Adaptation** | Responding to unexpected events | Recovery time after setbacks |
| **Multi-System Balance** | Not neglecting any domain | Minimum sub-score across dimensions |
| **Communication** (multi-agent) | Negotiation effectiveness, deception | Promise-keeping rate, deal quality, message efficiency |

## 8. Open Questions

1. **What difficulty level best differentiates frontier models?** Prince (no bonuses) may be too easy; Deity (massive AI bonuses) may be too hard. The sweet spot is likely King or Emperor.

2. **How many games are needed for stable ELO?** Chess uses thousands of games; Diplomacy Arena uses 20 [[7]](#ref-diplomacy-arena). Given Civ 6's high variance (map generation, barbarian spawns), likely 30-50 games per model for a confidence interval under ±50 ELO.

3. **Can FireTuner support multi-agent play?** The single-connection limitation is a technical challenge for LLM-vs-LLM scenarios. Solutions include custom mods, hotseat automation, or a message-passing proxy that serialises multiple agents' commands through one connection.

4. **Would LLM agents develop emergent strategies?** Vox Deorum found divergent play styles in Civ V [[13]](#ref-vox-deorum). AlphaGo Zero and AlphaStar demonstrated that novel strategies can emerge from self-play in Go and StarCraft II respectively [[11]](#ref-alphago-zero) [[12]](#ref-alphastar). In a full multi-agent messaging environment, the potential for emergent metas — coordinated economics, deception detection, alliance formation — is the most scientifically interesting open question.

5. **Does the synchronous/asynchronous choice change which model wins?** A model that excels at game-theoretic prediction (simultaneous moves) may differ from one that excels at reactive adaptation (sequential turns). Both are valid strategic competencies.

6. **How does search augmentation affect the capability hierarchy?** If a weaker model with search access outperforms a stronger model without it, that tells us something important about the relative value of retrieval vs. reasoning in strategic domains.

7. **Is Civ 6 the right Civilization?** Civ 7 is now available and may offer improved modding/API support. FreeCiv is free but mechanically simpler. The benchmark framework should be game-version-agnostic where possible.

## 9. Conclusion

Civilization VI via MCP occupies a unique position in the benchmark landscape: it tests high-volume tool use (3,000+ calls per game) combined with long-horizon multi-domain strategy (300+ turns across 9 interconnected systems including espionage) against adversarial opponents — all through the same tool-calling protocol used by production AI agents.

As traditional benchmarks saturate and the field searches for evaluations that meaningfully differentiate frontier models, complex strategy games represent a natural frontier. The cost of evaluation is higher than a knowledge quiz — but the signal is commensurately richer. A model that can manage an economy, command an army, negotiate an alliance, run an espionage network, and adapt to a crisis across 300 turns of escalating complexity is demonstrating capabilities that no existing benchmark measures.

The most exciting possibility lies in the CICERO extension: multi-agent play with natural language messaging. When LLM civilizations can talk to each other — negotiate, threaten, deceive, and cooperate — we enter territory that combines the strategic depth of AlphaGo's self-play discoveries [[11]](#ref-alphago-zero), the multi-agent dynamics of AlphaStar's league training [[12]](#ref-alphastar), and the natural language persuasion of CICERO's Diplomacy play [[10]](#ref-cicero). The question is no longer whether an AI can answer questions about strategy — it's whether an AI can practice it. And when AI civilizations compete, what emerges?

The infrastructure exists. The interface is built. The first 150-turn playtest shows competent mid-game play with identifiable weaknesses. The next step is formalising scenarios, running multi-model evaluations, and finding out.

---

## References

<a id="ref-mmlu-saturation"></a>[1] "MMLU Benchmark in 2025: Strengths, Limits, and the Future of AI Evaluation." GraphLogic, 2025. https://graphlogic.ai/blog/utilities/mmlu-better-benchmarking-for-llm-language-understanding/ ; "LLM Benchmarks 2026 — Complete Evaluation Suite." https://llm-stats.com/benchmarks

<a id="ref-civrealm"></a>[2] Qi, S. et al. "CivRealm: A Learning and Reasoning Odyssey in Civilization for Decision-Making Agents." ICLR 2024. https://arxiv.org/abs/2401.10568

<a id="ref-balrog"></a>[3] Paglieri, A. et al. "BALROG: Benchmarking Agentic LLM and VLM Reasoning On Games." ICLR 2025. https://arxiv.org/abs/2411.13543

<a id="ref-vendbench"></a>[4] Andon Labs. "Vending-Bench: A Benchmark for Long-Term Coherence of Autonomous Agents." arXiv:2502.15840, Feb 2025. https://arxiv.org/abs/2502.15840 ; "Vending-Bench 2." https://andonlabs.com/evals/vending-bench-2

<a id="ref-hle"></a>[5] "The Great Reasoning Wall: Why Humanity's Last Exam Has Become the Ultimate Gatekeeper for AGI." TokenRing, Feb 2026. https://markets.financialcontent.com/bpas/article/tokenring-2026-2-6-the-great-reasoning-wall-why-humanitys-last-exam-has-become-the-ultimate-gatekeeper-for-agi

<a id="ref-mcpagentbench"></a>[6] MCPAgentBench. "A Real-world Task Benchmark for Evaluating LLM Agent MCP Tool Use." arXiv:2512.24565, Dec 2025. https://arxiv.org/abs/2512.24565

<a id="ref-diplomacy-arena"></a>[7] Good Start Labs. "Diplomacy Arena: AI Strategy Benchmarks." NeurIPS Multi-Agent Workshop 2025. https://goodstartlabs.com/leaderboards/diplomacy

<a id="ref-civ-tier"></a>[8] "Civ 6 Tier List: Best Leaders (February 2026)." MetaTierList. https://metatierlist.com/civ-6-tier-list/

<a id="ref-chatbot-arena"></a>[9] Zheng, L. et al. "Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference." arXiv:2403.04132, 2024. https://lmarena.ai/

<a id="ref-cicero"></a>[10] Meta Fundamental AI Research Diplomacy Team (FAIR). "Human-level play in the game of Diplomacy by combining language models with strategic reasoning." Science, Vol 378, Issue 6624, pp. 1067-1074, Nov 2022. https://www.science.org/doi/10.1126/science.ade9097

<a id="ref-alphago-zero"></a>[11] Silver, D. et al. "Mastering the game of Go without human knowledge." Nature 550, 354-359, Oct 2017. https://www.nature.com/articles/nature24270

<a id="ref-alphastar"></a>[12] Vinyals, O. et al. "Grandmaster level in StarCraft II using multi-agent reinforcement learning." Nature 575, 350-354, Oct 2019. https://www.nature.com/articles/s41586-019-1724-z

<a id="ref-vox-deorum"></a>[13] "Vox Deorum: A Hybrid LLM Architecture for 4X / Grand Strategy Game AI — Lessons from Civilization V." arXiv:2512.18564, Dec 2025. https://arxiv.org/abs/2512.18564

<a id="ref-civagent"></a>[14] FuxiAILab. "CivAgent: LLM-based Human-like Agent for Unciv." https://github.com/fuxiAIlab/CivAgent

<a id="ref-mcp-bench"></a>[15] Accenture. "MCP-Bench: Benchmarking Tool-Using LLM Agents with Complex Real-World Tasks via MCP Servers." arXiv:2508.20453, 2025. https://arxiv.org/abs/2508.20453

<a id="ref-api-pricing"></a>[16] Anthropic. "Claude API Pricing." https://platform.claude.com/docs/en/about-claude/pricing ; Google. "Gemini Developer API Pricing." https://ai.google.dev/gemini-api/docs/pricing
