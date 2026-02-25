interface PulsingDotProps {
  color?: string;
  ping?: boolean;
  className?: string;
}

export function PulsingDot({
  color = "bg-patina",
  ping = true,
  className = "h-2 w-2",
}: PulsingDotProps) {
  return (
    <span className={`relative flex ${className}`}>
      {ping && (
        <span
          className={`absolute inline-flex h-full w-full animate-ping rounded-full ${color} opacity-75`}
        />
      )}
      <span
        className={`relative inline-flex ${className} rounded-full ${color}`}
      />
    </span>
  );
}
