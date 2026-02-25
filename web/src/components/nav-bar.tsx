"use client";

import Link from "next/link";
import { ThemeToggle } from "./theme-toggle";

interface NavBarProps {
  active: "home" | "about" | "docs" | "games" | "leaderboard";
  connected?: boolean;
  turn?: number | null;
}

export function NavBar({ active, connected, turn }: NavBarProps) {
  return (
    <header className="shrink-0 border-b border-marble-300 bg-marble-50">
      <div className="mx-auto grid max-w-5xl items-center px-4 py-3 sm:px-6 lg:grid-cols-[1fr_1px_340px]">
        {/* Left — civ6-mcp brand + project nav */}
        <div className="flex items-baseline gap-3 sm:gap-6 lg:pr-12">
          <Link href="/">
            <h1
              className={`font-display text-sm font-bold tracking-[0.15em] uppercase transition-colors hover:text-gold-dark ${
                active === "home" ? "text-gold-dark" : "text-marble-800"
              }`}
            >
              civ6-mcp
            </h1>
          </Link>
          <nav className="flex gap-4">
            <Link
              href="/about"
              className={`text-sm transition-colors ${
                active === "about"
                  ? "font-semibold text-gold-dark"
                  : "text-marble-500 hover:text-marble-700"
              }`}
            >
              About
            </Link>
            <Link
              href="/docs"
              className={`text-sm transition-colors ${
                active === "docs"
                  ? "font-semibold text-gold-dark"
                  : "text-marble-500 hover:text-marble-700"
              }`}
            >
              Docs
            </Link>
            <Link
              href="/games"
              className={`text-sm transition-colors lg:hidden ${
                active === "games"
                  ? "font-semibold text-gold-dark"
                  : "text-marble-500 hover:text-marble-700"
              }`}
            >
              Games
            </Link>
            <Link
              href="/civbench"
              className={`text-sm transition-colors lg:hidden ${
                active === "leaderboard"
                  ? "font-semibold text-gold-dark"
                  : "text-marble-500 hover:text-marble-700"
              }`}
            >
              CivBench
            </Link>
          </nav>
        </div>

        {/* Vertical divider */}
        <div className="hidden lg:block self-stretch bg-marble-300/50" />

        {/* Right — CivBench brand + bench nav */}
        <div className="hidden lg:flex items-center gap-3 sm:gap-6 pl-12">
          <Link href="/civbench">
            <span
              className={`font-display text-sm font-bold tracking-[0.15em] uppercase transition-colors hover:text-gold-dark ${
                active === "leaderboard" ? "text-gold-dark" : "text-marble-800"
              }`}
            >
              CivBench
            </span>
          </Link>
          <nav className="flex items-baseline gap-4">
            <Link
              href="/games"
              className={`text-sm transition-colors ${
                active === "games"
                  ? "font-semibold text-gold-dark"
                  : "text-marble-500 hover:text-marble-700"
              }`}
            >
              Games
            </Link>
            <Link
              href="/civbench"
              className={`text-sm transition-colors ${
                active === "leaderboard"
                  ? "font-semibold text-gold-dark"
                  : "text-marble-500 hover:text-marble-700"
              }`}
            >
              Leaderboard
            </Link>
          </nav>
          <div className="flex-1" />
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
  );
}
