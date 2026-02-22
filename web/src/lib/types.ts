export interface LogEntry {
  game: string
  civ: string
  seed: number
  session: string
  ts: number
  turn: number | null
  seq: number
  type: "tool_call" | "turn_report" | "error"
  tool: string
  category: "query" | "action" | "turn" | "error"
  params: Record<string, unknown> | null
  result_summary: string | null
  result: string | null
  duration_ms: number | null
  success: boolean
  events?: TurnEvent[]
  agent_model?: string | null
  /** Line number in the JSONL file (set by API) */
  line: number
}

export interface GameLogInfo {
  game: string
  civ: string
  seed: string
  count: number
  first_ts: number
  last_ts: number
  min_turn: number | null
  max_turn: number | null
  sessions: string[]
}

/** Classify tools into visual categories */
export function getToolCategory(tool?: string): "query" | "action" | "turn" | "error" {
  if (!tool) return "query"
  if (tool === "end_turn") return "turn"
  if (tool.startsWith("get_") || tool === "screenshot") return "query"
  return "action"
}

export interface TurnEvent {
  priority: string
  category: string
  message: string
}

/** Group of log entries sharing the same turn number */
export interface TurnGroup {
  turn: number | null
  entries: LogEntry[]
}

export function groupByTurn(entries: LogEntry[]): TurnGroup[] {
  const groups: TurnGroup[] = []
  let current: TurnGroup | null = null

  for (const entry of entries) {
    if (!current || current.turn !== entry.turn) {
      current = { turn: entry.turn, entries: [] }
      groups.push(current)
    }
    current.entries.push(entry)
  }

  return groups
}
