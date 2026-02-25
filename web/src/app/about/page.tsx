"use client";

import Link from "next/link";
import { PageShell } from "@/components/page-shell";
import { CivIcon } from "@/components/civ-icon";
import { CIV6_COLORS } from "@/lib/civ-colors";
import {
  Github,
  Swords,
  Building2,
  Handshake,
  FlaskConical,
  Flame,
  Trophy,
  Eye,
  BookOpen,
  Terminal,
  Cpu,
  Map,
  ScrollText,
  BrainCircuit,
} from "lucide-react";

const DOMAINS = [
  { label: "Economic", icon: Building2, color: CIV6_COLORS.gold },
  { label: "Scientific", icon: FlaskConical, color: CIV6_COLORS.science },
  { label: "Cultural", icon: Flame, color: CIV6_COLORS.culture },
  { label: "Military", icon: Swords, color: CIV6_COLORS.military },
  { label: "Diplomatic", icon: Handshake, color: CIV6_COLORS.favor },
  { label: "Spatial", icon: Map, color: CIV6_COLORS.marine },
  { label: "Temporal", icon: Trophy, color: CIV6_COLORS.goldMetal },
];

const STATS = [
  { value: "76", label: "MCP tools" },
  { value: "300+", label: "turns per game" },
  { value: "3,000+", label: "tool calls per episode" },
  { value: "6", label: "victory conditions" },
];

const ARCHITECTURE = [
  {
    step: "LLM Agent",
    detail: "Claude, GPT, Gemini — any model that speaks MCP",
    icon: BrainCircuit,
    color: CIV6_COLORS.science,
  },
  {
    step: "MCP Server",
    detail: "76 tools + narration layer translating visuals to text",
    icon: Terminal,
    color: CIV6_COLORS.production,
  },
  {
    step: "FireTuner",
    detail: "Binary TCP protocol injecting Lua into the live game",
    icon: Cpu,
    color: CIV6_COLORS.military,
  },
  {
    step: "Civilization VI",
    detail: "Full game engine enforcing all rules — no cheats, no omniscience",
    icon: Swords,
    color: CIV6_COLORS.goldMetal,
  },
];

export default function AboutPage() {
  return (
    <PageShell active="about">
      <main className="flex-1">
        <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 sm:py-10">
          {/* Hero */}
          <h1 className="font-display text-3xl font-bold tracking-[0.08em] uppercase text-marble-800">
            About civ6-mcp
          </h1>
          <p className="mt-4 text-base leading-relaxed text-marble-600">
            Can a language model play a full game of Civilization VI? Not
            tic-tac-toe, not chess &mdash; a 300-turn 4X strategy game with fog
            of war, seven concurrent domains, six victory paths, and an action
            space that grows to 10<sup className="text-[10px]">166</sup>{" "}
            possible moves.
          </p>
          <p className="mt-3 text-base leading-relaxed text-marble-600">
            civ6-mcp is the environment that makes this question testable. It
            connects any MCP-compatible model to a live Civ VI game through the
            same tool-calling protocol agents already use for databases, APIs,
            and file operations &mdash; then lets them play.
          </p>

          {/* Stats bar */}
          <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {STATS.map((s) => (
              <div
                key={s.label}
                className="rounded-sm border border-marble-300/50 bg-marble-50 px-3 py-2.5 text-center"
              >
                <div className="font-display text-xl font-bold tracking-wide text-marble-800">
                  {s.value}
                </div>
                <div className="mt-0.5 text-[10px] font-medium uppercase tracking-[0.1em] text-marble-500">
                  {s.label}
                </div>
              </div>
            ))}
          </div>

          {/* Divider */}
          <div className="my-10 border-t border-marble-300/50" />

          {/* Architecture */}
          <section>
            <h2 className="font-display text-xs font-bold uppercase tracking-[0.12em] text-marble-500">
              How It Works
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-marble-600">
              The agent never touches the game directly. Every command flows
              through four layers, each translating between the world above and
              below it.
            </p>
            <div className="mt-5 space-y-0">
              {ARCHITECTURE.map((a, i) => (
                <div key={a.step} className="flex items-stretch gap-4">
                  {/* Vertical connector line + icon */}
                  <div className="flex flex-col items-center">
                    <div
                      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full"
                      style={{ backgroundColor: a.color, opacity: 0.8 }}
                    >
                      <a.icon className="h-4 w-4 text-white" />
                    </div>
                    {i < ARCHITECTURE.length - 1 && (
                      <div className="w-px flex-1 bg-marble-300/60" />
                    )}
                  </div>
                  {/* Text */}
                  <div className="pb-6">
                    <h3 className="font-display text-sm font-bold uppercase tracking-[0.06em] text-marble-800">
                      {a.step}
                    </h3>
                    <p className="mt-0.5 text-sm leading-relaxed text-marble-600">
                      {a.detail}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Divider */}
          <div className="my-10 border-t border-marble-300/50" />

          {/* Seven domains */}
          <section>
            <h2 className="font-display text-xs font-bold uppercase tracking-[0.12em] text-marble-500">
              Seven Concurrent Domains
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-marble-600">
              Every turn requires reasoning across all of these simultaneously.
              There is no phase structure &mdash; the agent decides what to
              attend to, what to defer, and what to ignore. Ignore the wrong
              thing and a religious victory you never saw coming ends the game.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {DOMAINS.map((d) => (
                <div
                  key={d.label}
                  className="flex items-center gap-1.5 rounded-sm border border-marble-300/50 bg-marble-50 px-2.5 py-1.5"
                >
                  <CivIcon icon={d.icon} color={d.color} size="sm" />
                  <span className="text-xs font-medium text-marble-700">
                    {d.label}
                  </span>
                </div>
              ))}
            </div>
          </section>

          {/* Divider */}
          <div className="my-10 border-t border-marble-300/50" />

          {/* Narration layer */}
          <section>
            <h2 className="font-display text-xs font-bold uppercase tracking-[0.12em] text-marble-500">
              The Narration Layer
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-marble-600">
              A human player absorbs the minimap, score ticker, religion lens,
              unit health bars, and army positions at a glance. An LLM gets
              none of that passively. The narration layer translates Civ
              VI&apos;s visual state into structured text &mdash; markdown hex
              maps with terrain and threat markers, per-unit status readouts,
              city yield summaries, diplomatic relationship graphs &mdash;
              preserving the decision-relevant information a human extracts from
              the screen.
            </p>
            <div className="mt-4 rounded-sm border border-marble-300/50 bg-marble-900 p-4 font-mono text-[11px] leading-relaxed text-marble-200">
              <div className="text-marble-500">
                {"//"} get_map_area(x=10, y=22, radius=3)
              </div>
              <div className="mt-2">
                <span className="text-marble-400">(9,22):</span> GRASS Hills
                [WHEAT] (FARM){" "}
                <span className="text-green-400">{"{F:4 P:1}"}</span>
              </div>
              <div>
                <span className="text-marble-400">(10,22):</span> GRASS JUNGLE
                [BANANAS]{" "}
                <span className="text-green-400">{"{F:4 P:1}"}</span>{" "}
                <span className="text-blue-400">[my: WARRIOR]</span>
              </div>
              <div>
                <span className="text-marble-400">(13,24):</span> GRASS FOREST{" "}
                <span className="text-green-400">{"{F:1 P:2}"}</span>{" "}
                <span className="font-bold text-red-400">
                  **[Barbarian WARRIOR]**
                </span>
              </div>
              <div>
                <span className="text-marble-400">(14,25):</span> PLAINS Hills
                [DIAMONDS+]{" "}
                <span className="text-green-400">{"{F:1 P:2}"}</span>{" "}
                <span className="text-marble-500">[fog]</span>
              </div>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-marble-600">
              Each narration function flags urgency (bold threat markers,{" "}
              <code className="rounded bg-marble-200 px-1 py-0.5 text-[11px] text-marble-700">
                !!
              </code>{" "}
              warnings), provides context for action (valid attack targets,
              buildable improvements), and compresses intelligently (fog tiles
              marked rather than omitted, resources classified by type).
            </p>
          </section>

          {/* Divider */}
          <div className="my-10 border-t border-marble-300/50" />

          {/* The Sensorium Effect */}
          <section>
            <div className="flex items-center gap-2">
              <CivIcon icon={Eye} color={CIV6_COLORS.culture} size="md" />
              <h2 className="font-display text-xs font-bold uppercase tracking-[0.12em] text-marble-500">
                The Sensorium Effect
              </h2>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-marble-600">
              The narration layer can tell the agent everything a human sees
              &mdash; but it can&apos;t replicate{" "}
              <em>how</em> a human sees it. A player glances at the minimap and
              notices a religion spreading. The agent only knows what it
              explicitly queries. Information it doesn&apos;t ask for doesn&apos;t
              enter its world model.
            </p>
            <p className="mt-3 text-sm leading-relaxed text-marble-600">
              This produces a consistent pattern: game systems that need
              proactive monitoring go unmonitored until crisis forces attention.
              A rival converts every city to their religion over 100 turns. A
              barbarian camp spawns armies six tiles away. Gold piles up past
              2,000 while the diary says &ldquo;should spend.&rdquo; The agent
              articulates the right strategy and then doesn&apos;t execute it
              &mdash; not because it can&apos;t, but because it doesn&apos;t
              look.
            </p>
            <p className="mt-3 text-sm leading-relaxed text-marble-600">
              This is an architectural property of any agent that perceives a
              rich environment through text queries. It generalises well beyond
              Civilization, and it&apos;s what makes this environment
              interesting as a benchmark.
            </p>
          </section>

          {/* Divider */}
          <div className="my-10 border-t border-marble-300/50" />

          {/* Open source + links */}
          <section>
            <h2 className="font-display text-xs font-bold uppercase tracking-[0.12em] text-marble-500">
              Open Source
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-marble-600">
              The environment, all 76 tools, the narration layer, and the agent
              playbook are MIT-licensed. Any model that supports MCP can play.
              Game archives with full turn-by-turn diaries, agent reflections,
              and tool call logs are browsable on this site.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <a
                href="https://github.com/lmwilki/civ6-mcp"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-sm border border-marble-400 bg-marble-100 px-4 py-2 text-sm font-medium text-marble-700 transition-colors hover:border-marble-500 hover:bg-marble-200"
              >
                <Github className="h-4 w-4" />
                GitHub
              </a>
              <Link
                href="/docs"
                className="inline-flex items-center gap-2 rounded-sm border border-marble-400 bg-marble-100 px-4 py-2 text-sm font-medium text-marble-700 transition-colors hover:border-marble-500 hover:bg-marble-200"
              >
                <BookOpen className="h-4 w-4" />
                Docs
              </Link>
              <Link
                href="/games"
                className="inline-flex items-center gap-2 rounded-sm border border-gold/40 bg-gold/10 px-4 py-2 text-sm font-medium text-gold-dark transition-colors hover:bg-gold/20"
              >
                <ScrollText className="h-4 w-4" />
                Browse Games
              </Link>
            </div>
          </section>

          {/* Authors */}
          <div className="mt-10 border-t border-marble-300/50 pt-6">
            <p className="text-xs text-marble-500">
              Built by Liam Wilkinson, Jamie Heagherty, Harry Coppock, and
              Austin Andrews.
            </p>
          </div>
        </div>
      </main>
    </PageShell>
  );
}
