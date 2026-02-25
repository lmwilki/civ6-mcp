"use client";

import { PulsingDot } from "./pulsing-dot";

interface LiveIndicatorProps {
  live: boolean;
  connected: boolean;
  onToggle: () => void;
}

export function LiveIndicator({
  live,
  connected,
  onToggle,
}: LiveIndicatorProps) {
  const color =
    live && connected ? "bg-patina" : live ? "bg-terracotta" : "bg-marble-400";

  return (
    <button
      onClick={onToggle}
      className="flex items-center gap-2 rounded-sm border border-marble-300 bg-marble-100 px-3 py-1.5 text-xs font-medium text-marble-700 transition-colors hover:bg-marble-200"
    >
      <PulsingDot color={color} ping={live && connected} />
      {live ? (connected ? "Live" : "Disconnected") : "Paused"}
    </button>
  );
}
