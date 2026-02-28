"use client";

import { useMemo } from "react";
import type { SpatialTurn } from "@/lib/diary-types";
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
} from "lucide-react";

// Attention type metadata for display
const ATTENTION_TYPES = [
  { key: "deliberate_scan" as const, label: "Deliberate Scan", color: "#9333EA", icon: Crosshair },
  { key: "deliberate_action" as const, label: "Deliberate Action", color: "#D4A853", icon: MousePointerClick },
  { key: "survey" as const, label: "Survey", color: "#44B3EA", icon: Radar },
  { key: "peripheral" as const, label: "Peripheral", color: "#7A9B8A", icon: Radio },
  { key: "reactive" as const, label: "Reactive", color: "#C4785C", icon: Bell },
] as const;

// ── Chart constants ──────────────────────────────────────────────────────

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

// ── Chart section wrapper ────────────────────────────────────────────────

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

// ── Stats bar ────────────────────────────────────────────────────────────

export function SpatialStatsBar({ data }: { data: SpatialTurn[] }) {
  const stats = useMemo(() => {
    if (data.length === 0) return null;
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
    };
  }, [data]);

  if (!stats) return null;

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

// ── Coverage chart (cumulative unique tiles) ─────────────────────────────

function CoverageChart({ data }: { data: SpatialTurn[] }) {
  const { points, max, labels } = useMemo(() => {
    const vals = data.map((d) => d.cumulative_tiles);
    const mx = Math.max(...vals) || 1;
    const pts = vals
      .map((v, i) => {
        const x =
          CHART_PAD + (i / Math.max(vals.length - 1, 1)) * (CHART_W - 2 * CHART_PAD);
        const y =
          CHART_H - CHART_PAD - (v / mx) * (CHART_H - 2 * CHART_PAD);
        return `${x},${y}`;
      })
      .join(" ");
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
      {labels.map((l) => {
        const y = CHART_H - CHART_PAD - (l / (max || 1)) * (CHART_H - 2 * CHART_PAD);
        return (
          <g key={l}>
            <line x1={CHART_PAD} y1={y} x2={CHART_W - CHART_PAD} y2={y} stroke="#E0DBD3" strokeWidth="0.5" />
            <text x={CHART_PAD - 4} y={y + 3} textAnchor="end" fill="#A39B8F" fontSize="8" fontFamily="monospace">{l}</text>
          </g>
        );
      })}
      {turnLabels.map((tl) => (
        <text key={tl.turn} x={tl.x} y={CHART_H - 4} textAnchor="middle" fill="#A39B8F" fontSize="8" fontFamily="monospace">T{tl.turn}</text>
      ))}
      <polygon
        points={`${CHART_PAD},${CHART_H - CHART_PAD} ${points} ${CHART_W - CHART_PAD},${CHART_H - CHART_PAD}`}
        fill={CIV6_COLORS.spatial}
        opacity="0.1"
      />
      <polyline points={points} fill="none" stroke={CIV6_COLORS.spatial} strokeWidth="2" strokeLinejoin="round" opacity="0.8" />
    </svg>
  );
}

// ── Tiles per turn bar chart ─────────────────────────────────────────────

function TilesPerTurnChart({ data }: { data: SpatialTurn[] }) {
  const { bars, max } = useMemo(() => {
    const mx = Math.max(...data.map((d) => d.tiles_observed)) || 1;
    const barWidth = (CHART_W - 2 * CHART_PAD) / Math.max(data.length, 1) - 1;
    const bs = data.map((d, i) => {
      const h = (d.tiles_observed / mx) * (CHART_H - 2 * CHART_PAD);
      const x = CHART_PAD + (i / Math.max(data.length, 1)) * (CHART_W - 2 * CHART_PAD);
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
      {[0, 0.5, 1].map((frac) => {
        const val = Math.round(max * frac);
        const y = CHART_H - CHART_PAD - frac * (CHART_H - 2 * CHART_PAD);
        return (
          <g key={frac}>
            <line x1={CHART_PAD} y1={y} x2={CHART_W - CHART_PAD} y2={y} stroke="#E0DBD3" strokeWidth="0.5" />
            <text x={CHART_PAD - 4} y={y + 3} textAnchor="end" fill="#A39B8F" fontSize="8" fontFamily="monospace">{val}</text>
          </g>
        );
      })}
      {turnLabels.map((tl) => (
        <text key={tl.turn} x={tl.x} y={CHART_H - 4} textAnchor="middle" fill="#A39B8F" fontSize="8" fontFamily="monospace">T{tl.turn}</text>
      ))}
      {bars.map((b) => (
        <rect key={b.turn} x={b.x} y={b.y} width={b.width} height={b.height} fill={CIV6_COLORS.spatial} opacity="0.6" rx="1" />
      ))}
    </svg>
  );
}

// ── Attention type stacked area chart ────────────────────────────────────

function AttentionStackedChart({ data }: { data: SpatialTurn[] }) {
  const { areas, maxTotal, turnLabels } = useMemo(() => {
    if (data.length === 0) return { areas: [], maxTotal: 1, turnLabels: [] };
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
      return CHART_PAD + (i / Math.max(data.length - 1, 1)) * (CHART_W - 2 * CHART_PAD);
    }
    function toY(val: number) {
      return CHART_H - CHART_PAD - (val / mx) * (CHART_H - 2 * CHART_PAD);
    }
    const areaData = keys.map((_, layerIdx) => {
      const topLine = stacked.map((s, i) => `${toX(i)},${toY(s[layerIdx])}`);
      const bottomLine =
        layerIdx === 0
          ? data.map((_, i) => `${toX(i)},${toY(0)}`)
          : stacked.map((s, i) => `${toX(i)},${toY(s[layerIdx - 1])}`);
      return {
        key: keys[layerIdx],
        color: ATTENTION_TYPES[layerIdx].color,
        polygon: [...topLine, ...bottomLine.reverse()].join(" "),
      };
    });
    return { areas: areaData, maxTotal: mx, turnLabels: computeTurnLabels(data, toX) };
  }, [data]);

  return (
    <div>
      <svg viewBox={`0 0 ${CHART_W} ${CHART_H}`} className="h-40 w-full">
        {[0, 0.5, 1].map((frac) => {
          const val = Math.round(maxTotal * frac);
          const y = CHART_H - CHART_PAD - frac * (CHART_H - 2 * CHART_PAD);
          return (
            <g key={frac}>
              <line x1={CHART_PAD} y1={y} x2={CHART_W - CHART_PAD} y2={y} stroke="#E0DBD3" strokeWidth="0.5" />
              <text x={CHART_PAD - 4} y={y + 3} textAnchor="end" fill="#A39B8F" fontSize="8" fontFamily="monospace">{val}</text>
            </g>
          );
        })}
        {turnLabels.map((tl) => (
          <text key={tl.turn} x={tl.x} y={CHART_H - 4} textAnchor="middle" fill="#A39B8F" fontSize="8" fontFamily="monospace">T{tl.turn}</text>
        ))}
        {areas.map((area) => (
          <polygon key={area.key} points={area.polygon} fill={area.color} opacity="0.5" />
        ))}
      </svg>
      <div className="mt-2 flex flex-wrap gap-3">
        {ATTENTION_TYPES.map((t) => {
          const Icon = t.icon;
          return (
            <div key={t.key} className="flex items-center gap-1">
              <Icon className="h-3 w-3" style={{ color: t.color }} />
              <span className="text-[10px] text-marble-600">{t.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Combined spatial charts section ──────────────────────────────────────

export function SpatialCharts({ data }: { data: SpatialTurn[] }) {
  if (data.length === 0) return null;

  return (
    <div className="space-y-4">
      <SpatialStatsBar data={data} />

      <ChartSection title="Cumulative Coverage" icon={Eye} color={CIV6_COLORS.spatial}>
        <CoverageChart data={data} />
      </ChartSection>

      <ChartSection title="Tiles Observed Per Turn" icon={ScanSearch} color={CIV6_COLORS.spatial}>
        <TilesPerTurnChart data={data} />
      </ChartSection>

      <ChartSection title="Attention Type Breakdown" icon={Zap} color={CIV6_COLORS.goldMetal}>
        <AttentionStackedChart data={data} />
      </ChartSection>
    </div>
  );
}
