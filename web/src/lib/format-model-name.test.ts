import { describe, it, expect } from "vitest"
import { formatModelName } from "./model-registry"

describe("formatModelName", () => {
  it("formats claude-opus-4-6", () => {
    expect(formatModelName("claude-opus-4-6")).toBe("Claude Opus 4.6")
  })

  it("formats claude-sonnet-4-6", () => {
    expect(formatModelName("claude-sonnet-4-6")).toBe("Claude Sonnet 4.6")
  })

  it("formats claude-opus-4-5-20250620", () => {
    expect(formatModelName("claude-opus-4-5-20250620")).toBe("Claude Opus 4.5")
  })

  it("formats claude-sonnet-4-5-20250514", () => {
    expect(formatModelName("claude-sonnet-4-5-20250514")).toBe("Claude Sonnet 4.5")
  })

  it("formats claude-haiku-4-5-20251001", () => {
    expect(formatModelName("claude-haiku-4-5-20251001")).toBe("Claude Haiku 4.5")
  })

  it("formats gpt-5", () => {
    expect(formatModelName("gpt-5")).toBe("GPT-5")
  })

  it("formats gpt-4o", () => {
    expect(formatModelName("gpt-4o")).toBe("GPT-4o")
  })

  it("formats o3", () => {
    expect(formatModelName("o3")).toBe("o3")
  })

  it("falls back to title-cased string for unknown models", () => {
    expect(formatModelName("gemini-2-pro")).toBe("Gemini 2 Pro")
  })

  it("handles single-word unknown model", () => {
    expect(formatModelName("llama")).toBe("Llama")
  })
})
