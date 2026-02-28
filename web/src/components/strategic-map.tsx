"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "convex/react";
import { api } from "../../convex/_generated/api";
import {
  cleanCivName,
  unpackTerrain,
  unpackOwnerFrames,
  unpackCityFrames,
  unpackRoadFrames,
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
import { getCivColors } from "@/lib/civ-registry";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Map as MapIcon,
} from "lucide-react";
import { CivIcon } from "./civ-icon";
import { CIV6_COLORS } from "@/lib/civ-colors";

const SQRT3 = Math.sqrt(3);

const CS_TYPE_COLORS: Record<string, string> = {
  Scientific: "#4A90D9",
  Cultural: "#9B59B6",
  Militaristic: "#CA1415",
  Religious: "#F9F9F9",
  Trade: "#F7D801",
  Industrial: "#FF8112",
};

interface StrategicMapProps {
  gameId: string;
}

export function StrategicMap({ gameId }: StrategicMapProps) {
  const rawMapData = useQuery(api.diary.getMapData, { gameId });

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

  return <MapCanvas mapData={rawMapData} />;
}

// ── Canvas map renderer ──────────────────────────────────────────────────

function MapCanvas({ mapData }: { mapData: MapDataDoc }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const terrainCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const dprRef = useRef(typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1);

  const [currentTurn, setCurrentTurn] = useState(mapData.initialTurn);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(0);
  const animRef = useRef(0);
  const lastFrameRef = useRef(0);

  // ── Unpack & precompute ────────────────────────────────────────────────

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
    // Convex stores large arrays as JSON strings (8192 array cap)
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
      for (const ch of frame.changes) {
        owners[ch.tileIdx] = ch.owner;
      }
      ownerKf.push({ turn: frame.turn, owners: Int8Array.from(owners) });
    }

    // Road keyframes (accumulating)
    const roads = new Int8Array(tileCount).fill(-1);
    const roadKf: { turn: number; roads: Int8Array }[] = [
      { turn: mapData.initialTurn, roads: Int8Array.from(roads) },
    ];
    for (const frame of rf) {
      for (const ch of frame.changes) {
        roads[ch.tileIdx] = ch.owner; // reusing owner field for routeType
      }
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

  // ── Player color lookup ────────────────────────────────────────────────

  const playerColors = useMemo(() => {
    const map = new Map<number, { primary: string; secondary: string }>();
    for (const p of players) {
      if (p.csType) {
        // City-state: dark fill, type-colored borders
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

  // ── Hex sizing (responsive) ────────────────────────────────────────────

  const [hexSize, setHexSize] = useState(6);

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

  // ── Keyframe lookup (binary search for latest snapshot <= turn) ─────

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

  // ── Hex geometry (pointy-top, even-r offset) ──────────────────────────

  const hexPos = useCallback(
    (col: number, row: number): [number, number] => {
      // Flip Y: game Y increases southward, minimap renders north-at-top
      const flippedRow = gridH - 1 - row;
      // Pointy-top even-r: even rows shifted right by half a hex width
      const cx =
        SQRT3 * hexSize * (col + 0.5 * (flippedRow & 1)) +
        (SQRT3 * hexSize) / 2;
      const cy = 1.5 * hexSize * flippedRow + hexSize;
      return [cx, cy];
    },
    [hexSize, gridH],
  );

  const drawHex = useCallback(
    (ctx: CanvasRenderingContext2D, cx: number, cy: number, s: number) => {
      // Pointy-top: vertex at top, clockwise
      const h = (SQRT3 / 2) * s;
      ctx.beginPath();
      ctx.moveTo(cx, cy - s); // top
      ctx.lineTo(cx + h, cy - s / 2); // NE
      ctx.lineTo(cx + h, cy + s / 2); // SE
      ctx.lineTo(cx, cy + s); // bottom
      ctx.lineTo(cx - h, cy + s / 2); // SW
      ctx.lineTo(cx - h, cy - s / 2); // NW
      ctx.closePath();
    },
    [],
  );

  // ── Static terrain render (offscreen canvas, once per resize) ──────────

  useEffect(() => {
    const dpr = dprRef.current;
    const offscreen = document.createElement("canvas");
    offscreen.width = canvasW * dpr;
    offscreen.height = canvasH * dpr;
    const ctx = offscreen.getContext("2d");
    if (!ctx) return;

    ctx.scale(dpr, dpr);
    ctx.fillStyle = "#1a1a2e";
    ctx.fillRect(0, 0, canvasW, canvasH);

    for (let y = 0; y < gridH; y++) {
      for (let x = 0; x < gridW; x++) {
        const idx = y * gridW + x;
        const tile = terrain[idx];
        if (!tile) continue;

        const [cx, cy] = hexPos(x, y);

        // Terrain fill
        drawHex(ctx, cx, cy, hexSize * 0.98);
        ctx.fillStyle = getTerrainColor(tile.terrain);
        ctx.fill();

        // Feature overlay (forest, jungle, etc.)
        const featureColor = getFeatureOverlay(tile.feature);
        if (featureColor) {
          ctx.globalAlpha = FEATURE_OVERLAY_ALPHA;
          ctx.fillStyle = featureColor;
          ctx.fill();
          ctx.globalAlpha = 1;
        }
      }
    }

    terrainCanvasRef.current = offscreen;
  }, [terrain, gridW, gridH, hexSize, canvasW, canvasH, hexPos, drawHex]);

  // ── Frame renderer ─────────────────────────────────────────────────────

  const renderFrame = useCallback(
    (turn: number) => {
      const canvas = canvasRef.current;
      const terrainCanvas = terrainCanvasRef.current;
      if (!canvas || !terrainCanvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const dpr = dprRef.current;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      // Layer 1: static terrain (blit from offscreen — use full pixel dims)
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.drawImage(terrainCanvas, 0, 0);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      // Layer 2: solid territory fill
      const owners = getOwnersAtTurn(turn);
      for (let y = 0; y < gridH; y++) {
        for (let x = 0; x < gridW; x++) {
          const idx = y * gridW + x;
          const owner = owners[idx];
          if (owner < 0) continue;
          const colors = playerColors.get(owner);
          if (!colors) continue;
          const [cx, cy] = hexPos(x, y);
          drawHex(ctx, cx, cy, hexSize * 0.98);
          ctx.fillStyle = colors.primary;
          ctx.fill();
        }
      }

      // Layer 2b: inner territory borders
      // Pointy-top, even-r offset: even rows shifted right
      // Directions: E, SE, SW, W, NW, NE
      const neighborsEven = [[1, 0], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1]];
      const neighborsOdd  = [[1, 0], [1, 1], [0, 1], [-1, 0], [0, -1], [1, -1]];
      // Edge vertex indices matching the 6 directions
      // Pointy-top vertices: 0=top, 1=NE, 2=SE, 3=bottom, 4=SW, 5=NW
      const edgeVertices: [number, number][] = [[1, 2], [2, 3], [3, 4], [4, 5], [5, 0], [0, 1]];
      const INSET = 0.82;
      const h = (SQRT3 / 2) * hexSize * 0.98;
      const s98 = hexSize * 0.98;
      // Pointy-top vertex offsets from hex center
      const vOffsets: [number, number][] = [
        [0, -s98],          // 0: top
        [h, -s98 / 2],      // 1: NE
        [h, s98 / 2],       // 2: SE
        [0, s98],           // 3: bottom
        [-h, s98 / 2],      // 4: SW
        [-h, -s98 / 2],     // 5: NW
      ];

      ctx.lineWidth = Math.max(1, hexSize * 0.2);
      ctx.lineCap = "round";
      for (let y = 0; y < gridH; y++) {
        for (let x = 0; x < gridW; x++) {
          const idx = y * gridW + x;
          const owner = owners[idx];
          if (owner < 0) continue;
          const colors = playerColors.get(owner);
          if (!colors) continue;
          const [cx, cy] = hexPos(x, y);
          // Use original y for parity (game coordinates, not flipped)
          const deltas = y % 2 === 0 ? neighborsEven : neighborsOdd;
          ctx.strokeStyle = colors.secondary;
          for (let d = 0; d < 6; d++) {
            const nx = x + deltas[d][0];
            const ny = y + deltas[d][1];
            // Draw border if neighbor is out of bounds or different owner
            const nOwner = (nx >= 0 && nx < gridW && ny >= 0 && ny < gridH)
              ? owners[ny * gridW + nx]
              : -1;
            if (nOwner === owner) continue;
            const [vi, vj] = edgeVertices[d];
            const x1 = cx + vOffsets[vi][0] * INSET;
            const y1 = cy + vOffsets[vi][1] * INSET;
            const x2 = cx + vOffsets[vj][0] * INSET;
            const y2 = cy + vOffsets[vj][1] * INSET;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
          }
        }
      }

      // Layer 3: roads (dots)
      const roads = getRoadsAtTurn(turn);
      for (let y = 0; y < gridH; y++) {
        for (let x = 0; x < gridW; x++) {
          const idx = y * gridW + x;
          const routeType = roads[idx];
          if (routeType < 0) continue;
          const [cx, cy] = hexPos(x, y);
          ctx.fillStyle = ROAD_COLORS[routeType] ?? ROAD_COLORS[0];
          ctx.beginPath();
          ctx.arc(cx, cy, hexSize * 0.15, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // Layer 4: cities
      const cities = getCitiesAtTurn(turn);
      for (const city of cities) {
        const [cx, cy] = hexPos(city.x, city.y);
        const colors = playerColors.get(city.pid);
        const radius =
          CITY_MARKER.baseRadius +
          Math.sqrt(city.pop) * CITY_MARKER.popScale;

        // Fill
        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.fillStyle = colors?.secondary ?? "#ffffff";
        ctx.fill();

        // Stroke
        ctx.strokeStyle = CITY_MARKER.strokeColor;
        ctx.lineWidth = CITY_MARKER.strokeWidth;
        ctx.stroke();
      }
    },
    [
      gridW,
      gridH,
      hexSize,
      hexPos,
      drawHex,
      getOwnersAtTurn,
      getCitiesAtTurn,
      getRoadsAtTurn,
      playerColors,
    ],
  );

  // Re-render when turn changes
  useEffect(() => {
    renderFrame(currentTurn);
  }, [currentTurn, renderFrame]);

  // ── Replay animation ───────────────────────────────────────────────────

  useEffect(() => {
    if (!playing) return;

    const speeds = [500, 250, 100, 50]; // 1x, 2x, 5x, 10x
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

  // ── UI ─────────────────────────────────────────────────────────────────

  const speedLabels = ["1x", "2x", "5x", "10x"];
  const dpr = dprRef.current;

  return (
    <div className="mx-auto max-w-4xl space-y-4 px-3 py-6 sm:px-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="flex items-center gap-1.5 font-display text-[10px] font-bold uppercase tracking-[0.12em] text-marble-500">
          <CivIcon icon={MapIcon} color={CIV6_COLORS.spatial} size="sm" />
          Strategic Map
        </h3>
        <span className="font-mono text-sm tabular-nums text-marble-600">
          Turn {currentTurn}
        </span>
      </div>

      {/* Canvas */}
      <div
        ref={containerRef}
        className="overflow-x-auto rounded-sm border border-marble-300 bg-[#1a1a2e]"
      >
        <canvas
          ref={canvasRef}
          width={canvasW * dpr}
          height={canvasH * dpr}
          style={{ width: canvasW, height: canvasH }}
        />
      </div>

      {/* Replay controls */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => {
            setPlaying(false);
            setCurrentTurn(initialTurn);
          }}
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
          onClick={() => {
            setPlaying(false);
            setCurrentTurn(maxTurn);
          }}
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

      {/* Civ legend */}
      <div className="flex flex-wrap gap-2">
        {players
          .filter((p) => !p.csType)
          .map((p) => {
            const colors = playerColors.get(p.pid);
            return (
              <div
                key={p.pid}
                className="flex items-center gap-1.5 rounded-full border border-marble-300 bg-marble-50 px-2.5 py-1"
              >
                <span
                  className="inline-block h-2.5 w-2.5 rounded-sm"
                  style={{ backgroundColor: colors?.primary ?? "#888" }}
                />
                <span className="text-[10px] font-medium text-marble-600">
                  {cleanCivName(p.civ)}
                </span>
              </div>
            );
          })}
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
                      {cleanCivName(p.civ)}
                    </span>
                  </div>
                );
              })}
          </>
        )}
      </div>
    </div>
  );
}
