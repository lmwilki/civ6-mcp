# CivBench: A Multi-Domain Strategic Reasoning Benchmark for Tool-Using Language Model Agents

**Authors:** [Names], [Affiliations]

**Corresponding author:** [email]

**Keywords:** benchmark, language model agents, strategic reasoning, tool use, game AI, multi-agent systems, diplomacy

---

## Abstract

We present CivBench, a benchmark for evaluating language model agents in Sid Meier's Civilization VI through the Model Context Protocol --- the same tool-calling interface used by production AI systems. A single episode spans 300+ turns across seven concurrent strategic domains, producing thousands of tool invocations. Unlike the Alpha paradigm (AlphaGo, AlphaStar), CivBench evaluates general-purpose models with no game-specific training, measuring strategic reasoning as a transferable capability. Validation across five games (865+ turns, 70 MCP tools) reveals two primary capability bottlenecks. The *sensorium effect*: unlike human players who passively absorb game-state signals through vision, the agent only knows what it explicitly queries, causing unprompted information to go unmonitored until crisis forces attention. The *reflection-action gap*: the agent articulates correct strategic priorities but fails to execute them, writing the same self-corrections 3--5 times per game without acting on them. These findings generalise beyond Civilization to any agent operating through text queries in a visually-rich environment. No existing benchmark simultaneously tests high-volume tool use, long-horizon planning, and multi-domain strategic reasoning within a single integrated evaluation.

---

## 1. Introduction

Evaluation of frontier language models has entered a period of diminishing returns. MMLU-Pro, designed as a harder successor to MMLU, was topped at 90.1% by Gemini 3 Pro in November 2025; GPQA Diamond, intended to pose PhD-level difficulty, reached 93.8% in the same period (GraphLogic, 2025). Humanity's Last Exam was introduced as a response to this saturation, but static question-answering benchmarks have repeatedly demonstrated a shelf life measured in months, with contamination concerns compounding the problem (TokenRing, 2026).

The community has responded by developing *agentic* benchmarks in which models must act within dynamic environments rather than answer fixed questions. Vending-Bench 2 tests long-horizon coherence over 365 simulated days and 20 million tokens (Andon Labs, 2025). BALROG evaluates game-playing across multiple environments (Paglieri et al., 2025). MCPAgentBench measures tool selection accuracy across 841 tasks (MCPAgentBench, 2025). Each of these, however, measures a relatively narrow slice of agentic capability. No existing benchmark simultaneously evaluates an agent's ability to negotiate trade agreements, position military units on a spatial grid, optimise a technology tree, manage production queues across multiple cities, conduct espionage operations, and adapt to emergent threats---all through the same tool-calling interface, over hundreds of sequential decisions.

We propose CivBench, a benchmark framework in which language model agents play Civilization VI through the Model Context Protocol. The choice of substrate is motivated by several properties: (i) the game requires simultaneous reasoning across multiple interconnected strategic domains; (ii) the action space grows continuously from approximately $10^4$ possible actions in the early game to $10^{166}$ in the late game, as measured in the related FreeCiv environment (Qi et al., 2024); (iii) the MCP interface mirrors production agentic workflows, making benchmark performance directly relevant to real-world tool-use capability; and (iv) the game provides rich continuous performance signals beyond binary win/loss outcomes.

### Contributions

This paper makes the following contributions:

1. **Benchmark design and implementation.** We present civ6-mcp, an open-source tool suite comprising 70 MCP tools covering all major game systems, integrated with the UK AISI Inspect evaluation framework. Five agent games (865+ turns across different civilizations and game conditions) validate that the infrastructure supports sustained strategic play.

2. **Paradigm analysis.** We distinguish the CivBench evaluation paradigm from the Alpha paradigm of game AI research (Silver et al., 2016, 2017; Vinyals et al., 2019), arguing that measuring strategic reasoning in general-purpose models addresses a different and complementary question to training specialised game-playing systems.

3. **Multi-dimensional evaluation methodology.** We define evaluation dimensions spanning strategic planning, economic management, military competence, diplomatic skill, spatial reasoning, tool-use fluency, and long-horizon coherence, with continuous performance signals extracted from game state trajectories.

4. **Preliminary empirical results and behavioural analysis.** We report findings from five games across different civilizations and difficulty levels, identifying the *sensorium effect* (the information asymmetry between human visual perception and agent text queries) and the *reflection-action gap* (correct strategic analysis without follow-through) as primary capability bottlenecks, establishing baselines for future multi-model comparison.

The remainder of this paper is organised as follows. Section 2 surveys related work. Section 3 analyses the paradigm gap between specialised game AI and general-purpose agent evaluation. Section 4 describes the game environment and MCP interface. Section 5 presents the evaluation framework. Section 6 addresses prior knowledge and search augmentation. Section 7 covers practical considerations. Section 8 defines the evaluation dimensions. Section 9 presents preliminary results. Section 10 discusses the knowing-doing gap, structured reflection as a mitigation, scaling, and limitations. Section 11 concludes.

---

## 2. Related Work

### 2.1 Game-Based AI Evaluation

Games have served as evaluation environments for artificial intelligence since Samuel's checkers program (Samuel, 1959) and have produced several landmark results. Deep Blue's victory over Kasparov in chess (Campbell et al., 2002) and AlphaGo's defeat of Lee Sedol in Go (Silver et al., 2016) demonstrated superhuman performance in perfect-information two-player games. AlphaGo Zero subsequently showed that self-play alone, without human training data, could discover novel strategies that overturned centuries of human theory (Silver et al., 2017). AlphaStar extended these results to the imperfect-information, real-time domain of StarCraft II, reaching Grandmaster level---above 99.8% of active human players---through multi-agent reinforcement learning with a league of continually adapting strategies (Vinyals et al., 2019).

These achievements, however, involved purpose-built reinforcement learning systems operating in a fundamentally different paradigm from language model agents. Section 3 analyses this paradigm gap in detail. The question of whether *general-purpose* language models can exhibit strategic competence in complex games remains comparatively underexplored.

### 2.2 Civilization as an AI Environment

CivRealm (Qi et al., 2024) is the most directly related prior work. Built on FreeCiv, an open-source implementation of Civilization, CivRealm provides both a Gymnasium-compatible tensor API for reinforcement learning agents and a LangChain-based text interface for language model agents. The authors report that both agent paradigms struggle with full-game play, with language model agents in particular failing to manage the expanding action space. CivRealm's action space analysis---$10^4$ early-game to $10^{166}$ late-game---provides a quantitative measure of the domain's complexity, though FreeCiv lacks several systems present in Civilization VI, including districts, governors, loyalty, espionage, World Congress, and Great People mechanics.

CivAgent (FuxiAILab, 2024), built on Unciv (another open-source Civilization implementation), demonstrated that language model agents can engage in strategic gameplay and diplomatic negotiation, positioning strategy games as evaluation environments for LLMs due to their "large decision and state spaces."

Vox Deorum (2025) explored a hybrid architecture combining language models with auxiliary systems for Civilization V gameplay. Across 2,327 games, the authors found that LLM-based agents "exhibit play styles that diverge substantially from algorithmic AI and from each other," suggesting that language models bring qualitatively different strategic reasoning to 4X games compared to classical AI.

### 2.3 Agentic and Tool-Use Benchmarks

The shift from static to agentic evaluation has produced several benchmark families. Vending-Bench 2 (Andon Labs, 2025) tests autonomous business management over 365 simulated days, with agents managing inventory, pricing, and supplier negotiation across approximately 5 tools and 20 million tokens of context. BALROG (Paglieri et al., 2025) evaluates game-playing competence across NetHack, BabyAI, and other environments, finding a persistent gap between models' ability to *explain* optimal strategies and their ability to *execute* them. MCPAgentBench (2025) and MCP-Bench (Accenture, 2025) evaluate tool selection and complex task execution through MCP servers, measuring accuracy across 841 and comparable task counts respectively.

These benchmarks test important but largely orthogonal capabilities. CivBench is designed to test their *intersection*: high-volume tool use (as in MCPAgentBench), long-horizon coherence (as in Vending-Bench), game-playing competence (as in BALROG), and strategic depth (as in CivRealm), within a single integrated evaluation.

### 2.4 Reflection and Memory in LLM Agents

A growing body of work addresses the gap between what LLM agents *know* and what they *do* through structured reflection and persistent memory mechanisms.

Reflexion (Shinn et al., 2023) introduced verbal self-reflection as episodic memory, improving ALFWorld success rates from 75% to 97% within 12 trials. Self-Refine (Madaan et al., 2023) showed that iterative self-critique improves output quality by 5--20% absolute without external feedback. Generative Agents (Park et al., 2023) demonstrated that persistent memory with periodic reflection enables coherent multi-day behaviour through a retrieve-reflect-plan cycle. MemGPT (Packer et al., 2023) formalised this as a virtual memory hierarchy for unlimited-context agent operation. Voyager (Wang et al., 2023) applied persistent skill libraries in Minecraft, enabling progressive capability acquisition across sessions.

Schmied et al. (2025) quantified the knowing-doing gap directly: models produced valid strategic rationales 87% of the time but selected correct actions only 21% of the time --- a 66-point gap that persists even with chain-of-thought prompting. ReflAct (Kim et al., 2025) showed that goal-state reflection ("am I on track?") outperforms action-planning reflection ("what next?") by 27.7% on ALFWorld and WebShop, suggesting the *type* of reflection matters for strategic checkpoints. Outside AI, Gollwitzer's (1999) implementation intentions framework provides theoretical grounding: "if-then" plans show a d=0.65 effect size across 94 studies in closing the intention-behaviour gap (Section 10.2).

### 2.5 Multi-Agent Communication and Diplomacy

Meta's CICERO system (FAIR, 2022) achieved human-level play in Diplomacy by combining a controllable dialogue model with a strategic planning module, ranking in the top 10% of human players across 40 games. The key finding --- that natural language communication is a core component of strategic play, not merely an auxiliary capability --- motivates CivBench's planned multi-agent tiers (Section 5.2). Golechha and Garriga-Alonso (2025) extended game-based evaluation to social intelligence, finding asymmetric deception capabilities across 18 models in Among Us, while Diplomacy Arena (Good Start Labs, 2025) provides a leaderboard for AI negotiation. The Chatbot Arena methodology (Zheng et al., 2024) provides a precedent for ELO-based rating systems adaptable to strategic game outcomes.

---

## 3. The Paradigm Gap: From Specialised Game AI to General-Purpose Agents

The landmark results in game AI---Deep Blue, AlphaGo, AlphaGo Zero, AlphaStar, CICERO---share a common structure that differs fundamentally from the evaluation paradigm proposed here. Understanding this gap is essential for positioning CivBench accurately.

**The Alpha paradigm.** Each of these systems was purpose-built for a single game. AlphaGo combined deep neural networks with Monte Carlo tree search, trained on 30 million positions from human games before self-play refinement (Silver et al., 2016). AlphaGo Zero eliminated human data but required 4.9 million self-play games and 72 hours on 4 TPUs to reach superhuman performance (Silver et al., 2017). AlphaStar trained for the equivalent of approximately 200 years of StarCraft II play time using a league of specialised agents, each running on 16 TPUs (Vinyals et al., 2019). CICERO combined a 2.7 billion parameter dialogue model with a planning module trained on over 125,000 human Diplomacy games, producing a piRL (planning-informed reinforcement learning) agent specialised entirely for one game's action space (FAIR, 2022).

The defining characteristics of this paradigm are: (i) architectures designed around the specific game's state and action representations; (ii) training budgets measured in millions of games or equivalent compute; (iii) gradient-based optimisation of game-specific reward signals; and (iv) a goal of *mastery*---superhuman performance in the target domain.

**The CivBench paradigm.** CivBench proposes something categorically different: evaluating general-purpose language models that receive no game-specific training. The agent is a frozen model interacting through a generic tool-calling interface. There is no training loop, no self-play, no gradient signal from game outcomes. The model's strategic capability derives entirely from (a) general reasoning ability developed during pre-training and (b) whatever game-relevant knowledge was incidentally present in the training corpus.

This is not a weakness to be apologised for---it is the point. CivBench does not aim to produce a system that masters Civilization VI. It aims to measure whether general-purpose AI systems, of the kind deployed as coding assistants, research agents, and autonomous operators, can exhibit strategic competence when placed in a complex multi-domain environment. The question is not "can we build an AI that wins at Civ?" (the Alpha question) but "do today's general-purpose agents *reason strategically*, and how can we tell?" (the evaluation question).

**Table 1.** Paradigm comparison: specialised game AI vs. general-purpose agent evaluation.

| Property | Alpha paradigm | CivBench paradigm |
|----------|---------------|-------------------|
| Architecture | Game-specific neural network | General-purpose language model |
| Training | Millions of games, game-specific reward | Pre-trained on text; no game training |
| Interface | Native game API or tensor observation | MCP tool calls (same as production use) |
| Optimisation | Gradient descent on game outcomes | None; in-context reasoning only |
| Goal | Superhuman mastery of one game | Measurement of general strategic capability |
| Compute per campaign | 10,000+ TPU-hours | 2--4 GPU-hours per game (inference only) |
| Novel strategy discovery | Through self-play over millions of games | Through in-context reasoning in single games |
| Transfer to other domains | None (game-specific) | Direct (same model, same interface) |

This paradigm distinction has practical implications. AlphaGo's Move 37 emerged from millions of self-play games that explored regions of the strategy space no human had visited. An LLM agent cannot discover strategies this way---it has one game, no gradient, and must reason from what it already knows. But it brings something the Alpha systems lacked: broad prior knowledge, natural language understanding, and the ability to transfer strategic reasoning across domains. An agent that manages Civilization's economy competently is likely also competent at managing a project budget through tool calls. An AlphaGo that plays superhuman Go tells us nothing about its capacity for any other task.

The appropriate comparison class for CivBench is therefore not AlphaGo or AlphaStar, but rather other *evaluation frameworks* for general-purpose agents: SWE-bench for software engineering (Jimenez et al., 2024), Vending-Bench for business operations (Andon Labs, 2025), and WebArena for web navigation (Zhou et al., 2024). CivBench extends this family into the strategic reasoning domain, using the same tool-calling protocol these agents already use for production work.

---

## 4. Environment Description

### 4.1 Civilization VI as a Strategic Domain

Civilization VI is a commercially published 4X strategy game in which players develop civilizations from the Ancient Era through the Information Age. A standard game spans 300 to 500 turns, each requiring decisions across multiple concurrent strategic domains:

1. **Economic.** Gold income, trade routes, city yields, resource management, luxury and strategic resource stockpiles.
2. **Scientific.** A technology tree comprising 67 technologies across 8 eras, with eureka boost mechanics rewarding in-game achievements.
3. **Cultural.** A civic tree, government selection, policy card optimisation, and Great Works.
4. **Military.** Unit production and composition, hex-grid positioning, combat strength calculations, promotions, and upgrade paths.
5. **Diplomatic.** Bilateral relationships, grievance tracking, delegations, embassies, trade deals, World Congress voting, and formal alliances.
6. **Spatial.** A hex grid comprising approximately 4,000 tiles with procedurally generated terrain, features, rivers, resources, fog of war, district adjacency bonuses, and city spacing constraints.
7. **Temporal.** Multi-turn production queues, research timelines, growth projections, era progression, and irreversible commitment decisions.

Additional systems (religion, espionage, Great People) add further complexity in the mid-to-late game, though our current tool suite provides partial rather than full coverage of these subsystems.

The game supports six distinct victory conditions (Science, Culture, Domination, Religion, Diplomacy, and Score), each requiring sustained investment across different domain subsets. This forces agents to balance competing priorities under resource constraints.

The built-in AI provides eight difficulty tiers, from Settler (no bonuses) to Deity (substantial yield, combat, and starting-unit bonuses for AI opponents). Each tier defines an implicit opponent skill level against which agent performance can be calibrated.

### 4.2 The Model Context Protocol Interface

The MCP interface to Civilization VI is implemented through civ6-mcp, an open-source server that connects to the game's FireTuner debug protocol over TCP. The connection uses a length-prefixed binary protocol on port 4318: each message comprises a 4-byte little-endian length, a 4-byte tag indicating message type (command, handshake, or help query), and a null-terminated payload containing Lua source code or its output. The game acts as TCP server, accepting a single connection at a time --- a constraint that imposes serialisation on multi-agent configurations (Section 10.4).

The server exposes 70 tools covering all major game systems (Table 2). Tools follow standard MCP conventions: structured input parameters, structured output, and error reporting.

**Table 2.** Tool inventory by category.

| Category | Count | Representative tools |
|----------|-------|---------------------|
| State queries | 26 | `get_game_overview`, `get_units`, `get_map_area`, `get_diplomacy`, `get_victory_progress` |
| Unit actions | 10 | `execute_unit_action`, `upgrade_unit`, `promote_unit`, `skip_remaining_units` |
| City management | 8 | `set_city_production`, `purchase_item`, `purchase_tile`, `set_city_focus` |
| Diplomacy | 6 | `diplomacy_respond`, `send_diplomatic_action`, `propose_trade`, `form_alliance` |
| Governance | 10 | `set_research`, `set_policies`, `change_government`, `appoint_governor` |
| Religion and culture | 4 | `choose_pantheon`, `choose_dedication`, `vote_world_congress` |
| Game lifecycle | 6 | `end_turn`, `dismiss_popup`, `quicksave`, `load_save` |
| **Total** | **70** | |

A representative turn involves 5 to 15 tool invocations:

```
get_game_overview()                → yields, research, score, turn number
get_units()                        → unit positions, health, available actions
get_map_area(x, y, radius)         → terrain, resources, threats, improvements
execute_unit_action(id, action, …) → movement, combat, city founding
get_cities()                       → production queues, population, defences
set_city_production(city_id, …)    → queue management
set_research(tech)                 → technology selection
end_turn()                         → blocker detection, event reporting
```

Over a 300-turn game at approximately 10 invocations per turn, a single evaluation episode produces upwards of 3,000 tool calls. This is one to two orders of magnitude beyond any existing tool-use benchmark.

The use of MCP as the interface protocol has a notable property: it is the same protocol used by production AI agents for database queries, API calls, file operations, and other real-world tool use. Benchmark performance in CivBench therefore has direct relevance to production agent capability, unlike custom gymnasium APIs or game-specific action spaces.

### 4.3 Continuous Performance Signals

The game state extraction infrastructure provides structured data at every turn, enabling continuous performance measurement beyond binary outcomes:

- **Score trajectory.** Game score decomposed by category (era, military, civic, etc.) at every turn.
- **Yield curves.** Gold, science, culture, and faith per turn tracked longitudinally.
- **City development metrics.** Population growth, district completion rates, production throughput.
- **Military effectiveness.** Kill/loss ratio, territory held, threat response latency.
- **Diplomatic standing.** Relationship modifiers, grievance accumulation, suzerainty count, World Congress influence.
- **Espionage outcomes.** Mission success rate, intelligence yield, counterintelligence intercepts.
- **Technology pace.** Mean turns per technology, eureka and inspiration capture rates.
- **Expansion timing.** Turns to second, third, and fourth city---a well-established strategic indicator.

These signals permit fine-grained capability decomposition rather than aggregate-only scoring.

---

## 5. Evaluation Framework

We propose an evaluation framework with an implemented core tier and planned extensions of increasing complexity.

### 5.1 Tier 1: Single-Agent Play Against Classical AI

The most straightforward evaluation format places a single LLM agent against the game's built-in AI opponents. Performance is measured at fixed turn checkpoints (turns 50, 100, 150, 200, 250, 300), at milestone events (first district, first Great Person, first settler), and at game completion (victory type and turn, or final score if no victory is achieved).

We propose a standardised scenario suite:

| Scenario | Map Type | Difficulty | Purpose |
|----------|----------|------------|---------|
| A | Pangaea, standard | Prince | Baseline strategic competence |
| B | Continents, standard | King | Naval awareness, cross-ocean diplomacy |
| C | Small map | Emperor | Performance under AI yield pressure |
| D | True Start Earth | Deity | Adaptation to severe handicap |

Each scenario is defined by a fixed dual seed (map seed and game seed), game version, and DLC configuration, ensuring deterministic map generation and opponent placement.

#### ELO Rating

Agent performance across games can be aggregated into an ELO rating using the Bradley-Terry model, following the methodology established by Chatbot Arena (Zheng et al., 2024). The classical AI at each difficulty level defines an implicit rating anchor. Bootstrap confidence intervals over the game sample provide uncertainty estimates.

ELO is computed separately per scenario, per difficulty, and in aggregate, revealing whether a model excels at economic play but fails under military pressure, or handles moderate difficulty competently but collapses at higher tiers.

This would constitute, to our knowledge, the first *strategic ELO leaderboard* for language models---evaluating not linguistic fluency but strategic competence.

### 5.2 Future Tiers: Multi-Agent Competition and Strategic Communication

Beyond single-agent evaluation, two additional tiers are planned pending validation of the underlying wire protocol's support for multi-player control:

**Tier 2: Multi-Agent LLM Competition.** Multiple LLM agents on the same map, competing against each other and classical AI. Civilization VI supports multiplayer through hotseat mode, which may be instrumentable through the debug protocol. Configurations of interest include cross-model competition, prompt sensitivity analysis, and self-play convergence studies.

**Tier 3: Strategic Communication.** Drawing on CICERO's insight that natural language communication is a core component of strategic play (FAIR, 2022), this tier would augment multi-agent play with a messaging channel, testing negotiation, deception, and commitment under strategic uncertainty.

These tiers are described in detail in a companion design document. The remainder of this paper focuses on Tier 1, which is fully implemented and validated.

### 5.3 Agent Architecture as an Evaluation Variable

The choice of agent architecture may dominate model capability in benchmark outcomes. We identify three architectural patterns --- single-agent, multi-agent with orchestrator, and swarm --- summarised in Table 3. Our feasibility validation uses the single-agent architecture (one model, one conversation thread). Multi-agent configurations, where domain-specific sub-agents (military, economic, diplomatic) coordinate through an orchestrator, offer context partitioning and specialised prompting but introduce coordination overhead. The gap between a model's single-agent score and its best open-architecture score quantifies the *value of scaffolding* --- how much architectural engineering compensates for base model capability.

CivBench defines both tracks: a **standardised single-agent baseline** (fixed harness, fixed prompt) that isolates model-level strategic reasoning, and an **open-architecture track** where participants submit complete agent systems, analogous to SWE-bench's agent track (Jimenez et al., 2024). The full baseline system prompt is reproduced in Appendix A.

**Table 3.** Agent architecture comparison for CivBench evaluation.

| Property | Single-Agent | Multi-Agent + Orchestrator | Swarm |
|----------|-------------|---------------------------|-------|
| Context management | Single growing window | Partitioned per domain | Partitioned per unit/city |
| Domain expertise | Generalist | Specialist sub-agents | Semi-specialist |
| Coordination cost | None | Orchestrator overhead | Coordination protocol |
| Failure modes | Context overflow, domain neglect | Conflicting advice, orchestrator bottleneck | Strategic incoherence, resource contention |
| Cost profile | Single model, high context | Multiple models, lower per-agent context | Multiple models, parallel inference |
| What it measures | Model capability | System design + model capability | Emergent coordination |
| Production relevance | Simple agent deployments | Enterprise agent systems | Experimental |

---

## 6. The Role of Prior Knowledge and Search

### 6.1 Training Data as Strategic Prior

A distinctive property of LLM-based game agents, compared with reinforcement learning agents trained tabula rasa, is that they arrive with substantial prior knowledge derived from internet training data. The Civilization community has produced decades of strategy content, including civilization tier lists,[^1] consensus opening build orders, district adjacency optimisation guides, and victory-specific playbooks.

This prior knowledge creates a novel evaluation dimension. BALROG's central finding was a persistent gap between language models' ability to *articulate* optimal game strategies and their ability to *execute* them (Paglieri et al., 2025). CivRealm similarly found that language model agents with extensive game knowledge struggled with full-game play (Qi et al., 2024). Our own preliminary observations are consistent: an agent with knowledge of standard expansion timings still settled a third city approximately 50 turns behind optimal pace due to barbarian pressure and tactical misjudgments.

The knowing-doing gap is itself a valuable measurement target. A benchmark that can quantify how effectively an agent translates declarative strategic knowledge into situated action addresses a capability dimension absent from static benchmarks.

### 6.2 Search Augmentation

An additional configuration of interest equips agents with web search or retrieval tools during gameplay, enabling real-time strategy lookup (e.g., unit counters, district adjacency calculations). This mirrors production agentic workflows in which tool-augmented reasoning supplements parametric knowledge.

CivBench can evaluate both configurations:

- **Closed-book.** The agent relies solely on parametric knowledge from training.
- **Open-book.** The agent has access to search and retrieval tools alongside game tools.

The performance gap between these modes would measure the marginal value of retrieval-augmented reasoning in strategic domains---a question of practical importance for production agent design.

### 6.3 Contamination and Countermeasures

Known strategies in training data present a dual-edged evaluation challenge. An agent that recognises civilisation-specific synergies (e.g., Poland's faith-based reliquary strategy) demonstrates useful knowledge transfer. However, if benchmark scenarios use well-known map seeds with published strategy guides, performance may reflect memorisation rather than reasoning.

The game's combinatorial state space provides a natural defence: even with knowledge of optimal openings, an agent must adapt when a barbarian encampment spawns adjacent to its second city at turn 40, or when an opponent forward-settles an unexpected location. Additional mitigations include rotating seed pools across evaluation cycles, distributing mid-game save-state scenarios that cannot be memorised as openings, maintaining a held-out test set used only for official evaluation, and monitoring tool-call traces for stereotyped behaviour patterns (e.g., identical opening sequences regardless of start position).

---

## 7. Practical Considerations

### 7.1 Licensing

Civilization VI is commercially licensed by 2K Games (Firaxis). Benchmark participants must own a copy of the game (approximately \$15--60 depending on edition and DLC). The MCP server (civ6-mcp) is MIT-licensed and distributes no game assets or proprietary code.

This licensing model is comparable to benchmarks requiring paid API access. Vending-Bench 2 consumes real API credits; SWE-bench requires Docker infrastructure. The game licence is a one-time cost per evaluation machine.

### 7.2 Cost of Evaluation

The primary cost driver is the growing conversation context. Each turn, the agent processes its full conversation history alongside new tool results. With periodic context compression (standard in production agent frameworks), we estimate an average of approximately 35,000 input tokens per turn across a full game, based on live playtest data.

Table 4 presents per-game cost projections based on estimated token volumes. Actual per-game costs were not logged during our playtests.

**Table 4.** Projected cost per game (300 turns) by model. Pricing as of February 2026.

| Model | Input rate (per 1M tokens) | Output rate (per 1M tokens) | Est. input tokens | Est. output tokens | Total per game |
|-------|------------|-------------|----------------|--------------|--------------|
| Gemini 3 Pro | \$2.00 | \$12.00 | ~13M | ~450K | ~\$31 |
| GPT-4o | \$2.50 | \$10.00 | ~13M | ~450K | ~\$37 |
| Claude Sonnet 4.5 | \$3.00 | \$15.00 | ~13M | ~450K | ~\$46 |
| Claude Opus 4.6 | \$15.00 | \$75.00 | ~13M | ~450K | ~\$229 |

A 20-game evaluation suite (comparable to Diplomacy Arena; Good Start Labs, 2025) costs \$620--4,580 depending on model. A 50-game suite sufficient for stable ELO estimation costs \$1,550--11,450.

Additional per-evaluation costs include the game licence (\$15--60 one-time), wall-clock time (2--4 hours per game), and one machine running Civilization VI per concurrent evaluation. For multi-agent configurations with messaging, costs scale with the number of LLM-controlled players.

These costs are substantially higher than static benchmarks (\$0.10 for MMLU) but within the range of agentic evaluations (SWE-bench: \$50--200 per run) and well below human evaluation studies. In an environment where the top ten models score within 2% of each other on MMLU-Pro, a benchmark capable of differentiating strategic reasoning at \$30--230 per game represents reasonable evaluation economics.

### 7.3 Reproducibility

Civilization VI's dual-seed system (map seed and game seed) deterministically generates identical maps, resource placements, and starting positions given identical game version, DLC configuration, and settings. A benchmark specification would pin these parameters exactly.

For stronger guarantees, benchmark scenarios can be distributed as save files---pre-configured game states at specific turns. This enables both full-game evaluation and targeted mid-game assessment (e.g., a turn-150 military crisis requiring immediate response).

### 7.4 Technical Feasibility

The civ6-mcp implementation demonstrates the required infrastructure: 70 MCP tools covering all major game systems, structured data extraction, continuous performance logging in JSONL format, and a real-time web dashboard for observation. A Claude Opus 4.6 agent has completed five games (865+ turns total across different civilizations and difficulty levels) through this interface, demonstrating that the tool suite supports sustained strategic play over hundreds of turns.

Infrastructure remaining for a formal benchmark includes automated game reset and scenario loading, multi-agent orchestration, and expansion of tool coverage for religion and espionage subsystems.

### 7.5 Implementation in Inspect

CivBench is implemented within the UK AI Security Institute's Inspect framework (AISI, 2024), an open-source Python evaluation platform with native MCP support and over 107 community-contributed benchmarks.

Inspect's architecture maps cleanly onto CivBench. Each game scenario is a `Sample` in a `Dataset`, parameterised by save file, difficulty, turn limit, and victory condition. The civ6-mcp server is consumed directly as an MCP tool source via `mcp_server_stdio()`, requiring no modifications to the existing tool suite. The agent is either the built-in `react()` loop (for the standardised single-agent baseline) or a custom `@agent` implementation (for the open-architecture track). A custom `@scorer` extracts game metrics from the tool-call transcript, reporting per-dimension scores including overall score, economic growth, military actions, research progress, spatial expansion, diplomatic engagement, and tool-use fluency.

Inspect provides several capabilities that would be costly to build independently:

- **Model portability.** The same evaluation runs against any supported model with a flag change (`--model anthropic/claude-opus-4-6`, `--model openai/gpt-4o`, etc.), supporting 15+ providers. This eliminates the need to implement provider-specific API integrations.
- **Structured logging.** Every message, tool call, tool result, and model response is captured in structured `EvalLog` files, enabling the trajectory analysis discussed in Section 7.6. The `inspect view` UI provides interactive drill-down into any game turn.
- **Robustness.** Eval sets provide automatic retries, work reuse from failed runs, and checkpoint recovery---important for multi-hour game sessions that may encounter transient failures.
- **Community adoption.** Publishing CivBench as an Inspect eval makes it instantly accessible to the AI safety research community, which already uses the framework for SWE-bench, GAIA, AgentBench, and OSWorld. This is the most direct path to the scale needed for meaningful results.

The main integration work involves game lifecycle management: automating save-file loading between scenarios and ensuring clean game state between evaluation samples. The existing MCP tools, game state extraction, and connection infrastructure require no changes.

### 7.6 Trajectory Analysis

The complete tool-call trace for every game constitutes a rich research artifact beyond aggregate scoring. Each turn's sequence of observations, reasoning, and actions is logged, enabling post-hoc analysis of:

- **Decision quality at each turn.** Did the agent gather sufficient information (map scans, threat checks) before committing to actions? Did it respond to threats visible in its observations?
- **Strategic coherence over time.** Does the agent maintain a consistent strategic direction, or does it exhibit drift---pursuing a science victory for 50 turns, then abruptly switching to military buildup without provocation?
- **Error taxonomy.** Classification of failures by type: tool-use errors (wrong parameters, invalid actions), strategic errors (poor city placement, neglected defence), knowledge gaps (not knowing game mechanics), and reasoning errors (correct observations, incorrect conclusions).
- **The knowing-doing gap.** Comparing the agent's stated intentions (in its reasoning traces) with its actual actions. An agent that articulates "I need to build walls before the barbarian wave arrives" and then queues a Monument is exhibiting a specific, measurable failure mode.

For Inspect-based evaluation, these trajectories are captured automatically in structured log format.

---

## 8. Evaluation Dimensions

We propose a multi-dimensional scorecard enabling disaggregated capability assessment. Table 5 defines the evaluation dimensions.

**Table 5.** Evaluation dimensions for CivBench. Dimensions marked with * are implemented in the current Inspect scorer; others require trajectory analysis at scale.

| Dimension | Signal | Measurement |
|-----------|--------|-------------|
| Overall Score* | Aggregate game score | Raw Civ 6 score at checkpoints |
| Economic Management* | Yield optimisation, trade route efficiency | Gold, science, culture per turn growth |
| Military Competence* | Threat response, unit positioning | Attack actions, kill/loss ratio |
| Scientific Progress* | Technology path quality | Research changes per N turns |
| Cultural Progress* | Civic path quality | Civic changes, government transitions |
| Diplomatic Skill* | Relationship management, deal quality | Diplomatic actions taken |
| Spatial Reasoning* | Map awareness, settlement quality | Map scans, cities founded |
| Tool-Use Fluency* | Correct tool selection, parameter accuracy | Error rate, tool diversity |
| Turns Played* | Game progression rate | Actual turns advanced per session |
| Long-Horizon Coherence | Maintaining strategic direction | Score variance, strategy drift |
| Adaptation | Response to unexpected events | Recovery time after setbacks |

These dimensions can be reported individually, enabling comparison across specific capability axes, or aggregated into a composite score for leaderboard ranking.

This disaggregated approach is motivated by the phenomenon Gans (2026) formalises as *artificial jagged intelligence*: the empirical observation that frontier models exhibit sharply uneven capability profiles, excelling at complex tasks while failing at superficially simpler ones. Gans models this as an information problem where users observe coarse global quality signals but require local reliability, and shows that scaling laws improve average quality without eliminating jaggedness. CivBench's multi-dimensional scorecard is designed to expose exactly this structure---a model might demonstrate strong economic management while exhibiting poor spatial reasoning, or vice versa---producing the kind of fine-grained capability map that aggregate benchmarks obscure.

---

## 9. Preliminary Results

We report initial results from five single-agent games played by Claude Opus 4.6 (Anthropic, 2025) against classical AI, using the single-agent `react()` architecture with the standardised baseline prompt (Appendix A). All gameplay used the civ6-mcp tool suite over the MCP stdio transport. These results constitute a *feasibility demonstration*: they validate that the infrastructure produces interpretable signals across multiple evaluation dimensions, not that the findings generalise beyond the tested configuration (one model, five games). Multi-model comparison at scale is left to future work.

### 9.1 Game Configurations

**Table 6.** Game configurations for preliminary evaluation. Games are listed chronologically; tooling and prompt were iteratively refined between games.

| Property | Game 1 | Game 2 | Game 3 | Game 4 | Game 5 |
|----------|--------|--------|--------|--------|--------|
| Civilization | Poland (Jadwiga) | Rome (Trajan) | Macedon (Alexander) | Byzantium (Basil II) | Macedon (Alexander) |
| Difficulty | Prince | Prince | King | King | King |
| AI opponents | 5 | 3 | 4 | 5 | 4 |
| Turns played | 125--323 | 1--221 | 1--70 | 1--182 | 1--110 |
| Outcome | Conceded | Ongoing | Eliminated | Defeated | Conceded |
| Final score | 350 | 455 | -- | -- | 139 |
| Final rank | 6th of 6 | 4th of 4 | -- (eliminated) | -- (defeated) | 4th of 4 |
| Defeat cause | -- | -- | Sweden military conquest | Russia religious victory | -- (unwinnable) |

Game 1 was loaded from a mid-game save at turn 125. Game 2 was played from a fresh start (turn 1) with an improved tool suite and refined system prompt. Games 3 and 4 tested higher difficulty (King) and different civilizations with specialised victory affinities (Macedon for domination, Byzantium for religion). Game 5 retried Macedon with accumulated tooling fixes and an explicit domination-oriented game plan. Across all five games, the agent defaulted to the same science-first opening regardless of civ-specific strengths --- even in Game 5, where the domination plan was written on turn 1 but Campus production was prioritised over Encampment by turn 70 (Section 9.5).

### 9.2 Score Trajectories

**Table 7.** Score trajectory at selected checkpoints for Game 1 (Poland). Agent rank is position among all players by score.

| Turn | Score | Gold/turn | Science/turn | Culture/turn | Cities | Units | Rank |
|------|-------|-----------|--------------|--------------|--------|-------|------|
| 125 | 150 | +16 | 23.8 | 14.3 | 3 | 6 | 3/3 |
| 150 | 179 | +20 | 26.6 | 16.2 | 3 | 6 | 3/3 |
| 200 | 241 | +20 | 45.6 | 20.5 | 4 | 6 | 6/6 |
| 250 | 280 | +10 | 47.3 | 21.9 | 4 | 9 | 6/6 |
| 300 | 325 | +42 | 54.4 | 20.8 | 4 | 12 | 6/6 |
| 323 | 350 | +42 | 54.4 | 20.8 | 4 | 14 | 6/6 |

**Table 8.** Score trajectory at selected checkpoints for Game 2 (Rome, improved tooling).

| Turn | Score | Gold/turn | Science/turn | Culture/turn | Cities | Units | Rank |
|------|-------|-----------|--------------|--------------|--------|-------|------|
| 1 | 0 | +0 | 0.0 | 0.0 | 0 | 4 | -- |
| 35 | 32 | +6 | 4.5 | 6.5 | 2 | 6 | 2/2 |
| 60 | 67 | +7 | 9.0 | 9.0 | 2 | 8 | 2/2 |
| 90 | 135 | +22 | 17.0 | 12.8 | 3 | 8 | 2/2 |
| 112 | 199 | +27 | 26.8 | 19.4 | 5 | 8 | 3/3 |
| 150 | 312 | +25 | 99.8 | 46.9 | 7 | 11 | 3/3 |
| 186 | 450 | +54 | 153.0 | 59.5 | 7 | 12 | 3/4 |

In Game 1, the agent ranked last throughout, expanding to only 4 cities against AI opponents with 6--8 cities each. Science and culture growth stalled in the mid-game (turns 200--270) before partially recovering. In Game 2, with improved tooling and a refined prompt, the agent maintained a competitive position through turn 90 (2nd of 2 visible players) and expanded to 7 cities. Science output grew strongly (0 to 153/turn), though the agent fell behind late-game as additional AI civilizations were encountered.

*[Figure 1: Score trajectories for both games, with AI opponent scores overlaid, will be generated from this data.]*

### 9.3 Tool-Use Patterns

**Table 9.** Tool call distribution by category across both games.

| Category | Game 1 (Poland) | Game 2 (Rome) | Combined |
|----------|-----------------|---------------|----------|
| Unit actions (move, attack, found city) | 798 | 833 | 1,631 |
| State queries (overview, units, map, cities) | 520 | 699 | 1,219 |
| Management (production, research, policies) | 199 | 293 | 492 |
| Diplomacy (respond, send action, envoys) | 99 | 94 | 193 |
| End turn | 235 | 248 | 483 |
| Raw Lua (execute_lua) | 324 | 278 | 602 |
| **Total** | **2,169** | **2,438** | **4,607** |

The tool distribution reveals that the agent spends the majority of its actions on unit management (35%) and state observation (26%), with management decisions (production, research) comprising only 11% of calls. The relatively high use of raw Lua execution (13%) reflects tool coverage gaps that the agent worked around by issuing direct game commands.

The 2.5--2.7% error rate across both games indicates robust tool-use fluency. Errors were predominantly application-level (invalid unit actions, stacking conflicts) rather than protocol-level, suggesting the agent understands the MCP interface but occasionally misjudges game state constraints.

### 9.4 Agent-AI Performance Gap and Infrastructure Improvement

The agent underperformed AI opponents in both games, but the trajectory between games reveals that infrastructure quality materially affects gameplay outcomes.

In Game 1 (Poland, initial tooling), the agent ranked last of 6 throughout, expanding to only 4 cities while AI opponents reached 6--8 each. The leading AI (Kongo, score 1,040) outscored the agent (350) by 3:1 at turn 323. Key failures included: zero exploration beyond immediate surroundings, 588 accumulated diplomatic favor left invisible due to a GameCore/InGame API context bug, and 2,818 faith unspent due to missing pantheon and religion tooling. The game was conceded at turn 323.

In Game 2 (Rome, improved tooling and prompt), the agent expanded more aggressively (7 cities by turn 143), achieved a commanding science lead (152 science/turn at turn 185, approximately double the nearest rival), and maintained competitive scores against AI through the mid-game. Notable improvements between games included: spatial awareness tools (`get_strategic_map`, `get_global_settle_advisor`) that enabled better city placement, enhanced diplomacy tools that surfaced favor income, and exploration coverage statistics added to `get_game_overview` as a persistent nudge. The agent still ranked 4th of 4 at turn 186, but the score gap narrowed substantially (450 vs. leader China at 489, compared to Poland's 350 vs. Kongo's 1,040).

This cross-game improvement is consistent with BALROG's knowing-doing gap finding (Paglieri et al., 2025): the agent's strategic *knowledge* was similar across both games, but better tooling reduced the translation cost between knowledge and action. The agent articulated correct strategic priorities in both games (expand early, build campuses, defend against barbarians) but executed them far more effectively with improved tool coverage.

The remaining gap is primarily **expansion timing**: the agent founded its 3rd city at turn 84 in Game 2, approximately 30--50 turns behind optimal pace. Since yields compound with city count, this early-game deficit propagates through all dimensions.

### 9.5 Agent Playstyle Characterization

Analysis of detailed gameplay logs from all five games reveals a consistent behavioural profile that persists across different civilizations, difficulty levels, tooling versions, and game conditions. While early-stage harness bugs caused some lost turns (diplomacy popup race conditions, unit promotion failures, LOS check errors), these are expected in an evolving agentic rig and are progressively fixed between games. The more significant finding is a set of *strategic* failures that persist even after the agent explicitly identifies and attempts to correct them. We organise the findings around a root cause we term the *sensorium effect*, followed by the failure modes it produces and a meta-pattern that cuts across all of them.

#### The Sensorium Effect

A human Civilization player passively absorbs dozens of game-state signals per second through vision: the minimap shows fog boundaries and territory shapes, the score ticker tracks relative standing, the religion lens reveals missionary movements, unit health bars flag damage, and AI army positions are visible at a glance. The agent has none of this. It only knows what it explicitly queries, and each query costs time and context window capacity.

This asymmetry is the root cause of the agent's most consequential failures. Information requiring active polling --- exploration status, victory progress, religious spread, diplomatic trends --- goes unmonitored until a crisis forces attention. In Game 4 (Byzantium), Russia converted all 21 cities to Orthodoxy over 112 turns; the agent never checked `get_victory_progress` between turn 0 and turn 182 (the defeat turn). In Game 1, 588 diplomatic favor accumulated invisibly because the overview query ran in a context where the API returned nil, and the agent never questioned the anomalous zero. In Game 2, the agent's own diagnosis captured the asymmetry precisely: *"I never see tiles I don't explicitly query."*

The sensorium effect is not merely a tooling gap --- it operates even when the relevant data is present in the agent's context. In Game 5 (Macedon), at turn 61 the agent's own `get_units` output contained "Nearby threats: Sumeria 2 units" showing a War Cart and Warrior flanking an undefended city from one tile away. The agent read this output, noted it in its log, and did not reposition any units. Its post-hoc analysis: *"I had the threat data but didn't act on it. Classic case of reading data without processing implications."* The turn loop is driven by *notifications* --- production completions, unit orders needed, research finished --- not by threat assessment or strategic monitoring. Unprompted information competes with prompted tactical demands, and loses.

#### Failure Modes

The sensorium effect cascades into a hierarchy of downstream failures, each observed across all five games:

**Exploration neglect.** Game 1: zero scouts after turn 54, five directions unexplored for 323 turns. Game 2: 34\% explored at turn 160, fourth AI civ not met until turn 163. Game 3: 11\% explored at elimination (turn 70). Game 4: 9\% at turn 40, the agent wrote "CRITICAL --- need more scouting" at turns 40, 65, and 101 without producing another scout. Game 5 showed partial improvement --- three scouts running from turn 7, reaching 32\% explored by turn 70 --- but still fell short of benchmarks and left two of four AI civilizations unmet. Exploration generates no notifications, no blockers, and no urgency signals, so it is perpetually deprioritised.

**Expansion failure.** Expansion is downstream of exploration: you cannot settle what you cannot see. Game 1: 3 cities at turn 100 (benchmark: 4--5), never exceeded 4. Game 2: 2 cities for 49 consecutive turns. Game 3: 2 cities at elimination. Game 4: 3 cities at defeat versus Russia's 11. In every game, the agent prioritised infrastructure in existing cities (monuments, granaries, campuses) over producing settlers, despite settlers being the single highest-impact early investment.

**Science fixation and civ identity blindness.** The agent pursued a science-first opening in all five games regardless of civilisation identity. In Game 3 (Macedon/Alexander), whose unique abilities reward aggressive military conquest (no war weariness, unique melee units), the agent built campuses and libraries. In Game 4 (Byzantium), whose signature ability requires founding a religion (+3 combat strength per converted city), the agent never built a Holy Site and had 3 faith at turn 103. Game 5 (Macedon again) is the most revealing case. The agent showed genuine improvement in *strategic awareness*: it wrote a domination plan on turn 1, researched Iron Working for its unique Hypaspist unit, chose Oligarchy (+4 combat strength) over Classical Republic, and framed its approach around Macedon's "science-from-military engine." But it never built the Encampment district that enables that engine. When Sumeria declared war at turn 99, a city fell immediately because all military had been pulled east to escort a settler. By turn 109, domination was rated 15\% viable and the agent wrote a "Science Sprint" plan --- the same default as every previous game. It conceded at turn 110, last of four, with its own post-mortem noting: *"Macedon's kit requires an Encampment with Basilikoi Paides. We never built one --- the entire civ ability was wasted."* The gap between strategic awareness and execution had narrowed, but not closed.

**Diplomacy passivity.** Game 1: 495 favor, zero alliances, zero friendships in 323 turns. Game 2: zero favor income for the first 163 turns despite friendships being available. Game 3: delegations sent and rejected, no follow-up. Game 4: 230 favor accumulated but never spent on World Congress votes. In every game, diplomacy was treated as an interruption to respond to rather than a yield source to cultivate.

**Resource hoarding.** Game 1: 2,578 gold and 2,818 faith unspent at concession. Game 2: 3,936 gold at turn 221. Game 4: 646 gold and 876 faith idle at turn 174. The agent identified hoarding as a problem in post-game reflections after Games 1 and 2, explicitly listing "spend gold and faith" as a lesson --- then continued hoarding in Games 3 and 4.

These failures form a causal chain: the sensorium effect causes exploration neglect, which prevents expansion, which limits district count and yield growth, which makes the chosen victory path (invariably science) unviable --- but the agent never reassesses because victory progress goes unmonitored. Table 10 quantifies these failure modes across all five games.

**Table 10.** Quantified failure modes across five games. Benchmarks for competent play: 4--5 cities by T100, 35%+ explored by T70, gold below 500.

| Metric | Game 1 (Poland) | Game 2 (Rome) | Game 3 (Macedon) | Game 4 (Byzantium) | Game 5 (Macedon) |
|--------|-----------------|---------------|------------------|--------------------|--------------------|
| Exploration at T70 | 30% | ~28% | 11% (eliminated) | 12% | 32% |
| Cities at T100 | 3 | 3 | 0 (elim. T70) | 2 | 3 |
| City 3 founding turn | T84 | T84 | Never | T102 | T70 |
| Peak gold hoarded | 1,618 | 3,936 | N/A | 646 | --- |
| Peak faith hoarded | 2,818 | 524 | N/A | 876 | --- |
| Victory progress checks | 0 | ~2 | 0 | 0 | ~1 |
| Scouts active at T50 | 0 | 1 (stuck) | ~0 | 0 | 3 |
| Alliances formed | 0 | 0 | 0 | 0 | 0 |

**Generalisability.** The sensorium effect is an *architectural* property of any agent that perceives a visually-rich environment through text queries --- it will manifest regardless of model, prompt, or tool design. Exploration neglect and expansion failure are downstream consequences we expect to recur across models, though their severity may vary with prompt engineering (Game 5's improved system prompt partially mitigated exploration neglect). Science fixation and civ identity blindness may be partially *model-specific* --- they could reflect Claude Opus 4.6's training data distribution, in which science victory guides are overrepresented. Resource hoarding is likely *prompt-addressable* through hard spending triggers. Multi-model comparison is required to decompose these effects; the single-model results reported here establish the *existence* of these failure modes but cannot attribute them to model vs. architecture vs. prompt.

#### The Reflection-Action Gap

The most striking meta-pattern is the systematic disconnect between the agent's strategic analysis and its subsequent actions. The gameplay logs across all five games contain detailed, accurate assessments of strategic weaknesses --- "build Theater Squares," "spend gold aggressively," "explore before it's too late," "escort all civilians" --- that are written 3--5 times per game without being acted upon. Game 3's pre-game reflection explicitly listed every lesson from Games 1 and 2; nearly every lesson was violated within 30 turns.

Game 5 represents the strongest test of this pattern. The agent introduced an explicit self-check mechanism at turn 17 --- a literal checkbox audit of playbook compliance --- and used the term "sensorium failure" as a real-time diagnostic label during gameplay. It showed genuine strategic improvement: choosing Oligarchy, researching military techs, upgrading to unique units. But the core gap persisted. The agent read Sumerian troops flanking Methone at turn 61 and didn't react. It never built the Encampment that makes Macedon unique despite 110 turns of opportunity. And when its domination plan collapsed at turn 99, it immediately reverted to a science sprint --- producing an elaborate three-phase plan to reach a Science Victory by turn 300 from a position its own assessment rated at 15\% domination viability. The self-awareness improved markedly; the behavioural default did not change.

The agent's planning horizon appears to be effectively one turn: it optimises the current turn's decisions competently but lacks a mechanism to enforce multi-turn strategic commitments against the pull of immediate-return actions (production queues, unit orders, research selections). This extends the knowing-doing gap identified in BALROG (Paglieri et al., 2025) and quantified by Schmied et al. (2025) at 66 percentage points (87% valid rationales, 21% correct actions) to a finer granularity: the failure is not in *identifying* the correct action, nor even in *intending* to act, but in *maintaining priority* against competing immediate demands within the turn loop. Section 10.2 discusses a structural intervention --- a mandatory turn diary --- designed to address this gap.

#### Why Science? Victory Type as Capability Signal

The agent's invariant default to science victory across all five games --- including games played as domination and religious civilizations --- is not a strategic choice but a behavioural artefact of the sensorium effect and reflection-action gap.

Science is the only victory path where the critical actions are *notification-driven*. When a technology completes, the game blocks the turn until the player selects the next research target. Campus is the consensus "safe first district" in the Civilization strategy community, reinforced in training data. Science per turn is always visible in the game overview. The tech tree is a linear dependency graph navigable one decision at a time. No opponent interaction is required --- the agent simply accumulates technologies.

Every other victory type demands precisely the capabilities the agent lacks:

- **Domination** requires sustained multi-turn coordination: positioning units across tiles, timing ranged and melee attacks, managing supply lines and war weariness, governing captured cities. This is the multi-turn commitment that the reflection-action gap prevents. The agent wrote a domination plan in Game 5 and still prioritised Campus production.

- **Religious victory** requires early unprompted commitment with delayed payoff: building a Holy Site before a Campus, founding a pantheon, waiting for a Great Prophet, choosing beliefs, producing missionaries, and physically moving them to opponent cities. Every step is proactive. Nothing in the turn loop prompts "check religious spread" --- which is why Russia's religious victory in Game 4 was invisible for 112 turns.

- **Diplomatic victory** depends on passive accumulation that the agent never monitors: maintaining friendships for favor income, spending favor in World Congress votes, pursuing alliances. In Game 1, 588 favor sat unspent for 200 turns.

- **Cultural victory** requires Theater Squares (never built in any game), Great Works, open borders agreements, and understanding the tourism mechanic --- the most opaque system in the game even for human players.

The pattern reveals that science is what remains when you subtract everything requiring unprompted multi-turn commitment, proactive monitoring, or cross-domain coordination. The agent does not *choose* science strategically; it *defaults* to science because science is the one yield where the knowing-doing gap is smallest --- actions are simple, mostly prompted, and require no opponent interaction.

This observation has direct implications for benchmark interpretation: the *victory type achieved* is itself a capability signal. An agent that wins through domination or religion has demonstrated multi-domain coordination, proactive monitoring, and sustained strategic commitment that a science victory does not require. Future multi-model comparisons should report not just score but victory path, as a qualitative indicator of strategic sophistication.

*[Placeholder: Multi-model comparison table will be added when additional model evaluations are completed.]*

*[Placeholder: Per-dimension radar chart comparing agent profile across evaluation dimensions will be generated from scorer output.]*

---

## 10. Discussion

### 10.1 Beyond the Knowing-Doing Gap: What Does CivBench Actually Measure?

A legitimate concern is whether CivBench reduces to a sophisticated Tower of Hanoi---a task where the optimal algorithm exists in training data, and the benchmark merely measures whether the model can execute a known solution. If so, the benchmark tells us little beyond what simpler execution tests already reveal.

We argue that CivBench is fundamentally different, for three reasons.

First, **there is no single optimal strategy**. Tower of Hanoi has an O(1) recursive solution. Civilization has no equivalent. The optimal play depends on map generation (random), opponent behaviour (reactive), and the continuous interaction of multiple strategic systems. An agent cannot look up "the answer" because the answer changes with every game state. The benchmark tests *situated reasoning*---the ability to apply general strategic knowledge to a specific, evolving context.

Second, **the knowing-doing gap is itself multi-dimensional in CivBench**, unlike in execution-only tasks. In Tower of Hanoi, the gap is between knowing the algorithm and correctly issuing the move sequence. In Civilization, the gap manifests differently across domains: an agent may execute economic management competently while failing at military response, or handle unit-level tactics while neglecting long-term strategic planning. The per-dimension scoring (Section 8) decomposes the knowing-doing gap into capability-specific measurements, revealing *where* models fail to translate knowledge into action rather than merely *that* they fail.

Third, **the benchmark measures capabilities that have no "known solution" to memorise**: adaptation to unexpected events (a barbarian invasion disrupting expansion plans), multi-objective balancing under resource constraints (gold needed for both military and infrastructure), and long-horizon coherence (maintaining a strategic direction across 300 turns of accumulating context). These are capabilities of the reasoning system, not retrieval of stored procedures.

That said, the concern has a valid kernel. If all models score poorly on CivBench in similar ways---struggling with the same mechanical execution issues regardless of strategic sophistication---then the benchmark is measuring agentic tooling quality (context management, error recovery, tool-use reliability) more than strategic reasoning. This is why the agent architecture analysis (Section 5.3) and the dual-track design (standardised baseline vs. open architecture) matter: they help separate the contribution of the model's strategic reasoning from the contribution of the scaffolding that supports it. The preliminary results in Section 9 show that the agent exhibits domain-specific variation (stronger economic than military play), which is encouraging for discriminative power.

### 10.2 Structured Reflection: From Diagnosis to Intervention

The reflection-action gap identified in Section 9.5 is not unique to CivBench. Schmied et al. (2025) measured a 66-point gap between reasoning quality (87% valid rationales) and action execution (21% correct actions) in LLM decision-making, finding that the gap persists even with chain-of-thought prompting. The five CivBench games exhibit the same pattern at finer temporal resolution: the agent produces strategy-guide-quality analysis at turn boundaries but operates as if each turn is independent of the last.

The literature on agent reflection (Section 2.4) suggests that the gap is addressable not through better prompting but through *structural forcing functions* that make reflection mandatory and persistent. Reflexion (Shinn et al., 2023) demonstrated that storing verbal self-critiques as episodic memory closes the gap in task-retry settings. ReflAct (Kim et al., 2025) showed that goal-state reflection (asking "am I on track?") outperforms action-planning reflection (asking "what next?") by 27.7%. Generative Agents (Park et al., 2023) and MemGPT (Packer et al., 2023) showed that persistent memory with periodic reflection enables multi-day coherence in agent behaviour.

Drawing on these findings, we have implemented a *turn diary* mechanism as a structural intervention. At each turn boundary, the `end_turn` tool requires five non-empty reflection fields before advancing the game:

- **Tactical**: What happened this turn? Combat outcomes, movements, improvements completed.
- **Strategic**: Where do you stand relative to rivals? Yield comparisons, city count, victory path viability.
- **Tooling**: Any tool failures or observations. Surfaces harness issues for iterative improvement.
- **Planning**: Concrete actions for the next 5--10 turns. Serves as an implementation intention (Gollwitzer, 1999).
- **Hypothesis**: Predictions about opponent behaviour, resource needs, and timelines.

Each entry is persisted as a JSONL record with an auto-captured score snapshot (turn number, yields, city count, exploration percentage, era). A companion `get_diary` tool allows the agent to retrieve recent entries at any time, and is particularly valuable after context compactions --- the primary mechanism by which strategic memory is lost in long-horizon play.

The design draws directly from Gollwitzer's (1999) implementation intentions framework: by requiring the agent to articulate specific plans ("finish Campus, improve Coffee, send settler east") rather than abstract goals ("expand more"), the diary converts intentions into commitments with a temporal anchor. The planning field is the implementation intention; the hypothesis field creates a falsifiable prediction the agent can check against on subsequent turns; the strategic field forces the periodic monitoring that the sensorium effect otherwise prevents.

Whether this mechanism closes the reflection-action gap is an empirical question that future games will address. The diary data also serves a benchmark purpose: the five reflection dimensions provide a structured record of the agent's *stated* reasoning at every turn boundary, enabling post-hoc analysis of where stated intentions diverge from observed actions. This offers a richer signal than tool-call transcripts alone, decomposing the knowing-doing gap into intention formation, commitment persistence, and execution fidelity.

### 10.3 From Preliminary Results to Meaningful Scale

While Section 9 presents initial results from five games, meaningful benchmark conclusions require larger-scale evaluation. This section discusses the path forward.

The path from preliminary results to a production-grade benchmark involves: (a) running multi-model comparisons (3--4 frontier models, 10--20 games each) to demonstrate that the benchmark differentiates meaningfully; (b) automating game reset and scenario loading to enable unattended evaluation runs; (c) extending tool coverage for religion and espionage subsystems; and (d) publishing the resulting leaderboard to catalyse community adoption.

The aspiration is to provide the strategic reasoning equivalent of what SWE-bench provides for software engineering: a credible, reproducible measurement of how well general-purpose AI systems perform in a domain that matters. The preliminary results in Section 9 demonstrate that the benchmark produces rich, interpretable signals --- the question is whether those signals differentiate meaningfully across models.

### 10.4 Limitations

Several limitations merit explicit acknowledgement.

**Single-connection constraint.** The FireTuner debug protocol accepts only one TCP connection at a time. Multi-agent configurations require either a serialising proxy, hotseat automation, or custom modification. This is an engineering constraint rather than a fundamental limitation, but it affects ease of adoption.

**Commercial dependency.** Reliance on a commercially licensed game introduces a risk of version changes, discontinued support, or licensing complications. FreeCiv-based alternatives (CivRealm) avoid this dependency at the cost of reduced game complexity. The benchmark framework should be designed to be substrate-agnostic where possible; Civilization VII may offer improved modding or API support.

**Cost.** At \$31--76 per game, CivBench is one to two orders of magnitude more expensive than static benchmarks. This limits the number of games feasible per evaluation cycle and may restrict participation to well-funded research groups. Cost will decrease as model pricing declines, but the growing context window remains a structural cost driver.

**Nondeterminism.** While map generation is deterministic given fixed seeds, agent behaviour introduces nondeterminism through stochastic sampling in model inference. Multiple games per scenario are required for statistical stability, further increasing evaluation cost.

**Contamination surface.** The Civilization franchise has an extensive online strategy community. Models trained on this data arrive with prior knowledge that may conflate memorisation with reasoning. The mitigations described in Section 6.3 reduce but do not eliminate this concern.

---

## 11. Conclusion

We have presented CivBench, a benchmark framework and working implementation for evaluating language model agents in the complex strategic domain of Civilization VI. The benchmark addresses a gap in the current evaluation landscape: no existing framework simultaneously tests high-volume tool use (thousands of invocations per episode), long-horizon planning (300+ sequential decisions), and multi-domain reasoning across concurrent strategic systems.

CivBench occupies a distinct position relative to the two major traditions in game AI research. It does not follow the Alpha paradigm of training specialised systems through millions of self-play episodes to achieve domain mastery (Silver et al., 2016, 2017; Vinyals et al., 2019). Nor does it reduce game interaction to a simplified gym-style API as in CivRealm (Qi et al., 2024) or BALROG (Paglieri et al., 2025). Instead, it evaluates general-purpose models through production-standard tool calling, positioning strategic gameplay as a *capability measurement* for the same systems deployed as coding assistants, research agents, and autonomous operators.

Preliminary results from five games across different civilizations and difficulty levels demonstrate that the infrastructure supports sustained agent play and produces rich, interpretable performance signals. A Claude Opus 4.6 agent exhibited a consistent behavioural profile --- strong single-yield optimisation but systematic failures in exploration, expansion, and multi-domain balance --- that persisted across games despite explicit self-correction attempts. The *sensorium effect* (the fundamental asymmetry between human visual perception and agent text queries) and the *reflection-action gap* (correct strategic analysis without follow-through) emerge as the primary capability bottlenecks, suggesting that CivBench measures genuine strategic reasoning limitations rather than mechanical tool-use failures.

The civ6-mcp implementation provides 70 MCP tools, integrated with the UK AISI Inspect evaluation framework, and is open-source and available for immediate use. What remains is multi-model comparison at scale: the most compelling question is whether different models exhibit meaningfully different *strategic profiles*---not merely scoring higher or lower in aggregate, but excelling in distinct capability dimensions.

We invite the community to adopt, extend, and run CivBench.

---

## References

Andon Labs. (2025). Vending-Bench: A benchmark for long-term coherence of autonomous agents. *arXiv:2502.15840*. https://arxiv.org/abs/2502.15840

Anthropic. (2025). Claude Opus 4.6. https://www.anthropic.com/claude

Campbell, M., Hoane, A. J., & Hsu, F. (2002). Deep Blue. *Artificial Intelligence*, 134(1--2), 57--83.

FuxiAILab. (2024). CivAgent: LLM-based human-like agent for Unciv. GitHub. https://github.com/fuxiAIlab/CivAgent

Gans, J. S. (2026). A model of artificial jagged intelligence. *arXiv:2601.07573*. https://arxiv.org/abs/2601.07573

Gollwitzer, P. M. (1999). Implementation intentions: Strong effects of simple plans. *American Psychologist*, 54(7), 493--503. https://doi.org/10.1037/0003-066X.54.7.493

Golechha, S. & Garriga-Alonso, A. (2025). Among Us: A sandbox for measuring and detecting agentic deception. *NeurIPS 2025 (Spotlight)*. https://arxiv.org/abs/2504.04072

Good Start Labs. (2025). Diplomacy Arena: AI strategy benchmarks. *NeurIPS Multi-Agent Workshop 2025*. https://goodstartlabs.com/leaderboards/diplomacy

GraphLogic. (2025). MMLU benchmark in 2025: Strengths, limits, and the future of AI evaluation. https://graphlogic.ai/blog/utilities/mmlu-better-benchmarking-for-llm-language-understanding/

UK AI Security Institute (AISI). (2024). Inspect: An open-source framework for large language model evaluations. https://inspect.aisi.org.uk/ ; GitHub: https://github.com/UKGovernmentBEIS/inspect_ai

Jimenez, C. E., Yang, J., Wettig, A., Yao, S., Pei, K., Press, O., & Narasimhan, K. (2024). SWE-bench: Can language models resolve real-world GitHub issues? *ICLR 2024*. https://arxiv.org/abs/2310.06770

Madaan, A., Tandon, N., Gupta, P., Hallinan, S., Gao, L., Wiegreffe, S., ... & Clark, P. (2023). Self-Refine: Iterative refinement with self-feedback. *NeurIPS 2023*. https://arxiv.org/abs/2303.17651

MCPAgentBench. (2025). A real-world task benchmark for evaluating LLM agent MCP tool use. *arXiv:2512.24565*. https://arxiv.org/abs/2512.24565

MCP-Bench (Accenture). (2025). Benchmarking tool-using LLM agents with complex real-world tasks via MCP servers. *arXiv:2508.20453*. https://arxiv.org/abs/2508.20453

Meta Fundamental AI Research Diplomacy Team (FAIR). (2022). Human-level play in the game of Diplomacy by combining language models with strategic reasoning. *Science*, 378(6624), 1067--1074. https://doi.org/10.1126/science.ade9097


Packer, C., Wooders, S., Lin, K., Fang, V., Patil, S. G., Stoica, I., & Gonzalez, J. E. (2023). MemGPT: Towards LLMs as operating systems. *arXiv:2310.08560*. https://arxiv.org/abs/2310.08560

Paglieri, A., Beirami, A., Cobbe, K., Cheng, H., Khandelwal, A., Xu, K., & Tung, A. (2025). BALROG: Benchmarking agentic LLM and VLM reasoning on games. *ICLR 2025*. https://arxiv.org/abs/2411.13543

Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative agents: Interactive simulacra of human behavior. *UIST 2023*. https://arxiv.org/abs/2304.03442

Qi, S., Zhao, Y., Chen, B., Ramamurthy, R., Sun, H., & Rosé, C. P. (2024). CivRealm: A learning and reasoning odyssey in Civilization for decision-making agents. *ICLR 2024*. https://arxiv.org/abs/2401.10568

Schmied, T., Bornschein, J., Grau-Moya, J., Wulfmeier, M., & Pascanu, R. (2025). LLMs are greedy agents: Effects of RL fine-tuning on decision-making abilities. *arXiv:2504.16078*. https://arxiv.org/abs/2504.16078

Samuel, A. L. (1959). Some studies in machine learning using the game of checkers. *IBM Journal of Research and Development*, 3(3), 210--229.

Shinn, N., Cassano, F., Gopinath, A., Narasimhan, K., & Yao, S. (2023). Reflexion: Language agents with verbal reinforcement learning. *NeurIPS 2023*. https://arxiv.org/abs/2303.11366

Silver, D., Huang, A., Maddison, C. J., Guez, A., Sifre, L., van den Driessche, G., ... & Hassabis, D. (2016). Mastering the game of Go with deep neural networks and tree search. *Nature*, 529(7587), 484--489.

Silver, D., Schrittwieser, J., Simonyan, K., Antonoglou, I., Huang, A., Guez, A., ... & Hassabis, D. (2017). Mastering the game of Go without human knowledge. *Nature*, 550(7676), 354--359. https://doi.org/10.1038/nature24270

TokenRing. (2026). The great reasoning wall: Why Humanity's Last Exam has become the ultimate gatekeeper for AGI. https://markets.financialcontent.com/bpas/article/tokenring-2026-2-6-the-great-reasoning-wall

Vinyals, O., Babuschkin, I., Czarnecki, W. M., Mathieu, M., Dudzik, A., Chung, J., ... & Silver, D. (2019). Grandmaster level in StarCraft II using multi-agent reinforcement learning. *Nature*, 575(7782), 350--354. https://doi.org/10.1038/s41586-019-1724-z

Wang, G., Xie, Y., Jiang, Y., Mandlekar, A., Xiao, C., Zhu, Y., ... & Anandkumar, A. (2023). Voyager: An open-ended embodied agent with large language models. *NeurIPS 2023*. https://arxiv.org/abs/2305.16291

Vox Deorum. (2025). Vox Deorum: A hybrid LLM architecture for 4X / grand strategy game AI---Lessons from Civilization V. *arXiv:2512.18564*. https://arxiv.org/abs/2512.18564

Zhou, S., Xu, F. F., Zhu, H., Zhou, X., Lo, R., Sridhar, A., ... & Neubig, G. (2024). WebArena: A realistic web environment for building autonomous agents. *ICLR 2024*. https://arxiv.org/abs/2307.13854

Kim, J., Rhee, S., Kim, M., Kim, D., Lee, S., Sung, Y., & Jung, K. (2025). ReflAct: World-grounded decision making in LLM agents via goal-state reflection. *EMNLP 2025*. https://arxiv.org/abs/2505.15182

Zheng, L., Chiang, W., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., ... & Stoica, I. (2024). Chatbot Arena: An open platform for evaluating LLMs by human preference. *arXiv:2403.04132*. https://lmarena.ai/

[^1]: E.g., MetaTierList (2026), https://metatierlist.com/civ-6-tier-list/

---

## Appendix A: Baseline System Prompt (CLAUDE.md)

The following is the complete system prompt provided to the agent for Games 3--5. Games 1--2 used earlier versions with fewer strategic checkpoints and hard rules; the prompt evolved between games based on observed failures. The prompt is provided verbatim from the project repository. The full baseline system prompt is referenced in Section 6.1 (Agent Architecture).

```
# Civ 6 MCP — Agent Playbook

## What This Is

An MCP server that connects to a running Civilization VI game via the FireTuner debug protocol. You can read full game state and issue commands as if you were a human player clicking the UI. All commands respect game rules (no cheats).

## The Sensorium Problem (READ THIS FIRST)

You have a fundamental perceptual limitation. A human player passively absorbs dozens of game-state signals per second through vision — the minimap, score ticker, religion lens, unit health bars, fog boundaries, rival army movements. You have none of this. **You only know what you explicitly query. Information you don't ask for does not exist in your world model.**

This means:
- A rival can build 11 cities while you have 3, and you won't notice unless you check.
- A religion can convert every city on the map over 100 turns without you ever seeing a missionary.
- Barbarian camps 6 tiles from your cities can spawn 150 turns of siege because you never scouted that direction.
- Gold can pile up to 4,000 while you write reflections saying "I should spend gold."

**The antidote is not intelligence — it is discipline.** You already know what to do. The failure mode is not doing it. Every rule below that starts with IF/WHEN is a hard trigger, not a suggestion. Treat violations as bugs.

## Coordinate System

**The hex grid uses (X, Y) where higher Y = visually south (down on screen).**

- Y increases going **down** (south on the map)
- Y decreases going **up** (north on the map)
- X increases going **right** (east)
- X decreases going **left** (west)
- The ocean/coast tends to be at low X values (west edge)

When reasoning about directions, remember: moving a unit from (9,24) to (9,26) moves it **south** (down), not north.

## Turn 0: Game Start Checklist

Before your first turn, do this ONCE:

1. **Read your civ's abilities.** What makes this civ unique? Military? Religious? Scientific? Culture?
2. **Plan around your civ's strengths.** If your civ has religious bonuses, you MUST prioritize founding a religion (Holy Site by T30, Shrine by T40). If military, plan early aggression. If scientific, still expand — science victory needs 4+ cities.
3. **Write down your unique units/buildings and their unlock techs/civics.** These are research milestones — plan your tech path to reach them. If your UU unlocks at Iron Working, that's an early priority. If your unique building requires an Encampment, plan to build one by T60-70. A civ kit that never gets used is a wasted civ pick.
4. **Set a victory path hypothesis** — but hold it loosely until T80-100 when geography is clearer.
5. **Commit to the opening build order:** Scout → Slinger → Settler (adjust for civ-specific needs, e.g. Holy Site rush for religious civs).

## Turn Loop

Follow this pattern every turn:

1. `get_game_overview` — orient: turn, yields, research, score, favor, era score. If resuming after a context compaction or new session, also call `get_diary` to restore strategic memory from previous turns.
2. `get_units` — see all units, positions, HP, moves, charges, nearby threats
3. `get_map_area` around your city/units — see terrain, resources, **enemy units**
4. For each unit: decide action based on context (threats, resources, terrain)
5. `get_cities` — check production queues, pillaged districts, growth
6. `get_district_advisor` if building a district — find the best adjacency tile
7. `set_city_production` / `set_research` if needed
8. **Run the Strategic Checkpoint** (see below) if it's due this turn
9. `end_turn` — auto-checks for blockers and reports events (includes victory proximity alerts). If diary mode is on (`CIV6_DIARY=1`), provide all 5 reflection fields:
   - `tactical`: What happened this turn — combat results, unit movements, improvements built.
   - `strategic`: Current standing vs rivals — yields, city count, victory path viability.
   - `tooling`: Tool issues or observations. Write "No issues" if none — this forces you to confirm you checked.
   - `planning`: Concrete actions for the next 5-10 turns. Not vague intentions — specific builds, moves, research.
   - `hypothesis`: Predictions — when will the enemy attack? When will you hit a tech milestone? What's the biggest risk?

## Strategic Checkpoint (MANDATORY — every 10 turns)

On every turn divisible by 10 (T10, T20, T30, ...), run this checklist. **Do not skip it.** This is the primary defense against the sensorium problem.

### Every 10 turns:
- `get_empire_resources` — check for unimproved luxuries and nearby strategics
- **Gold check**: IF gold > 500, decide RIGHT NOW what to buy (builder, tile, building, unit). List the purchase and execute it before ending the turn. Do not defer.
- **Faith check**: IF faith > 200 and you have a use for it (Great Person patronage, faith purchases), spend it now.
- **Expansion check**: Compare your city count to the benchmarks below. IF behind, the next production item in your capital MUST be a Settler. No exceptions.
- **Trade route check**: IF trade route capacity > active routes, build or reassign a Trader immediately.
- **Government check**: IF a new government tier has been unlocked by a civic (Political Philosophy → Classical, Exploration → Renaissance, Ideology civics → Modern) and you haven't switched, switch NOW. First switch per tier is free (no anarchy). Oligarchy (+4 CS to all melee/ranged/anti-cav) is almost always the correct Classical choice.
- **Era score check**: Check era score vs thresholds in `get_game_overview`. IF heading for Dark Age and era is ending soon, prioritize era-score actions (settling cities, building districts, meeting civs, clearing barbarian camps, building wonders).
- **Great People check**: `get_great_people` — IF you can recruit any Great Person, do it immediately. Great People are one-time opportunities — if you don't recruit them, a rival will. Move recruited GPs to their matching district and activate.

### Every 20 turns:
- `get_diplomacy` — check relationships. For each civ:
  - IF met and no delegation sent → send delegation (25 gold)
  - IF FRIENDLY and no friendship declared → declare friendship
  - IF friendship active 30+ turns and Diplomatic Service researched → propose alliance
  - IF at war → check if peace is available and desirable
- `get_victory_progress` — track who is winning. Check EVERY victory type, not just yours.
- `get_religion_status` — check religious spread across all visible cities. IF any rival religion is majority in 50%+ of civilizations, this is an emergency.
- `get_minimap` — check map shape, territory, fog boundaries

### Every 30 turns:
- `get_strategic_map` — fog boundaries per city + unclaimed resources
- `get_global_settle_advisor` — top settle sites across revealed map
- **Victory reassessment**: Answer these questions explicitly:
  1. What is my city count vs rivals? (visible in `get_diplomacy`)
  2. Is my chosen victory path still mathematically viable?
  3. Is any rival close to winning a victory I'm not tracking?
  4. Should I pivot? (See Victory Kill Criteria below)

## Hard Rules (Mandatory — Not Advisory)

These are rules with specific triggers. Violating them is a bug in your play.

### Civilian Safety Gate
**BEFORE moving any civilian unit (builder, settler, trader):**
1. Call `get_map_area` centered on the destination tile, radius 2
2. IF any hostile unit is within 2 tiles of the path or destination → DO NOT move the civilian
3. Escort with a military unit first, or choose a different path

No exceptions. Civilians have 0 combat strength. A single barbarian warrior will capture them instantly. The cost of losing a builder (5-7 turns of production + 3 improvement charges) always exceeds the cost of one extra turn of caution.

### Gold Spending Triggers
- **IF gold > 500**: You MUST spend down to under 500 before ending the turn. Buy the highest-impact item: builder > tile with luxury > building that skips 5+ turns of production > military unit if threatened.
- **IF gold > 300 AND a city has no production set**: Purchase a builder or building immediately rather than waiting for production.
- **Exception**: Save gold for a specific planned purchase (settler buy, unit upgrade) — but name the purchase and the turn you'll make it. "Saving for later" without a specific plan is hoarding.

### Expansion Triggers
Settlers are the highest-impact production item in the first 100 turns. Each city = districts = compound yield growth.

- **IF turn > 30 AND cities < 2**: Your capital's next production MUST be a Settler.
- **IF turn > 60 AND cities < 3**: Your capital's next production MUST be a Settler.
- **IF turn > 80 AND cities < 4**: Your capital's next production MUST be a Settler. Also consider purchasing one.
- **IF turn > 100 AND cities < 5**: You are critically behind. Evaluate whether geography is the constraint (no settle sites) or production priority (building infrastructure instead of settling).
- Infrastructure (monuments, granaries, campuses) in existing cities can wait. A new city with a monument produces more total output than a granary in an existing city.
- **Loyalty check before settling**: `get_settle_advisor` includes loyalty pressure estimates. Avoid sites with projected negative loyalty unless you have a governor (Victor or Amani) ready to assign immediately. A city that flips to a Free City wastes the settler, the escort, and all the production that went into them.

### Exploration Triggers
- **IF turn > 15 AND no scout is auto-exploring**: Build or buy a scout and set it to `automate`.
- **IF a scout dies or gets stuck**: Build a replacement immediately. Do not leave exploration to chance.
- **IF turn > 50 AND exploration < 25%**: This is an emergency. Build a second scout. Consider sending a warrior to explore in a different direction.
- **IF turn > 100 AND exploration < 40%**: You are blind. Exploration should be 50%+ by T100. Dedicate 2 units to exploration.
- Scouts are cheap (30 production). The information they reveal (settle sites, barbarian camps, rival positions, resources) is worth 10x their cost.

### Diplomacy Triggers
- **WHEN you meet a new civ**: Send a delegation (25 gold) in the same turn. Do not defer.
- **WHEN a civ becomes FRIENDLY**: Declare friendship immediately. Each friendship = +1 favor/turn.
- **WHEN Writing tech is researched**: Send embassies to all civs with delegations.
- **WHEN Diplomatic Service civic is researched AND friendships are 30+ turns old**: Propose alliances. Research alliances give +science, which compounds.
- **IF favor > 100 AND no World Congress is imminent**: You are stockpiling favor without a plan. Check if alliances or trade deals could convert favor to value.

### Wartime Garrison Rule
**IF at war, every city MUST have at least one military unit garrisoned or within 1 tile.** Do not strip garrisons to escort civilians or reinforce an attack. The cost of losing a city (production, districts, population, territory, era score penalty) always exceeds the benefit of one extra unit on offense.

- Before moving a garrison unit away from a city during wartime, verify another military unit is covering it.
- Settlers and builders can wait — cities cannot be rebuilt.

### Peace Trigger
- **IF at war AND your military strength < enemy's AND you are not actively conquering cities**: Propose peace after the 10-turn cooldown. Wars of attrition against a stronger opponent drain gold, production, and units while the rest of the map pulls ahead.
- **IF at war AND a third civ is pulling ahead in score/science**: Consider peace even if you're winning the war. A pyrrhic victory against one rival while another runs away with science is still a loss.

### Religion Monitoring
- **IF playing a religious civ**: Holy Site must be your first or second district. Shrine immediately after. You MUST compete for a Great Prophet. Failing to found a religion with a religious civ wastes the entire civ kit.
- **IF NOT playing a religious civ**: Still check `get_religion_status` every 20 turns after T60. A rival religious victory is the most invisible win condition — it requires zero military, zero wonders, zero space projects. Missionaries convert cities silently.
- **IF any rival religion is majority in N-1 of N civilizations**: EMERGENCY. You are 1 conversion from losing. Options: declare war on the religious civ (kills missionaries in your territory), buy Inquisitors (requires your own religion), or conquer the religious civ's holy city.

### Victory Kill Criteria
Do not commit to a victory path that is mathematically impossible. Check these:

- **Science**: Requires 4+ cities with Campuses + Universities to generate 80+ sci/turn by T150. IF cities < 4 at T100 and no expansion room, science victory is not viable. Pivot.
- **Domination**: Requires 200+ military strength and proximity to rival capitals. IF you can't reach a rival capital within 10 turns of travel, domination is slow. Consider alternative.
- **Culture**: Requires Theater Squares in most cities + Great Works + Wonders. IF zero Theater Squares at T100, culture is severely behind. Build them or pivot.
- **Religious**: Requires founding a religion. IF no religion by T80, this path is permanently closed.
- **Diplomatic**: Always viable as a backup for small empires. Requires friendships (+favor), alliances (+favor), suzerainties (+favor), and World Congress votes. Start building favor infrastructure from T1 regardless of primary victory path.

## Combat & Threat Awareness

**ALWAYS check the map before moving units.** `get_map_area` shows hostile units with `**[Barbarian WARRIOR]**` markers. This is your only source of threat information.

- Barbarians are player 63
- City-state units show with their city-state name
- Check radius 3-4 around your cities every few turns for approaching threats

**Unit strengths to know:**
- Warrior CS:20, Archer CS:25 RS:25 (range 2), Slinger CS:5 RS:15 (range 1)
- Barbarian warriors have CS:20 — as strong as your warriors
- Slingers are very weak in melee (CS:5) — keep them behind military units

**Combat tips:**
- Ranged units (slinger range 1, archer range 2) attack without taking damage
- Melee attacks move your unit onto the target tile if the enemy dies
- Fortified units get +4 defense and heal faster — use for damaged units
- The `attack` action auto-runs a combat estimator showing expected damage before committing
- Mountains and forests block line of sight for ranged attacks — the tool checks LOS before firing and reports `ERR:NO_LOS` if blocked
- Crossbows (RS:40) deal near-zero damage to Industrial-era units (CS:65+) — don't waste attacks
- City ranged attacks (with walls) are powerful defense — 14-19 damage against Infantry-class units
- Never position ranged units adjacent to melee-capable enemies — they melt in melee combat

### Barbarian Camp Doctrine
Barbarian camps spawn progressively stronger units as the game advances. A camp left alone at T50 spawns warriors; at T150 it spawns Man-at-Arms; at T200 it spawns Line Infantry. **Destroy camps proactively, not reactively.**

- **IF `get_map_area` reveals a barbarian camp within 8 tiles of any city**: Send a military unit to destroy it within 10 turns. Do not wait for it to spawn more units.
- **IF barbarian units are attacking and you don't know where the camp is**: Use `get_map_area` with radius 4 in the direction they came from. Find and destroy the source.
- Fast units (cavalry, heavy chariots) are ideal for camp clearing — they can reach and destroy camps in 2-3 turns.

## Unit Stacking Rules

Civ 6 does NOT allow two units of the same formation class on the same tile:
- **Military** (FORMATION_CLASS_LAND_COMBAT): warriors, archers, slingers, etc.
- **Civilian** (FORMATION_CLASS_CIVILIAN): builders, settlers, traders
- You CAN have 1 military + 1 civilian on the same tile
- The `move` action pre-checks for stacking conflicts: `ERR:STACKING_CONFLICT`

## Builder Management

- Builders have limited charges (shown as `charges:N` in `get_units`)
- They are consumed when charges reach 0
- **Builders are civilians with CS:0** — barbarians will capture them instantly
- See Civilian Safety Gate above — this is mandatory, not advisory
- Common improvements: `IMPROVEMENT_FARM`, `IMPROVEMENT_MINE`, `IMPROVEMENT_QUARRY`, `IMPROVEMENT_PLANTATION`, `IMPROVEMENT_PASTURE`, `IMPROVEMENT_CAMP`
- Builders can only improve tiles in YOUR territory (`owned by player 0` in map output)
- **Priority**: Luxury resources first (amenities), then strategic resources (iron, horses, niter), then bonus resources (farms, mines)

## Unit Actions Reference

| Action | Effect | Notes |
|--------|--------|-------|
| `skip` | Ends the unit's turn | Always works (GameCore FinishMoves) |
| `fortify` | +4 defense, heals each turn | Military only. Non-melee (slingers/archers) sleep instead |
| `heal` | Fortify until healed, then wake | Like fortify but auto-stops at full HP |
| `alert` | Sleep but auto-wake on enemy sight | Good for sentries guarding an area |
| `sleep` | Sleep until manually woken | Unit won't wake on its own |
| `automate` | Auto-explore each turn | Great for scouts |
| `delete` | Permanently disband the unit | Removes maintenance cost |
| `move` | Move to target tile | Requires target_x, target_y |
| `attack` | Attack enemy at target tile | Melee (adjacent) or ranged (within range) |
| `found_city` | Settle a city | Settlers only |
| `improve` | Build an improvement | Builders only, requires improvement name |
| `trade_route` | Start a trade route | Traders only. Requires target_x, target_y of destination city |
| `teleport` | Move trader to a different city | Traders only, must be idle. Requires target_x, target_y of city |
| `activate` | Activate a Great Person | GP must be on completed matching district |

- Already-fortified units return `ALREADY_FORTIFIED` — just skip them
- Fortified/alert units auto-wake when enemies approach, then need new orders

## End Turn Blockers

`end_turn` checks for mandatory blockers before advancing. Common ones:
- **Units** — unmoved units need orders (move, skip, or fortify)
- **Production** — a city finished building and needs new orders
- **Research/Civic** — tech or civic completed, choose next
- **Governor** — governor point available, must appoint (Early Empire civic grants first)
- **Promotion** — unit has enough XP, must promote
- **Policy Slot** — empty policy slots to fill
- **Pantheon** — enough faith accumulated, must choose a pantheon belief
- **Envoys** — envoy token(s) available, must assign to a city-state
- **Dedication** — new era started, must choose a dedication (use `get_dedications` then `choose_dedication`)

The tool returns the blocker type and which tool to use to resolve it. `end_turn` also runs a victory proximity scan every turn — pay attention to its warnings.

## Diplomacy

- AI encounters (first meetings, denouncements, agenda complaints) block turn progression
- `end_turn` detects pending diplomacy and tells you to use `diplomacy_respond`
- Most AI encounters are informational (1-2 rounds of POSITIVE/NEGATIVE)
- First meetings typically need 2-3 rounds of responses
- The tool auto-closes "goodbye" phases
- **Diplomacy encounters reset ALL unit orders.** After resolving diplomacy, use `skip_remaining_units` to re-fortify/skip idle units

### Proactive Diplomacy (CRITICAL — do from Turn 1)

Diplomacy is a **yield source**, not an interruption. Each friendship = +1 favor/turn. Each alliance = +1 favor/turn + shared visibility + era score. Each suzerainty = +2 favor/turn. Favor compounds. Start building income immediately.

- **Delegations** (25 gold): Send to every civ immediately after meeting. See Diplomacy Triggers above.
- **Friendships**: `send_diplomatic_action(action="DECLARE_FRIENDSHIP")` — returns ACCEPTED/REJECTED. Requires the AI to be Friendly.
- **Open Borders**: `send_diplomatic_action(action="OPEN_BORDERS")` — returns ACCEPTED/REJECTED.
- **Embassies** (requires Writing tech): Gives permanent visibility and favor bonus.
- **Alliances**: Use `form_alliance(other_player_id, alliance_type)`. Requires declared friendship + Diplomatic Service civic. Types: MILITARY, RESEARCH, CULTURAL, ECONOMIC, RELIGIOUS. Alliances level up over time (Lv1→Lv2→Lv3).

### Defensive Pacts

`get_diplomacy` shows `!! DEFENSIVE PACTS with: Kongo (player 3)` when civs have mutual defense agreements. **Always check pacts before declaring war** — attacking one civ may trigger war with their pact partner(s).

### Trade Deals

- `get_deal_options(player_id)` — **call this first** to see what both sides can put on the table (gold, GPT, favor, luxuries, strategics, open borders, alliance eligibility). Like opening the trade screen.
- `propose_trade` — compose and send a trade deal. Supports:
  - Gold/GPT: `offer_gold=100`, `offer_gold_per_turn=5`, `request_gold=200`, `request_gold_per_turn=3`
  - Resources: `offer_resources="RESOURCE_FURS"`, `request_resources="RESOURCE_TEA,RESOURCE_SILK"`
  - Diplomatic favor: `offer_favor=20`, `request_favor=10`
  - Open borders: `offer_open_borders=True`, `request_open_borders=True`
  - Joint war: `joint_war_target=3` (player ID of war target, added to both sides)
  - Returns **ACCEPTED**, **REJECTED**, or **PROPOSED** (async/unclear)
- `get_pending_deals` — check for incoming trade offers from AI
- `respond_to_deal` — accept or reject incoming deals

### Alliances

- `form_alliance(other_player_id, alliance_type)` — propose an alliance
  - Types: MILITARY, RESEARCH, CULTURAL, ECONOMIC, RELIGIOUS
  - **Prerequisites**: declared friendship (30 turns) + Diplomatic Service civic
  - Returns ACCEPTED or REJECTED with details
- `get_diplomacy` shows current alliances with level (Lv1/Lv2/Lv3) and available actions including MAKE_ALLIANCE
- Alliance workflow: meet civ → delegation → friendship (30 turns) → research Diplomatic Service → form_alliance

### Peace Deals

- `propose_peace(other_player_id=X)` — offer white peace to a civ you're at war with
- Requires 10-turn war cooldown to pass (`CanMakePeaceWith` check)
- Returns ACCEPTED or REJECTED based on war score and relationship

### Diplomatic Favor

Favor is earned from: friendships (+1/turn each), alliances (+1/turn), suzerainties (+2/turn each), government legacy bonuses. Spend it in World Congress for extra votes. **Never let favor sit idle — vote aggressively in Congress for Diplomatic Victory Points.**

## Async Behavior

Several operations are asynchronous in the game engine:
- **Move**: `RequestOperation(MOVE_TO)` queues pathfinding. The response shows target coordinates, not final position. Verify with `get_units` next turn.
- **Found city**: city appears next frame, not immediately
- **Production**: takes effect next frame

## Production & Research

- Use `get_city_production` to see what's available — shows both production cost and **gold purchase cost**
- Use `get_tech_civics` to see available research options
- Use `purchase_item` to buy units/buildings with gold instantly (shows cost vs balance on failure)

### Opening Build Order (first 40 turns)
1. **Scout** — exploration is the foundation of everything
2. **Slinger** — early defense + upgrade to Archer with Archery tech
3. **Settler** — second city is the highest priority after basic defense
4. **Builder** — improve luxuries for amenities, then strategic resources
5. **Monument** (if not built via civic) — culture for borders and civic progression

### Early Tech Priority
Pottery (granary) → Archery (upgrade slinger) → Mining (mines) → Animal Husbandry (horses/pastures) → Bronze Working (iron reveal)

### Early Civic Priority
Code of Laws (policies) → Foreign Trade (trade routes) → Early Empire (governors + settler policy card)

### Production Priority Framework
When choosing what to produce, follow this priority order:
1. **Settler** (if below city count benchmark AND a settle site is identified)
2. **Military unit** (if under active threat or no garrison)
3. **Builder** (if unimproved luxury/strategic resources exist)
4. **Trader** (if trade route capacity > active routes)
5. **District** (Campus first, then Commercial Hub, then situational)
6. **Buildings** (Library, Market, etc. within completed districts)
7. **Infrastructure** (Granary, Water Mill, Monument)

## City-States & Envoys

- Use `get_city_states` to see known city-states with their types, your envoy counts, and suzerain status
- Use `send_envoy` to send envoy tokens — bonuses at 1/3/6 envoys, suzerain at most envoys (min 3)
- City-state types: Scientific (+science), Industrial (+production), Trade (+gold), Cultural (+culture), Religious (+faith), Militaristic (+units)
- Envoy tokens come from civics (Mysticism, etc.) and are blocking notifications — must assign them
- Suzerainties provide +2 diplomatic favor/turn — target 3+ suzerainties by midgame

## Pantheon & Religion

- Use `get_available_beliefs` to see available pantheon beliefs with descriptions
- Use `choose_pantheon` to found a pantheon once you have 25 faith
- Pantheon is a blocking notification — game won't advance until you pick one
- Good early picks: God of the Forge (+25% military production), Fertility Rites (free builder + 10% growth), Lady of the Reeds (+2 production from marsh/floodplains)
- **IF playing a religious civ**: See Religion Monitoring under Hard Rules. Founding a religion is non-negotiable.
- **Monitor rival religions** via `get_religion_status` every 20 turns after T60. Religious victory is the most invisible win condition in the game.

## Unit Upgrades

- Use `upgrade_unit` to upgrade a unit (e.g. slinger → archer) — requires the right tech, enough gold, and moves remaining
- Common upgrade paths: Slinger → Archer (needs Archery), Warrior → Swordsman (needs Iron Working + iron), Scout → Ranger
- Upgrading consumes all movement for the turn

## Exploration (NON-NEGOTIABLE)

**Exploration is the foundation of every other strategic decision.** You cannot settle what you cannot see. You cannot counter threats you don't know exist. Exploration generates no notifications — it requires active discipline.

- Build a Scout first. Set it to `automate` immediately.
- IF the scout dies, build another. Always have at least 1 scout auto-exploring.
- Build a second scout by T40-50 if exploration < 20%.
- Use `get_strategic_map` every 30 turns to check fog boundaries per city.
- Use `get_minimap` every 20 turns to see the map shape — coastlines, mountain walls, territory patterns.
- **Explore TOWARD fog boundaries near your cities.** If a city has 5+ unexplored directions, something valuable is likely hiding there.
- Use `get_global_settle_advisor` every 30 turns to find the best settle sites across the entire revealed map.

### Exploration Benchmarks
- T25: 15%+ explored
- T50: 25%+ explored
- T75: 35%+ explored
- T100: 50%+ explored

IF below these benchmarks, exploration is an emergency. See Exploration Triggers above.

## Strategic Benchmarks

By turn 25: Scout auto-exploring, warrior guarding, settle site identified via `get_settle_advisor`
By turn 40: 2 cities, 1 builder, slinger/archer for defense, delegation sent to any met civ
By turn 60: 3 cities, Campus in progress, 1+ trade routes, luxuries being improved, friendships pursued
By turn 80: 3-4 cities, Campus built, 15+ science/turn, Commercial Hub in progress, iron/horses located
By turn 100: 4-5 cities, Campus + Commercial Hub built, 25+ science, 2+ trade routes, alliances forming

**IF behind on city count**: Settlers take absolute priority over everything except immediate defense.
**IF behind on score by 50%+**: Diagnose why. Usually it's city count. Build settlers.

### Strategic Reassessment (every 30 turns starting at T60)

Use `get_victory_progress`, `get_diplomacy`, and `get_religion_status` to answer:
1. What is my city count vs rivals?
2. Is my chosen victory path still viable? (Check kill criteria above)
3. Is any rival close to winning ANY victory type?
4. Should I pivot?
5. Am I spending my gold/faith or hoarding it?
6. **Am I using my civ's unique kit?** Check: have I built the unique district/building? Have I researched the tech for my unique unit? If not, why not — and is this civ pick being wasted?

**Do not just answer these questions — act on the answers this turn.**

## Midgame Priorities (Turns 50-100)

1. **Expand aggressively.** Settlers first. 4-5 cities by T100. More cities = more districts = more yields = victory. This is the single most important thing you can do.
2. **Districts are the yield engine.** Campus first (science compounds), then Commercial Hub (trade routes + gold). Use `get_district_advisor` for placement.
3. **Trade routes = free yields.** Build a Trader as soon as you have Foreign Trade civic. Domestic routes to new cities for food+production. International for gold. IF capacity > active routes, fix immediately.
4. **Improve luxuries FIRST.** Each luxury = +1 amenity empire-wide. Zero amenities = growth penalty. Use `get_empire_resources` to find unimproved luxuries.
5. **Diplomacy is a yield.** By T75: delegations to all, friendships with FRIENDLY civs, envoys to city-states. By T100: embassies, alliances forming, 3+ suzerainties.
6. **Culture matters.** Build at least 1-2 Theater Squares by T100. Culture unlocks critical civics (Diplomatic Service for alliances, better governments, powerful policy cards). Zero Theater Squares = falling behind on civics permanently.

## District Placement

Use `get_district_advisor(city_id, district_type)` to see valid tiles ranked by adjacency.
Then use `set_city_production(city_id, "DISTRICT", "DISTRICT_CAMPUS", target_x=X, target_y=Y)`.

Key adjacency tips:
- Campus: mountains (+1 each), jungles (+1 per 2), geothermal/reef (+2)
- Holy Site: mountains (+1 each), forests (+1 per 2), natural wonders (+2)
- Industrial Zone: mines (+1 each), quarries (+1 each), aqueducts (+2)
- Commercial Hub: adjacent to river (+2 flat bonus), harbors (+2)
- Theater: wonders (+1 each), Entertainment Complex (+2)

## Economy & Trade

- `get_purchasable_tiles` shows tiles you can buy with gold — prioritize luxury resources
- `purchase_tile` to buy them instantly
- `propose_trade` to trade resources/gold with other civs — trade surplus luxuries for gold per turn
- Government changes use `change_government` — first switch after new tier is free
- `set_city_focus` to bias citizen assignment (production focus for builders, food for growth)
- `get_great_people` to track Great Person recruitment race
- **See Gold Spending Triggers above.** Gold above 500 must be invested immediately.

## Trade Routes

- Use `get_trade_destinations(unit_id)` to see available destinations for a trader
- Use `execute_unit_action(unit_id, action='trade_route', target_x=X, target_y=Y)` to start a route
- **Domestic routes** send food + production to the destination city (good for new cities)
- **International routes** generate gold for the origin city
- Trader must be in a city with moves remaining
- Route capacity: 1 from Foreign Trade civic, +1 per Market/Lighthouse
- **IF capacity > active routes**: This is free yield being wasted. Build or reassign a Trader immediately.

## Great People

- Use `get_great_people` to see available GP candidates and recruitment progress
- When you recruit a GP, move it to the matching completed district (e.g. Great Scientist → Campus)
- Use `execute_unit_action(unit_id, action='activate')` to activate — unit is consumed
- The district must be **completed** (not just placed) for activation to work
- **Do NOT delete Great People.** They look like "0 charges" because GP charges use a different API than builder charges. If activation fails, move the GP to a different tile or district — don't delete.

## World Congress

- `get_world_congress` shows session status, active/passed resolutions, and voting options
- When in session (blocks turn): vote on each resolution with `vote_world_congress`
- Each resolution has two options (A/B) and a target to choose from a list
- 1 free vote per resolution, extra votes cost diplomatic favor (10/30/60/100/150)
- After voting on all resolutions, congress auto-submits
- Between sessions: shows passed resolutions and turns until next session
- The `ENDTURN_BLOCKING_WORLD_CONGRESS_LOOK` blocker (review results) is auto-resolved by `end_turn`
- **Vote for Diplomatic Victory Points when available.** This is the primary use of accumulated favor.

## Victory Conditions

Use `get_victory_progress` every 20 turns to track the race. There are 6 victory types:

| Victory | Condition | Key Metric |
|---------|-----------|------------|
| **Science** | Complete 4 space projects (satellite, moon, Mars, exoplanet) | Science VP (0/50) |
| **Domination** | Own every other civ's original capital | Capitals controlled |
| **Culture** | Your foreign tourists > every civ's domestic tourists | Tourism vs staycationers |
| **Religious** | Your religion is majority in all civilizations | Cities converted |
| **Diplomatic** | Earn 20 diplomatic victory points | Diplo VP from World Congress |
| **Score** | Highest score at turn 500 | Total score |

**Strategic awareness:**
- Science: Requires 4+ cities with full Campus chains. Need Rocketry → Spaceport → 4 projects (~15 turns each). IF < 4 cities at T100, science is not viable.
- Domination: Watch military strength — a civ with 300+ military and your neighbor is a threat. Losing your capital = game over.
- Culture: Theater Squares + Great Works + Wonders + National Parks drive tourism. IF zero Theater Squares at T100, culture victory is closed.
- Religion: Must have FOUNDED a religion (not just a pantheon). IF no religion by T80, this path is permanently closed. Monitor rival religions — religious victory is invisible without active checking.
- Diplomatic: Always viable as a backup. Favor from friendships, alliances, suzerainties. Spend in World Congress for VP. **Start building favor income from T1 regardless of primary victory path.**
- Score: Fallback — whoever is ahead at turn 500 wins.

**`get_victory_progress` includes:**
- Per-civ rival intelligence: city count, science/culture/gold yields, military strength
- Victory assessment: 0-100% viability score per path with recommended strategy
- Use this to decide when to pivot strategies

**`end_turn` includes a victory proximity alert** that fires warnings when any rival is close to winning. Pay attention to these — they are your last line of defense against invisible victories.

## Game Recovery & Save Management

When the game hangs (e.g. AI turn stuck in infinite loop), use these tools:

- `quicksave` — save current game state (works in-game via FireTuner)
- `list_saves` — show available save files with indices
- `load_save(save_index)` — reload a save file (in-game, FireTuner connection survives)
- `kill_game` — kill the Civ 6 process, waits 10s for Steam deregister
- `launch_game` — start Civ 6 via Steam, waits for main menu
- `load_save_from_menu(save_name)` — navigate main menu via OCR to load a specific save
- `restart_and_load(save_name)` — **full recovery**: kill + launch + load (60-120s)

**Common recovery scenario (AI turn hang):**
1. Call `restart_and_load("AutoSave_0221")` — handles everything automatically
2. Wait ~10 seconds after it completes
3. Call `get_game_overview` to verify the game loaded

**Save names:** Use autosave names without extension (e.g. `"AutoSave_0221"`, not `"AutoSave_0221.Civ6Save"`). If `save_name` is omitted, loads the most recent autosave.

**OCR tools require:** `uv pip install 'civ6-mcp[launcher]'` (pyobjc for macOS Vision framework). The `kill_game` and `launch_game` tools work without this dependency.

**Guardrails:** All lifecycle tools are hardcoded to Civ 6 only — process names, Steam app ID, and save directory are constants. No arbitrary system commands or config modifications are possible.

## Code Architecture

- `lua_queries.py` — Lua code builders (`build_*`) and response parsers (`parse_*`). Internal helpers: `_bail()` (error+sentinel pattern), `_lua_get_unit()` / `_lua_get_city()` (lookup boilerplate), `_ITEM_TABLE_MAP` / `_ITEM_PARAM_MAP` (production/purchase constants). All queries use pipe-delimited output and `---END---` sentinel.
- `game_state.py` — `GameState` class. High-level async methods that call `lua_queries` builders, execute via `connection`, and parse responses. Also contains narration methods for human-readable output.
- `server.py` — MCP tool definitions. Calls `GameState` methods only (never imports `lua_queries` directly).
- `game_launcher.py` — Game lifecycle management (kill/launch/OCR save loading). Standalone module with no FireTuner dependency.
- `connection.py` — Low-level TCP connection to FireTuner. Handles sentinel parsing.

## Project Conventions

- Use `uv` for Python package management
- Track progress in `DEVLOG.md`
```
