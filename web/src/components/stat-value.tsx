interface StatValueProps {
  label: string;
  children: React.ReactNode;
  mono?: boolean;
}

export function StatValue({ label, children, mono = true }: StatValueProps) {
  return (
    <span className="text-marble-600">
      {label}:{" "}
      <span
        className={
          mono
            ? "font-mono tabular-nums text-marble-800"
            : "font-medium text-marble-800"
        }
      >
        {children}
      </span>
    </span>
  );
}
