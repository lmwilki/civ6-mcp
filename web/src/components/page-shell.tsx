import { NavBar } from "./nav-bar";

interface PageShellProps {
  active: "home" | "about" | "docs" | "games" | "leaderboard";
  connected?: boolean;
  turn?: number | null;
  footer?: boolean;
  children: React.ReactNode;
}

export function PageShell({
  active,
  connected,
  turn,
  footer = true,
  children,
}: PageShellProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <NavBar active={active} connected={connected} turn={turn} />
      {children}
      {footer && (
        <footer className="border-t border-marble-300 px-6 py-4 text-center">
          <p className="font-mono text-xs text-marble-500">MIT License</p>
        </footer>
      )}
    </div>
  );
}
