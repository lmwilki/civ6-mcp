import { NavBar } from "@/components/nav-bar";
import { Github } from "lucide-react";

export default function DocsPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <NavBar active="docs" />

      <main className="flex-1">
        <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 sm:py-10">
          <h1 className="font-display text-2xl font-bold tracking-[0.08em] uppercase text-marble-800">
            Docs
          </h1>
          <p className="mt-2 text-sm text-marble-600">
            Setup guides, tool reference, and agent configuration.
          </p>

          <div className="mt-8 space-y-6">
            <section>
              <h2 className="font-display text-xs font-bold uppercase tracking-[0.12em] text-marble-500">
                Getting Started
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-marble-600">
                Full installation and usage instructions are maintained in the
                project README on GitHub.
              </p>
              <div className="mt-3">
                <a
                  href="https://github.com/lmwilki/civ6-mcp#readme"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-sm border border-marble-400 bg-marble-100 px-4 py-2 text-sm font-medium text-marble-700 transition-colors hover:border-marble-500 hover:bg-marble-200"
                >
                  <Github className="h-4 w-4" />
                  View README
                </a>
              </div>
            </section>
          </div>
        </div>
      </main>

      <footer className="border-t border-marble-300 px-6 py-4 text-center">
        <p className="font-mono text-xs text-marble-500">MIT License</p>
      </footer>
    </div>
  );
}
