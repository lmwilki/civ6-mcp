import { useCallback, useMemo, useState } from "react";
import type { DiaryFile } from "./diary-types";
import { deriveStatus, deriveProvider, deriveVictoryLabel } from "./game-utils";
import { SCENARIOS, DIFFICULTY_META } from "./scenarios";

// ── Types ────────────────────────────────────────────────────

export interface Filters {
  status: Set<string>;
  civs: Set<string>;
  providers: Set<string>;
  models: Set<string>;
  victoryTypes: Set<string>;
  scenarios: Set<string>;
  difficulties: Set<string>;
}

export type SortKey = "updated" | "score" | "turns";
export type SortDir = "asc" | "desc";

export const SORT_OPTIONS: { key: SortKey; label: string }[] = [
  { key: "updated", label: "Updated" },
  { key: "score", label: "Score" },
  { key: "turns", label: "Turns" },
];

export const STATUS_OPTIONS = ["live", "victory", "defeat", "unfinished"];

const EMPTY_FILTERS: Filters = {
  status: new Set(),
  civs: new Set(),
  providers: new Set(),
  models: new Set(),
  victoryTypes: new Set(),
  scenarios: new Set(),
  difficulties: new Set(),
};

export function hasActiveFilters(f: Filters): boolean {
  return (
    f.status.size + f.civs.size + f.providers.size + f.models.size +
    f.victoryTypes.size + f.scenarios.size + f.difficulties.size > 0
  );
}

// ── Hook ─────────────────────────────────────────────────────

export function useGameFilters(
  games: DiaryFile[],
  initialScenario?: string | null,
) {
  const [filters, setFilters] = useState<Filters>(() => {
    if (initialScenario && SCENARIOS[initialScenario]) {
      return { ...EMPTY_FILTERS, scenarios: new Set([initialScenario]) };
    }
    return EMPTY_FILTERS;
  });
  const [sortKey, setSortKey] = useState<SortKey>("updated");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const toggleFilter = useCallback(
    (field: keyof Filters, value: string) => {
      setFilters((prev) => {
        const next = new Set(prev[field]);
        if (next.has(value)) next.delete(value);
        else next.add(value);
        return { ...prev, [field]: next };
      });
    },
    [],
  );

  const clearFilters = useCallback(() => setFilters(EMPTY_FILTERS), []);

  const handleSort = useCallback(
    (key: SortKey) => {
      if (key === sortKey) {
        setSortDir((d) => (d === "desc" ? "asc" : "desc"));
      } else {
        setSortKey(key);
        setSortDir("desc");
      }
    },
    [sortKey],
  );

  // Derive available filter options from data
  const filterOptions = useMemo(() => {
    const civs = [...new Set(games.map((g) => g.label))].sort();
    const providers = [...new Set(games.map(deriveProvider))].sort();
    const models = [
      ...new Set(
        games.map((g) => g.agentModel).filter((m): m is string => !!m),
      ),
    ].sort();
    const victoryTypes = [
      ...new Set(
        games.map(deriveVictoryLabel).filter((v): v is string => v !== null),
      ),
    ].sort();
    const scenarios = [
      ...new Set(
        games.map((g) => g.scenarioId).filter((s): s is string => !!s),
      ),
    ].sort();
    const difficulties = [
      ...new Set(
        games.map((g) => g.difficulty).filter((d): d is string => !!d),
      ),
    ].sort(
      (a, b) => (DIFFICULTY_META[a]?.order ?? 99) - (DIFFICULTY_META[b]?.order ?? 99),
    );
    return { civs, providers, models, victoryTypes, scenarios, difficulties };
  }, [games]);

  // Filter
  const filtered = useMemo(() => {
    return games.filter((game) => {
      if (filters.status.size > 0 && !filters.status.has(deriveStatus(game)))
        return false;
      if (filters.civs.size > 0 && !filters.civs.has(game.label)) return false;
      if (filters.providers.size > 0 && !filters.providers.has(deriveProvider(game)))
        return false;
      if (filters.models.size > 0 && (!game.agentModel || !filters.models.has(game.agentModel)))
        return false;
      if (filters.victoryTypes.size > 0) {
        const vt = deriveVictoryLabel(game);
        if (!vt || !filters.victoryTypes.has(vt)) return false;
      }
      if (filters.scenarios.size > 0 && (!game.scenarioId || !filters.scenarios.has(game.scenarioId)))
        return false;
      if (filters.difficulties.size > 0 && (!game.difficulty || !filters.difficulties.has(game.difficulty)))
        return false;
      return true;
    });
  }, [games, filters]);

  // Sort
  const sorted = useMemo(() => {
    const dir = sortDir === "desc" ? -1 : 1;
    return [...filtered].sort((a, b) => {
      // Live games always first regardless of sort
      if (a.status === "live" && b.status !== "live") return -1;
      if (b.status === "live" && a.status !== "live") return 1;

      let cmp = 0;
      switch (sortKey) {
        case "updated":
          cmp = (a.lastUpdated ?? 0) - (b.lastUpdated ?? 0);
          break;
        case "score":
          cmp = (a.score ?? 0) - (b.score ?? 0);
          break;
        case "turns":
          cmp = a.count - b.count;
          break;
      }
      return cmp * dir;
    });
  }, [filtered, sortKey, sortDir]);

  const active = hasActiveFilters(filters);

  return {
    filters,
    sortKey,
    sortDir,
    filterOptions,
    sorted,
    active,
    toggleFilter,
    clearFilters,
    handleSort,
  };
}
