import {
  SQRT3,
  NEIGHBORS_EVEN,
  NEIGHBORS_ODD,
  EDGE_VERTICES,
  hexCenter,
} from "./hex-geometry";

export interface BorderLoop {
  owner: number;
  points: number[]; // flat [x, y, x, y, ...]
}

/**
 * Compute closed border contour loops for territory boundaries.
 * Collects directed boundary edges per owner, then walks closed loops.
 */
export function computeBorderLoops(
  gridW: number,
  gridH: number,
  hexSize: number,
  ox: number,
  owners: Int8Array,
): BorderLoop[] {
  const bh = (SQRT3 / 2) * hexSize;
  const vOffsets: [number, number][] = [
    [0, -hexSize],      [bh, -hexSize / 2], [bh, hexSize / 2],
    [0, hexSize],       [-bh, hexSize / 2],  [-bh, -hexSize / 2],
  ];
  const vKey = (vx: number, vy: number) =>
    `${Math.round(vx * 100)},${Math.round(vy * 100)}`;

  // Per-owner edge map: fullVertexKey → { coords of destination, full key of destination }
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

  // Walk closed loops per owner
  const result: BorderLoop[] = [];
  for (const [owner, edges] of edgesByOwner) {
    const visited = new Set<string>();
    for (const [startKey] of edges) {
      if (visited.has(startKey)) continue;
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
      result.push({ owner, points: loop });
    }
  }

  return result;
}
