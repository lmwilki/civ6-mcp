"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "convex/react";
import { api } from "../../convex/_generated/api";
import { Application, Graphics } from "pixi.js";
import {
  cleanCivName,
  unpackTerrain,
  unpackOwnerFrames,
  unpackCityFrames,
  unpackRoadFrames,
  unpackSpatialTiles,
  type MapDataDoc,
  type MapCitySnapshot,
} from "@/lib/diary-types";
import {
  getTerrainColor,
  getFeatureOverlay,
  FEATURE_OVERLAY_ALPHA,
  ROAD_COLORS,
  CITY_MARKER,
} from "@/lib/terrain-colors";
import { getCivColors, getDefaultLeader, canonicalCivName } from "@/lib/civ-registry";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Map as MapIcon,
  Eye,
  EyeOff,
} from "lucide-react";
import { CivIcon, CivSymbol } from "./civ-icon";
import { CIV6_COLORS } from "@/lib/civ-colors";
import { SpatialCharts } from "./spatial-charts";
import type { SpatialTurn } from "@/lib/diary-types";

// ── Constants ─────────────────────────────────────────────────────────────

const SQRT3 = Math.sqrt(3);

const CS_TYPE_COLORS: Record<string, string> = {
  Scientific: "#4A90D9",
  Cultural: "#9B59B6",
  Militaristic: "#CA1415",
  Religious: "#F9F9F9",
  Trade: "#F7D801",
  Industrial: "#FF8112",
};

// Odd-r offset neighbors: E, SE, SW, W, NW, NE
const NEIGHBORS_EVEN = [[1, 0], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1]];
const NEIGHBORS_ODD  = [[1, 0], [1, 1], [0, 1], [-1, 0], [0, -1], [1, -1]];

// Edge-vertex indices for border drawing (accounting for Y-flip)
// Screen vertices: 0=top, 1=NE, 2=SE, 3=bottom, 4=SW, 5=NW
// After Y-flip: game-N→screen-bottom, game-S→screen-top
const EDGE_VERTICES: [number, number][] = [
  [1, 2], [0, 1], [5, 0], [4, 5], [3, 4], [2, 3],
];

// ── Pure geometry helpers ─────────────────────────────────────────────────

/** Hex center in CSS-pixel coords (pointy-top, odd-r offset, Y-flipped) */
function hexCenter(
  col: number, row: number, hexSize: number, gridH: number,
): [number, number] {
  const flippedRow = gridH - 1 - row;
  const cx = SQRT3 * hexSize * (col + 0.5 * (row & 1)) + (SQRT3 * hexSize) / 2;
  const cy = 1.5 * hexSize * flippedRow + hexSize;
  return [cx, cy];
}

/** Flat array of pointy-top hex vertices (12 numbers: x0,y0,...x5,y5) */
function hexVerts(cx: number, cy: number, s: number): number[] {
  const h = (SQRT3 / 2) * s;
  return [
    cx,     cy - s,      // 0: top
    cx + h, cy - s / 2,  // 1: NE
    cx + h, cy + s / 2,  // 2: SE
    cx,     cy + s,      // 3: bottom
    cx - h, cy + s / 2,  // 4: SW
    cx - h, cy - s / 2,  // 5: NW
  ];
}

/** Approximate screen pixel → game hex (col, row) via nearest-center search */
function screenToHex(
  px: number, py: number,
  hexSize: number, gridW: number, gridH: number,
): [number, number] | null {
  // Approximate row from cy = 1.5 * hexSize * flippedRow + hexSize
  const flippedRow = Math.round((py - hexSize) / (1.5 * hexSize));
  const row = gridH - 1 - flippedRow;
  // Approximate col from cx
  const offset = 0.5 * (row & 1);
  const col = Math.round(px / (SQRT3 * hexSize) - 0.5 - offset);

  // Check this hex and its 6 neighbors — find closest center
  const deltas = row % 2 === 0 ? NEIGHBORS_EVEN : NEIGHBORS_ODD;
  const candidates: [number, number][] = [[col, row]];
  for (const [dx, dy] of deltas) candidates.push([col + dx, row + dy]);

  let bestDist = Infinity;
  let best: [number, number] | null = null;

  for (const [c, r] of candidates) {
    if (c < 0 || c >= gridW || r < 0 || r >= gridH) continue;
    const [cx, cy] = hexCenter(c, r, hexSize, gridH);
    const d = (px - cx) ** 2 + (py - cy) ** 2;
    if (d < bestDist) { bestDist = d; best = [c, r]; }
  }

  if (!best || bestDist > hexSize * hexSize) return null;
  return best;
}

// ── Outer component (loading states) ──────────────────────────────────────

interface StrategicMapProps {
  gameId: string;
}

export function StrategicMap({ gameId }: StrategicMapProps) {
  const rawMapData = useQuery(api.diary.getMapData, { gameId });
  const spatialMap = useQuery(api.diary.getSpatialMap, { gameId });
  const spatialTurns = useQuery(api.diary.getSpatialTurns, { gameId });

  if (rawMapData === undefined) {
    return (
      <div className="flex flex-1 items-center justify-center py-20 text-marble-500">
        Loading map data...
      </div>
    );
  }

  if (rawMapData === null) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 py-20">
        <CivIcon icon={MapIcon} color={CIV6_COLORS.spatial} size="md" />
        <p className="text-sm text-marble-500">
          No strategic map data recorded for this game.
        </p>
        <p className="max-w-md text-center text-xs text-marble-400">
          Map data is captured automatically when a game runs with the latest
          MCP server. It records terrain, territory, cities, and roads for
          replay.
        </p>
      </div>
    );
  }

  return (
    <MapRenderer
      mapData={rawMapData}
      spatialMap={spatialMap ?? null}
      spatialTurns={(spatialTurns as SpatialTurn[] | undefined) ?? null}
    />
  );
}

// ── Pixi.js map renderer ──────────────────────────────────────────────────

// Attention type weights — higher = more intentional observation
const ATTENTION_WEIGHTS = { ds: 5, da: 4, sv: 3, pe: 2, re: 1 };
const MAX_DARK = 0.6; // unobserved tile darkness (0=clear, 1=black)

interface SpatialMapDoc {
  minX: number; maxX: number; minY: number; maxY: number;
  tileCount: number; tiles: number[];
}

function MapRenderer({ mapData, spatialMap, spatialTurns }: {
  mapData: MapDataDoc;
  spatialMap: SpatialMapDoc | null;
  spatialTurns: SpatialTurn[] | null;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const renderTurnRef = useRef<((turn: number) => void) | null>(null);
  const currentTurnRef = useRef(mapData.initialTurn);

  const [currentTurn, setCurrentTurn] = useState(mapData.initialTurn);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(0);
  const animRef = useRef(0);
  const lastFrameRef = useRef(0);
  const [hexSize, setHexSize] = useState(6);
  const [showAttention, setShowAttention] = useState(true);
  const showAttentionRef = useRef(true);

  // ── Unpack & precompute ───────────────────────────────────────────────

  const {
    terrain,
    ownerKeyframes,
    cityKeyframes,
    roadKeyframes,
    gridW,
    gridH,
    players,
    maxTurn,
    initialTurn,
  } = useMemo(() => {
    const terrainArr: number[] = JSON.parse(mapData.terrain);
    const initialOwnersArr: number[] = JSON.parse(mapData.initialOwners);
    const ownerFramesArr: number[] = JSON.parse(mapData.ownerFrames);
    const cityFramesArr: number[] = JSON.parse(mapData.cityFrames);
    const roadFramesArr: number[] = JSON.parse(mapData.roadFrames);

    const t = unpackTerrain(terrainArr);
    const of_ = unpackOwnerFrames(ownerFramesArr);
    const cf = unpackCityFrames(cityFramesArr);
    const rf = unpackRoadFrames(roadFramesArr);

    const tileCount = mapData.gridW * mapData.gridH;

    // Ownership keyframes (snapshots at change points)
    const owners = new Int8Array(tileCount);
    for (let i = 0; i < tileCount; i++) {
      owners[i] = initialOwnersArr[i] ?? -1;
    }
    const ownerKf: { turn: number; owners: Int8Array }[] = [
      { turn: mapData.initialTurn, owners: Int8Array.from(owners) },
    ];
    for (const frame of of_) {
      for (const ch of frame.changes) owners[ch.tileIdx] = ch.owner;
      ownerKf.push({ turn: frame.turn, owners: Int8Array.from(owners) });
    }

    // Road keyframes (accumulating)
    const roads = new Int8Array(tileCount).fill(-1);
    const roadKf: { turn: number; roads: Int8Array }[] = [
      { turn: mapData.initialTurn, roads: Int8Array.from(roads) },
    ];
    for (const frame of rf) {
      for (const ch of frame.changes) roads[ch.tileIdx] = ch.owner;
      roadKf.push({ turn: frame.turn, roads: Int8Array.from(roads) });
    }

    return {
      terrain: t,
      ownerKeyframes: ownerKf,
      cityKeyframes: cf,
      roadKeyframes: roadKf,
      gridW: mapData.gridW,
      gridH: mapData.gridH,
      players: mapData.players,
      maxTurn: mapData.maxTurn,
      initialTurn: mapData.initialTurn,
    };
  }, [mapData]);

  // ── Player color lookup ───────────────────────────────────────────────

  const playerColors = useMemo(() => {
    const map = new Map<number, { primary: string; secondary: string }>();
    for (const p of players) {
      if (p.csType) {
        map.set(p.pid, {
          primary: "#1a1a2e",
          secondary: CS_TYPE_COLORS[p.csType] ?? "#888888",
        });
      } else {
        map.set(p.pid, getCivColors(cleanCivName(p.civ)));
      }
    }
    return map;
  }, [players]);

  // ── Attention data lookup ─────────────────────────────────────────────

  const attentionData = useMemo(() => {
    if (!spatialMap) return null;
    const tiles = unpackSpatialTiles(spatialMap.tiles);
    const W = ATTENTION_WEIGHTS;
    const lookup = new Map<string, { weight: number; firstTurn: number }>();
    let maxW = 0;
    for (const t of tiles) {
      const w = W.ds * t.ds + W.da * t.da + W.sv * t.sv + W.pe * t.pe + W.re * t.re;
      lookup.set(`${t.x},${t.y}`, { weight: w, firstTurn: t.firstTurn });
      if (w > maxW) maxW = w;
    }
    return { lookup, maxWeight: maxW };
  }, [spatialMap]);

  // ── Responsive hex sizing ─────────────────────────────────────────────

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width ?? 800;
      const s = Math.min(8, (w - 20) / (SQRT3 * (gridW + 0.5)));
      setHexSize(Math.max(2, s));
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [gridW]);

  const canvasW = Math.ceil(SQRT3 * hexSize * (gridW + 0.5) + SQRT3 * hexSize);
  const canvasH = Math.ceil(1.5 * hexSize * gridH + hexSize * 2);

  // ── Keyframe lookups (binary search for latest snapshot <= turn) ────

  const getOwnersAtTurn = useCallback(
    (turn: number): Int8Array => {
      let lo = 0;
      let hi = ownerKeyframes.length - 1;
      while (lo < hi) {
        const mid = (lo + hi + 1) >> 1;
        if (ownerKeyframes[mid].turn <= turn) lo = mid;
        else hi = mid - 1;
      }
      return ownerKeyframes[lo].owners;
    },
    [ownerKeyframes],
  );

  const getCitiesAtTurn = useCallback(
    (turn: number): MapCitySnapshot[] => {
      if (cityKeyframes.length === 0) return [];
      let lo = 0;
      let hi = cityKeyframes.length - 1;
      while (lo < hi) {
        const mid = (lo + hi + 1) >> 1;
        if (cityKeyframes[mid].turn <= turn) lo = mid;
        else hi = mid - 1;
      }
      return cityKeyframes[lo].turn <= turn ? cityKeyframes[lo].cities : [];
    },
    [cityKeyframes],
  );

  const getRoadsAtTurn = useCallback(
    (turn: number): Int8Array => {
      let lo = 0;
      let hi = roadKeyframes.length - 1;
      while (lo < hi) {
        const mid = (lo + hi + 1) >> 1;
        if (roadKeyframes[mid].turn <= turn) lo = mid;
        else hi = mid - 1;
      }
      return roadKeyframes[lo].roads;
    },
    [roadKeyframes],
  );

  // ── Pixi.js lifecycle ─────────────────────────────────────────────────

  useEffect(() => {
    const app = new Application();
    let destroyed = false;

    (async () => {
      await app.init({
        background: 0x1a1a2e,
        width: canvasW,
        height: canvasH,
        autoDensity: true,
        resolution: window.devicePixelRatio || 1,
        antialias: true,
      });
      if (destroyed) return;

      const container = containerRef.current;
      if (!container) return;
      container.insertBefore(app.canvas, container.firstChild);

      // Scene layers (bottom to top)
      const terrainGfx = new Graphics();
      const territoryGfx = new Graphics();
      const borderGfx = new Graphics();
      const roadGfx = new Graphics();
      const cityGfx = new Graphics();
      const attentionGfx = new Graphics();
      const hoverGfx = new Graphics();
      app.stage.addChild(
        terrainGfx, territoryGfx, borderGfx, roadGfx, cityGfx,
        attentionGfx, hoverGfx,
      );

      // ── Static terrain (drawn once) ──────────────────────────────────

      for (let y = 0; y < gridH; y++) {
        for (let x = 0; x < gridW; x++) {
          const idx = y * gridW + x;
          const tile = terrain[idx];
          if (!tile) continue;
          const [cx, cy] = hexCenter(x, y, hexSize, gridH);
          const verts = hexVerts(cx, cy, hexSize * 0.98);

          terrainGfx.poly(verts).fill(getTerrainColor(tile.terrain));

          const featureColor = getFeatureOverlay(tile.feature);
          if (featureColor) {
            terrainGfx.poly(verts).fill({
              color: featureColor, alpha: FEATURE_OVERLAY_ALPHA,
            });
          }
        }
      }

      // ── Dynamic turn renderer ────────────────────────────────────────

      const renderTurn = (turn: number) => {
        territoryGfx.clear();
        borderGfx.clear();
        roadGfx.clear();
        cityGfx.clear();

        const owners = getOwnersAtTurn(turn);

        // Territory fill
        for (let y = 0; y < gridH; y++) {
          for (let x = 0; x < gridW; x++) {
            const idx = y * gridW + x;
            const owner = owners[idx];
            if (owner < 0) continue;
            const colors = playerColors.get(owner);
            if (!colors) continue;
            const [cx, cy] = hexCenter(x, y, hexSize, gridH);
            territoryGfx
              .poly(hexVerts(cx, cy, hexSize * 0.98))
              .fill(colors.primary);
          }
        }

        // Territory borders — batch segments by owner for fewer draw calls
        const bordersByOwner = new Map<number, number[]>();
        const INSET = 0.82;
        const h = (SQRT3 / 2) * hexSize * 0.98;
        const s98 = hexSize * 0.98;
        const vOffsets: [number, number][] = [
          [0, -s98],     [h, -s98 / 2], [h, s98 / 2],
          [0, s98],      [-h, s98 / 2], [-h, -s98 / 2],
        ];

        for (let y = 0; y < gridH; y++) {
          for (let x = 0; x < gridW; x++) {
            const idx = y * gridW + x;
            const owner = owners[idx];
            if (owner < 0) continue;
            const [cx, cy] = hexCenter(x, y, hexSize, gridH);
            const deltas = y % 2 === 0 ? NEIGHBORS_EVEN : NEIGHBORS_ODD;

            for (let d = 0; d < 6; d++) {
              const nx = x + deltas[d][0];
              const ny = y + deltas[d][1];
              const nOwner =
                nx >= 0 && nx < gridW && ny >= 0 && ny < gridH
                  ? owners[ny * gridW + nx]
                  : -1;
              if (nOwner === owner) continue;

              const [vi, vj] = EDGE_VERTICES[d];
              let segs = bordersByOwner.get(owner);
              if (!segs) { segs = []; bordersByOwner.set(owner, segs); }
              segs.push(
                cx + vOffsets[vi][0] * INSET, cy + vOffsets[vi][1] * INSET,
                cx + vOffsets[vj][0] * INSET, cy + vOffsets[vj][1] * INSET,
              );
            }
          }
        }

        const bw = Math.max(1, hexSize * 0.2);
        for (const [owner, segs] of bordersByOwner) {
          const colors = playerColors.get(owner);
          if (!colors) continue;
          for (let i = 0; i < segs.length; i += 4) {
            borderGfx.moveTo(segs[i], segs[i + 1]).lineTo(segs[i + 2], segs[i + 3]);
          }
          borderGfx.stroke({ width: bw, color: colors.secondary, cap: "round" });
        }

        // Roads (dots)
        const roads = getRoadsAtTurn(turn);
        for (let y = 0; y < gridH; y++) {
          for (let x = 0; x < gridW; x++) {
            const idx = y * gridW + x;
            const routeType = roads[idx];
            if (routeType < 0) continue;
            const [cx, cy] = hexCenter(x, y, hexSize, gridH);
            roadGfx
              .circle(cx, cy, hexSize * 0.15)
              .fill(ROAD_COLORS[routeType] ?? ROAD_COLORS[0]);
          }
        }

        // Cities
        const cities = getCitiesAtTurn(turn);
        for (const city of cities) {
          const [cx, cy] = hexCenter(city.x, city.y, hexSize, gridH);
          const colors = playerColors.get(city.pid);
          const r =
            CITY_MARKER.baseRadius + Math.sqrt(city.pop) * CITY_MARKER.popScale;
          cityGfx
            .circle(cx, cy, r)
            .fill(colors?.secondary ?? "#ffffff")
            .stroke({
              width: CITY_MARKER.strokeWidth,
              color: CITY_MARKER.strokeColor,
            });
        }

        // Sensorium attention overlay — darkness lifts where the agent has observed
        attentionGfx.clear();
        if (attentionData && showAttentionRef.current) {
          const logMax = Math.log(attentionData.maxWeight + 1);
          for (let y = 0; y < gridH; y++) {
            for (let x = 0; x < gridW; x++) {
              const entry = attentionData.lookup.get(`${x},${y}`);
              let alpha = MAX_DARK;

              if (entry && entry.firstTurn <= turn) {
                const t = Math.log(entry.weight + 1) / logMax;
                alpha = MAX_DARK * (1 - t);
              }

              if (alpha < 0.01) continue;
              const [hx, hy] = hexCenter(x, y, hexSize, gridH);
              attentionGfx
                .poly(hexVerts(hx, hy, hexSize * 0.98))
                .fill({ color: 0x000000, alpha });
            }
          }
        }
      };

      renderTurnRef.current = renderTurn;
      renderTurn(currentTurnRef.current);

      // ── Hover interaction ────────────────────────────────────────────

      app.stage.eventMode = "static";
      app.stage.hitArea = app.screen;

      let lastHexKey = "";

      app.stage.on("pointermove", (e) => {
        const { x: px, y: py } = e.global;
        const hex = screenToHex(px, py, hexSize, gridW, gridH);
        const tooltip = tooltipRef.current;

        if (!hex) {
          hoverGfx.clear();
          lastHexKey = "";
          if (tooltip) tooltip.style.display = "none";
          return;
        }

        const [col, row] = hex;
        const key = `${col},${row}`;

        // Redraw highlight only when hex changes
        if (key !== lastHexKey) {
          lastHexKey = key;
          const [cx, cy] = hexCenter(col, row, hexSize, gridH);
          hoverGfx.clear();
          hoverGfx
            .poly(hexVerts(cx, cy, hexSize * 0.98))
            .stroke({ width: 1.5, color: "#ffffff", alpha: 0.7 });
        }

        // Update tooltip content & position
        if (!tooltip) return;

        const owners = getOwnersAtTurn(currentTurnRef.current);
        const idx = row * gridW + col;
        const owner = owners[idx];

        if (owner < 0) {
          tooltip.style.display = "none";
          return;
        }

        const player = players.find((p) => p.pid === owner);
        if (!player) {
          tooltip.style.display = "none";
          return;
        }

        const civName = canonicalCivName(cleanCivName(player.civ));
        const cities = getCitiesAtTurn(currentTurnRef.current);
        const city = cities.find((c) => c.x === col && c.y === row);

        let html = `<span class="font-medium">${civName}</span>`;
        if (player.csType) {
          html += ` <span style="opacity:0.6">(${player.csType})</span>`;
        }
        if (city) {
          html += `<br/><span style="opacity:0.6">Pop ${city.pop}</span>`;
        }

        tooltip.innerHTML = html;
        tooltip.style.display = "block";

        // Position via canvas bounding rect for scroll-safe fixed positioning
        const rect = app.canvas.getBoundingClientRect();
        tooltip.style.left = `${rect.left + px + 12}px`;
        tooltip.style.top = `${rect.top + py - 8}px`;
      });

      app.canvas.addEventListener("mouseleave", () => {
        hoverGfx.clear();
        lastHexKey = "";
        if (tooltipRef.current) tooltipRef.current.style.display = "none";
      });
    })();

    return () => {
      destroyed = true;
      const container = containerRef.current;
      if (container?.contains(app.canvas)) {
        container.removeChild(app.canvas);
      }
      app.destroy(true, { children: true });
    };
  }, [
    canvasW, canvasH, hexSize, terrain, gridW, gridH,
    playerColors, getOwnersAtTurn, getCitiesAtTurn, getRoadsAtTurn, players,
    attentionData,
  ]);

  // Sync turn changes to Pixi (lightweight — no Pixi teardown)
  useEffect(() => {
    currentTurnRef.current = currentTurn;
    renderTurnRef.current?.(currentTurn);
  }, [currentTurn]);

  // Sync attention toggle to Pixi
  useEffect(() => {
    showAttentionRef.current = showAttention;
    renderTurnRef.current?.(currentTurnRef.current);
  }, [showAttention]);

  // ── Replay animation ─────────────────────────────────────────────────

  useEffect(() => {
    if (!playing) return;

    const speeds = [500, 250, 100, 50];
    const interval = speeds[Math.min(speed, speeds.length - 1)];

    const tick = (time: number) => {
      if (time - lastFrameRef.current >= interval) {
        lastFrameRef.current = time;
        setCurrentTurn((prev) => {
          if (prev >= maxTurn) {
            setPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }
      animRef.current = requestAnimationFrame(tick);
    };

    animRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animRef.current);
  }, [playing, speed, maxTurn]);

  // ── UI ────────────────────────────────────────────────────────────────

  const speedLabels = ["1x", "2x", "5x", "10x"];

  return (
    <div className="mx-auto max-w-4xl space-y-4 px-3 py-6 sm:px-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="flex items-center gap-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
          <CivIcon icon={MapIcon} color={CIV6_COLORS.spatial} size="sm" />
          Strategic Map
        </h3>
        <div className="flex items-center gap-3">
          {attentionData && (
            <button
              onClick={() => setShowAttention((s) => !s)}
              className={`flex items-center gap-1 rounded-full border px-2.5 py-1 text-[10px] font-medium transition-opacity ${
                showAttention
                  ? "border-purple-400/50 bg-purple-50 text-purple-700"
                  : "border-marble-300 bg-marble-50 text-marble-400"
              }`}
              title={showAttention ? "Hide attention overlay" : "Show attention overlay"}
            >
              {showAttention ? (
                <Eye className="h-3 w-3" />
              ) : (
                <EyeOff className="h-3 w-3" />
              )}
              Sensorium
            </button>
          )}
          <span className="font-mono text-sm tabular-nums text-marble-600">
            Turn {currentTurn}
          </span>
        </div>
      </div>

      {/* Pixi canvas container */}
      <div
        ref={containerRef}
        className="overflow-x-auto rounded-sm border border-marble-300 bg-[#1a1a2e]"
      />

      {/* Hover tooltip (fixed positioning — scroll-safe) */}
      <div
        ref={tooltipRef}
        className="pointer-events-none fixed z-50 hidden rounded bg-marble-900/90 px-2 py-1 text-[10px] leading-snug text-marble-100"
        style={{ display: "none" }}
      />

      {/* Replay controls */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => { setPlaying(false); setCurrentTurn(initialTurn); }}
          className="rounded p-1.5 text-marble-500 hover:bg-marble-200 hover:text-marble-700"
          title="Reset to start"
        >
          <SkipBack className="h-4 w-4" />
        </button>

        <button
          onClick={() => {
            if (currentTurn >= maxTurn) setCurrentTurn(initialTurn);
            setPlaying(!playing);
          }}
          className="rounded p-1.5 text-marble-500 hover:bg-marble-200 hover:text-marble-700"
          title={playing ? "Pause" : "Play"}
        >
          {playing ? (
            <Pause className="h-4 w-4" />
          ) : (
            <Play className="h-4 w-4" />
          )}
        </button>

        <button
          onClick={() => { setPlaying(false); setCurrentTurn(maxTurn); }}
          className="rounded p-1.5 text-marble-500 hover:bg-marble-200 hover:text-marble-700"
          title="Jump to end"
        >
          <SkipForward className="h-4 w-4" />
        </button>

        <input
          type="range"
          min={initialTurn}
          max={maxTurn}
          value={currentTurn}
          onChange={(e) => {
            setPlaying(false);
            setCurrentTurn(Number(e.target.value));
          }}
          className="flex-1 accent-gold-dark"
        />

        <button
          onClick={() => setSpeed((s) => (s + 1) % speedLabels.length)}
          className="rounded border border-marble-300 px-2 py-0.5 font-mono text-[10px] tabular-nums text-marble-600 hover:bg-marble-200"
          title="Change speed"
        >
          {speedLabels[speed]}
        </button>
      </div>

      {/* Legend — major civs */}
      <div className="flex flex-wrap gap-2">
        {players
          .filter((p) => !p.csType)
          .map((p) => {
            const civName = canonicalCivName(cleanCivName(p.civ));
            const leader = getDefaultLeader(civName);
            return (
              <div
                key={p.pid}
                className="flex items-center gap-1.5 rounded-full border border-marble-300 bg-marble-50 px-2.5 py-1"
              >
                <CivSymbol civ={civName} className="h-3 w-3" />
                <span className="text-[10px] font-medium text-marble-600">
                  {civName}
                </span>
                {leader && (
                  <span className="text-[9px] text-marble-400">{leader}</span>
                )}
              </div>
            );
          })}

        {/* Legend — city-states */}
        {players.some((p) => p.csType) && (
          <>
            <span className="self-center text-[9px] text-marble-400">|</span>
            {players
              .filter((p) => p.csType)
              .map((p) => {
                const colors = playerColors.get(p.pid);
                return (
                  <div
                    key={p.pid}
                    className="flex items-center gap-1.5 rounded-full border border-marble-300 bg-marble-50 px-2.5 py-1"
                  >
                    <span
                      className="inline-block h-2 w-2 rotate-45"
                      style={{
                        backgroundColor: "#1a1a2e",
                        border: `1.5px solid ${colors?.secondary ?? "#888"}`,
                      }}
                    />
                    <span className="text-[10px] font-medium text-marble-400">
                      {canonicalCivName(cleanCivName(p.civ))}
                    </span>
                  </div>
                );
              })}
          </>
        )}
      </div>

      {/* Spatial attention charts */}
      {spatialTurns && spatialTurns.length > 0 && (
        <SpatialCharts data={spatialTurns} />
      )}
    </div>
  );
}
