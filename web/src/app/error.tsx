"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6">
      <h2 className="font-display text-xl font-bold tracking-[0.1em] uppercase text-marble-800">
        Something went wrong
      </h2>
      <p className="max-w-md text-center text-sm text-marble-600">
        {error.message || "An unexpected error occurred."}
      </p>
      <button
        onClick={reset}
        className="rounded-sm border border-marble-400 bg-marble-100 px-4 py-2 text-sm font-medium text-marble-700 transition-colors hover:border-marble-500 hover:bg-marble-200"
      >
        Try again
      </button>
    </div>
  );
}
