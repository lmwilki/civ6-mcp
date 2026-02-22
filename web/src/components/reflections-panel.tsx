"use client"

import { useState } from "react"
import type { Reflections } from "@/lib/diary-types"
import { CIV6_COLORS } from "@/lib/civ-colors"
import { CivIcon } from "./civ-icon"
import {
  Crosshair,
  BrainCircuit,
  Wrench,
  CalendarClock,
  Lightbulb,
  ChevronDown,
  ChevronUp,
} from "lucide-react"

const reflectionConfig = [
  { key: "tactical" as const, label: "Tactical", icon: Crosshair, color: CIV6_COLORS.military },
  { key: "strategic" as const, label: "Strategic", icon: BrainCircuit, color: CIV6_COLORS.science },
  { key: "tooling" as const, label: "Tooling", icon: Wrench, color: CIV6_COLORS.iron },
  { key: "planning" as const, label: "Planning", icon: CalendarClock, color: CIV6_COLORS.marine },
  { key: "hypothesis" as const, label: "Hypothesis", icon: Lightbulb, color: CIV6_COLORS.goldMetal },
]

interface ReflectionsPanelProps {
  reflections?: Reflections
}

export function ReflectionsPanel({ reflections }: ReflectionsPanelProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set(["tactical", "strategic"]))

  if (!reflections) return null

  const toggle = (key: string) => {
    setExpanded((s) => {
      const next = new Set(s)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  return (
    <div className="mx-auto w-full max-w-2xl space-y-1">
      {reflectionConfig.map(({ key, label, icon, color }) => {
        const text = reflections[key]
        if (!text) return null
        const isOpen = expanded.has(key)
        return (
          <div key={key} className="rounded-sm border border-marble-300/50 bg-marble-50">
            <button
              onClick={() => toggle(key)}
              className="flex w-full items-center gap-2 px-3 py-2 text-left transition-colors hover:bg-marble-100"
            >
              <CivIcon icon={icon} color={color} size="sm" />
              <span className="flex-1 font-display text-xs font-bold uppercase tracking-[0.1em] text-marble-700">
                {label}
              </span>
              {isOpen ? (
                <ChevronUp className="h-3 w-3 text-marble-400" />
              ) : (
                <ChevronDown className="h-3 w-3 text-marble-400" />
              )}
            </button>
            {isOpen && (
              <div className="border-t border-marble-300/30 px-3 py-2">
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-marble-700">
                  {text}
                </p>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
