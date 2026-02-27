"use client";

import { useParams, useSearchParams, useRouter } from "next/navigation";
import { PageShell } from "@/components/page-shell";
import { GameDiaryView } from "@/components/game-diary-view";
import { GameLogView } from "@/components/game-log-view";
import { SpatialView } from "@/components/spatial-view";

type Tab = "diary" | "log" | "spatial";

export default function GameDetailPage() {
  const params = useParams<{ slug: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();

  const slug = params.slug;
  const filename = `diary_${slug}.jsonl`;
  const rawTab = searchParams.get("tab");
  const tab: Tab = rawTab === "log" ? "log" : rawTab === "spatial" ? "spatial" : "diary";

  const setTab = (t: Tab) => {
    const url = t === "diary" ? `/games/${slug}` : `/games/${slug}?tab=${t}`;
    router.replace(url);
  };

  return (
    <PageShell active="games" footer={false}>

      {/* Tab bar */}
      <div className="shrink-0 border-b border-marble-300 bg-marble-50 px-3 sm:px-6">
        <div className="mx-auto flex max-w-4xl">
          <button
            onClick={() => setTab("diary")}
            className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
              tab === "diary"
                ? "border-gold-dark text-gold-dark"
                : "border-transparent text-marble-500 hover:text-marble-700"
            }`}
          >
            Diary
          </button>
          <button
            onClick={() => setTab("log")}
            className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
              tab === "log"
                ? "border-gold-dark text-gold-dark"
                : "border-transparent text-marble-500 hover:text-marble-700"
            }`}
          >
            Turn Log
          </button>
          <button
            onClick={() => setTab("spatial")}
            className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
              tab === "spatial"
                ? "border-gold-dark text-gold-dark"
                : "border-transparent text-marble-500 hover:text-marble-700"
            }`}
          >
            Spatial
          </button>
        </div>
      </div>

      {/* Tab content */}
      {tab === "diary" ? (
        <GameDiaryView filename={filename} />
      ) : tab === "log" ? (
        <GameLogView gameSlug={slug} />
      ) : (
        <SpatialView gameId={slug} />
      )}
    </PageShell>
  );
}
