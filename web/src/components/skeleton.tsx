/** Animated placeholder for a single line of text. */
export function SkeletonLine({ className = "w-24" }: { className?: string }) {
  return (
    <div
      className={`h-3.5 animate-pulse rounded-sm bg-marble-200/70 ${className}`}
    />
  );
}

/** Animated placeholder block with configurable height. */
export function SkeletonBlock({
  className = "h-20 w-full",
}: {
  className?: string;
}) {
  return (
    <div
      className={`animate-pulse rounded-sm bg-marble-200/70 ${className}`}
    />
  );
}
