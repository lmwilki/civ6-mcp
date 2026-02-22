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


def cities_diary_path(civ: str, seed: int) -> Path:
    """Per-game cities diary file: diary_{civ}_{seed}_cities.jsonl"""
    return DIARY_DIR / f"diary_{civ}_{seed}_cities.jsonl"


def write_diary_entry(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")


def merge_agent_reflections(path: Path, turn: int, new_reflections: dict) -> bool:
    """Merge new reflections into the most recent agent row for this turn.

    Finds the last is_agent=True row matching the given turn, appends each
    non-empty reflection field with ' | ' separator, and rewrites the file.
    Returns True if a row was found and merged, False otherwise.
    """
    if not path.exists():
        return False
    lines = path.read_text().strip().splitlines()
    target_idx = None
    for i in range(len(lines) - 1, -1, -1):
        try:
            row = json.loads(lines[i])
            if row.get("is_agent") and row.get("turn") == turn:
                target_idx = i
                break
        except json.JSONDecodeError:
            continue
    if target_idx is None:
        return False

    row = json.loads(lines[target_idx])
    existing = row.get("reflections") or {}
    for field in _REFLECTION_FIELDS:
        new_val = new_reflections.get(field, "").strip()
        old_val = existing.get(field, "").strip()
        if new_val and new_val != old_val:
            existing[field] = f"{old_val} | {new_val}" if old_val else new_val
    row["reflections"] = existing
    lines[target_idx] = json.dumps(row, separators=(",", ":"))

    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return True


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
    # New flat format (v2) — detected by "v" key
    if "v" in e:
        return _format_flat_entry(e)
    # Legacy nested format
    return _format_legacy_entry(e)


def _format_flat_entry(e: dict) -> str:
    """Format a v2 flat-key diary entry (one row per player, is_agent=True)."""
    t = e.get("turn", "?")
    r = e.get("reflections") or {}
    header = f"=== Turn {t} ==="
    score_line = (
        f"  Score: {e.get('score', '?')} | Cities: {e.get('cities', '?')} | "
        f"Pop: {e.get('pop', '?')} | "
        f"Sci: {e.get('science', '?')} | Cul: {e.get('culture', '?')} | "
        f"Gold: {e.get('gold', '?')} ({e.get('gold_per_turn', '?')}/t) | "
        f"Faith: {e.get('faith', '?')} | Favor: {e.get('favor', '?')} | "
        f"Explored: {e.get('exploration_pct', '?')}% | "
        f"Era: {e.get('era', '?')} ({e.get('era_score', '?')})"
    )
    stk = e.get("stockpiles")
    stk_line = ""
    if stk:
        parts = [f"{k}: {v}" for k, v in stk.items()]
        stk_line = "\n  Resources: " + ", ".join(parts)
    ref_lines = "\n".join(f"  {k}: {v}" for k, v in r.items())
    return f"{header}\n{score_line}{stk_line}\n{ref_lines}"


def _format_legacy_entry(e: dict) -> str:
    """Format a legacy nested-format diary entry."""
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
    ref_lines = "\n".join(f"  {k}: {v}" for k, v in r.items())
    return f"{header}\n{score_line}{stk_line}\n{ref_lines}"
