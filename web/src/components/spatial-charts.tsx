"use client";

import { useMemo } from "react";
import type { SpatialTurn } from "@/lib/diary-types";
import { CivIcon } from "./civ-icon";
import { CIV6_COLORS } from "@/lib/civ-colors";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
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

// ── Shared chart styling ─────────────────────────────────────────────────

const AXIS_STYLE = { fontSize: 11, fill: "#A39B8F", fontFamily: "monospace" };
const GRID_STROKE = "#E0DBD3";
const REFERENCE_LINE_COLOR = "#D4A853";

function turnFormatter(v: number) {
  return `T${v}`;
}

function tickInterval(dataLength: number) {
  return Math.max(1, Math.ceil(dataLength / 6));
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CustomTooltip({ active, payload, label, formatter }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded border border-marble-300 bg-marble-50 px-3 py-2 shadow-sm">
      <p className="mb-1 font-mono text-[11px] font-semibold text-marble-700">Turn {label}</p>
      {payload.map((entry: { name: string; value: number; color: string }) => (
        <div key={entry.name} className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-[11px] text-marble-600">
            {formatter ? formatter(entry.name) : entry.name}:
          </span>
          <span className="font-mono text-[11px] tabular-nums text-marble-800">
            {entry.value.toLocaleString()}
          </span>
        </div>
      ))}
    </div>
  );
}

// ── Chart section wrapper ────────────────────────────────────────────────

function ChartSection({
  title,
  icon,
  color,
  description,
  children,
}: {
  title: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  color: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-sm border border-marble-300 bg-marble-50 p-4">
      <h3 className="mb-1 flex items-center gap-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
        <CivIcon icon={icon} color={color} size="sm" />
        {title}
      </h3>
      {description && (
        <p className="mb-3 text-xs leading-relaxed text-marble-500">{description}</p>
      )}
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

function CoverageChart({ data, currentTurn }: { data: SpatialTurn[]; currentTurn: number }) {
  const interval = tickInterval(data.length);
  return (
    <ResponsiveContainer width="100%" height={160}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} />
        <XAxis
          dataKey="turn"
          tickFormatter={turnFormatter}
          interval={interval}
          {...AXIS_STYLE}
        />
        <YAxis width={45} {...AXIS_STYLE} />
        <Tooltip content={<CustomTooltip formatter={() => "Tiles"} />} />
        <ReferenceLine x={currentTurn} stroke={REFERENCE_LINE_COLOR} strokeDasharray="3 3" />
        <Area
          type="monotone"
          dataKey="cumulative_tiles"
          name="Cumulative Tiles"
          stroke={CIV6_COLORS.spatial}
          fill={CIV6_COLORS.spatial}
          fillOpacity={0.15}
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

// ── Tiles per turn bar chart ─────────────────────────────────────────────

function TilesPerTurnChart({ data, currentTurn }: { data: SpatialTurn[]; currentTurn: number }) {
  const interval = tickInterval(data.length);
  return (
    <ResponsiveContainer width="100%" height={160}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} />
        <XAxis
          dataKey="turn"
          tickFormatter={turnFormatter}
          interval={interval}
          {...AXIS_STYLE}
        />
        <YAxis width={45} {...AXIS_STYLE} />
        <Tooltip content={<CustomTooltip formatter={() => "Tiles"} />} />
        <ReferenceLine x={currentTurn} stroke={REFERENCE_LINE_COLOR} strokeDasharray="3 3" />
        <Bar
          dataKey="tiles_observed"
          name="Tiles Observed"
          fill={CIV6_COLORS.spatial}
          opacity={0.7}
          radius={[2, 2, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── Attention type stacked area chart ────────────────────────────────────

const ATTENTION_LABEL_MAP: Record<string, string> = {
  deliberate_scan: "Deliberate Scan",
  deliberate_action: "Deliberate Action",
  survey: "Survey",
  peripheral: "Peripheral",
  reactive: "Reactive",
};

function AttentionStackedChart({ data, currentTurn }: { data: SpatialTurn[]; currentTurn: number }) {
  const flatData = useMemo(
    () => data.map((d) => ({ turn: d.turn, ...d.by_type })),
    [data],
  );
  const interval = tickInterval(data.length);

  return (
    <div>
      <ResponsiveContainer width="100%" height={160}>
        <AreaChart data={flatData}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} />
          <XAxis
            dataKey="turn"
            tickFormatter={turnFormatter}
            interval={interval}
            {...AXIS_STYLE}
          />
          <YAxis width={45} {...AXIS_STYLE} />
          <Tooltip content={<CustomTooltip formatter={(name: string) => ATTENTION_LABEL_MAP[name] ?? name} />} />
          <ReferenceLine x={currentTurn} stroke={REFERENCE_LINE_COLOR} strokeDasharray="3 3" />
          {ATTENTION_TYPES.map((t) => (
            <Area
              key={t.key}
              type="monotone"
              dataKey={t.key}
              name={t.key}
              stackId="1"
              stroke={t.color}
              fill={t.color}
              fillOpacity={0.6}
              strokeWidth={0}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
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

export function SpatialCharts({ data, currentTurn }: { data: SpatialTurn[]; currentTurn: number }) {
  if (data.length === 0) return null;

  return (
    <div className="space-y-4">
      <SpatialStatsBar data={data} />

      <ChartSection
        title="Cumulative Coverage"
        icon={Eye}
        color={CIV6_COLORS.spatial}
        description="Running total of unique map tiles the agent has queried. Steeper slopes indicate bursts of exploration; plateaus show the agent focused on known territory."
      >
        <CoverageChart data={data} currentTurn={currentTurn} />
      </ChartSection>

      <ChartSection
        title="Tiles Observed Per Turn"
        icon={ScanSearch}
        color={CIV6_COLORS.spatial}
        description="Distinct tiles observed each turn. Spikes often correlate with scouting sweeps, settling decisions, or military reconnaissance."
      >
        <TilesPerTurnChart data={data} currentTurn={currentTurn} />
      </ChartSection>

      <ChartSection
        title="Attention Type Breakdown"
        icon={Zap}
        color={CIV6_COLORS.goldMetal}
        description="Breakdown of spatial queries by intentionality. Deliberate scans are explicit map reads the agent chose to make. Deliberate actions are commands issued at specific tiles. Surveys are broad reconnaissance sweeps. Peripheral tiles appeared in query results without being the primary focus. Reactive queries responded to game notifications."
      >
        <AttentionStackedChart data={data} currentTurn={currentTurn} />
      </ChartSection>
    </div>
  );
}
