"use client"

import Link from "next/link"
import { ThemeToggle } from "./theme-toggle"

interface NavBarProps {
  active: "home" | "diary" | "timeline"
  connected?: boolean
  turn?: number | null
}

export function NavBar({ active, connected, turn }: NavBarProps) {
  return (
    <header className="shrink-0 border-b border-marble-300 bg-marble-50 px-3 py-3 sm:px-6">
      <div className="mx-auto flex max-w-6xl items-center justify-between">
        <div className="flex items-baseline gap-3 sm:gap-6">
          <Link href="/">
            <h1 className={`font-display text-sm font-bold tracking-[0.15em] uppercase transition-colors hover:text-gold-dark ${
              active === "home" ? "text-gold-dark" : "text-marble-800"
            }`}>
              civ6-mcp
            </h1>
          </Link>
          <nav className="flex gap-4">
            <Link
              href="/diary"
              className={`text-sm transition-colors ${
                active === "diary"
                  ? "font-semibold text-gold-dark"
                  : "text-marble-500 hover:text-marble-700"
              }`}
            >
              Diary
            </Link>
            <Link
              href="/timeline"
              className={`text-sm transition-colors ${
                active === "timeline"
                  ? "font-semibold text-gold-dark"
                  : "text-marble-500 hover:text-marble-700"
              }`}
            >
              Timeline
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-3">
          {turn !== null && turn !== undefined && (
            <span className="font-mono text-xs tabular-nums text-marble-500">
              Turn {turn}
            </span>
          )}
          <ThemeToggle />
          <span className="relative flex h-2 w-2">
            <span
              className={`inline-flex h-2 w-2 rounded-full ${
                connected ? "bg-patina" : "bg-marble-400"
              }`}
            />
          </span>
        </div>
      </div>
    </header>
  )
}
