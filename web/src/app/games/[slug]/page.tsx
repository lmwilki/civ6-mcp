"use client";

import { useParams, useSearchParams, useRouter } from "next/navigation";
import { Download } from "lucide-react";
import { PageShell } from "@/components/page-shell";
import { GameDiaryView } from "@/components/game-diary-view";
import { StrategicMap } from "@/components/strategic-map";
import { useDiarySummary } from "@/lib/use-diary";

type Tab = "diary" | "map";

const BLOB_BASE = process.env.NEXT_PUBLIC_BLOB_BASE_URL;

function TabButton({ tab, active, label, setTab }: { tab: Tab; active: Tab; label: string; setTab: (t: Tab) => void }) {
  return (
    <button
      role="tab"
      aria-selected={active === tab}
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
  // "spatial" and "log" redirect to "map" and "diary" respectively
  const tab: Tab =
    rawTab === "spatial" || rawTab === "map" ? "map" :
    "diary";

  const { runId } = useDiarySummary(filename);
  const logUrl = BLOB_BASE && runId ? `${BLOB_BASE}/runs/${runId}/log.jsonl` : null;

  const setTab = (t: Tab) => {
    const url = t === "diary" ? `/games/${slug}` : `/games/${slug}?tab=${t}`;
    router.replace(url);
  };

  return (
    <PageShell active="games" footer={false}>

      {/* Tab bar */}
      <div className="shrink-0 border-b border-marble-300 bg-marble-50 px-3 sm:px-6">
        <div className="mx-auto flex max-w-4xl items-center" role="tablist">
          <TabButton tab="diary" active={tab} label="Diary" setTab={setTab} />
          <TabButton tab="map" active={tab} label="Map" setTab={setTab} />
          {logUrl && (
            <a
              href={logUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-auto inline-flex items-center gap-1.5 border-b-2 border-transparent px-4 py-2 text-sm font-medium text-marble-500 transition-colors hover:text-marble-700"
            >
              <Download className="h-3.5 w-3.5" />
              Turn Log
            </a>
          )}
        </div>
      </div>

      {/* Tab content */}
      {tab === "diary" ? (
        <GameDiaryView filename={filename} />
      ) : (
        <StrategicMap gameId={slug} />
      )}
    </PageShell>
  );
}
