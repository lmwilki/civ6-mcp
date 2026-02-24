import { describe, it, expect } from "vitest"
import { computeElo, type GameResult } from "./elo"

function makeParticipant(
  id: string,
  won: boolean,
  type: "model" | "ai_leader" = "ai_leader",
  civ = "ROME"
) {
  return { id, name: id, type, civ, won }
}

describe("computeElo", () => {
  it("returns empty array for empty input", () => {
    expect(computeElo([])).toEqual([])
  })

  it("skips games with fewer than 2 participants", () => {
    const results: GameResult[] = [
      { gameId: "g1", participants: [makeParticipant("a", true)] },
    ]
    expect(computeElo(results)).toEqual([])
  })

  it("skips games with no winner", () => {
    const results: GameResult[] = [
      {
        gameId: "g1",
        participants: [
          makeParticipant("a", false),
          makeParticipant("b", false),
        ],
      },
    ]
    expect(computeElo(results)).toEqual([])
  })

  it("computes correct ELO for a 2-player game", () => {
    const results: GameResult[] = [
      {
        gameId: "g1",
        participants: [
          makeParticipant("winner", true, "model"),
          makeParticipant("loser", false, "ai_leader"),
        ],
      },
    ]
    const ratings = computeElo(results)
    expect(ratings).toHaveLength(2)

    const winner = ratings.find((r) => r.id === "winner")!
    const loser = ratings.find((r) => r.id === "loser")!

    // Both start at 1500, equal expected = 0.5
    // K_eff = 32 / sqrt(1) = 32
    // winner: 1500 + 32*(1-0.5) = 1516
    // loser:  1500 + 32*(0-0.5) = 1484
    expect(winner.elo).toBe(1516)
    expect(loser.elo).toBe(1484)
    expect(winner.wins).toBe(1)
    expect(winner.losses).toBe(0)
    expect(loser.wins).toBe(0)
    expect(loser.losses).toBe(1)
  })

  it("handles multiplayer free-for-all correctly", () => {
    const results: GameResult[] = [
      {
        gameId: "g1",
        participants: [
          makeParticipant("p1", true, "model"),
          makeParticipant("p2", false),
          makeParticipant("p3", false),
          makeParticipant("p4", false),
        ],
      },
    ]
    const ratings = computeElo(results)
    expect(ratings).toHaveLength(4)

    const winner = ratings.find((r) => r.id === "p1")!
    expect(winner.elo).toBeGreaterThan(1500)
    expect(winner.wins).toBe(1)
    expect(winner.games).toBe(1)

    // Each loser should be below 1500
    for (const r of ratings.filter((r) => r.id !== "p1")) {
      expect(r.elo).toBeLessThan(1500)
      expect(r.losses).toBe(1)
    }
  })

  it("consistent winner rises, consistent loser sinks", () => {
    const results: GameResult[] = Array.from({ length: 10 }, (_, i) => ({
      gameId: `g${i}`,
      participants: [
        makeParticipant("strong", true, "model"),
        makeParticipant("weak", false, "ai_leader"),
      ],
    }))
    const ratings = computeElo(results)
    const strong = ratings.find((r) => r.id === "strong")!
    const weak = ratings.find((r) => r.id === "weak")!

    expect(strong.elo).toBeGreaterThan(1600)
    expect(weak.elo).toBeLessThan(1400)
    expect(strong.wins).toBe(10)
    expect(weak.losses).toBe(10)
  })

  it("ELO changes are symmetric in 2-player games", () => {
    const results: GameResult[] = [
      {
        gameId: "g1",
        participants: [
          makeParticipant("a", true),
          makeParticipant("b", false),
        ],
      },
    ]
    const ratings = computeElo(results)
    const a = ratings.find((r) => r.id === "a")!
    const b = ratings.find((r) => r.id === "b")!

    // Total ELO should be conserved
    expect(a.elo + b.elo).toBe(3000)
  })

  it("K scaling prevents excessive inflation in large games", () => {
    // 7-player game: K_eff = 32/sqrt(6) ≈ 13.1
    const results: GameResult[] = [
      {
        gameId: "g1",
        participants: [
          makeParticipant("w", true),
          ...Array.from({ length: 6 }, (_, i) =>
            makeParticipant(`l${i}`, false)
          ),
        ],
      },
    ]
    const ratings = computeElo(results)
    const winner = ratings.find((r) => r.id === "w")!

    // With K_eff ≈ 13.1 and 6 pairings at E=0.5, gain ≈ 6*13.1*0.5 ≈ 39
    // Without scaling it would be 6*32*0.5 = 96
    expect(winner.elo).toBeLessThan(1500 + 50)
    expect(winner.elo).toBeGreaterThan(1500 + 30)
  })

  it("preserves participant types correctly", () => {
    const results: GameResult[] = [
      {
        gameId: "g1",
        participants: [
          makeParticipant("model:claude-opus-4-6", true, "model"),
          makeParticipant("ai:Trajan", false, "ai_leader"),
        ],
      },
    ]
    const ratings = computeElo(results)
    expect(ratings.find((r) => r.id === "model:claude-opus-4-6")!.type).toBe(
      "model"
    )
    expect(ratings.find((r) => r.id === "ai:Trajan")!.type).toBe("ai_leader")
  })

  it("aggregates across multiple games", () => {
    const results: GameResult[] = [
      {
        gameId: "g1",
        participants: [
          makeParticipant("a", true),
          makeParticipant("b", false),
        ],
      },
      {
        gameId: "g2",
        participants: [
          makeParticipant("b", true),
          makeParticipant("c", false),
        ],
      },
    ]
    const ratings = computeElo(results)
    expect(ratings).toHaveLength(3)

    const a = ratings.find((r) => r.id === "a")!
    const b = ratings.find((r) => r.id === "b")!
    const c = ratings.find((r) => r.id === "c")!

    expect(a.games).toBe(1)
    expect(b.games).toBe(2)
    expect(c.games).toBe(1)

    // b won one, lost one — elo should be near 1500 but slightly above
    // because b's loss was at 1500 vs 1500, but b's win was at 1484 vs 1500
    expect(b.elo).toBeGreaterThanOrEqual(1495)
    expect(b.elo).toBeLessThanOrEqual(1505)
  })
})
