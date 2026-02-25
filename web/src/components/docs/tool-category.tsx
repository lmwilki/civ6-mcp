import toolsData from "@content/tools.json";
import { ToolReference, type ToolData } from "./tool-reference";

interface ToolCategoryProps {
  category: "query" | "action" | "system";
}

const CATEGORY_LABELS: Record<string, string> = {
  query: "Read-only tools for inspecting game state, map, diplomacy, and progress.",
  action: "Tools that modify game state — unit commands, production, research, diplomacy.",
  system: "Game lifecycle tools — saving, loading, and advancing turns.",
};

export function ToolCategory({ category }: ToolCategoryProps) {
  const tools = (toolsData as unknown as ToolData[]).filter(
    (t) => t.category === category,
  );

  return (
    <div>
      <p className="mb-4 text-sm text-fd-muted-foreground">
        {CATEGORY_LABELS[category]} ({tools.length} tools)
      </p>
      <div className="space-y-4">
        {tools.map((tool) => (
          <ToolReference key={tool.name} tool={tool} />
        ))}
      </div>
    </div>
  );
}
