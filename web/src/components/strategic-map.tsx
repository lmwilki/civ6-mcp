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
  Download,
  Camera,
  Film,
  ImageIcon,
  X,
} from "lucide-react";
import { exportPng, exportVideo, exportGif } from "@/lib/map-export";
import { CivIcon, CivSymbol } from "./civ-icon";
import { CIV6_COLORS } from "@/lib/civ-colors";
import { SpatialCharts } from "./spatial-charts";
import type { SpatialTurn } from "@/lib/diary-types";
import {
  SQRT3,
  CS_TYPE_COLORS,
  hexCenter,
  hexVerts,
  screenToHex,
} from "@/lib/hex-geometry";
import { computeBorderLoops } from "@/lib/map-borders";

// ── Helpers ───────────────────────────────────────────────────────────────

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

// ── Export controls sub-component ─────────────────────────────────────────

interface MapExportControlsProps {
  exporting: string | null;
  exportProgress: number;
  exportMenuOpen: boolean;
  exportMenuRef: React.RefObject<HTMLDivElement | null>;
  onToggleMenu: () => void;
  onExport: (format: "png" | "video" | "gif") => void;
  onCancel: () => void;
}

function MapExportControls({
  exporting,
  exportProgress,
  exportMenuOpen,
  exportMenuRef,
  onToggleMenu,
  onExport,
  onCancel,
}: MapExportControlsProps) {
  if (exporting) {
    return (
      <div className="flex items-center gap-2 rounded border border-marble-300 px-2 py-1">
        <div className="h-1.5 w-16 overflow-hidden rounded-full bg-marble-200">
          <div
            className="h-full rounded-full bg-gold-dark transition-all"
            style={{ width: `${exportProgress * 100}%` }}
          />
        </div>
        <span className="font-mono text-xs tabular-nums text-marble-500">
          {Math.round(exportProgress * 100)}%
        </span>
        <button
          onClick={onCancel}
          className="rounded p-0.5 text-marble-400 hover:bg-marble-200 hover:text-marble-700"
          title="Cancel export"
        >
          <X className="h-3 w-3" />
        </button>
      </div>
    );
  }

  return (
    <div className="relative" ref={exportMenuRef}>
      <button
        onClick={onToggleMenu}
        className="rounded p-1.5 text-marble-500 hover:bg-marble-200 hover:text-marble-700"
        title="Export map"
      >
        <Download className="h-4 w-4" />
      </button>
      {exportMenuOpen && (
        <div className="absolute bottom-full right-0 mb-1 rounded border border-marble-300 bg-white shadow-md z-50">
          <button
            onClick={() => onExport("png")}
            className="flex w-full items-center gap-2 whitespace-nowrap px-3 py-1.5 text-xs text-marble-700 hover:bg-marble-100"
          >
            <Camera className="h-3 w-3" /> Screenshot (PNG)
          </button>
          <button
            onClick={() => onExport("video")}
            className="flex w-full items-center gap-2 whitespace-nowrap px-3 py-1.5 text-xs text-marble-700 hover:bg-marble-100"
          >
            <Film className="h-3 w-3" /> Export Video
          </button>
          <button
            onClick={() => onExport("gif")}
            className="flex w-full items-center gap-2 whitespace-nowrap px-3 py-1.5 text-xs text-marble-700 hover:bg-marble-100"
          >
            <ImageIcon className="h-3 w-3" /> Export GIF
          </button>
        </div>
      )}
    </div>
  );
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
      gameId={gameId}
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

function MapRenderer({ gameId, mapData, spatialMap, spatialTurns }: {
  gameId: string;
  mapData: MapDataDoc;
  spatialMap: SpatialMapDoc | null;
  spatialTurns: SpatialTurn[] | null;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const renderTurnRef = useRef<((turn: number) => void) | null>(null);
  const currentTurnRef = useRef(mapData.maxTurn);
  const appRef = useRef<Application | null>(null);
  const hoverGfxRef = useRef<Graphics | null>(null);

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

  // Export state
  const [exporting, setExporting] = useState<"video" | "gif" | null>(null);
  const [exportProgress, setExportProgress] = useState(0);
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const exportAbortRef = useRef<AbortController | null>(null);

  // Auto-advance: follow latest turn when slider is at the end
  const followingLatestRef = useRef(true);
  const prevMaxTurnRef = useRef(mapData.maxTurn);

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
    let cleanupRectListeners: (() => void) | null = null;

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
        preserveDrawingBuffer: true, // needed for export frame capture
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
      appRef.current = app;
      hoverGfxRef.current = hoverGfx;

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

          // Territory borders — contour walk
          const borderLoops = computeBorderLoops(gridW, gridH, hexSize, ox, owners);
          const bw = Math.max(1, hexSize * 0.22);
          for (const { owner, points } of borderLoops) {
            const colors = playerColors.get(owner);
            if (!colors) continue;
            borderGfx.moveTo(points[0], points[1]);
            for (let i = 2; i < points.length; i += 2) {
              borderGfx.lineTo(points[i], points[i + 1]);
            }
            borderGfx.closePath();
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

        // Build tooltip content via DOM (no innerHTML)
        tooltip.textContent = "";
        const heading = document.createElement("span");
        heading.className = "font-medium";

        if (city) {
          const name = cityNames[`${col},${row}`];
          if (name) {
            heading.textContent = name;
            tooltip.appendChild(heading);
            const detail = document.createElement("span");
            detail.style.opacity = "0.6";
            detail.textContent = `${civName} · Pop ${city.pop}`;
            tooltip.appendChild(document.createElement("br"));
            tooltip.appendChild(detail);
          } else {
            heading.textContent = civName;
            tooltip.appendChild(heading);
            if (player.csType) {
              const cs = document.createElement("span");
              cs.style.opacity = "0.6";
              cs.textContent = ` (${player.csType})`;
              tooltip.appendChild(cs);
            }
            const pop = document.createElement("span");
            pop.style.opacity = "0.6";
            pop.textContent = `Pop ${city.pop}`;
            tooltip.appendChild(document.createElement("br"));
            tooltip.appendChild(pop);
          }
          // Ownership history
          const hist = cityHistory.get(`${col},${row}`);
          if (hist && hist.length > 1) {
            const histSpan = document.createElement("span");
            histSpan.style.opacity = "0.5";
            histSpan.style.fontSize = "10px";
            histSpan.textContent = hist.map((h) => {
              const p = players.find((pp) => pp.pid === h.pid);
              const cn = p ? canonicalCivName(cleanCivName(p.civ)) : `P${h.pid}`;
              return `T${h.turn} ${cn}`;
            }).join(" → ");
            tooltip.appendChild(document.createElement("br"));
            tooltip.appendChild(histSpan);
          }
        } else {
          heading.textContent = civName;
          tooltip.appendChild(heading);
          if (player.csType) {
            const cs = document.createElement("span");
            cs.style.opacity = "0.6";
            cs.textContent = ` (${player.csType})`;
            tooltip.appendChild(cs);
          }
        }
        tooltip.style.display = "block";

        // Position tooltip using cached canvas rect (updated on scroll/resize)
        tooltip.style.left = `${canvasRect.left + sx + 12}px`;
        tooltip.style.top = `${canvasRect.top + sy - 8}px`;
      });

      // Cache canvas rect, update on scroll/resize
      let canvasRect = app.canvas.getBoundingClientRect();
      const updateRect = () => { canvasRect = app.canvas.getBoundingClientRect(); };
      window.addEventListener("resize", updateRect);
      window.addEventListener("scroll", updateRect, true);
      cleanupRectListeners = () => {
        window.removeEventListener("resize", updateRect);
        window.removeEventListener("scroll", updateRect, true);
      };

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
      appRef.current = null;
      hoverGfxRef.current = null;
      const el = containerRef.current;
      if (el?.contains(app.canvas)) {
        el.removeChild(app.canvas);
      }
      app.destroy(true, { children: true });
      cleanupRectListeners?.();
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

  // ── Auto-advance slider when new data arrives ───────────────────────

  useEffect(() => {
    if (maxTurn > prevMaxTurnRef.current) {
      prevMaxTurnRef.current = maxTurn;
      if (followingLatestRef.current) {
        setCurrentTurn(maxTurn);
      }
    }
  }, [maxTurn]);

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
            followingLatestRef.current = true; // at end, resume following
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

  // ── Export handler ───────────────────────────────────────────────────

  // Compute crop region to show only the center map copy (not 3x cylindrical)
  const getCropRegion = useCallback(() => {
    const world = worldContainerRef.current;
    if (!world) return undefined;
    // The center copy starts at x=0 in world coords, spanning tileW wide
    // Transform to screen coords using world's transform
    const sx = world.x + 0 * world.scale.x;
    const sy = world.y;
    const sw = tileW * world.scale.x;
    const sh = worldH * world.scale.y;
    return { x: Math.round(sx), y: Math.round(sy), w: Math.round(sw), h: Math.round(sh) };
  }, [tileW, worldH]);

  // Build descriptive filename: civ_gameId_T5-T120.ext
  const exportFilename = useCallback(
    (ext: string, singleTurn?: number) => {
      const agentPlayer = players.find((p) => !p.csType);
      const civSlug = agentPlayer
        ? canonicalCivName(cleanCivName(agentPlayer.civ)).toLowerCase().replace(/\s+/g, "-")
        : "map";
      const turnPart =
        singleTurn != null
          ? `T${singleTurn}`
          : `T${initialTurn}-T${maxTurn}`;
      return `${civSlug}_${gameId}_${turnPart}.${ext}`;
    },
    [players, gameId, initialTurn, maxTurn],
  );

  const handleExport = useCallback(
    async (format: "png" | "video" | "gif") => {
      const app = appRef.current;
      if (!app || !renderTurnRef.current) return;

      setExportMenuOpen(false);
      hoverGfxRef.current?.clear();

      const crop = getCropRegion();

      if (format === "png") {
        const blob = await exportPng(app, crop);
        triggerDownload(blob, exportFilename("png", currentTurn));
        return;
      }

      const abort = new AbortController();
      exportAbortRef.current = abort;
      setExporting(format);
      setExportProgress(0);
      setPlaying(false);

      try {
        const fn = format === "video" ? exportVideo : exportGif;
        const blob = await fn({
          app,
          renderTurn: renderTurnRef.current,
          initialTurn,
          maxTurn,
          onProgress: setExportProgress,
          signal: abort.signal,
          cropRegion: crop,
        });
        if (!abort.signal.aborted) {
          const ext = format === "video" ? "webm" : "gif";
          triggerDownload(blob, exportFilename(ext));
        }
      } finally {
        exportAbortRef.current = null;
        setExporting(null);
        setExportProgress(0);
        renderTurnRef.current?.(currentTurnRef.current);
      }
    },
    [initialTurn, maxTurn, currentTurn, getCropRegion, exportFilename],
  );

  const cancelExport = useCallback(() => {
    exportAbortRef.current?.abort();
  }, []);

  // Close export menu on outside click
  const exportMenuRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!exportMenuOpen) return;
    const close = (e: MouseEvent) => {
      if (exportMenuRef.current && !exportMenuRef.current.contains(e.target as Node)) {
        setExportMenuOpen(false);
      }
    };
    document.addEventListener("click", close);
    return () => document.removeEventListener("click", close);
  }, [exportMenuOpen]);

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
              className={`flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium transition-opacity ${
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
        aria-label="Strategic map replay"
        className="overflow-hidden rounded-sm border border-marble-300 bg-[#1a1a2e] cursor-grab active:cursor-grabbing"
        style={{ height: VIEWPORT_H }}
      />

      {/* Hover tooltip (fixed positioning — scroll-safe) */}
      <div
        ref={tooltipRef}
        className="pointer-events-none fixed z-50 hidden rounded bg-marble-900/90 px-2 py-1 text-xs leading-snug text-marble-100"
        style={{ display: "none" }}
      />

      {/* Replay controls */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => { setPlaying(false); setCurrentTurn(initialTurn); followingLatestRef.current = false; }}
          disabled={!!exporting}
          className="rounded p-1.5 text-marble-500 hover:bg-marble-200 hover:text-marble-700 disabled:opacity-30 disabled:pointer-events-none"
          title="Reset to start"
        >
          <SkipBack className="h-4 w-4" />
        </button>

        <button
          onClick={() => {
            if (currentTurn >= maxTurn) {
              setCurrentTurn(initialTurn);
              followingLatestRef.current = false;
            }
            setPlaying(!playing);
          }}
          disabled={!!exporting}
          className="rounded p-1.5 text-marble-500 hover:bg-marble-200 hover:text-marble-700 disabled:opacity-30 disabled:pointer-events-none"
          title={playing ? "Pause" : "Play"}
        >
          {playing ? (
            <Pause className="h-4 w-4" />
          ) : (
            <Play className="h-4 w-4" />
          )}
        </button>

        <button
          onClick={() => { setPlaying(false); setCurrentTurn(maxTurn); followingLatestRef.current = true; }}
          disabled={!!exporting}
          className="rounded p-1.5 text-marble-500 hover:bg-marble-200 hover:text-marble-700 disabled:opacity-30 disabled:pointer-events-none"
          title="Jump to end"
        >
          <SkipForward className="h-4 w-4" />
        </button>

        <input
          type="range"
          min={initialTurn}
          max={maxTurn}
          value={currentTurn}
          disabled={!!exporting}
          aria-label="Turn navigation"
          onChange={(e) => {
            setPlaying(false);
            const newTurn = Number(e.target.value);
            setCurrentTurn(newTurn);
            followingLatestRef.current = newTurn === maxTurn;
          }}
          className="flex-1 accent-gold-dark disabled:opacity-30"
        />

        <button
          onClick={() => setSpeed((s) => (s + 1) % speedLabels.length)}
          disabled={!!exporting}
          className="rounded border border-marble-300 px-2 py-0.5 font-mono text-xs tabular-nums text-marble-600 hover:bg-marble-200 disabled:opacity-30 disabled:pointer-events-none"
          title="Change speed"
        >
          {speedLabels[speed]}
        </button>

        {/* Export */}
        <MapExportControls
          exporting={exporting}
          exportProgress={exportProgress}
          exportMenuOpen={exportMenuOpen}
          exportMenuRef={exportMenuRef}
          onToggleMenu={() => setExportMenuOpen((s) => !s)}
          onExport={handleExport}
          onCancel={cancelExport}
        />
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
                <span className="text-xs font-medium text-marble-600">
                  {civName}
                </span>
                {leader && (
                  <span className="text-xs text-marble-400">{leader}</span>
                )}
              </div>
            );
          })}

        {/* Legend — city-states */}
        {players.some((p) => p.csType) && (
          <>
            <span className="self-center text-xs text-marble-400">|</span>
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
                    <span className="text-xs font-medium text-marble-400">
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
