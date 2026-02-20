"use client"

import { memo, useEffect, useMemo, useRef } from "react"
import { TurnDivider } from "./turn-divider"
import { LogEntry } from "./log-entry"
import { groupByTurn } from "@/lib/types"
import type { LogEntry as LogEntryType } from "@/lib/types"

interface TimelineProps {
  entries: LogEntryType[]
  live: boolean
}

const MemoLogEntry = memo(LogEntry)

export function Timeline({ entries, live }: TimelineProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (live && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [entries.length, live])

  const groups = useMemo(() => groupByTurn(entries), [entries])

  if (entries.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <div className="text-center">
          <p className="font-display text-sm tracking-[0.12em] uppercase text-marble-500">
            Awaiting dispatches
          </p>
          <p className="mt-2 text-sm text-marble-600">
            Start a game and make some tool calls
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto pb-8">
      <div className="mx-auto max-w-4xl">
        {groups.map((group, gi) => (
          <div key={gi}>
            <TurnDivider turn={group.turn} />
            <div className="rounded-sm border border-marble-300/40 bg-marble-100/50 shadow-[0_1px_3px_rgba(42,37,33,0.04)]">
              {group.entries.map((entry, i) => (
                <div key={entry.line}>
                  {i > 0 && <div className="mx-4 h-px bg-marble-300/30" />}
                  <MemoLogEntry entry={entry} />
                </div>
              ))}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
