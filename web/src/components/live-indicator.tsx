"use client";

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
  return (
    <button
      onClick={onToggle}
      className="flex items-center gap-2 rounded-sm border border-marble-300 bg-marble-100 px-3 py-1.5 text-xs font-medium text-marble-700 transition-colors hover:bg-marble-200"
    >
      <span className="relative flex h-2 w-2">
        {live && connected && (
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-patina opacity-75" />
        )}
        <span
          className={`relative inline-flex h-2 w-2 rounded-full ${
            live && connected
              ? "bg-patina"
              : live
                ? "bg-terracotta"
                : "bg-marble-400"
          }`}
        />
      </span>
      {live ? (connected ? "Live" : "Disconnected") : "Paused"}
    </button>
  );
}
