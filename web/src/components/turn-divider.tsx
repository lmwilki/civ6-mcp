interface TurnDividerProps {
  turn: number | null;
}

export function TurnDivider({ turn }: TurnDividerProps) {
  return (
    <div className="flex items-center gap-4 py-4">
      <div className="h-px flex-1 bg-gradient-to-r from-transparent via-marble-400/60 to-transparent" />
      <span className="font-display text-xs font-bold tracking-[0.15em] uppercase text-marble-700">
        {turn !== null ? `Turn ${turn}` : "Pre-Game"}
      </span>
      <div className="h-px flex-1 bg-gradient-to-r from-transparent via-marble-400/60 to-transparent" />
    </div>
  );
}
