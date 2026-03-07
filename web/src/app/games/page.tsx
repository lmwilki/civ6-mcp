"use client";

import Image from "next/image";
import { useState, useRef, useEffect } from "react";
import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ChevronDown, X } from "lucide-react";
import { PageShell } from "@/components/page-shell";
import { useDiaryList } from "@/lib/use-diary";
import { slugFromFilename } from "@/lib/diary-types";
import { getCivColors } from "@/lib/civ-colors";
import { CivSymbol } from "@/components/civ-icon";
import { getModelMeta, formatModelName } from "@/lib/model-registry";
import { LeaderPortrait } from "@/components/leader-portrait";
import {
  GameStatusBadge,
  getGameStatusColor,
  statusColor,
} from "@/components/game-status-badge";
import { SCENARIOS, DIFFICULTY_META } from "@/lib/scenarios";
import { chipBase, chipDefault, chipActive } from "@/lib/chip-styles";
import { formatTimeAgo, deriveProvider } from "@/lib/game-utils";
import {
  useGameFilters,
  SORT_OPTIONS,
  STATUS_OPTIONS,
  type Filters,
  type SortKey,
  type SortDir,
} from "@/lib/use-game-filters";

// ── Filter chip components ───────────────────────────────────

function ToggleChip({
  label,
  active,
  onClick,
  color,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  color?: string;
}) {
  return (
    <button
      className={`${chipBase} ${active ? chipActive : chipDefault}`}
      onClick={onClick}
      aria-pressed={active}
    >
      {color && (
        <span
          className="inline-block h-1.5 w-1.5 rounded-full"
          style={{ backgroundColor: color }}
        />
      )}
      {label}
    </button>
  );
}

function DropdownFilter({
  label,
  options,
  selected,
  onToggle,
  renderOption,
}: {
  label: string;
  options: string[];
  selected: Set<string>;
  onToggle: (val: string) => void;
  renderOption?: (val: string) => React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open]);

  const filtered = search
    ? options.filter((o) => o.toLowerCase().includes(search.toLowerCase()))
    : options;

  const count = selected.size;

  return (
    <div className="relative" ref={ref}>
      <button
        className={`${chipBase} ${count > 0 ? chipActive : chipDefault}`}
        onClick={() => setOpen(!open)}
      >
        {label}
        {count > 0 && (
          <span className="font-mono text-xs">({count})</span>
        )}
        <ChevronDown className="h-2.5 w-2.5" />
      </button>
      {open && (
        <div className="absolute left-0 top-full z-20 mt-1 min-w-[160px] rounded-sm border border-marble-300/50 bg-marble-50 shadow-sm">
          {options.length > 6 && (
            <div className="border-b border-marble-300/30 px-2 py-1.5">
              <input
                type="text"
                placeholder="Search..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-transparent text-xs text-marble-700 placeholder-marble-400 outline-none"
                autoFocus
              />
            </div>
          )}
          <div className="max-h-48 overflow-y-auto py-1">
            {filtered.map((opt) => (
              <button
                key={opt}
                className="flex w-full items-center gap-2 px-2 py-1 text-left text-xs text-marble-700 transition-colors hover:bg-marble-100"
                onClick={() => onToggle(opt)}
              >
                <span
                  className={`inline-flex h-3 w-3 shrink-0 items-center justify-center rounded-sm border text-[9px] ${
                    selected.has(opt)
                      ? "border-gold-dark bg-gold-dark/20 text-gold-dark"
                      : "border-marble-400"
                  }`}
                >
                  {selected.has(opt) && "✓"}
                </span>
                {renderOption ? renderOption(opt) : opt}
              </button>
            ))}
            {filtered.length === 0 && (
              <p className="px-2 py-1.5 text-xs text-marble-400">
                No matches
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Sortable column header ───────────────────────────────────

function SortTh({
  label,
  sortKey: colKey,
  activeSortKey,
  activeSortDir,
  onSort,
  className,
}: {
  label: string;
  sortKey: SortKey;
  activeSortKey: SortKey;
  activeSortDir: SortDir;
  onSort: (key: SortKey) => void;
  className?: string;
}) {
  const isActive = activeSortKey === colKey;
  return (
    <th
      className={`px-3 py-2.5 cursor-pointer select-none transition-colors hover:text-marble-700 ${className ?? ""}`}
      onClick={() => onSort(colKey)}
    >
      <span className="inline-flex items-center gap-0.5">
        {label}
        {isActive && (
          <span className="text-gold-dark">
            {activeSortDir === "desc" ? "▼" : "▲"}
          </span>
        )}
      </span>
    </th>
  );
}

// ── Main page ────────────────────────────────────────────────

export default function GamesPage() {
  return (
    <Suspense>
      <GamesPageInner />
    </Suspense>
  );
}

function GamesPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const games = useDiaryList();

  const {
    filters,
    sortKey,
    sortDir,
    filterOptions,
    sorted,
    active,
    toggleFilter,
    clearFilters,
    handleSort,
  } = useGameFilters(games, searchParams.get("scenario"));

  return (
    <PageShell active="games">
      <main className="flex-1 px-3 py-6 sm:px-6 sm:py-10">
        <div className="mx-auto max-w-5xl">
          <h2 className="font-display text-3xl font-bold tracking-[0.08em] uppercase text-marble-800">
            Games
          </h2>
          <p className="mt-1 text-base text-marble-500">
            Turn-by-turn diaries, agent reflections, and strategic maps.
          </p>

          {games.length === 0 ? (
            <div className="mt-12 flex items-center justify-center">
              <p className="font-display text-sm tracking-[0.08em] uppercase text-marble-500">
                No games yet
              </p>
            </div>
          ) : (
            <>
              {/* Filter bar */}
              <div className="mt-5 flex flex-wrap items-center gap-2">
                {/* Status — inline toggles */}
                {STATUS_OPTIONS.map((s) => (
                  <ToggleChip
                    key={s}
                    label={s}
                    active={filters.status.has(s)}
                    onClick={() => toggleFilter("status", s)}
                    color={statusColor(s)}
                  />
                ))}

                <span className="mx-1 h-4 w-px bg-marble-300/50" />

                {/* Civ dropdown */}
                {filterOptions.civs.length > 0 && (
                  <DropdownFilter
                    label="Civ"
                    options={filterOptions.civs}
                    selected={filters.civs}
                    onToggle={(v) => toggleFilter("civs", v)}
                    renderOption={(civ) => (
                      <span className="inline-flex items-center gap-1.5">
                        <CivSymbol civ={civ} className="h-3 w-3" />
                        {civ}
                      </span>
                    )}
                  />
                )}

                {/* Provider dropdown */}
                {filterOptions.providers.length > 0 && (
                  <DropdownFilter
                    label="Provider"
                    options={filterOptions.providers}
                    selected={filters.providers}
                    onToggle={(v) => toggleFilter("providers", v)}
                    renderOption={(provider) => {
                      const model = games.find((g) => deriveProvider(g) === provider)?.agentModel;
                      const logo = model ? getModelMeta(model).providerLogo : "";
                      return (
                        <span className="inline-flex items-center gap-1.5">
                          {logo && (
                            <Image src={logo} alt="" width={10} height={10} className="h-2.5 w-2.5" />
                          )}
                          {provider}
                        </span>
                      );
                    }}
                  />
                )}

                {/* Model dropdown */}
                {filterOptions.models.length > 0 && (
                  <DropdownFilter
                    label="Model"
                    options={filterOptions.models}
                    selected={filters.models}
                    onToggle={(v) => toggleFilter("models", v)}
                    renderOption={(model) => (
                      <span className="inline-flex items-center gap-1.5">
                        {getModelMeta(model).providerLogo && (
                          <Image
                            src={getModelMeta(model).providerLogo}
                            alt=""
                            width={10}
                            height={10}
                            className="h-2.5 w-2.5"
                          />
                        )}
                        {formatModelName(model)}
                      </span>
                    )}
                  />
                )}

                {/* Victory type dropdown */}
                {filterOptions.victoryTypes.length > 0 && (
                  <DropdownFilter
                    label="Victory"
                    options={filterOptions.victoryTypes}
                    selected={filters.victoryTypes}
                    onToggle={(v) => toggleFilter("victoryTypes", v)}
                  />
                )}

                {/* Scenario dropdown */}
                {filterOptions.scenarios.length > 0 && (
                  <DropdownFilter
                    label="Scenario"
                    options={filterOptions.scenarios}
                    selected={filters.scenarios}
                    onToggle={(v) => toggleFilter("scenarios", v)}
                    renderOption={(id) => (
                      <span className="inline-flex items-center gap-1.5">
                        <span
                          className="inline-block h-1.5 w-1.5 rounded-full"
                          style={{ backgroundColor: DIFFICULTY_META[SCENARIOS[id]?.difficulty]?.color }}
                        />
                        {SCENARIOS[id]?.name ?? id}
                      </span>
                    )}
                  />
                )}

                {/* Difficulty dropdown */}
                {filterOptions.difficulties.length > 0 && (
                  <DropdownFilter
                    label="Difficulty"
                    options={filterOptions.difficulties}
                    selected={filters.difficulties}
                    onToggle={(v) => toggleFilter("difficulties", v)}
                    renderOption={(d) => (
                      <span className="inline-flex items-center gap-1.5">
                        <span
                          className="inline-block h-1.5 w-1.5 rounded-full"
                          style={{ backgroundColor: DIFFICULTY_META[d]?.color }}
                        />
                        {d}
                      </span>
                    )}
                  />
                )}

                {active && (
                  <button
                    className="inline-flex items-center gap-0.5 text-xs font-medium text-marble-500 transition-colors hover:text-marble-700"
                    onClick={clearFilters}
                  >
                    <X className="h-2.5 w-2.5" />
                    Clear
                  </button>
                )}

                {/* Sort selector — pushed right */}
                <div className="ml-auto flex items-center gap-1.5">
                  <span className="text-xs font-bold uppercase tracking-[0.08em] text-marble-400">
                    Sort
                  </span>
                  {SORT_OPTIONS.map((opt) => (
                    <button
                      key={opt.key}
                      className={`${chipBase} ${sortKey === opt.key ? chipActive : chipDefault}`}
                      onClick={() => handleSort(opt.key)}
                    >
                      {opt.label}
                      {sortKey === opt.key && (
                        <span className="text-[9px]">
                          {sortDir === "desc" ? "▼" : "▲"}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Table */}
              {sorted.length === 0 ? (
                <div className="mt-8 flex flex-col items-center justify-center gap-2">
                  <p className="font-display text-sm tracking-[0.08em] uppercase text-marble-500">
                    No games match filters
                  </p>
                  <button
                    onClick={clearFilters}
                    className="text-xs text-marble-500 underline transition-colors hover:text-marble-700"
                  >
                    Clear filters
                  </button>
                </div>
              ) : (
                <div className="mt-3 overflow-x-auto rounded-sm border border-marble-300/50">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-marble-300/50 bg-marble-100 text-left text-xs font-bold uppercase tracking-[0.08em] text-marble-500">
                        <th className="px-3 py-2.5">Game</th>
                        <th className="hidden px-3 py-2.5 sm:table-cell">
                          Model
                        </th>
                        <SortTh
                          label="Score"
                          sortKey="score"
                          activeSortKey={sortKey}
                          activeSortDir={sortDir}
                          onSort={handleSort}
                          className="hidden text-right md:table-cell"
                        />
                        <SortTh
                          label="Updated"
                          sortKey="updated"
                          activeSortKey={sortKey}
                          activeSortDir={sortDir}
                          onSort={handleSort}
                          className="hidden text-right md:table-cell"
                        />
                        <SortTh
                          label="Result"
                          sortKey="turns"
                          activeSortKey={sortKey}
                          activeSortDir={sortDir}
                          onSort={handleSort}
                          className="text-right"
                        />
                      </tr>
                    </thead>
                    <tbody>
                      {sorted.map((game) => {
                        const slug = slugFromFilename(game.filename);
                        const colors = getCivColors(game.label, game.leader);
                        const modelMeta = game.agentModel
                          ? getModelMeta(game.agentModel)
                          : null;

                        return (
                          <tr
                            key={game.filename}
                            className="border-b border-marble-300/30 last:border-0 transition-colors hover:bg-marble-100/50 cursor-pointer"
                            style={{
                              borderLeftWidth: 5,
                              borderLeftColor: getGameStatusColor(
                                game.status,
                                game.outcome,
                              ),
                            }}
                            onClick={() => {
                              router.push(`/games/${slug}`);
                            }}
                          >
                            {/* Game — portrait + civ info */}
                            <td className="px-3 py-2">
                              <div className="flex items-center gap-2.5">
                                <LeaderPortrait
                                  leader={game.leader}
                                  agentModel={game.agentModel}
                                  fallbackColor={colors.primary}
                                  size="md"
                                />
                                <div className="min-w-0">
                                  <div className="flex items-center gap-1.5">
                                    <CivSymbol civ={game.label} />
                                    <span className="font-display text-sm font-bold tracking-wide uppercase text-marble-800">
                                      {game.label}
                                    </span>
                                  </div>
                                  {game.leader && (
                                    <p className="mt-0.5 text-xs text-marble-500 truncate">
                                      {game.leader}
                                    </p>
                                  )}
                                  {game.scenarioId && SCENARIOS[game.scenarioId] && (
                                    <p className="mt-0.5 flex items-center gap-1 text-xs text-marble-400">
                                      <span
                                        className="inline-block h-1.5 w-1.5 rounded-full"
                                        style={{ backgroundColor: DIFFICULTY_META[game.difficulty ?? ""]?.color }}
                                      />
                                      {SCENARIOS[game.scenarioId].name}
                                      {game.difficulty && (
                                        <span className="text-marble-400">
                                          &middot; {game.difficulty}
                                        </span>
                                      )}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </td>

                            {/* Model */}
                            <td className="hidden px-3 py-2 sm:table-cell">
                              {modelMeta ? (
                                <div className="flex items-center gap-1.5">
                                  {modelMeta.providerLogo && (
                                    <Image
                                      src={modelMeta.providerLogo}
                                      alt=""
                                      width={14}
                                      height={14}
                                      className="h-3.5 w-3.5"
                                    />
                                  )}
                                  <span className="text-sm text-marble-600">
                                    {formatModelName(game.agentModel!)}
                                  </span>
                                </div>
                              ) : (
                                <span className="text-xs text-marble-400">
                                  &mdash;
                                </span>
                              )}
                            </td>

                            {/* Score */}
                            <td className="hidden px-3 py-2 text-right md:table-cell">
                              {game.score != null ? (
                                <span className="font-mono text-sm tabular-nums text-marble-600">
                                  {game.score}
                                </span>
                              ) : (
                                <span className="text-xs text-marble-400">
                                  &mdash;
                                </span>
                              )}
                            </td>

                            {/* Updated */}
                            <td className="hidden px-3 py-2 text-right md:table-cell">
                              {game.lastUpdated ? (
                                <span className="text-sm text-marble-500">
                                  {formatTimeAgo(game.lastUpdated)}
                                </span>
                              ) : (
                                <span className="text-xs text-marble-400">
                                  &mdash;
                                </span>
                              )}
                            </td>

                            {/* Result — merged status + outcome + turns */}
                            <td className="px-3 py-2">
                              <GameStatusBadge
                                status={game.status}
                                outcome={game.outcome}
                                turnCount={game.count}
                              />
                              {game.outcome?.winnerLeader && (
                                <p className="mt-0.5 text-right text-xs text-marble-400">
                                  {game.outcome.winnerLeader}
                                </p>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </PageShell>
  );
}
