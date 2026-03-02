// ── Hex grid constants & pure geometry helpers ──────────────────────────

export const SQRT3 = Math.sqrt(3);

export const CS_TYPE_COLORS: Record<string, string> = {
  Scientific: "#4A90D9",
  Cultural: "#9B59B6",
  Militaristic: "#CA1415",
  Religious: "#F9F9F9",
  Trade: "#F7D801",
  Industrial: "#FF8112",
};

// Odd-r offset neighbors: E, SE, SW, W, NW, NE
export const NEIGHBORS_EVEN = [[1, 0], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1]];
export const NEIGHBORS_ODD  = [[1, 0], [1, 1], [0, 1], [-1, 0], [0, -1], [1, -1]];

// Edge-vertex indices for border drawing (accounting for Y-flip)
// Screen vertices: 0=top, 1=NE, 2=SE, 3=bottom, 4=SW, 5=NW
// After Y-flip: game-N→screen-bottom, game-S→screen-top
export const EDGE_VERTICES: [number, number][] = [
  [1, 2], [0, 1], [5, 0], [4, 5], [3, 4], [2, 3],
];

/** Hex center in CSS-pixel coords (pointy-top, odd-r offset, Y-flipped) */
export function hexCenter(
  col: number, row: number, hexSize: number, gridH: number,
): [number, number] {
  const flippedRow = gridH - 1 - row;
  const cx = SQRT3 * hexSize * (col + 0.5 * (row & 1)) + (SQRT3 * hexSize) / 2;
  const cy = 1.5 * hexSize * flippedRow + hexSize;
  return [cx, cy];
}

/** Flat array of pointy-top hex vertices (12 numbers: x0,y0,...x5,y5) */
export function hexVerts(cx: number, cy: number, s: number): number[] {
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
export function screenToHex(
  px: number, py: number,
  hexSize: number, gridW: number, gridH: number,
): [number, number] | null {
  const flippedRow = Math.round((py - hexSize) / (1.5 * hexSize));
  const row = gridH - 1 - flippedRow;
  const offset = 0.5 * (row & 1);
  const col = Math.round(px / (SQRT3 * hexSize) - 0.5 - offset);

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
