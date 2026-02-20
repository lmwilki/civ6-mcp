"""Diary feature — structured per-turn reflections, always on.

Writes/reads JSONL diary files stored in ~/.civ6-mcp/.
"""

from __future__ import annotations

import json
from pathlib import Path

DIARY_DIR = Path.home() / ".civ6-mcp"
_REFLECTION_FIELDS = ("tactical", "strategic", "tooling", "planning", "hypothesis")


def diary_path(civ: str, seed: int) -> Path:
    """Per-game diary file: diary_{civ}_{seed}.jsonl"""
    return DIARY_DIR / f"diary_{civ}_{seed}.jsonl"


def write_diary_entry(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")


def read_diary_entries(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().strip().splitlines():
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def format_diary_entry(e: dict) -> str:
    t = e.get("turn", "?")
    s = e.get("score") or {}
    r = e.get("reflections") or {}
    header = f"=== Turn {t} ==="
    pop_str = f" Pop: {s['population']} |" if "population" in s else ""
    score_line = (
        f"  Score: {s.get('total', '?')} | Cities: {s.get('cities', '?')} |{pop_str} "
        f"Sci: {s.get('science', '?')} | Cul: {s.get('culture', '?')} | "
        f"Gold: {s.get('gold', '?')} ({s.get('gold_per_turn', '?')}/t) | "
        f"Faith: {s.get('faith', '?')} | Favor: {s.get('favor', '?')} | "
        f"Explored: {s.get('exploration_pct', '?')}% | "
        f"Era: {s.get('era', '?')} ({s.get('era_score', '?')})"
    )
    stk = s.get("stockpiles")
    stk_line = ""
    if stk:
        parts = []
        for name, v in stk.items():
            net = v.get("per_turn", 0) - v.get("demand", 0)
            parts.append(f"{name}: {v['amount']} ({net:+d}/t)")
        stk_line = "\n  Resources: " + ", ".join(parts)
    # NOTE: "rivals" key exists in JSONL for research/analysis but is
    # intentionally NOT displayed here — the agent shouldn't see hidden AI stats.
    ref_lines = "\n".join(f"  {k}: {v}" for k, v in r.items())
    return f"{header}\n{score_line}{stk_line}\n{ref_lines}"
