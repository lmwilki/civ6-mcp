#!/usr/bin/env python3
"""Extract MCP tool metadata from FastMCP into JSON for the docs site.

Usage: python scripts/extract_tool_docs.py
Output: web/content/tools.json
"""

import json
import os
import sys
from pathlib import Path

# Add src to path so we can import the server module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from civ_mcp.server import mcp  # noqa: E402


def categorize(annotations) -> str:
    if annotations and annotations.destructiveHint:
        return "system"
    if annotations and annotations.readOnlyHint:
        return "query"
    return "action"


CATEGORY_ORDER = {"query": 0, "action": 1, "system": 2}


def main():
    tools = mcp._tool_manager.list_tools()
    output = []

    for t in tools:
        ann = t.annotations
        entry = {
            "name": t.name,
            "description": t.description,
            "parameters": t.parameters,
            "annotations": {
                "readOnlyHint": bool(ann and ann.readOnlyHint),
                "destructiveHint": bool(ann and ann.destructiveHint),
            },
            "category": categorize(ann),
        }
        output.append(entry)

    # Sort: by category order, then alphabetically within category
    output.sort(key=lambda t: (CATEGORY_ORDER.get(t["category"], 9), t["name"]))

    out_path = Path(__file__).resolve().parent.parent / "web" / "content" / "tools.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2) + "\n")

    # Summary
    counts = {}
    for t in output:
        counts[t["category"]] = counts.get(t["category"], 0) + 1
    print(f"Extracted {len(output)} tools → {out_path}")
    for cat, count in sorted(counts.items(), key=lambda x: CATEGORY_ORDER.get(x[0], 9)):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
