"use client";

import { useParams, useSearchParams, useRouter } from "next/navigation";
import { PageShell } from "@/components/page-shell";
import { GameDiaryView } from "@/components/game-diary-view";
import { GameLogView } from "@/components/game-log-view";
import { StrategicMap } from "@/components/strategic-map";

type Tab = "diary" | "log" | "map";

function TabButton({ tab, active, label, setTab }: { tab: Tab; active: Tab; label: string; setTab: (t: Tab) => void }) {
  return (
    <button
      onClick={() => setTab(tab)}
      className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
        active === tab
          ? "border-gold-dark text-gold-dark"
          : "border-transparent text-marble-500 hover:text-marble-700"
      }`}
    >
      {label}
    </button>
  );
}

export default function GameDetailPage() {
  const params = useParams<{ slug: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();

  const slug = params.slug;
  const filename = `diary_${slug}.jsonl`;
  const rawTab = searchParams.get("tab");
  // "spatial" redirects to "map" (spatial data is now in the map tab)
  const tab: Tab =
    rawTab === "log" ? "log" :
    rawTab === "spatial" || rawTab === "map" ? "map" :
    "diary";

  const setTab = (t: Tab) => {
    const url = t === "diary" ? `/games/${slug}` : `/games/${slug}?tab=${t}`;
    router.replace(url);
  };

  return (
    <PageShell active="games" footer={false}>

      {/* Tab bar */}
      <div className="shrink-0 border-b border-marble-300 bg-marble-50 px-3 sm:px-6">
        <div className="mx-auto flex max-w-4xl">
          <TabButton tab="diary" active={tab} label="Diary" setTab={setTab} />
          <TabButton tab="log" active={tab} label="Turn Log" setTab={setTab} />
          <TabButton tab="map" active={tab} label="Map" setTab={setTab} />
        </div>
      </div>

      {/* Tab content */}
      {tab === "diary" ? (
        <GameDiaryView filename={filename} />
      ) : tab === "log" ? (
        <GameLogView gameSlug={slug} />
      ) : (
        <StrategicMap gameId={slug} />
      )}
    </PageShell>
  );
}
