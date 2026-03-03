"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useDiaryList } from "@/lib/use-diary";
import { slugFromFilename, sortGamesLiveFirst } from "@/lib/diary-types";
import { getCivColors } from "@/lib/civ-colors";
import { CivSymbol } from "./civ-icon";
import { LeaderPortrait } from "@/components/leader-portrait";
import { GameStatusBadge, getGameStatusColor } from "@/components/game-status-badge";
import { formatModelName } from "@/lib/model-registry";
import { SkeletonBlock, SkeletonLine } from "./skeleton";

export function RecentGames() {
  const games = useDiaryList();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (games.length > 0) {
      setReady(true);
    } else {
      const t = setTimeout(() => setReady(true), 500);
      return () => clearTimeout(t);
    }
  }, [games.length]);

  if (games.length === 0 && !ready) {
    return (
      <div className="space-y-1.5">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="flex items-stretch gap-0 rounded-sm border border-marble-300/50 bg-marble-50"
          >
            <div className="w-1.5 shrink-0 rounded-l-sm bg-marble-200" />
            <div className="flex flex-1 items-center gap-2 px-2.5 py-2.5">
              <SkeletonBlock className="h-8 w-8 shrink-0 rounded-full" />
              <div className="flex-1 space-y-1.5">
                <SkeletonLine className="w-24" />
                <SkeletonLine className="w-16" />
              </div>
              <SkeletonLine className="w-14" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (games.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center rounded-sm border border-marble-300/50 bg-marble-50">
        <p className="text-sm text-marble-500">No games yet</p>
      </div>
    );
  }

  const sorted = sortGamesLiveFirst(games);

  return (
    <div className="space-y-1.5">
      {sorted.map((game) => {
        const colors = getCivColors(game.label, game.leader);

        return (
          <Link
            key={game.filename}
            href={`/games/${slugFromFilename(game.filename)}`}
            className="group flex items-stretch gap-0 rounded-sm border border-marble-300/50 bg-marble-50 transition-colors hover:border-marble-400 hover:bg-marble-100"
          >
            {/* Color accent bar */}
            <div
              className="w-1.5 shrink-0 rounded-l-sm"
              style={{ backgroundColor: getGameStatusColor(game.status, game.outcome) }}
            />

            <div className="flex flex-1 items-center justify-between gap-2 px-2.5 py-2.5">
              <div className="flex min-w-0 items-center gap-2">
                <LeaderPortrait
                  leader={game.leader}
                  agentModel={game.agentModel}
                  fallbackColor={colors.primary}
                  size="sm"
                />
                <div className="min-w-0">
                  <div className="flex items-center gap-1">
                    <CivSymbol civ={game.label} />
                    <span className="font-display text-sm font-bold tracking-wide uppercase text-marble-800">
                      {game.label}
                    </span>
                  </div>
                  {game.leader && (
                    <p className="text-xs text-marble-500 truncate">
                      {game.leader}
                    </p>
                  )}
                  {game.agentModel && (
                    <p className="text-xs text-marble-400 truncate">
                      {formatModelName(game.agentModel)}
                    </p>
                  )}
                </div>
              </div>

              <GameStatusBadge
                status={game.status}
                outcome={game.outcome}
                turnCount={game.count}
              />
            </div>
          </Link>
        );
      })}
    </div>
  );
}
