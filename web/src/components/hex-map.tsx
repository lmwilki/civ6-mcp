"use client"

import { useMemo } from "react"
import type { TileInfo, CityInfo, UnitInfo } from "@/lib/game-types"

// --- Hex geometry (pointy-top, odd-r offset) ---

const HEX_SIZE = 18
const HEX_W = Math.sqrt(3) * HEX_SIZE
const HEX_H = 2 * HEX_SIZE

function hexToPixel(x: number, y: number): [number, number] {
  const px = HEX_W * (x + (y % 2 === 1 ? 0.5 : 0))
  const py = HEX_H * 0.75 * y
  return [px, py]
}

function hexPoints(): string {
  const pts: string[] = []
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 180) * (60 * i - 30)
    pts.push(`${HEX_SIZE * Math.cos(angle)},${HEX_SIZE * Math.sin(angle)}`)
  }
  return pts.join(" ")
}

const HEX_POLYGON = hexPoints()

// --- Terrain colors ---

function terrainColor(tile: TileInfo): string {
  const t = tile.terrain
  if (t.includes("OCEAN")) return "#3b6d8f"
  if (t.includes("COAST")) return "#5a9bb5"
  if (t.includes("MOUNTAIN") || t.includes("_MOUNTAIN")) return "#6b6560"
  if (t.includes("SNOW")) return "#d8d5d0"
  if (t.includes("TUNDRA")) return "#8a9a7a"
  if (t.includes("DESERT")) return "#d4c5a0"

  const isPlains = t.includes("PLAINS")
  const isHills = tile.is_hills

  if (isHills) return isPlains ? "#a89868" : "#6a8a4a"
  return isPlains ? "#b8a878" : "#7a9a5a"
}

function featureOverlay(tile: TileInfo): string | null {
  if (!tile.feature) return null
  const f = tile.feature
  if (f.includes("FOREST")) return "rgba(40, 70, 30, 0.35)"
  if (f.includes("JUNGLE")) return "rgba(30, 80, 25, 0.4)"
  if (f.includes("MARSH")) return "rgba(60, 90, 70, 0.3)"
  if (f.includes("FLOODPLAINS")) return "rgba(90, 130, 60, 0.2)"
  if (f.includes("REEF")) return "rgba(50, 130, 120, 0.3)"
  if (f.includes("ICE")) return "rgba(200, 220, 240, 0.5)"
  return null
}

// --- Resource symbology ---

type ResourceStyle = { color: string; shape: "diamond" | "circle" | "square"; letter?: string }

function resourceStyle(tile: TileInfo): ResourceStyle | null {
  if (!tile.resource) return null
  const rc = tile.resource_class
  const r = tile.resource.toUpperCase()

  // Color by class
  const classColor =
    rc === "strategic" ? "#c0392b" :
    rc === "luxury" ? "#8e44ad" :
    "#27ae60" // bonus

  // Letter abbreviation for recognizable resources
  let letter: string | undefined
  if (r.includes("IRON")) letter = "Fe"
  else if (r.includes("HORSE")) letter = "Ho"
  else if (r.includes("NITER")) letter = "Ni"
  else if (r.includes("COAL")) letter = "Co"
  else if (r.includes("OIL")) letter = "Oi"
  else if (r.includes("ALUMINUM")) letter = "Al"
  else if (r.includes("URANIUM")) letter = "U"
  else if (r.includes("WHEAT")) letter = "Wh"
  else if (r.includes("RICE")) letter = "Ri"
  else if (r.includes("CATTLE")) letter = "Ca"
  else if (r.includes("SHEEP")) letter = "Sh"
  else if (r.includes("DEER")) letter = "De"
  else if (r.includes("FISH")) letter = "Fi"
  else if (r.includes("STONE")) letter = "St"
  else if (r.includes("DIAMOND")) letter = "Di"
  else if (r.includes("SILK")) letter = "Si"
  else if (r.includes("IVORY")) letter = "Iv"
  else if (r.includes("FURS")) letter = "Fu"
  else if (r.includes("SILVER")) letter = "Ag"
  else if (r.includes("GOLD")) letter = "Au"
  else if (r.includes("MARBLE")) letter = "Ma"
  else if (r.includes("SPICE")) letter = "Sp"
  else if (r.includes("SUGAR")) letter = "Su"
  else if (r.includes("COPPER")) letter = "Cu"
  else if (r.includes("SALT")) letter = "Sa"
  else if (r.includes("AMBER")) letter = "Am"
  else if (r.includes("JADE")) letter = "Ja"
  else if (r.includes("MERCURY")) letter = "Hg"
  else if (r.includes("BANANA")) letter = "Ba"
  else if (r.includes("CITRUS")) letter = "Ci"
  else if (r.includes("CRAB")) letter = "Cr"
  else if (r.includes("PEARL")) letter = "Pe"
  else if (r.includes("TRUFFLE")) letter = "Tr"
  else if (r.includes("WINE")) letter = "Wi"
  else if (r.includes("TEA")) letter = "Te"
  else if (r.includes("COFFEE")) letter = "Cf"
  else if (r.includes("TOBACCO")) letter = "Tb"
  else if (r.includes("COCOA")) letter = "Cc"
  else if (r.includes("DYE")) letter = "Dy"
  else if (r.includes("INCENSE")) letter = "In"
  else if (r.includes("COTTON")) letter = "Ct"

  const shape: "diamond" | "circle" | "square" =
    rc === "strategic" ? "square" :
    rc === "luxury" ? "diamond" :
    "circle"

  return { color: classColor, shape, letter }
}

// SVG shapes for resources (drawn at origin, scaled to ~4px)
function ResourceMarker({ style }: { style: ResourceStyle }) {
  const { color, shape, letter } = style
  return (
    <g>
      {shape === "diamond" && (
        <polygon points="0,-3.5 3,-0.5 0,2.5 -3,-0.5" fill={color} stroke="#fff" strokeWidth={0.6} opacity={0.9} />
      )}
      {shape === "square" && (
        <rect x={-2.8} y={-3} width={5.6} height={5.6} rx={0.8} fill={color} stroke="#fff" strokeWidth={0.6} opacity={0.9} />
      )}
      {shape === "circle" && (
        <circle cy={-0.2} r={3} fill={color} stroke="#fff" strokeWidth={0.6} opacity={0.9} />
      )}
      {letter && (
        <text
          y={0.6}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize={3.4}
          fontFamily="monospace"
          fontWeight="bold"
          fill="#fff"
        >
          {letter}
        </text>
      )}
    </g>
  )
}

// --- Unit symbology ---

// SVG icons for unit types (small, ~5px, drawn at origin)
function UnitMarker({ unit, offsetX }: { unit: UnitInfo; offsetX: number }) {
  const t = unit.unit_type.toUpperCase()
  const isMilitary = unit.combat_strength > 0
  const isHurt = unit.health < unit.max_health

  // Colors
  const bg = isMilitary ? "#C4785C" : "#7A9B8A"
  const fg = "#fff"
  const hurtRing = isHurt ? "#e74c3c" : undefined

  return (
    <g transform={`translate(${offsetX}, 6)`}>
      {/* Background circle */}
      <circle r={3.5} fill={bg} stroke={hurtRing || "#2a2521"} strokeWidth={hurtRing ? 1 : 0.6} />

      {/* Icon glyph */}
      {t.includes("WARRIOR") || t.includes("SWORDSMAN") || t.includes("MAN_AT_ARMS") || t.includes("MUSKET") ? (
        // Sword: diagonal line with crossguard
        <g fill="none" stroke={fg} strokeWidth={0.8} strokeLinecap="round">
          <line x1={-1.5} y1={1.5} x2={1.5} y2={-1.5} />
          <line x1={-0.8} y1={-0.3} x2={0.8} y2={0.3} />
        </g>
      ) : t.includes("ARCHER") || t.includes("CROSSBOW") ? (
        // Bow: arc with line
        <g fill="none" stroke={fg} strokeWidth={0.7} strokeLinecap="round">
          <path d="M-1,-2 Q2,0 -1,2" />
          <line x1={-1} y1={-1.2} x2={-1} y2={1.2} />
        </g>
      ) : t.includes("SLINGER") ? (
        // Sling: small S curve
        <g fill="none" stroke={fg} strokeWidth={0.8} strokeLinecap="round">
          <path d="M-1,-1.5 Q1,-0.5 -1,0.5 Q1,1.5 -1,1.5" />
        </g>
      ) : t.includes("BUILDER") ? (
        // Hammer
        <g fill="none" stroke={fg} strokeWidth={0.8} strokeLinecap="round">
          <line x1={0} y1={-1.5} x2={0} y2={1.5} />
          <line x1={-1.3} y1={-1.5} x2={1.3} y2={-1.5} />
        </g>
      ) : t.includes("SETTLER") ? (
        // Flag
        <g fill={fg} stroke={fg} strokeWidth={0.5}>
          <line x1={-1} y1={-2} x2={-1} y2={2} strokeLinecap="round" />
          <polygon points="-1,-2 2,-1 -1,0" />
        </g>
      ) : t.includes("TRADER") ? (
        // Package: small box
        <g fill="none" stroke={fg} strokeWidth={0.7} strokeLinecap="round" strokeLinejoin="round">
          <rect x={-1.5} y={-1.2} width={3} height={2.4} rx={0.3} />
          <line x1={0} y1={-1.2} x2={0} y2={1.2} />
        </g>
      ) : t.includes("SCOUT") || t.includes("RANGER") ? (
        // Compass: cross with circle
        <g fill="none" stroke={fg} strokeWidth={0.6}>
          <circle r={1.5} />
          <line x1={0} y1={-2} x2={0} y2={2} />
          <line x1={-2} y1={0} x2={2} y2={0} />
        </g>
      ) : t.includes("KNIGHT") || t.includes("CAVALRY") || t.includes("HORSEMAN") ? (
        // Horse: chevron
        <g fill="none" stroke={fg} strokeWidth={0.8} strokeLinecap="round" strokeLinejoin="round">
          <polyline points="-1.5,1 0,-1.5 1.5,1" />
        </g>
      ) : t.includes("CATAPULT") || t.includes("BOMBARD") || t.includes("TREBUCHET") ? (
        // Siege: triangle
        <polygon points="0,-2 2,1.5 -2,1.5" fill="none" stroke={fg} strokeWidth={0.7} />
      ) : (
        // Default: simple dot
        <circle r={1.2} fill={fg} />
      )}
    </g>
  )
}

// --- Improvement symbology ---

function ImprovementMarker({ improvement }: { improvement: string }) {
  const imp = improvement.toUpperCase()
  const color = "#D4A853"

  if (imp.includes("FARM")) {
    // Grid pattern (field rows)
    return (
      <g stroke={color} strokeWidth={0.5} opacity={0.7}>
        <line x1={-2.5} y1={-1} x2={2.5} y2={-1} />
        <line x1={-2.5} y1={0.5} x2={2.5} y2={0.5} />
        <line x1={-2.5} y1={2} x2={2.5} y2={2} />
      </g>
    )
  }
  if (imp.includes("MINE") || imp.includes("QUARRY")) {
    // Pickaxe-like
    return (
      <g stroke={color} strokeWidth={0.7} strokeLinecap="round" opacity={0.7}>
        <line x1={-1.5} y1={1.5} x2={1.5} y2={-1.5} />
        <line x1={0} y1={-1.5} x2={1.5} y2={-1.5} />
        <line x1={1.5} y1={-1.5} x2={1.5} y2={0} />
      </g>
    )
  }
  if (imp.includes("PLANTATION") || imp.includes("CAMP")) {
    // Small triangle (tent/tree)
    return (
      <polygon points="0,-2 2,1.5 -2,1.5" fill="none" stroke={color} strokeWidth={0.6} opacity={0.7} />
    )
  }
  if (imp.includes("PASTURE")) {
    // Fence
    return (
      <g stroke={color} strokeWidth={0.5} opacity={0.7}>
        <line x1={-2} y1={0} x2={2} y2={0} />
        <line x1={-1.2} y1={-1.5} x2={-1.2} y2={1} />
        <line x1={1.2} y1={-1.5} x2={1.2} y2={1} />
      </g>
    )
  }
  if (imp.includes("LUMBER_MILL")) {
    // Circular saw
    return (
      <g opacity={0.7}>
        <circle r={2} fill="none" stroke={color} strokeWidth={0.6} />
        <line x1={0} y1={-2} x2={0} y2={2} stroke={color} strokeWidth={0.4} />
      </g>
    )
  }
  if (imp.includes("FISHING")) {
    // Wave
    return (
      <g fill="none" stroke={color} strokeWidth={0.7} opacity={0.7}>
        <path d="M-2.5,0 Q-1.2,-1.5 0,0 Q1.2,1.5 2.5,0" />
      </g>
    )
  }
  // Default: small dot
  return <circle r={1.5} fill={color} opacity={0.5} />
}

// --- City marker ---

function CityMarker({ city }: { city: CityInfo }) {
  return (
    <g>
      {/* Outer ring */}
      <circle r={8} fill="none" stroke="#D4A853" strokeWidth={1.5} opacity={0.4} />
      {/* Main circle */}
      <circle r={6} fill="#D4A853" stroke="#2a2521" strokeWidth={1} />
      {/* City name label */}
      <text
        y={-11}
        textAnchor="middle"
        fontSize={5.5}
        fontWeight="bold"
        fontFamily="sans-serif"
        fill="#2a2521"
        stroke="#FAFAF8"
        strokeWidth={2}
        paintOrder="stroke"
      >
        {city.name}
      </text>
      {/* Population number */}
      <text
        y={2}
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize={5.5}
        fontWeight="bold"
        fontFamily="monospace"
        fill="#2a2521"
      >
        {city.population}
      </text>
    </g>
  )
}

// --- Component ---

interface HexMapProps {
  tiles: Map<string, TileInfo>
  cities: CityInfo[]
  units: UnitInfo[]
}

export function HexMap({ tiles, cities, units }: HexMapProps) {
  const { tileArray, viewBox } = useMemo(() => {
    const arr = Array.from(tiles.values())
    if (arr.length === 0) return { tileArray: arr, viewBox: "0 0 100 100" }

    let minPx = Infinity, minPy = Infinity, maxPx = -Infinity, maxPy = -Infinity
    for (const t of arr) {
      const [px, py] = hexToPixel(t.x, t.y)
      if (px < minPx) minPx = px
      if (py < minPy) minPy = py
      if (px > maxPx) maxPx = px
      if (py > maxPy) maxPy = py
    }

    const pad = HEX_SIZE * 2
    return {
      tileArray: arr,
      viewBox: `${minPx - pad} ${minPy - pad} ${maxPx - minPx + pad * 2} ${maxPy - minPy + pad * 2}`,
    }
  }, [tiles])

  const citySet = useMemo(() => {
    const m = new Map<string, CityInfo>()
    for (const c of cities) m.set(`${c.x},${c.y}`, c)
    return m
  }, [cities])

  const unitMap = useMemo(() => {
    const m = new Map<string, UnitInfo[]>()
    for (const u of units) {
      const key = `${u.x},${u.y}`
      if (!m.has(key)) m.set(key, [])
      m.get(key)!.push(u)
    }
    return m
  }, [units])

  if (tileArray.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-marble-400">
        <p className="font-display text-sm tracking-[0.12em] uppercase">No map data</p>
      </div>
    )
  }

  return (
    <svg
      viewBox={viewBox}
      className="h-full w-full"
      style={{ background: "#3b6d8f" }}
    >
      {/* Terrain hexes */}
      {tileArray.map((tile) => {
        const [px, py] = hexToPixel(tile.x, tile.y)
        const key = `${tile.x},${tile.y}`
        const city = citySet.get(key)
        const tileUnits = unitMap.get(key)
        const overlay = featureOverlay(tile)
        const resStyle = resourceStyle(tile)
        const isOwned = tile.owner_id === 0

        return (
          <g key={key} transform={`translate(${px},${py})`}>
            {/* Base terrain */}
            <polygon
              points={HEX_POLYGON}
              fill={terrainColor(tile)}
              stroke={isOwned ? "#D4A853" : "#2a2521"}
              strokeWidth={isOwned ? 1.2 : 0.3}
              strokeOpacity={isOwned ? 0.7 : 0.2}
            />

            {/* Feature overlay */}
            {overlay && (
              <polygon points={HEX_POLYGON} fill={overlay} />
            )}

            {/* River indicator */}
            {tile.is_river && !tile.terrain.includes("OCEAN") && !tile.terrain.includes("COAST") && (
              <line
                x1={-HEX_SIZE * 0.4} y1={HEX_SIZE * 0.5}
                x2={HEX_SIZE * 0.4} y2={HEX_SIZE * 0.5}
                stroke="#4a90b8"
                strokeWidth={1.2}
                strokeLinecap="round"
                opacity={0.6}
              />
            )}

            {/* Improvement marker (under resources & cities) */}
            {tile.improvement && !city && (
              <ImprovementMarker improvement={tile.improvement} />
            )}

            {/* Resource marker */}
            {resStyle && !city && (
              <ResourceMarker style={resStyle} />
            )}

            {/* City marker */}
            {city && <CityMarker city={city} />}

            {/* Player units */}
            {tileUnits && !city && tileUnits.map((u, i) => (
              <UnitMarker
                key={u.unit_id}
                unit={u}
                offsetX={i * 8 - (tileUnits.length - 1) * 4}
              />
            ))}

            {/* Units on city tiles — offset below */}
            {tileUnits && city && tileUnits.map((u, i) => (
              <UnitMarker
                key={u.unit_id}
                unit={u}
                offsetX={i * 8 - (tileUnits.length - 1) * 4}
              />
            ))}

            {/* Hostile unit markers (from tile.units) */}
            {tile.units && tile.units.length > 0 && !tileUnits && (
              <g>
                <circle r={4} fill="#e74c3c" stroke="#2a2521" strokeWidth={0.8} opacity={0.85} />
                <text
                  y={0.5}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fontSize={4}
                  fontWeight="bold"
                  fill="#fff"
                >
                  !
                </text>
              </g>
            )}
          </g>
        )
      })}
    </svg>
  )
}
