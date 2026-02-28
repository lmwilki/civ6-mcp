"use client";

import { useMemo, useState } from "react";
import { useQuery } from "convex/react";
import { api } from "../../convex/_generated/api";
import type { SpatialTurn } from "@/lib/diary-types";
import { unpackSpatialTiles } from "@/lib/diary-types";
import type { SpatialTile } from "@/lib/diary-types";
import { CivIcon } from "./civ-icon";
import { CIV6_COLORS } from "@/lib/civ-colors";
import {
  ScanSearch,
  Eye,
  Zap,
  Crosshair,
  Radio,
  Radar,
  MousePointerClick,
  Bell,
  Map as MapIcon,
} from "lucide-react";

// Attention type metadata for display
const ATTENTION_TYPES = [
  { key: "deliberate_scan" as const, label: "Deliberate Scan", color: "#9333EA", icon: Crosshair },
  { key: "deliberate_action" as const, label: "Deliberate Action", color: "#D4A853", icon: MousePointerClick },
  { key: "survey" as const, label: "Survey", color: "#44B3EA", icon: Radar },
  { key: "peripheral" as const, label: "Peripheral", color: "#7A9B8A", icon: Radio },
  { key: "reactive" as const, label: "Reactive", color: "#C4785C", icon: Bell },
] as const;

interface SpatialViewProps {
  gameId: string;
}

export function SpatialView({ gameId }: SpatialViewProps) {
  const rawData = useQuery(api.diary.getSpatialTurns, { gameId });
  const data: SpatialTurn[] | undefined = rawData as SpatialTurn[] | undefined;

  const stats = useMemo(() => {
    if (!data || data.length === 0) return null;
    const lastTurn = data[data.length - 1];
    const peakTiles = Math.max(...data.map((d) => d.tiles_observed));
    const avgTiles = Math.round(
      data.reduce((s, d) => s + d.tiles_observed, 0) / data.length,
    );
    const totalToolCalls = data.reduce((s, d) => s + d.tool_calls, 0);
    const totalMs = data.reduce((s, d) => s + d.total_ms, 0);
    const totalByType = ATTENTION_TYPES.map((t) => ({
      ...t,
      count: data.reduce((s, d) => s + d.by_type[t.key], 0),
    }));
    return {
      cumulativeTiles: lastTurn.cumulative_tiles,
      peakTiles,
      avgTiles,
      totalToolCalls,
      totalMs,
      totalByType,
      turns: data.length,
    };
  }, [data]);

  if (data === undefined) {
    return (
      <div className="flex flex-1 items-center justify-center py-20 text-marble-500">
        Loading spatial data...
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 py-20">
        <CivIcon icon={ScanSearch} color={CIV6_COLORS.spatial} size="md" />
        <p className="text-sm text-marble-500">
          No spatial attention data recorded for this game.
        </p>
        <p className="max-w-md text-center text-xs text-marble-400">
          Spatial tracking records which map tiles the agent observes through
          each tool call. Data appears once the game runs with the spatial
          tracker enabled.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-3 py-6 sm:px-6">
      {/* Summary stats */}
      {stats && <StatsBar stats={stats} />}

      {/* Hex heatmap */}
      <ChartSection title="Attention Heatmap" icon={MapIcon} color={CIV6_COLORS.spatial}>
        <HexHeatmap gameId={gameId} />
      </ChartSection>

      {/* Coverage chart */}
      <ChartSection title="Cumulative Coverage" icon={Eye} color={CIV6_COLORS.spatial}>
        <CoverageChart data={data} />
      </ChartSection>

      {/* Tiles per turn */}
      <ChartSection title="Tiles Observed Per Turn" icon={ScanSearch} color={CIV6_COLORS.spatial}>
        <TilesPerTurnChart data={data} />
      </ChartSection>

      {/* Attention type breakdown */}
      <ChartSection title="Attention Type Breakdown" icon={Zap} color={CIV6_COLORS.goldMetal}>
        <AttentionStackedChart data={data} />
      </ChartSection>
    </div>
  );
}

// ── Stats bar ────────────────────────────────────────────────────────────

function StatsBar({
  stats,
}: {
  stats: {
    cumulativeTiles: number;
    peakTiles: number;
    avgTiles: number;
    totalToolCalls: number;
    totalMs: number;
    totalByType: { key: string; label: string; color: string; count: number }[];
    turns: number;
  };
}) {
  const statItems = [
    { label: "Unique Tiles", value: stats.cumulativeTiles.toLocaleString() },
    { label: "Peak/Turn", value: stats.peakTiles.toLocaleString() },
    { label: "Avg/Turn", value: stats.avgTiles.toLocaleString() },
    { label: "Spatial Queries", value: stats.totalToolCalls.toLocaleString() },
    {
      label: "Query Time",
      value: stats.totalMs > 60_000
        ? `${(stats.totalMs / 60_000).toFixed(1)}m`
        : `${(stats.totalMs / 1000).toFixed(1)}s`,
    },
  ];

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-3">
        {statItems.map((s) => (
          <div
            key={s.label}
            className="flex-1 rounded-sm border border-marble-300 bg-marble-100 px-3 py-2 text-center"
            style={{ minWidth: 100 }}
          >
            <div className="font-mono text-lg font-semibold tabular-nums text-marble-800">
              {s.value}
            </div>
            <div className="text-[10px] font-medium uppercase tracking-wider text-marble-500">
              {s.label}
            </div>
          </div>
        ))}
      </div>
      {/* Attention type pills */}
      <div className="flex flex-wrap gap-2">
        {stats.totalByType.map((t) => (
          <div
            key={t.key}
            className="flex items-center gap-1.5 rounded-full border border-marble-300 bg-marble-50 px-2.5 py-1"
          >
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ backgroundColor: t.color }}
            />
            <span className="text-[10px] font-medium text-marble-600">
              {t.label}
            </span>
            <span className="font-mono text-[10px] tabular-nums text-marble-700">
              {t.count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Chart wrapper ────────────────────────────────────────────────────────

function ChartSection({
  title,
  icon,
  color,
  children,
}: {
  title: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  color: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-sm border border-marble-300 bg-marble-50 p-4">
      <h3 className="mb-3 flex items-center gap-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
        <CivIcon icon={icon} color={color} size="sm" />
        {title}
      </h3>
      {children}
    </div>
  );
}

// ── Coverage chart (cumulative unique tiles) ─────────────────────────────

const CHART_W = 600;
const CHART_H = 160;
const CHART_PAD = 24;

function computeTurnLabels(
  data: SpatialTurn[],
  toX: (i: number) => number,
): { turn: number; x: number }[] {
  if (data.length <= 1) return [];
  const step = Math.max(1, Math.floor(data.length / 5));
  const result: { turn: number; x: number }[] = [];
  for (let i = 0; i < data.length; i += step) {
    result.push({ turn: data[i].turn, x: toX(i) });
  }
  return result;
}

function CoverageChart({ data }: { data: SpatialTurn[] }) {
  const { points, max, labels } = useMemo(() => {
    const vals = data.map((d) => d.cumulative_tiles);
    const mn = 0;
    const mx = Math.max(...vals) || 1;
    const pts = vals
      .map((v, i) => {
        const x =
          CHART_PAD + (i / Math.max(vals.length - 1, 1)) * (CHART_W - 2 * CHART_PAD);
        const y =
          CHART_H -
          CHART_PAD -
          ((v - mn) / (mx - mn)) * (CHART_H - 2 * CHART_PAD);
        return `${x},${y}`;
      })
      .join(" ");

    // Y-axis labels
    const lbls = [0, Math.round(mx / 2), mx];

    return { points: pts, max: mx, labels: lbls };
  }, [data]);

  const turnLabels = useMemo(
    () =>
      computeTurnLabels(data, (i) =>
        CHART_PAD + (i / Math.max(data.length - 1, 1)) * (CHART_W - 2 * CHART_PAD),
      ),
    [data],
  );

  return (
    <svg viewBox={`0 0 ${CHART_W} ${CHART_H}`} className="h-40 w-full">
      {/* Y-axis labels */}
      {labels.map((l) => {
        const y =
          CHART_H - CHART_PAD - (l / (max || 1)) * (CHART_H - 2 * CHART_PAD);
        return (
          <g key={l}>
            <line
              x1={CHART_PAD}
              y1={y}
              x2={CHART_W - CHART_PAD}
              y2={y}
              stroke="#E0DBD3"
              strokeWidth="0.5"
            />
            <text
              x={CHART_PAD - 4}
              y={y + 3}
              textAnchor="end"
              fill="#A39B8F"
              fontSize="8"
              fontFamily="monospace"
            >
              {l}
            </text>
          </g>
        );
      })}
      {/* X-axis labels */}
      {turnLabels.map((tl) => (
        <text
          key={tl.turn}
          x={tl.x}
          y={CHART_H - 4}
          textAnchor="middle"
          fill="#A39B8F"
          fontSize="8"
          fontFamily="monospace"
        >
          T{tl.turn}
        </text>
      ))}
      {/* Area fill */}
      <polygon
        points={`${CHART_PAD},${CHART_H - CHART_PAD} ${points} ${CHART_W - CHART_PAD},${CHART_H - CHART_PAD}`}
        fill={CIV6_COLORS.spatial}
        opacity="0.1"
      />
      {/* Line */}
      <polyline
        points={points}
        fill="none"
        stroke={CIV6_COLORS.spatial}
        strokeWidth="2"
        strokeLinejoin="round"
        opacity="0.8"
      />
    </svg>
  );
}

// ── Tiles per turn bar chart ─────────────────────────────────────────────

function TilesPerTurnChart({ data }: { data: SpatialTurn[] }) {
  const { bars, max } = useMemo(() => {
    const mx = Math.max(...data.map((d) => d.tiles_observed)) || 1;
    const barWidth =
      (CHART_W - 2 * CHART_PAD) / Math.max(data.length, 1) - 1;
    const bs = data.map((d, i) => {
      const h =
        (d.tiles_observed / mx) * (CHART_H - 2 * CHART_PAD);
      const x =
        CHART_PAD +
        (i / Math.max(data.length, 1)) * (CHART_W - 2 * CHART_PAD);
      const y = CHART_H - CHART_PAD - h;
      return { x, y, width: Math.max(barWidth, 1), height: h, turn: d.turn };
    });
    return { bars: bs, max: mx };
  }, [data]);

  const turnLabels = useMemo(
    () =>
      computeTurnLabels(data, (i) =>
        CHART_PAD + (i / Math.max(data.length, 1)) * (CHART_W - 2 * CHART_PAD),
      ),
    [data],
  );

  return (
    <svg viewBox={`0 0 ${CHART_W} ${CHART_H}`} className="h-40 w-full">
      {/* Grid lines */}
      {[0, 0.5, 1].map((frac) => {
        const val = Math.round(max * frac);
        const y =
          CHART_H - CHART_PAD - frac * (CHART_H - 2 * CHART_PAD);
        return (
          <g key={frac}>
            <line
              x1={CHART_PAD}
              y1={y}
              x2={CHART_W - CHART_PAD}
              y2={y}
              stroke="#E0DBD3"
              strokeWidth="0.5"
            />
            <text
              x={CHART_PAD - 4}
              y={y + 3}
              textAnchor="end"
              fill="#A39B8F"
              fontSize="8"
              fontFamily="monospace"
            >
              {val}
            </text>
          </g>
        );
      })}
      {/* X-axis labels */}
      {turnLabels.map((tl) => (
        <text
          key={tl.turn}
          x={tl.x}
          y={CHART_H - 4}
          textAnchor="middle"
          fill="#A39B8F"
          fontSize="8"
          fontFamily="monospace"
        >
          T{tl.turn}
        </text>
      ))}
      {/* Bars */}
      {bars.map((b) => (
        <rect
          key={b.turn}
          x={b.x}
          y={b.y}
          width={b.width}
          height={b.height}
          fill={CIV6_COLORS.spatial}
          opacity="0.6"
          rx="1"
        />
      ))}
    </svg>
  );
}

// ── Attention type stacked area chart ────────────────────────────────────

function AttentionStackedChart({ data }: { data: SpatialTurn[] }) {
  const { areas, maxTotal, turnLabels } = useMemo(() => {
    if (data.length === 0) return { areas: [], maxTotal: 1, turnLabels: [] };

    // Compute stacked values per turn
    const keys = ATTENTION_TYPES.map((t) => t.key);
    const stacked = data.map((d) => {
      const values: number[] = [];
      let cumulative = 0;
      for (const key of keys) {
        cumulative += d.by_type[key];
        values.push(cumulative);
      }
      return values;
    });

    const mx = Math.max(...stacked.map((s) => s[s.length - 1])) || 1;

    function toX(i: number) {
      return (
        CHART_PAD +
        (i / Math.max(data.length - 1, 1)) * (CHART_W - 2 * CHART_PAD)
      );
    }
    function toY(val: number) {
      return (
        CHART_H - CHART_PAD - (val / mx) * (CHART_H - 2 * CHART_PAD)
      );
    }

    // Build area paths (bottom-up)
    const areaData = keys.map((_, layerIdx) => {
      const topLine = stacked.map((s, i) => `${toX(i)},${toY(s[layerIdx])}`);
      const bottomLine =
        layerIdx === 0
          ? data.map((_, i) => `${toX(i)},${toY(0)}`)
          : stacked.map((s, i) => `${toX(i)},${toY(s[layerIdx - 1])}`);

      const polygon = [...topLine, ...bottomLine.reverse()].join(" ");
      return {
        key: keys[layerIdx],
        color: ATTENTION_TYPES[layerIdx].color,
        polygon,
      };
    });

    const tLabels = computeTurnLabels(data, toX);

    return { areas: areaData, maxTotal: mx, turnLabels: tLabels };
  }, [data]);

  return (
    <div>
      <svg viewBox={`0 0 ${CHART_W} ${CHART_H}`} className="h-40 w-full">
        {/* Grid lines */}
        {[0, 0.5, 1].map((frac) => {
          const val = Math.round(maxTotal * frac);
          const y =
            CHART_H - CHART_PAD - frac * (CHART_H - 2 * CHART_PAD);
          return (
            <g key={frac}>
              <line
                x1={CHART_PAD}
                y1={y}
                x2={CHART_W - CHART_PAD}
                y2={y}
                stroke="#E0DBD3"
                strokeWidth="0.5"
              />
              <text
                x={CHART_PAD - 4}
                y={y + 3}
                textAnchor="end"
                fill="#A39B8F"
                fontSize="8"
                fontFamily="monospace"
              >
                {val}
              </text>
            </g>
          );
        })}
        {/* X-axis labels */}
        {turnLabels.map((tl) => (
          <text
            key={tl.turn}
            x={tl.x}
            y={CHART_H - 4}
            textAnchor="middle"
            fill="#A39B8F"
            fontSize="8"
            fontFamily="monospace"
          >
            T{tl.turn}
          </text>
        ))}
        {/* Stacked areas */}
        {areas.map((area) => (
          <polygon
            key={area.key}
            points={area.polygon}
            fill={area.color}
            opacity="0.5"
          />
        ))}
      </svg>
      {/* Legend */}
      <div className="mt-2 flex flex-wrap gap-3">
        {ATTENTION_TYPES.map((t) => {
          const Icon = t.icon;
          return (
            <div key={t.key} className="flex items-center gap-1">
              <Icon
                className="h-3 w-3"
                style={{ color: t.color }}
              />
              <span className="text-[10px] text-marble-600">{t.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Hex heatmap ──────────────────────────────────────────────────────────

const SQRT3 = Math.sqrt(3);

/** Short key → ATTENTION_TYPES index for color lookup */
const TYPE_SHORT_KEYS = [
  { short: "ds", key: "deliberate_scan" },
  { short: "da", key: "deliberate_action" },
  { short: "sv", key: "survey" },
  { short: "pe", key: "peripheral" },
  { short: "re", key: "reactive" },
] as const;

function hexColor(count: number, maxCount: number): string {
  if (count === 0) return "transparent";
  const t = Math.log(count + 1) / Math.log(maxCount + 1);
  const alpha = 0.15 + t * 0.75;
  return `rgba(147, 51, 234, ${alpha.toFixed(3)})`;
}

/** Flat-top hex polygon points centered at (cx, cy) with size s */
function hexPoints(cx: number, cy: number, s: number): string {
  const h = (SQRT3 / 2) * s;
  return [
    [cx + s, cy],
    [cx + s / 2, cy + h],
    [cx - s / 2, cy + h],
    [cx - s, cy],
    [cx - s / 2, cy - h],
    [cx + s / 2, cy - h],
  ]
    .map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`)
    .join(" ");
}

function HexHeatmap({ gameId }: { gameId: string }) {
  const rawMap = useQuery(api.diary.getSpatialMap, { gameId });
  const [activeTypes, setActiveTypes] = useState<Set<string>>(
    new Set(["ds", "da", "sv", "pe", "re"]),
  );
  const [hovered, setHovered] = useState<SpatialTile | null>(null);

  const computed = useMemo(() => {
    if (!rawMap) return null;

    const tiles = unpackSpatialTiles(rawMap.tiles);
    const gridW = rawMap.maxX - rawMap.minX + 1;
    const gridH = rawMap.maxY - rawMap.minY + 1;

    // Auto-size hexes to fit ~700px wide
    const hexSize = Math.min(10, 700 / (gridW * 1.5 + 0.5));
    const hexH = SQRT3 * hexSize;
    const svgW = gridW * 1.5 * hexSize + hexSize * 2;
    const svgH = (gridH + 0.5) * hexH + hexSize;

    // Compute filtered count per tile
    const tilesWithCount = tiles.map((t) => {
      let count = 0;
      if (activeTypes.has("ds")) count += t.ds;
      if (activeTypes.has("da")) count += t.da;
      if (activeTypes.has("sv")) count += t.sv;
      if (activeTypes.has("pe")) count += t.pe;
      if (activeTypes.has("re")) count += t.re;
      return { ...t, filteredCount: count };
    });

    const maxCount = Math.max(1, ...tilesWithCount.map((t) => t.filteredCount));

    // Compute pixel positions for each tile (flat-top offset coordinates)
    const hexes = tilesWithCount
      .filter((t) => t.filteredCount > 0)
      .map((t) => {
        const col = t.x - rawMap.minX;
        const row = t.y - rawMap.minY;
        const cx = hexSize + col * 1.5 * hexSize;
        const cy = hexH / 2 + row * hexH + (col % 2 !== 0 ? hexH / 2 : 0);
        return { ...t, cx, cy };
      });

    return { hexes, maxCount, svgW, svgH, hexSize, tileCount: tiles.length };
  }, [rawMap, activeTypes]);

  if (!rawMap) {
    return (
      <p className="py-4 text-center text-xs text-marble-400">
        No tile-level data available yet.
      </p>
    );
  }

  if (!computed || computed.hexes.length === 0) {
    return (
      <p className="py-4 text-center text-xs text-marble-400">
        No tiles match the selected attention types.
      </p>
    );
  }

  const { hexes, maxCount, svgW, svgH, hexSize, tileCount } = computed;

  return (
    <div className="space-y-3">
      {/* Attention type toggles */}
      <div className="flex flex-wrap gap-2">
        {TYPE_SHORT_KEYS.map(({ short, key }) => {
          const meta = ATTENTION_TYPES.find((t) => t.key === key)!;
          const active = activeTypes.has(short);
          return (
            <button
              key={short}
              onClick={() => {
                const next = new Set(activeTypes);
                if (active) next.delete(short);
                else next.add(short);
                setActiveTypes(next);
              }}
              className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-medium transition-opacity ${
                active
                  ? "border-marble-400 bg-marble-100 text-marble-700"
                  : "border-marble-200 bg-marble-50 text-marble-400 opacity-50"
              }`}
            >
              <span
                className="inline-block h-2 w-2 rounded-full"
                style={{ backgroundColor: meta.color }}
              />
              {meta.label}
            </button>
          );
        })}
      </div>

      {/* SVG hex grid */}
      <div className="relative overflow-x-auto">
        <svg
          viewBox={`0 0 ${svgW.toFixed(0)} ${svgH.toFixed(0)}`}
          className="w-full"
          style={{ maxHeight: 500 }}
        >
          {hexes.map((h) => (
            <polygon
              key={`${h.x},${h.y}`}
              points={hexPoints(h.cx, h.cy, hexSize * 0.95)}
              fill={hexColor(h.filteredCount, maxCount)}
              stroke="rgba(147, 51, 234, 0.15)"
              strokeWidth="0.5"
              onMouseEnter={() => setHovered(h)}
              onMouseLeave={() => setHovered(null)}
              className="cursor-crosshair"
            />
          ))}
        </svg>

        {/* Tooltip */}
        {hovered && (
          <div className="pointer-events-none absolute left-4 top-4 rounded border border-marble-300 bg-marble-50/95 px-3 py-2 shadow-sm">
            <div className="font-mono text-xs font-semibold text-marble-700">
              ({hovered.x}, {hovered.y})
            </div>
            <div className="mt-1 space-y-0.5 text-[10px] text-marble-600">
              <div>
                Total: <span className="font-mono font-semibold">{hovered.total}</span>
              </div>
              {TYPE_SHORT_KEYS.map(({ short, key }) => {
                const val = hovered[short as keyof SpatialTile] as number;
                if (val === 0) return null;
                const meta = ATTENTION_TYPES.find((t) => t.key === key)!;
                return (
                  <div key={short} className="flex items-center gap-1">
                    <span
                      className="inline-block h-1.5 w-1.5 rounded-full"
                      style={{ backgroundColor: meta.color }}
                    />
                    {meta.label}: <span className="font-mono">{val}</span>
                  </div>
                );
              })}
              <div className="mt-1 border-t border-marble-200 pt-1 text-marble-500">
                Turns {hovered.firstTurn}–{hovered.lastTurn}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="text-[10px] text-marble-400">
        {tileCount.toLocaleString()} tiles observed across{" "}
        {rawMap.maxX - rawMap.minX + 1}&times;{rawMap.maxY - rawMap.minY + 1} grid
      </div>
    </div>
  );
}
