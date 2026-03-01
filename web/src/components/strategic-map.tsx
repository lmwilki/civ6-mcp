"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "convex/react";
import { api } from "../../convex/_generated/api";
import { Application, Container, Graphics } from "pixi.js";
import {
  cleanCivName,
  unpackTerrain,
  unpackOwnerFrames,
  unpackCityFrames,
  unpackSpatialTiles,
  type MapDataDoc,
  type MapCitySnapshot,
} from "@/lib/diary-types";
import {
  getTerrainColor,
  getFeatureOverlay,
  FEATURE_OVERLAY_ALPHA,
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
const MAX_DARK = 0.9; // unobserved tile darkness (0=clear, 1=black)

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
  const currentTurnRef = useRef(mapData.maxTurn);

  const [currentTurn, setCurrentTurn] = useState(mapData.maxTurn);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(0);
  const animRef = useRef(0);
  const lastFrameRef = useRef(0);
  const hexSize = 6; // fixed base hex size — zoom handles magnification
  const [showAttention, setShowAttention] = useState(false);
  const showAttentionRef = useRef(false);
  const worldContainerRef = useRef<Container | null>(null);
  const dragRef = useRef<{ startX: number; startY: number; panX: number; panY: number } | null>(null);

  // ── Unpack & precompute ───────────────────────────────────────────────

  const {
    terrain,
    ownerKeyframes,
    cityKeyframes,
    cityNames,
    cityHistory,
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
    const t = unpackTerrain(terrainArr);
    const of_ = unpackOwnerFrames(ownerFramesArr);
    const cf = unpackCityFrames(cityFramesArr);

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

    // City name lookup: "x,y" → name
    const cn: Record<string, string> = mapData.cityNames
      ? JSON.parse(mapData.cityNames)
      : {};

    // City ownership history: "x,y" → [{pid, turn}] sorted by turn
    const ch = new Map<string, { pid: number; turn: number }[]>();
    for (const frame of cf) {
      for (const city of frame.cities) {
        const k = `${city.x},${city.y}`;
        let hist = ch.get(k);
        if (!hist) { hist = []; ch.set(k, hist); }
        // Only add if pid changed from previous entry
        if (hist.length === 0 || hist[hist.length - 1].pid !== city.pid) {
          hist.push({ pid: city.pid, turn: frame.turn });
        }
      }
    }

    return {
      terrain: t,
      ownerKeyframes: ownerKf,
      cityKeyframes: cf,
      cityNames: cn,
      cityHistory: ch,
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

  // ── World dimensions (fixed at base hexSize) ────────────────────────

  // Tile period for cylindrical wrapping — exactly one column-width per grid column
  const tileW = SQRT3 * hexSize * gridW;
  // Full world includes the half-hex padding on each side for rendering
  const worldW = Math.ceil(tileW + SQRT3 * hexSize);
  const worldH = Math.ceil(1.5 * hexSize * gridH + hexSize * 2);
  const VIEWPORT_H = 500;

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

  // ── Pixi.js lifecycle ─────────────────────────────────────────────────

  useEffect(() => {
    const app = new Application();
    let destroyed = false;

    (async () => {
      // Viewport = container width (or fallback) × fixed height
      const containerEl = containerRef.current;
      const viewW = containerEl?.clientWidth ?? 800;
      const viewH = VIEWPORT_H;

      await app.init({
        background: 0x1a1a2e,
        width: viewW,
        height: viewH,
        autoDensity: true,
        resolution: window.devicePixelRatio || 1,
        antialias: true,
      });
      if (destroyed) return;
      if (!containerEl) return;
      containerEl.insertBefore(app.canvas, containerEl.firstChild);

      // World container — holds all layers, transformed for pan/zoom
      const world = new Container();
      app.stage.addChild(world);
      worldContainerRef.current = world;

      // Scene layers (bottom to top)
      const terrainGfx = new Graphics();
      const territoryGfx = new Graphics();
      const borderGfx = new Graphics();
      const cityGfx = new Graphics();
      const attentionGfx = new Graphics();
      const hoverGfx = new Graphics();
      world.addChild(
        terrainGfx, territoryGfx, borderGfx, attentionGfx,
        cityGfx, hoverGfx,
      );

      // X offsets for cylindrical wrapping — draw world 3 times using tile period
      const xOffsets = [-tileW, 0, tileW];

      // ── Static terrain (drawn once, 3 copies for wrapping) ─────────

      for (const ox of xOffsets) {
        for (let y = 0; y < gridH; y++) {
          for (let x = 0; x < gridW; x++) {
            const idx = y * gridW + x;
            const tile = terrain[idx];
            if (!tile) continue;
            const [cx, cy] = hexCenter(x, y, hexSize, gridH);
            const verts = hexVerts(cx + ox, cy, hexSize);

            terrainGfx.poly(verts).fill(getTerrainColor(tile.terrain));

            const featureColor = getFeatureOverlay(tile.feature);
            if (featureColor) {
              terrainGfx.poly(verts).fill({
                color: featureColor, alpha: FEATURE_OVERLAY_ALPHA,
              });
            }
          }
        }
      }

      // ── Pan / zoom helpers ─────────────────────────────────────────

      function clamp(v: number, lo: number, hi: number) {
        return Math.max(lo, Math.min(hi, v));
      }

      function wrapAndClamp() {
        const scaledTileW = tileW * world.scale.x;
        // Horizontal wrap: keep world.x in [-scaledTileW, 0)
        world.x = ((world.x % scaledTileW) + scaledTileW) % scaledTileW - scaledTileW;
        // Vertical clamp — center if map smaller than viewport
        const scaledH = worldH * world.scale.y;
        if (scaledH <= viewH) {
          world.y = (viewH - scaledH) / 2;
        } else {
          world.y = clamp(world.y, viewH - scaledH, 0);
        }
      }

      // Initial view: fit to viewport, ensuring map fills viewport vertically
      const fitZoomW = viewW / worldW;
      const fitZoomH = viewH / worldH;
      const minZoom = Math.max(fitZoomW, fitZoomH); // never smaller than viewport
      const fitZoom = Math.max(minZoom, fitZoomW);
      world.scale.set(fitZoom);
      world.x = 0;
      wrapAndClamp();

      // ── Dynamic turn renderer (3-copy for each dynamic layer) ──────

      const renderTurn = (turn: number) => {
        territoryGfx.clear();
        borderGfx.clear();
        cityGfx.clear();

        const owners = getOwnersAtTurn(turn);

        for (const ox of xOffsets) {
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
                .poly(hexVerts(cx + ox, cy, hexSize))
                .fill(colors.primary);
            }
          }

          // Territory borders — boundary edge graph walk for continuous contours.
          // Collect directed boundary edges per owner, then walk closed loops.
          const bh = (SQRT3 / 2) * hexSize;
          const vOffsets: [number, number][] = [
            [0, -hexSize],      [bh, -hexSize / 2], [bh, hexSize / 2],
            [0, hexSize],       [-bh, hexSize / 2],  [-bh, -hexSize / 2],
          ];
          const vKey = (vx: number, vy: number) =>
            `${Math.round(vx * 100)},${Math.round(vy * 100)}`;

          // Per-owner edge map: fullVertexKey → { inset coords of destination, full key of destination }
          const edgesByOwner = new Map<number, Map<string, { ix: number; iy: number; nk: string }>>();

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
                // Full-size vertex positions (shared exactly between adjacent hexes)
                const fromX = cx + ox + vOffsets[vi][0];
                const fromY = cy + vOffsets[vi][1];
                const toX = cx + ox + vOffsets[vj][0];
                const toY = cy + vOffsets[vj][1];

                let edges = edgesByOwner.get(owner);
                if (!edges) { edges = new Map(); edgesByOwner.set(owner, edges); }
                const fk = vKey(fromX, fromY);
                if (!edges.has(fk)) {
                  edges.set(fk, { ix: toX, iy: toY, nk: vKey(toX, toY) });
                }
              }
            }
          }

          // Walk closed loops per owner and render
          const bw = Math.max(1, hexSize * 0.22);
          for (const [owner, edges] of edgesByOwner) {
            const colors = playerColors.get(owner);
            if (!colors) continue;
            const visited = new Set<string>();

            for (const [startKey] of edges) {
              if (visited.has(startKey)) continue;
              // Walk the loop
              const loop: number[] = [];
              let key = startKey;
              while (!visited.has(key)) {
                visited.add(key);
                const edge = edges.get(key);
                if (!edge) break;
                loop.push(edge.ix, edge.iy);
                key = edge.nk;
              }
              if (loop.length < 6) continue; // need at least 3 vertices

              borderGfx.moveTo(loop[0], loop[1]);
              for (let i = 2; i < loop.length; i += 2) {
                borderGfx.lineTo(loop[i], loop[i + 1]);
              }
              borderGfx.closePath();
            }

            borderGfx.stroke({ width: bw, color: colors.secondary, join: "miter", alignment: 1 });
          }

          // Cities — radius scales with population
          const cities = getCitiesAtTurn(turn);
          const minR = hexSize * 0.35;
          const maxR = hexSize * 0.8;
          const popNorm = 1 / Math.sqrt(30);
          for (const city of cities) {
            const [cx, cy] = hexCenter(city.x, city.y, hexSize, gridH);
            const colors = playerColors.get(city.pid);
            const t = Math.min(1, Math.sqrt(city.pop) * popNorm);
            const r = minR + t * (maxR - minR);
            cityGfx
              .circle(cx + ox, cy, r)
              .fill(colors?.secondary ?? "#ffffff")
              .stroke({
                width: CITY_MARKER.strokeWidth,
                color: CITY_MARKER.strokeColor,
              });
          }
        } // end xOffsets

        // Agent attention overlay — darkness lifts where the agent has observed
        attentionGfx.clear();
        if (attentionData && showAttentionRef.current) {
          const logMax = Math.log(attentionData.maxWeight + 1);
          for (const ox of xOffsets) {
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
                  .poly(hexVerts(hx + ox, hy, hexSize * 0.98))
                  .fill({ color: 0x000000, alpha });
              }
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
        // Suppress hover while dragging
        if (dragRef.current) return;
        // Convert screen coords → world coords accounting for container transform
        const { x: sx, y: sy } = e.global;
        const wx = (sx - world.x) / world.scale.x;
        const wy = (sy - world.y) / world.scale.y;
        // Wrap horizontally into [0, tileW) using tile period
        const wrappedWx = ((wx % tileW) + tileW) % tileW;
        const hex = screenToHex(wrappedWx, wy, hexSize, gridW, gridH);
        const tooltip = tooltipRef.current;

        if (!hex) {
          hoverGfx.clear();
          lastHexKey = "";
          if (tooltip) tooltip.style.display = "none";
          return;
        }

        const [col, row] = hex;
        const key = `${col},${row}`;

        // Redraw highlight (all 3 copies for wrapping)
        if (key !== lastHexKey) {
          lastHexKey = key;
          hoverGfx.clear();
          for (const ox of xOffsets) {
            const [cx, cy] = hexCenter(col, row, hexSize, gridH);
            hoverGfx
              .poly(hexVerts(cx + ox, cy, hexSize * 0.98))
              .stroke({ width: 1.5, color: "#ffffff", alpha: 0.7 });
          }
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
          const name = cityNames[`${col},${row}`];
          if (name) {
            html = `<span class="font-medium">${name}</span>`;
            html += `<br/><span style="opacity:0.6">${civName} · Pop ${city.pop}</span>`;
          } else {
            html += `<br/><span style="opacity:0.6">Pop ${city.pop}</span>`;
          }
          // Ownership history
          const hist = cityHistory.get(`${col},${row}`);
          if (hist && hist.length > 1) {
            html += `<br/><span style="opacity:0.5; font-size:10px">`;
            html += hist.map((h) => {
              const p = players.find((pp) => pp.pid === h.pid);
              const cn = p ? canonicalCivName(cleanCivName(p.civ)) : `P${h.pid}`;
              return `T${h.turn} ${cn}`;
            }).join(" → ");
            html += `</span>`;
          }
        }

        tooltip.innerHTML = html;
        tooltip.style.display = "block";

        // Position tooltip using screen coords
        const rect = app.canvas.getBoundingClientRect();
        tooltip.style.left = `${rect.left + sx + 12}px`;
        tooltip.style.top = `${rect.top + sy - 8}px`;
      });

      // ── Wheel zoom (centered on cursor) ────────────────────────────

      const onWheel = (e: WheelEvent) => {
        e.preventDefault();
        const factor = e.deltaY < 0 ? 1.1 : 0.9;
        const newScale = clamp(world.scale.x * factor, minZoom, 6);

        const rect = app.canvas.getBoundingClientRect();
        const mx = (e.clientX - rect.left) * (app.screen.width / rect.width);
        const my = (e.clientY - rect.top) * (app.screen.height / rect.height);

        // Zoom toward cursor
        const wx = (mx - world.x) / world.scale.x;
        const wy = (my - world.y) / world.scale.y;
        world.scale.set(newScale);
        world.x = mx - wx * newScale;
        world.y = my - wy * newScale;
        wrapAndClamp();
      };
      app.canvas.addEventListener("wheel", onWheel, { passive: false });

      // ── Drag pan ───────────────────────────────────────────────────

      const onPointerDown = (e: PointerEvent) => {
        dragRef.current = {
          startX: e.clientX, startY: e.clientY,
          panX: world.x, panY: world.y,
        };
        app.canvas.setPointerCapture(e.pointerId);
        // Hide tooltip and hover during drag
        hoverGfx.clear();
        lastHexKey = "";
        if (tooltipRef.current) tooltipRef.current.style.display = "none";
      };
      const onPointerMove = (e: PointerEvent) => {
        if (!dragRef.current) return;
        const dpr = app.screen.width / app.canvas.getBoundingClientRect().width;
        world.x = dragRef.current.panX + (e.clientX - dragRef.current.startX) * dpr;
        world.y = dragRef.current.panY + (e.clientY - dragRef.current.startY) * dpr;
        wrapAndClamp();
      };
      const onPointerUp = () => { dragRef.current = null; };

      app.canvas.addEventListener("pointerdown", onPointerDown);
      app.canvas.addEventListener("pointermove", onPointerMove);
      app.canvas.addEventListener("pointerup", onPointerUp);

      app.canvas.addEventListener("mouseleave", () => {
        hoverGfx.clear();
        lastHexKey = "";
        dragRef.current = null;
        if (tooltipRef.current) tooltipRef.current.style.display = "none";
      });
    })();

    return () => {
      destroyed = true;
      worldContainerRef.current = null;
      const el = containerRef.current;
      if (el?.contains(app.canvas)) {
        el.removeChild(app.canvas);
      }
      app.destroy(true, { children: true });
    };
  }, [
    worldW, worldH, VIEWPORT_H, hexSize, terrain, gridW, gridH,
    playerColors, getOwnersAtTurn, getCitiesAtTurn, players, cityNames, cityHistory,
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
        <h2 className="font-display text-lg font-semibold text-marble-800">
          Map
        </h2>
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
              Agent Attention
            </button>
          )}
          <span className="font-mono text-sm tabular-nums text-marble-600">
            Turn {currentTurn}
          </span>
        </div>
      </div>

      {/* Pixi canvas container — fixed height viewport */}
      <div
        ref={containerRef}
        className="overflow-hidden rounded-sm border border-marble-300 bg-[#1a1a2e] cursor-grab active:cursor-grabbing"
        style={{ height: VIEWPORT_H }}
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
        <SpatialCharts data={spatialTurns} currentTurn={currentTurn} />
      )}
    </div>
  );
}
