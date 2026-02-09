export interface LogEntry {
  ts: number
  session: string
  turn: number | null
  type: "tool_call" | "turn_report" | "error"
  tool?: string
  params?: Record<string, unknown>
  result?: string
  duration_ms?: number
  events?: TurnEvent[]
  /** Line number in the JSONL file (set by API) */
  line: number
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
