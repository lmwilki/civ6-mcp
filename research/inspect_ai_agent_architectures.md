# Inspect AI Agent Architectures Research

**Research Date**: 2026-02-10
**Framework**: Inspect AI (UK AISI)
**Purpose**: Understanding agent architecture support for Civilization VI strategic benchmark

---

## Executive Summary

Inspect AI provides **native support for single agents and multi-agent coordinator patterns** through built-in APIs, but **lacks explicit swarm/autonomous coordination primitives**. Custom agent architectures are fully supported via the `@agent` decorator and custom solver implementation. External framework integration (LangChain, OpenAI Agents SDK, Pydantic AI) is available via agent bridges.

**Key Findings**:
- ✅ Single agent (ReAct) is mature and well-documented
- ✅ Multi-agent coordinator via `handoff()` is native and production-ready
- ⚠️ Swarm patterns require custom implementation (no built-in primitives)
- ✅ Custom solvers/agents fully supported via decorators
- ✅ Agent bridges enable external framework integration

---

## 1. Single Agent: ReAct Pattern

### Overview
The `react()` agent is the primary built-in implementation, based on the ReAct (Reasoning + Acting) paper. It implements a tool-calling loop until the model explicitly submits an answer.

### API Signature

```python
from inspect_ai.agent import react

@agent
def react(
    *,
    name: str | None = None,
    description: str | None = None,
    prompt: str | AgentPrompt | None = AgentPrompt(),
    tools: Sequence[Tool | ToolDef | ToolSource] | None = None,
    model: str | Model | Agent | None = None,
    attempts: int | AgentAttempts = 1,
    submit: AgentSubmit | bool | None = None,
    on_continue: str | AgentContinue | None = None,
    retry_refusals: int | None = None,
    compaction: CompactionStrategy | None = None,
    truncation: Literal["auto", "disabled"] | MessageFilter = "disabled",
) -> Agent
```

### How It Works

1. **Tool Loop Execution**: Runs a loop where the model calls tools sequentially
2. **Explicit Submission**: Uses a special `submit()` tool to signal completion
3. **Continuation Logic**: If the model stops calling tools without submitting, continuation messages prompt it to proceed
4. **Multiple Attempts**: When `attempts > 1`, submissions are evaluated and the model receives feedback for retries

### Internal Behavior

```python
# Simplified internal loop pattern
state.output = await get_model().generate(
    input=state.messages,
    tools=tools,
)
state.messages.append(output.message)

if output.message.tool_calls:
    messages, state.output = await execute_tools(message, tools)
    state.messages.extend(messages)
else:
    break  # or continue based on on_continue callback
```

### Configuration Examples

**Basic Setup**:
```python
agent = react(
    description="Expert cybersecurity agent",
    prompt="You are a tenacious researcher skilled at web browsing and analysis.",
    tools=[bash_session(), text_editor(), web_search()],
    attempts=3
)
```

**With Custom Prompt Components**:
```python
agent = react(
    prompt=AgentPrompt(
        instructions=CUSTOM_INSTRUCTIONS,
        assistant_prompt="You have access to specialized tools...",
        handoff_prompt=None  # Suppress default handoff prompt
    ),
    tools=[bash(), python()],
    compaction=CompactionEdit(keep_tool_uses=3)
)
```

### Tool Access

- Tools are provided to the model as function definitions
- Model generates tool calls as structured outputs
- Inspect automatically executes tools and returns results
- Built-in tools include: `bash_session()`, `python()`, `text_editor()`, `web_search()`, `web_browser()`, `think()`

### Integration with Tasks

```python
from inspect_ai import Task, task
from inspect_ai.solver import generate
from inspect_ai.agent import react

@task
def cybersecurity_eval():
    return Task(
        dataset=json_dataset("security_guide.json"),
        solver=react(
            prompt="You are a cybersecurity expert...",
            tools=[bash(timeout=180), python(timeout=180)],
            attempts=3
        ),
        scorer=model_graded_fact(),
        sandbox="docker"
    )
```

---

## 2. Multi-Agent / Coordinator Pattern

### Overview
Inspect AI provides **native multi-agent support** through three composition patterns:
1. **Supervisor with handoffs** (recommended) - top-level agent delegates to specialists
2. **Explicit workflows** - agents invoked sequentially via `run()`
3. **Agent as tool** - agents wrapped with `as_tool()` for string-based delegation

### Handoff API (Recommended Pattern)

The `handoff()` function creates a tool that enables model-initiated delegation to specialist agents while preserving conversation context.

#### API Signature

```python
from inspect_ai.agent import handoff

def handoff(
    agent: Agent,
    description: str | None = None,
    input_filter: MessageFilter | None = None,
    output_filter: MessageFilter | None = content_only,
    tool_name: str | None = None,
    limits: list[Limit] = [],
    **agent_kwargs: Any,
) -> Tool
```

#### How It Works

1. **Tool Presentation**: Handoffs appear as tools with `transfer_to_` prefix (e.g., `transfer_to_web_surfer`)
2. **Context Sharing**: Target agent receives full conversation history (filtered via `input_filter`)
3. **Message Appending**: Target agent can append to shared message history
4. **Automatic Prompting**: Model is prompted to understand it's in a multi-agent system

#### Complete Example

```python
from inspect_ai.agent import react, handoff
from inspect_ai.tool import web_search

# Define specialist agents
web_surfer = react(
    name="web_surfer",
    description="Web research assistant expert at using a browser to find information",
    prompt="You are a tenacious web researcher. Use the browser to find accurate answers.",
    tools=[web_search(), web_browser()]
)

code_analyst = react(
    name="code_analyst",
    description="Code analysis expert who can read and understand source code",
    prompt="You are an expert code analyst. Examine code carefully for bugs and vulnerabilities.",
    tools=[bash_session(), text_editor()]
)

# Define supervisor with handoffs
supervisor = react(
    name="supervisor",
    prompt="You are a coordinator agent that delegates to specialists.",
    tools=[
        addition(),  # Regular tools
        handoff(web_surfer),
        handoff(code_analyst)
    ]
)
```

#### Message Filtering

**Default Behavior**: Target agents see global message history (excluding system messages) processed through `content_only()` filter, which removes system messages and tool calls.

**Built-in Filters**:
```python
from inspect_ai.agent import remove_tools, last_message, content_only

# Only pass recent context
handoff(web_surfer, input_filter=last_message)

# Strip all tool calls from history
handoff(web_surfer, input_filter=remove_tools)

# Default: clean output (no system msgs or tool calls)
handoff(web_surfer, output_filter=content_only)
```

**Custom Filter**:
```python
async def my_filter(messages: list[ChatMessage]) -> list[ChatMessage]:
    # Custom logic to transform message history
    return [msg for msg in messages if msg.role != "system"]

handoff(web_surfer, input_filter=my_filter)
```

### Explicit Workflow Pattern

Use `run()` for deterministic, sequential agent orchestration:

```python
from inspect_ai.agent import Agent, AgentState, agent, run

@agent
def research_pipeline() -> Agent:
    async def execute(state: AgentState) -> AgentState:
        # Sequential stages
        state = await run(research_planner(), state)
        state = await run(research_searcher(), state)
        state = await run(research_writer(), state)
        return state
    return execute
```

#### Parallel Workflow Execution

```python
from asyncio import gather

@agent
def parallel_research() -> Agent:
    async def execute(state: AgentState) -> AgentState:
        # Run planners in parallel
        plans = await gather(
            run(web_search_planner(), state),
            run(experiment_planner(), state),
            run(document_planner(), state)
        )

        # Merge results (custom logic)
        state.messages.extend(merge_plan_outputs(plans))

        # Execute synthesis
        state = await run(research_synthesizer(), state)
        return state
    return execute
```

**Important**: `run()` creates state copies automatically to prevent conflicts during parallel execution.

### Agent as Tool Pattern

Convert agents to standard tools with string input/output:

```python
from inspect_ai.agent import as_tool, react

calculator_agent = react(
    name="calculator",
    description="Performs complex mathematical calculations",
    tools=[python()]
)

supervisor = react(
    prompt="You can delegate math problems to a specialist.",
    tools=[
        web_search(),
        as_tool(calculator_agent)  # String-based delegation
    ]
)
```

**Key Difference**: `as_tool()` provides string-in/string-out interface, while `handoff()` shares full conversation context.

### Coordinator Architecture Decision Guide

| Pattern | Use When | Pros | Cons |
|---------|----------|------|------|
| **handoff()** | Model decides delegation dynamically | Flexible, context-aware | Less deterministic |
| **Workflow (run())** | Known sequence of stages | Predictable, debuggable | Rigid structure |
| **as_tool()** | Agent needs isolated context | Simple interface | No conversation sharing |

---

## 3. Swarm Patterns (Custom Implementation Required)

### Native Support Assessment

**Inspect AI does NOT provide built-in swarm primitives** such as:
- ❌ Autonomous agent spawning
- ❌ Decentralized coordination
- ❌ Emergent behavior frameworks
- ❌ Agent-to-agent negotiation protocols
- ❌ Dynamic agent pool management

### What IS Supported

✅ **Parallel Agent Execution**: Via `asyncio.gather()` and `run()`
✅ **State Forking**: Custom agents can fork `AgentState` for subtasks
✅ **Concurrent API Calls**: Automatic connection pooling and throttling

### Implementation Approach for Swarm

You can implement swarm-like patterns using custom agents:

```python
from inspect_ai.agent import agent, run, Agent, AgentState
from asyncio import gather
from typing import Sequence

@agent
def swarm_coordinator(
    worker_agents: Sequence[Agent],
    max_parallel: int = 5
) -> Agent:
    async def execute(state: AgentState) -> AgentState:
        # Divide work across agents
        tasks = partition_work(state, worker_agents)

        # Execute in batches for controlled parallelism
        results = []
        for batch in batched(tasks, max_parallel):
            batch_results = await gather(*[
                run(agent, task_state)
                for agent, task_state in batch
            ])
            results.extend(batch_results)

        # Aggregate results
        state = aggregate_agent_outputs(state, results)
        return state

    return execute
```

### Parallelism with asyncio.gather()

**Official Pattern from Inspect AI**:

```python
from inspect_ai.model import get_model
import asyncio

# Parallel model calls (automatically throttled by max_connections)
models = [get_model("openai/gpt-4"), get_model("anthropic/claude-3-opus"), ...]
graders = [model.generate(prompt) for model in models]  # Not awaited!
grader_outputs = await asyncio.gather(*graders)  # Await all at once
```

**Important Notes**:
- Inspect's internal `max_connections` throttles requests automatically
- No need to manually limit parallel operations
- Works with both model API calls and tool execution
- Use AnyIO library instead of asyncio directly for best compatibility

### Limitations for True Swarms

1. **No Agent Discovery**: Agents can't dynamically discover each other
2. **No Message Passing**: No pub/sub or broadcast primitives
3. **No Consensus Protocols**: Agents can't negotiate or vote
4. **No Emergent Coordination**: Must be explicitly orchestrated

### Recommendation for Swarm Track

If you need true swarm behavior, consider:
1. **Custom agent implementation** using the `@agent` decorator with internal coordination logic
2. **External framework bridge** (see Section 5) for frameworks like CrewAI or AutoGen
3. **Hybrid approach**: Inspect for evaluation harness, external system for swarm coordination

---

## 4. Custom Solver / Agent Implementation

### Overview

Inspect AI provides two layers of customization:
1. **Custom Solvers** - Transform `TaskState` objects (lower-level)
2. **Custom Agents** - Transform `AgentState` objects (higher-level)

Both use decorators and are fully integrated with the evaluation framework.

### Custom Solver API

#### Protocol Definition

```python
from inspect_ai.solver import Solver, TaskState, Generate

# Solver protocol: async function transforming TaskState
Solver = Callable[[TaskState, Generate], Awaitable[TaskState]]
```

#### @solver Decorator

```python
from inspect_ai.solver import solver

@solver
def my_custom_solver(template: str, model_name: str = "openai/gpt-4"):
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        # Access task state
        prompt = state.user_prompt.text
        metadata = state.metadata

        # Transform state
        state.messages.append(ChatMessage(role="system", content=template))

        # Call model
        state.output = await generate(state.messages)

        # Optionally set scores directly
        if state.output.completion == "expected":
            state.scores = {"correct": Score(value=True)}

        # Signal completion
        state.completed = True

        return state

    return solve
```

#### Key TaskState Members

| Member | Type | Purpose |
|--------|------|---------|
| `messages` | `list[ChatMessage]` | Full conversation history |
| `user_prompt` | `ChatMessageUser` | First user message (convenience property) |
| `output` | `ModelOutput` | Final model output from `generate()` |
| `scores` | `dict[str, Score]` | Scores set by solver directly |
| `completed` | `bool` | Early termination signal |
| `metadata` | `dict` | Custom task metadata |

#### Usage in Tasks

```python
@task
def custom_eval():
    return Task(
        dataset=json_dataset("data.json"),
        solver=my_custom_solver(
            template="You are an expert...",
            model_name="anthropic/claude-3-opus"
        ),
        scorer=model_graded_fact()
    )
```

#### Command-Line Override

```bash
# Use default solver
inspect eval task.py

# Override with custom solver
inspect eval task.py --solver my_custom_solver

# Pass solver parameters
inspect eval task.py --solver my_custom_solver -S template="custom.txt" -S model_name="openai/gpt-4"

# Via YAML config
inspect eval task.py --task-config config.yaml
```

**config.yaml**:
```yaml
solver:
  name: my_custom_solver
  params:
    template: "custom_instructions.txt"
    model_name: "anthropic/claude-3-opus"
```

### Custom Agent API

#### Agent Protocol

```python
from inspect_ai.agent import Agent, AgentState

# Agent protocol: async function transforming AgentState
class Agent(Protocol):
    async def __call__(
        self,
        state: AgentState,
        *args: Any,
        **kwargs: Any,
    ) -> AgentState
```

#### AgentState (Minimal State)

```python
from inspect_ai.agent import AgentState
from inspect_ai.model import ChatMessage, ModelOutput

class AgentState:
    messages: list[ChatMessage]  # Conversation history
    output: ModelOutput          # Last model output
```

**Design Philosophy**: AgentState is intentionally minimal to enable flexible usage (as tools, in multi-agent systems, or as standalone solvers).

#### @agent Decorator

```python
from inspect_ai.agent import agent, Agent, AgentState
from inspect_ai.model import get_model
from inspect_ai.tool import Tool
from typing import Sequence

@agent
def custom_react_agent(
    name: str = "custom_agent",
    tools: Sequence[Tool] = [],
    max_iterations: int = 10
) -> Agent:

    async def execute(state: AgentState) -> AgentState:
        model = get_model()

        for iteration in range(max_iterations):
            # Generate with tools
            state.output = await model.generate(
                input=state.messages,
                tools=tools,
            )
            state.messages.append(state.output.message)

            # Handle tool calls
            if state.output.message.tool_calls:
                # Execute tools (simplified)
                tool_results = await execute_tools(
                    state.output.message,
                    tools
                )
                state.messages.extend(tool_results)
            else:
                # No more tool calls, agent is done
                break

        return state

    return execute
```

#### Advanced Agent Features

**1. MCP Tool Support**:
```python
from inspect_ai.tool import mcp_connection

async def execute(state: AgentState) -> AgentState:
    async with mcp_connection(tools) as mcp_tools:
        state.output = await model.generate(
            input=state.messages,
            tools=mcp_tools
        )
    return state
```

**2. Context Compaction** (for long-running agents):
```python
from inspect_ai.agent import compaction
from inspect_ai.compaction import CompactionAuto

async def execute(state: AgentState) -> AgentState:
    async with compaction(CompactionAuto()) as compact:
        for iteration in range(100):
            state.output = await model.generate(...)
            state.messages.append(state.output.message)

            # Automatically compact when context is too large
            state.messages = await compact(state.messages, tools, model)
    return state
```

**3. Store Access** (persistent state across invocations):
```python
from inspect_ai.store import StoreModel

class AgentMemory(StoreModel):
    insights: list[str] = []
    facts: dict[str, str] = {}

@agent
def stateful_agent() -> Agent:
    async def execute(state: AgentState) -> AgentState:
        memory = AgentMemory()  # Automatically persists
        memory.insights.append("New insight from this run")
        return state
    return execute
```

**4. Transcript Logging**:
```python
from inspect_ai.agent import transcript

async def execute(state: AgentState) -> AgentState:
    await transcript.info("Starting custom reasoning phase")

    # Custom work
    result = await complex_operation()

    await transcript.step("Completed operation", result=result)
    return state
```

**5. Parallel Subtasks**:
```python
from inspect_ai.agent import collect

async def execute(state: AgentState) -> AgentState:
    # Run multiple subtasks in parallel
    results = await collect([
        analyze_code_task(),
        search_documentation_task(),
        test_hypothesis_task()
    ])

    # Integrate results
    state.messages.append(synthesize_results(results))
    return state
```

#### Conversion to Solver

```python
from inspect_ai.agent import as_solver

# Use custom agent as a task solver
@task
def agent_eval():
    return Task(
        dataset=json_dataset("data.json"),
        solver=as_solver(
            custom_react_agent(tools=[bash(), python()]),
            limits=[TokenLimit(100000)]
        ),
        scorer=includes()
    )
```

### Solver vs Agent: When to Use Each

| Use Case | Solver | Agent |
|----------|--------|-------|
| Simple prompt engineering | ✅ Recommended | ❌ Overkill |
| Tool-calling loops | ⚠️ Possible | ✅ Recommended |
| Multi-agent systems | ❌ Not suitable | ✅ Required |
| State across invocations | ❌ Limited | ✅ Full support |
| Used as a tool | ❌ No | ✅ Via `as_tool()` |
| CLI `--solver` override | ✅ Yes | ✅ Yes (via `as_solver()`) |

---

## 5. Agent Bridges (External Framework Integration)

### Overview

Inspect AI provides **agent bridges** to integrate third-party agent frameworks without rewriting agent code. Bridges work by intercepting OpenAI/Anthropic API calls and redirecting them to Inspect's model provider.

### Supported Frameworks

**Explicitly Documented**:
- ✅ **OpenAI Agents SDK** - Native support
- ✅ **LangChain** - Native support
- ✅ **Pydantic AI** - Native support
- ✅ **Custom research agents** - Any agent using OpenAI/Anthropic APIs
- ✅ **CLI-based agents** - Claude Code, Codex CLI, etc.

**Not Mentioned**:
- ❌ **AutoGen** - Not documented (but likely compatible via OpenAI API bridge)
- ❌ **CrewAI** - Not documented (but likely compatible via OpenAI API bridge)

### Python-Based Agent Bridge

#### API Signature

```python
from inspect_ai.agent import agent_bridge

@contextlib.asynccontextmanager
async def agent_bridge(
    state: AgentState | None = None,
    *,
    filter: GenerateFilter | None = None,
    retry_refusals: int | None = None,
    compaction: CompactionStrategy | None = None,
    web_search: WebSearchProviders | None = None,
    code_execution: CodeExecutionProviders | None = None,
) -> AsyncGenerator[AgentBridge, None]
```

#### How It Works

1. **API Interception**: Monkey-patches the OpenAI API client
2. **Model Redirection**: Routes calls to Inspect's model provider
3. **State Tracking**: Automatically updates `AgentState` with conversation history
4. **Message Conversion**: Uses `messages_to_openai()` helper for compatibility

#### Usage Example (Generic)

```python
from inspect_ai.agent import agent_bridge, AgentState
from some_framework import Agent as ExternalAgent

async def run_external_agent(state: AgentState) -> AgentState:
    async with agent_bridge(state) as bridge:
        # Configure external agent to use "inspect" model
        external_agent = ExternalAgent(model="inspect")

        # Run agent (calls are intercepted)
        result = await external_agent.run(bridge.state.messages)

        # State is automatically updated
        return bridge.state
```

#### Model Configuration

```python
# Standard model names work automatically
agent = ExternalAgent(model="inspect")

# Non-standard models require "inspect/" prefix
agent = ExternalAgent(model="inspect/google/gemini-1.5-pro")
agent = ExternalAgent(model="inspect/anthropic/claude-3-opus")
```

### Sandbox Agent Bridge

For agents running inside Docker containers, use `sandbox_agent_bridge()` which runs a proxy server.

#### API Signature

```python
from inspect_ai.agent import sandbox_agent_bridge

@contextlib.asynccontextmanager
async def sandbox_agent_bridge(
    state: AgentState | None = None,
    *,
    model: str | None = None,
    filter: GenerateFilter | None = None,
    retry_refusals: int | None = None,
    compaction: CompactionStrategy | None = None,
    sandbox: str | None = None,
    port: int = 13131,
    web_search: WebSearchProviders | None = None,
    code_execution: CodeExecutionProviders | None = None,
    bridged_tools: Sequence[BridgedToolsSpec] | None = None,
) -> AsyncIterator[SandboxAgentBridge]
```

#### How It Works

1. **Proxy Server**: Starts HTTP server on `localhost:{port}` inside container
2. **Environment Variables**: Configures `OPENAI_BASE_URL=http://localhost:13131/v1`
3. **Request Relaying**: Forwards API calls to Inspect's model provider
4. **MCP Tool Exposure**: Optionally bridges host-side tools via MCP

#### Usage Example

```python
from inspect_ai.agent import sandbox_agent_bridge
from inspect_ai.tool import bash, python

async def run_sandboxed_cli_agent(state: AgentState) -> AgentState:
    async with sandbox_agent_bridge(
        state,
        port=13131,
        sandbox="docker",
        bridged_tools=[
            BridgedToolsSpec(name="coding", tools=[bash(), python()])
        ]
    ) as bridge:
        # Run CLI agent inside sandbox
        result = await sandbox.exec([
            "claude-code",
            "--model", "inspect",
            "--task", "solve_problem.txt"
        ])

        return bridge.state
```

#### Bridged Tools

```python
from inspect_ai.agent import BridgedToolsSpec

# Expose host-side tools to sandboxed agent via MCP
bridged_tools = [
    BridgedToolsSpec(
        name="file_ops",
        tools=[read_file(), write_file()]
    ),
    BridgedToolsSpec(
        name="web_access",
        tools=[web_search(), web_browser()]
    )
]
```

### Integration Pattern Summary

| Framework Type | Bridge Type | Configuration |
|----------------|-------------|---------------|
| Python SDK (OpenAI, Pydantic AI) | `agent_bridge()` | `model="inspect"` |
| Python SDK (LangChain) | `agent_bridge()` | `model="inspect"` |
| CLI tools (Claude Code) | `sandbox_agent_bridge()` | `OPENAI_BASE_URL` env var |
| Custom research agents | `agent_bridge()` | Depends on implementation |

### Example: LangChain Integration (Hypothetical)

```python
from inspect_ai.agent import agent_bridge, Agent, agent
from langchain.agents import AgentExecutor
from langchain.tools import Tool as LCTool

@agent
def langchain_agent(lc_tools: list[LCTool]) -> Agent:
    async def execute(state: AgentState) -> AgentState:
        async with agent_bridge(state) as bridge:
            # Create LangChain agent configured to use Inspect
            executor = AgentExecutor.from_agent_and_tools(
                agent=create_openai_tools_agent(model="inspect"),
                tools=lc_tools
            )

            # Run agent
            result = await executor.ainvoke({"input": state.messages[-1].text})

            # State automatically updated via bridge
            return bridge.state

    return execute
```

---

## 6. Key Architectural Insights

### Decorator System

All Inspect AI components use decorators for registration:

```python
@task          # Registers task for CLI discovery
@solver        # Registers solver with name/params for logging
@agent         # Registers agent with name/description
@tool          # Registers tool for model use
```

**Benefits**:
- Automatic CLI discovery (`inspect eval package/task_name`)
- Parameter capture for reproducibility
- YAML configuration support
- Packaging via entry points

### State Hierarchy

```
TaskState (solvers, full evaluation)
    ├─ messages: list[ChatMessage]
    ├─ user_prompt: ChatMessageUser
    ├─ output: ModelOutput
    ├─ scores: dict[str, Score]
    ├─ metadata: dict
    └─ completed: bool

AgentState (agents, minimal scope)
    ├─ messages: list[ChatMessage]
    └─ output: ModelOutput
```

**Key Difference**: AgentState is intentionally narrow for flexible composition (as tools, in multi-agent systems, or as standalone solvers).

### Evaluation Lifecycle

```
1. Task Definition (@task)
2. Dataset Loading
3. Setup Solver (if defined)
4. Main Solver Execution
   ├─ Solver chain: [setup, solver1, solver2, ...]
   └─ Agent execution: react() or custom agent
5. Cleanup (if defined)
6. Scoring
7. Logging & Metrics
```

### Concurrency Model

```python
# Automatic throttling via max_connections (per-model)
tasks = [model.generate(prompt) for prompt in prompts]
results = await asyncio.gather(*tasks)  # Inspect throttles automatically

# Explicit limits via parameters
Task(
    solver=agent,
    message_limit=100,      # Max messages in conversation
    token_limit=1000000,    # Max tokens consumed
    time_limit=3600,        # Max seconds
)
```

### Sandbox Architecture

```
Host Machine
    ├─ Inspect Evaluation Process
    │   ├─ Model Provider (OpenAI, Anthropic, etc.)
    │   └─ Agent Bridge (optional)
    └─ Docker Container (sandbox)
        ├─ Agent Code (bash, python, CLI tools)
        ├─ Proxy Server (for API redirection)
        └─ MCP Tools (bridged from host)
```

---

## 7. Recommendations for Civ VI Strategic Benchmark

### Three Architecture Tracks

#### Track 1: Single Agent (ReAct)

**Best For**: Baseline evaluation, straightforward strategy problems

**Implementation**:
```python
@task
def civ_baseline():
    return Task(
        dataset=civ_scenarios(),
        solver=react(
            prompt=CIV_STRATEGY_PROMPT,
            tools=[
                get_game_state(),
                move_unit(),
                set_production(),
                end_turn()
            ],
            attempts=1,
            compaction=CompactionAuto()  # For long games
        ),
        scorer=victory_scorer(),
        sandbox="docker",
        time_limit=7200  # 2-hour games
    )
```

**Pros**: Simple, well-tested, good baseline
**Cons**: Single reasoning path, no specialization

#### Track 2: Multi-Agent Coordinator

**Best For**: Complex strategy requiring specialization (military, economy, diplomacy)

**Implementation**:
```python
# Specialist agents
military_commander = react(
    name="military_commander",
    description="Expert at warfare, unit positioning, and combat tactics",
    prompt=MILITARY_PROMPT,
    tools=[get_units(), move_unit(), attack_unit(), get_map_area()]
)

economic_planner = react(
    name="economic_planner",
    description="Expert at city development, production, and resource management",
    prompt=ECONOMY_PROMPT,
    tools=[get_cities(), set_production(), get_resources()]
)

diplomatic_advisor = react(
    name="diplomatic_advisor",
    description="Expert at diplomacy, city-state relations, and alliances",
    prompt=DIPLOMACY_PROMPT,
    tools=[get_diplomacy(), send_envoy(), make_deal()]
)

# Supervisor
@task
def civ_multi_agent():
    return Task(
        dataset=civ_scenarios(),
        solver=react(
            name="civ_coordinator",
            prompt=COORDINATOR_PROMPT,
            tools=[
                handoff(military_commander),
                handoff(economic_planner),
                handoff(diplomatic_advisor),
                end_turn()
            ]
        ),
        scorer=victory_scorer(),
        sandbox="docker"
    )
```

**Pros**: Specialization, clear delegation, conversation context
**Cons**: Handoff overhead, potential for coordinator confusion

#### Track 3: Swarm (Custom Implementation)

**Best For**: Exploring decentralized coordination, parallel city management

**Implementation** (requires custom agent):
```python
@agent
def civ_swarm(worker_count: int = 5) -> Agent:
    async def execute(state: AgentState) -> AgentState:
        # Get game state
        game_state = await get_game_state()

        # Spawn workers for each city
        city_workers = [
            react(
                name=f"city_manager_{city.id}",
                prompt=CITY_MANAGER_PROMPT.format(city=city.name),
                tools=[city_tools(city.id)]
            )
            for city in game_state.cities
        ]

        # Run workers in parallel (batched)
        city_states = [fork_state_for_city(state, city) for city in cities]
        results = []

        for batch in batched(zip(city_workers, city_states), 3):
            batch_results = await gather(*[
                run(worker, city_state)
                for worker, city_state in batch
            ])
            results.extend(batch_results)

        # Aggregate decisions
        state = aggregate_city_decisions(state, results)

        # Execute turn
        await execute_turn(state)
        return state

    return execute

@task
def civ_swarm_eval():
    return Task(
        dataset=civ_scenarios(),
        solver=as_solver(civ_swarm(worker_count=5)),
        scorer=victory_scorer(),
        sandbox="docker"
    )
```

**Pros**: Parallelism, scalable to many cities, novel approach
**Cons**: Custom implementation complexity, no built-in swarm primitives

### Evaluation Harness

```python
# Run all three tracks
inspect eval civ_benchmark.py \
    --model anthropic/claude-3-opus \
    --model openai/gpt-4 \
    --solver civ_baseline \
    --solver civ_multi_agent \
    --solver civ_swarm \
    --max-samples 10 \
    --max-connections 5
```

### Scorer Implementation

```python
from inspect_ai.scorer import scorer, Score, Target

@scorer(metrics=[accuracy(), mean()])
def victory_scorer():
    async def score(state: TaskState, target: Target) -> Score:
        game_state = extract_final_game_state(state)

        # Victory conditions
        if game_state.victory_type is not None:
            return Score(
                value=1.0,
                answer=game_state.victory_type,
                metadata={
                    "turns": game_state.turn,
                    "victory_type": game_state.victory_type,
                    "score": game_state.score
                }
            )
        else:
            return Score(
                value=game_state.score / 1000,  # Normalized score
                answer="incomplete",
                metadata={"turns": game_state.turn, "score": game_state.score}
            )

    return score
```

---

## 8. API Reference Quick Lookup

### Core Agent Functions

```python
from inspect_ai.agent import (
    agent,              # Decorator for custom agents
    react,              # Built-in ReAct agent
    run,                # Execute agent with input
    handoff,            # Create handoff tool
    as_tool,            # Convert agent to tool
    as_solver,          # Convert agent to solver
    agent_bridge,       # Bridge external Python agents
    sandbox_agent_bridge,  # Bridge sandboxed CLI agents
)

from inspect_ai.agent import (
    Agent,              # Agent protocol
    AgentState,         # Minimal agent state
    AgentPrompt,        # Prompt configuration
    MessageFilter,      # Message transformation function
    content_only,       # Remove system msgs and tool calls
    remove_tools,       # Strip tool calls
    last_message,       # Keep only last message
)
```

### Core Solver Functions

```python
from inspect_ai.solver import (
    solver,             # Decorator for custom solvers
    TaskState,          # Full task state
    Generate,           # Model generation function
    chain,              # Chain multiple solvers
    generate,           # Basic model call solver
    chain_of_thought,   # CoT prompting
    self_critique,      # Generate + critique + revise
    use_tools,          # Tool-use loop
)
```

### Task Definition

```python
from inspect_ai import (
    task,               # Decorator for tasks
    Task,               # Task class
    eval,               # Programmatic evaluation
)
```

### Models & Tools

```python
from inspect_ai.model import (
    get_model,          # Get model instance
    ChatMessage,        # Message class
    ModelOutput,        # Generation output
)

from inspect_ai.tool import (
    tool,               # Decorator for tools
    bash,               # Bash execution
    python,             # Python execution
    web_search,         # Web search
    web_browser,        # Headless browser
)
```

---

## Sources

### Official Documentation
- [Inspect AI Homepage](https://inspect.aisi.org.uk/)
- [Using Agents](https://inspect.aisi.org.uk/agents.html)
- [Multi-Agent Architectures](https://inspect.aisi.org.uk/multi-agent.html)
- [Custom Agents](https://inspect.aisi.org.uk/agent-custom.html)
- [ReAct Agent](https://inspect.aisi.org.uk/react-agent.html)
- [Agent Bridge](https://inspect.aisi.org.uk/agent-bridge.html)
- [Solvers](https://inspect.aisi.org.uk/solvers.html)
- [Tasks](https://inspect.aisi.org.uk/tasks.html)
- [Parallelism](https://inspect.aisi.org.uk/parallelism.html)
- [inspect_ai.agent API Reference](https://inspect.aisi.org.uk/reference/inspect_ai.agent.html)

### GitHub Repositories
- [UKGovernmentBEIS/inspect_ai](https://github.com/UKGovernmentBEIS/inspect_ai)
- [UKGovernmentBEIS/inspect_evals](https://github.com/UKGovernmentBEIS/inspect_evals)

### External Resources
- [Hamel's Blog: Inspect AI Overview](https://hamel.dev/notes/llm/evals/inspect.html)
- [Implementing a Deception Eval with Inspect](https://schmatz.github.io/deception-eval-with-inspect/)
- [OpenAI Cookbook: Parallel Agents](https://cookbook.openai.com/examples/agents_sdk/parallel_agents)

---

## Conclusion

Inspect AI provides **strong native support for single-agent and multi-agent coordinator patterns**, with clear APIs (`react()`, `handoff()`, `@agent`) and good documentation. **Swarm patterns require custom implementation** but are feasible using `asyncio.gather()` and the `@agent` decorator. **Custom solvers and agents are first-class citizens** with full CLI integration via `--solver` parameter and YAML configuration.

**For the Civ VI strategic benchmark**, the framework is well-suited for all three tracks:
1. **Single agent**: Use `react()` directly
2. **Coordinator**: Use `handoff()` for specialist delegation
3. **Swarm**: Implement custom `@agent` with parallel execution

The agent bridge support enables integration with external frameworks if needed, though native Inspect patterns are likely sufficient for the benchmark requirements.
