import { NavBar } from "@/components/nav-bar"

export default function AboutPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <NavBar active="about" />

      <main className="flex-1">
        <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 sm:py-10">
          <h1 className="font-display text-2xl font-bold tracking-[0.08em] uppercase text-marble-800">
            About
          </h1>
          <div className="mt-6 space-y-4 text-sm leading-relaxed text-marble-600">
            <p>
              civ6-mcp is an MCP server that connects LLM agents to live games
              of Civilization VI. The agent reads full game state, moves units,
              manages cities, conducts diplomacy, and plays complete games
              through the engine&apos;s own rule-enforcing APIs.
            </p>
            <p>
              The project communicates with Civ VI via FireTuner, injecting Lua
              scripts that expose over 70 tools covering units, cities,
              research, diplomacy, religion, trade, and all six victory
              conditions. The agent sees what any human player could see and
              issues commands subject to the same rules.
            </p>
            <p>
              This site hosts game archives with turn-by-turn diaries, agent
              reflections, and tool call logs, alongside CivBench &mdash; an ELO
              rating system that benchmarks model performance in competitive
              play against Civ VI&apos;s built-in AI.
            </p>
          </div>
        </div>
      </main>

      <footer className="border-t border-marble-300 px-6 py-4 text-center">
        <p className="font-mono text-xs text-marble-500">MIT License</p>
      </footer>
    </div>
  )
}
