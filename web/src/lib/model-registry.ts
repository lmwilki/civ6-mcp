// ─── Model Metadata Registry ────────────────────────────────────────────────
// Single source of truth for model display names, providers, logos, and colors.
// Add new models here as they're tested in games.

export interface ModelMeta {
  id: string;
  name: string;
  provider: string;
  providerLogo: string;
  color: string;
}

const PROVIDERS = {
  anthropic: {
    name: "Anthropic",
    logo: "/images/providers/anthropic_small.svg",
    color: "#D97757",
  },
  openai: {
    name: "OpenAI",
    logo: "/images/providers/openai_small.svg",
    color: "#00A67E",
  },
  google: {
    name: "Google",
    logo: "/images/providers/google_small.svg",
    color: "#4285F4",
  },
  meta: {
    name: "Meta",
    logo: "/images/providers/meta_small.svg",
    color: "#0668E1",
  },
  deepseek: {
    name: "DeepSeek",
    logo: "/images/providers/deepseek_small.svg",
    color: "#4D6BFE",
  },
  xai: { name: "xAI", logo: "/images/providers/xai.svg", color: "#6B7280" },
} as const;

function m(id: string, name: string, p: keyof typeof PROVIDERS): ModelMeta {
  const prov = PROVIDERS[p];
  return {
    id,
    name,
    provider: prov.name,
    providerLogo: prov.logo,
    color: prov.color,
  };
}

export const MODEL_REGISTRY: Record<string, ModelMeta> = {
  // ── Anthropic ──
  "claude-opus-4-6": m("claude-opus-4-6", "Claude Opus 4.6", "anthropic"),
  "claude-sonnet-4-6": m("claude-sonnet-4-6", "Claude Sonnet 4.6", "anthropic"),
  "claude-opus-4-5-20250620": m("claude-opus-4-5-20250620", "Claude Opus 4.5", "anthropic"),
  "claude-opus-4-5-20251101": m("claude-opus-4-5-20251101", "Claude Opus 4.5", "anthropic"),
  "claude-sonnet-4-5-20250514": m("claude-sonnet-4-5-20250514", "Claude Sonnet 4.5", "anthropic"),
  "claude-sonnet-4-5-20250929": m("claude-sonnet-4-5-20250929", "Claude Sonnet 4.5", "anthropic"),
  "claude-haiku-4-5-20251001": m("claude-haiku-4-5-20251001", "Claude Haiku 4.5", "anthropic"),
  "claude-opus-4-1-20250805": m("claude-opus-4-1-20250805", "Claude Opus 4.1", "anthropic"),
  "claude-sonnet-4-20250514": m("claude-sonnet-4-20250514", "Claude Sonnet 4", "anthropic"),
  "claude-opus-4-20250514": m("claude-opus-4-20250514", "Claude Opus 4", "anthropic"),
  // ── Google ──
  "gemini-3.1-pro-preview": m("gemini-3.1-pro-preview", "Gemini 3.1 Pro", "google"),
  "gemini-3-pro-preview": m("gemini-3-pro-preview", "Gemini 3 Pro", "google"),
  "gemini-3-flash-preview": m("gemini-3-flash-preview", "Gemini 3 Flash", "google"),
  "gemini-2.5-pro": m("gemini-2.5-pro", "Gemini 2.5 Pro", "google"),
  "gemini-2.5-flash": m("gemini-2.5-flash", "Gemini 2.5 Flash", "google"),
  "gemini-2.5-flash-lite": m("gemini-2.5-flash-lite", "Gemini 2.5 Flash Lite", "google"),
  // ── OpenAI ──
  "gpt-5.2": m("gpt-5.2", "GPT-5.2", "openai"),
  "gpt-5.1": m("gpt-5.1", "GPT-5.1", "openai"),
  "gpt-5": m("gpt-5", "GPT-5", "openai"),
  "gpt-5-mini": m("gpt-5-mini", "GPT-5 Mini", "openai"),
  "gpt-4.1": m("gpt-4.1", "GPT-4.1", "openai"),
  "gpt-4.1-mini": m("gpt-4.1-mini", "GPT-4.1 Mini", "openai"),
  "gpt-4o": m("gpt-4o", "GPT-4o", "openai"),
  o3: m("o3", "o3", "openai"),
  "o3-mini": m("o3-mini", "o3 Mini", "openai"),
  "o4-mini": m("o4-mini", "o4 Mini", "openai"),
  // ── xAI ──
  "grok-4-0709": m("grok-4-0709", "Grok 4", "xai"),
  "grok-3": m("grok-3", "Grok 3", "xai"),
  "grok-3-mini": m("grok-3-mini", "Grok 3 Mini", "xai"),
  // ── DeepSeek ──
  "deepseek-chat": m("deepseek-chat", "DeepSeek V3", "deepseek"),
  "deepseek-reasoner": m("deepseek-reasoner", "DeepSeek R1", "deepseek"),
  // ── Meta ──
  "llama-4-maverick": m("llama-4-maverick", "Llama 4 Maverick", "meta"),
  "llama-4-scout": m("llama-4-scout", "Llama 4 Scout", "meta"),
};

/** Prettify a model ID string: "claude-opus-4-6" -> "Claude Opus 4.6" */
export function formatModelName(raw: string): string {
  return getModelMeta(raw).name;
}

/** Get model metadata. Returns a sensible fallback for unknown model IDs. */
export function getModelMeta(modelId: string): ModelMeta {
  if (!modelId?.trim()) {
    return {
      id: "",
      name: "Unknown",
      provider: "Unknown",
      providerLogo: "",
      color: "#6b7280",
    };
  }
  if (MODEL_REGISTRY[modelId]) return MODEL_REGISTRY[modelId];

  // Fallback: infer provider from prefix, title-case the ID
  const prefixMap: [string, keyof typeof PROVIDERS][] = [
    ["claude", "anthropic"],
    ["gemini", "google"],
    ["gpt", "openai"],
    ["o1", "openai"],
    ["o3", "openai"],
    ["o4", "openai"],
    ["grok", "xai"],
    ["deepseek", "deepseek"],
    ["llama", "meta"],
  ];
  const lower = modelId.toLowerCase();
  const matched = prefixMap.find(([prefix]) => lower.startsWith(prefix));
  const prov = matched ? PROVIDERS[matched[1]] : null;
  const name = modelId
    .replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
  return {
    id: modelId,
    name,
    provider: prov?.name ?? "Unknown",
    providerLogo: prov?.logo ?? "",
    color: prov?.color ?? "#6b7280",
  };
}
