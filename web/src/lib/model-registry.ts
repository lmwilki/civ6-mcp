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
  // Anthropic
  "claude-opus-4-6": m("claude-opus-4-6", "Claude Opus 4.6", "anthropic"),
  "claude-opus-4-5-20250620": m(
    "claude-opus-4-5-20250620",
    "Claude Opus 4.5",
    "anthropic",
  ),
  "claude-sonnet-4-6": m("claude-sonnet-4-6", "Claude Sonnet 4.6", "anthropic"),
  "claude-sonnet-4-5-20250514": m(
    "claude-sonnet-4-5-20250514",
    "Claude Sonnet 4.5",
    "anthropic",
  ),
  "claude-haiku-4-5-20251001": m(
    "claude-haiku-4-5-20251001",
    "Claude Haiku 4.5",
    "anthropic",
  ),
  // OpenAI
  "gpt-5": m("gpt-5", "GPT-5", "openai"),
  "gpt-4o": m("gpt-4o", "GPT-4o", "openai"),
  o3: m("o3", "o3", "openai"),
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

  // Fallback: title-case the ID, unknown provider
  const name = modelId
    .replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
  return {
    id: modelId,
    name,
    provider: "Unknown",
    providerLogo: "",
    color: "#6b7280",
  };
}
