"use client"

import { useState } from "react"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { EventChip } from "./event-chip"
import { getToolCategory } from "@/lib/types"
import type { LogEntry as LogEntryType } from "@/lib/types"

const borderStyles: Record<string, string> = {
  query: "border-l-marble-300",
  action: "border-l-gold",
  turn: "border-l-gold-dark",
  error: "border-l-terracotta",
}

const badgeStyles: Record<string, string> = {
  query: "text-marble-700",
  action: "text-gold-dark bg-gold/10",
  turn: "text-gold-dark bg-gold/15 font-semibold",
  error: "text-terracotta bg-terracotta/10",
}

function formatTime(ts: number): string {
  return new Date(ts * 1000).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  })
}

function formatToolName(tool?: string): string {
  if (!tool) return "unknown"
  return tool
}

function truncate(s: string, max: number): string {
  if (s.length <= max) return s
  return s.slice(0, max) + "\u2026"
}

interface LogEntryProps {
  entry: LogEntryType
}

export function LogEntry({ entry }: LogEntryProps) {
  const [open, setOpen] = useState(false)
  const cat = entry.type === "error" ? "error" : getToolCategory(entry.tool)

  const hasDetails =
    entry.result ||
    (entry.params && Object.keys(entry.params).length > 0) ||
    (entry.events && entry.events.length > 0)

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger asChild>
        <div
          className={`flex cursor-pointer items-center gap-3 border-l-2 px-4 py-2 transition-colors hover:bg-marble-200/40 ${borderStyles[cat]}`}
        >
          {/* Timestamp */}
          <span className="shrink-0 font-mono text-xs tabular-nums text-marble-600">
            {formatTime(entry.ts)}
          </span>

          {/* Tool name */}
          <span
            className={`shrink-0 rounded-sm px-1.5 py-0.5 font-mono text-xs ${badgeStyles[cat]}`}
          >
            {formatToolName(entry.tool)}
          </span>

          {/* Result summary */}
          <span className="min-w-0 flex-1 truncate font-mono text-xs text-marble-700">
            {entry.result ? truncate(entry.result, 120) : ""}
          </span>

          {/* Duration */}
          {entry.duration_ms != null && (
            <span className="shrink-0 font-mono text-xs tabular-nums text-marble-500">
              {entry.duration_ms}ms
            </span>
          )}

          {/* Expand indicator */}
          {hasDetails && (
            <span className="shrink-0 text-xs text-marble-500">
              {open ? "\u25B4" : "\u25BE"}
            </span>
          )}
        </div>
      </CollapsibleTrigger>

      {hasDetails && (
        <CollapsibleContent>
          <div className="ml-6 space-y-2 border-l border-marble-300/50 py-2 pl-4">
            {/* Params */}
            {entry.params && Object.keys(entry.params).length > 0 && (
              <div>
                <span className="font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
                  Params
                </span>
                <pre className="mt-1 overflow-x-auto rounded-sm bg-marble-200/50 p-2 font-mono text-xs text-marble-700">
                  {JSON.stringify(entry.params, null, 2)}
                </pre>
              </div>
            )}

            {/* Full result */}
            {entry.result && (
              <div>
                <span className="font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
                  Result
                </span>
                <pre className="mt-1 max-h-64 overflow-auto whitespace-pre-wrap rounded-sm bg-marble-200/50 p-2 font-mono text-xs text-marble-700">
                  {entry.result}
                </pre>
              </div>
            )}

            {/* Turn events */}
            {entry.events && entry.events.length > 0 && (
              <div>
                <span className="font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
                  Events
                </span>
                <div className="mt-1 flex flex-wrap gap-1">
                  {entry.events.map((ev, i) => (
                    <EventChip key={i} event={ev} />
                  ))}
                </div>
              </div>
            )}
          </div>
        </CollapsibleContent>
      )}
    </Collapsible>
  )
}
