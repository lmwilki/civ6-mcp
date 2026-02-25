"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

interface CollapsiblePanelProps {
  icon: React.ReactNode;
  title: string;
  defaultOpen?: boolean;
  summary?: React.ReactNode;
  children: React.ReactNode;
}

export function CollapsiblePanel({
  icon,
  title,
  defaultOpen = false,
  summary,
  children,
}: CollapsiblePanelProps) {
  const [expanded, setExpanded] = useState(defaultOpen);

  return (
    <div className="mx-auto mb-4 w-full max-w-2xl rounded-sm border border-marble-300/50 bg-marble-50">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left transition-colors hover:bg-marble-100"
      >
        {icon}
        <span className="flex-1 font-display text-xs font-bold uppercase tracking-[0.1em] text-marble-700">
          {title}
        </span>
        {summary}
        {expanded ? (
          <ChevronUp className="h-3 w-3 text-marble-400" />
        ) : (
          <ChevronDown className="h-3 w-3 text-marble-400" />
        )}
      </button>
      {expanded && (
        <div className="border-t border-marble-300/30 px-3 py-2">
          {children}
        </div>
      )}
    </div>
  );
}
