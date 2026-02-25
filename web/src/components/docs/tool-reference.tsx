import { Shield, Zap, AlertTriangle, Eye } from "lucide-react";

interface ToolData {
  name: string;
  description: string;
  parameters: {
    properties?: Record<string, SchemaProperty>;
    required?: string[];
  };
  annotations: {
    readOnlyHint?: boolean;
    destructiveHint?: boolean;
  };
  category: string;
}

interface SchemaProperty {
  type?: string;
  title?: string;
  description?: string;
  default?: unknown;
  anyOf?: { type: string }[];
}

function AnnotationBadge({ tool }: { tool: ToolData }) {
  if (tool.annotations.readOnlyHint) {
    return (
      <span className="inline-flex items-center gap-1 rounded-sm bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-medium text-emerald-700 dark:text-emerald-400">
        <Eye className="h-3 w-3" />
        Read-only
      </span>
    );
  }
  if (tool.annotations.destructiveHint) {
    return (
      <span className="inline-flex items-center gap-1 rounded-sm bg-red-500/10 px-1.5 py-0.5 text-[10px] font-medium text-red-700 dark:text-red-400">
        <AlertTriangle className="h-3 w-3" />
        Destructive
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-sm bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium text-amber-700 dark:text-amber-400">
      <Zap className="h-3 w-3" />
      Action
    </span>
  );
}

function formatType(prop: SchemaProperty): string {
  if (prop.anyOf) {
    const types = prop.anyOf
      .map((s) => s.type)
      .filter((t) => t && t !== "null");
    return types.length > 0 ? types.join(" | ") : "any";
  }
  return prop.type || "any";
}

function formatDefault(value: unknown): string | null {
  if (value === undefined) return null;
  if (value === null) return "null";
  if (typeof value === "string") return `"${value}"`;
  return String(value);
}

function ParameterTable({ parameters }: { parameters: ToolData["parameters"] }) {
  const props = parameters.properties || {};
  const required = new Set(parameters.required || []);
  const entries = Object.entries(props);

  if (entries.length === 0) {
    return (
      <p className="mt-2 text-sm italic text-fd-muted-foreground">
        No parameters
      </p>
    );
  }

  return (
    <div className="mt-3 overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-fd-border text-left">
            <th className="py-1.5 pr-4 font-medium">Parameter</th>
            <th className="py-1.5 pr-4 font-medium">Type</th>
            <th className="py-1.5 pr-4 font-medium">Default</th>
            <th className="py-1.5 font-medium">Description</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(([name, schema]) => {
            const def = formatDefault(schema.default);
            return (
              <tr
                key={name}
                className="border-b border-fd-border/50"
              >
                <td className="py-1.5 pr-4 font-mono text-xs">
                  {name}
                  {required.has(name) && (
                    <span className="ml-0.5 text-red-500">*</span>
                  )}
                </td>
                <td className="py-1.5 pr-4 font-mono text-xs text-fd-muted-foreground">
                  {formatType(schema)}
                </td>
                <td className="py-1.5 pr-4 font-mono text-xs text-fd-muted-foreground">
                  {def ?? "—"}
                </td>
                <td className="py-1.5 text-fd-muted-foreground">
                  {schema.description || schema.title || ""}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function parseDescription(desc: string): {
  summary: string;
  details: string | null;
} {
  const trimmed = desc.trim();
  // Split on first double newline (blank line)
  const idx = trimmed.indexOf("\n\n");
  if (idx === -1) return { summary: trimmed, details: null };
  return {
    summary: trimmed.slice(0, idx).trim(),
    details: trimmed.slice(idx + 2).trim(),
  };
}

export function ToolReference({ tool }: { tool: ToolData }) {
  const { summary, details } = parseDescription(tool.description);

  return (
    <div
      id={tool.name}
      className="scroll-mt-20 rounded-lg border border-fd-border bg-fd-card p-4"
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-mono text-base font-bold">
          <a
            href={`#${tool.name}`}
            className="hover:text-fd-primary"
          >
            {tool.name}
          </a>
        </h3>
        <AnnotationBadge tool={tool} />
      </div>

      <p className="mt-1.5 text-sm">{summary}</p>

      {details && (
        <details className="mt-2">
          <summary className="cursor-pointer text-xs font-medium text-fd-muted-foreground hover:text-fd-foreground">
            Details
          </summary>
          <pre className="mt-1.5 whitespace-pre-wrap text-xs leading-relaxed text-fd-muted-foreground">
            {details}
          </pre>
        </details>
      )}

      <ParameterTable parameters={tool.parameters} />
    </div>
  );
}

export type { ToolData };
