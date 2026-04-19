"""Aggregate stats over a resample `.eval` produced by civbench_resample.

For each epoch in the resample log, pull the final assistant message and
compute:
  1. Tool-name histogram
  2. Full (tool, args) histogram
  3. Reasoning / text divergence (unique content snippets + frequency)
  4. Agreement with the original assistant message at `truncate_at_message`
     in the source log (name match rate + exact match rate)

Run:
    uv run --extra evals python scripts/inspect-log-analysis/analyze_resample.py \\
        --resample-log logs/<new>.eval \\
        --source-log logs/<orig>.eval \\
        --sample-id ground_control \\
        --truncate-at-message 42 \\
        [--json out.json] [--top-k 10] [--text-chars 500]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from inspect_ai.log import read_eval_log, read_eval_log_sample


@dataclass
class ResampleReport:
    resample_log: str
    source_log: str
    sample_id: str
    truncate_at_message: int
    n_epochs: int
    tool_name_hist: list[tuple[str, int]] = field(default_factory=list)
    tool_call_hist: list[tuple[str, str, int]] = field(default_factory=list)
    text_hist: list[tuple[str, int]] = field(default_factory=list)
    original_tool: str | None = None
    original_args: dict[str, Any] | None = None
    name_match_rate: float = 0.0
    exact_match_rate: float = 0.0
    no_tool_call_rate: float = 0.0
    errors: int = 0


def _final_assistant_message(messages: list) -> Any | None:
    """Return the last assistant message in `messages`, or None."""
    for m in reversed(messages):
        if m.role == "assistant":
            return m
    return None


def _original_action(source_log: str, sample_id: str, slice_idx: int, epoch: int = 1) -> tuple[str | None, dict[str, Any] | None, str]:
    """Return (tool_name, args_dict, text) of the assistant msg at messages[slice_idx]."""
    sample = read_eval_log_sample(source_log, id=sample_id, epoch=epoch)
    if slice_idx >= len(sample.messages):
        return None, None, ""
    m = sample.messages[slice_idx]
    if m.role != "assistant":
        return None, None, getattr(m, "text", "")
    tcs = getattr(m, "tool_calls", None) or []
    if not tcs:
        return None, None, m.text or ""
    first = tcs[0]
    return first.function, dict(first.arguments or {}), m.text or ""


def analyze(
    resample_log: str,
    source_log: str,
    sample_id: str,
    truncate_at_message: int,
    source_epoch: int = 1,
    top_k: int = 10,
    text_chars: int = 500,
) -> ResampleReport:
    log = read_eval_log(resample_log, header_only=False)
    epochs = log.samples or []

    tool_names: Counter[str] = Counter()
    tool_calls: Counter[tuple[str, str]] = Counter()
    texts: Counter[str] = Counter()
    errors = 0
    no_call = 0

    original_tool, original_args, _ = _original_action(
        source_log, sample_id, truncate_at_message, source_epoch
    )
    original_args_json = (
        json.dumps(original_args, sort_keys=True) if original_args is not None else None
    )

    name_matches = 0
    exact_matches = 0

    for sample in epochs:
        msg = _final_assistant_message(sample.messages or [])
        if msg is None:
            errors += 1
            continue
        tcs = getattr(msg, "tool_calls", None) or []
        text = (msg.text or "").strip()
        if text:
            snippet = text[:text_chars]
            texts[snippet] += 1
        if not tcs:
            no_call += 1
            continue
        tc = tcs[0]
        args_json = json.dumps(tc.arguments or {}, sort_keys=True)
        tool_names[tc.function] += 1
        tool_calls[(tc.function, args_json)] += 1
        if original_tool is not None:
            if tc.function == original_tool:
                name_matches += 1
                if args_json == original_args_json:
                    exact_matches += 1

    n = len(epochs)
    return ResampleReport(
        resample_log=resample_log,
        source_log=source_log,
        sample_id=sample_id,
        truncate_at_message=truncate_at_message,
        n_epochs=n,
        tool_name_hist=tool_names.most_common(top_k),
        tool_call_hist=[(name, args, c) for (name, args), c in tool_calls.most_common(top_k)],
        text_hist=texts.most_common(top_k),
        original_tool=original_tool,
        original_args=original_args,
        name_match_rate=(name_matches / n) if n else 0.0,
        exact_match_rate=(exact_matches / n) if n else 0.0,
        no_tool_call_rate=(no_call / n) if n else 0.0,
        errors=errors,
    )


def format_report(r: ResampleReport, text_chars: int = 500) -> str:
    lines: list[str] = []
    lines.append(f"# Resample report")
    lines.append("")
    lines.append(f"- resample log: `{r.resample_log}`")
    lines.append(f"- source log:   `{r.source_log}`")
    lines.append(f"- sample id:    `{r.sample_id}`")
    lines.append(f"- truncate at:  message {r.truncate_at_message}")
    lines.append(f"- epochs:       {r.n_epochs}  (errors: {r.errors}, no tool call: {r.no_tool_call_rate:.0%})")
    lines.append("")

    lines.append("## Tool name distribution")
    if not r.tool_name_hist:
        lines.append("_(no tool calls emitted)_")
    else:
        for name, c in r.tool_name_hist:
            pct = (c / r.n_epochs) * 100 if r.n_epochs else 0
            lines.append(f"- **{name}** — {c}/{r.n_epochs}  ({pct:.1f}%)")
    lines.append("")

    lines.append("## Full tool-call distribution (top)")
    if not r.tool_call_hist:
        lines.append("_(no tool calls emitted)_")
    else:
        for name, args, c in r.tool_call_hist:
            pct = (c / r.n_epochs) * 100 if r.n_epochs else 0
            lines.append(f"- `{name}({args})` — {c} ({pct:.1f}%)")
    lines.append("")

    lines.append("## Agreement with original transcript")
    if r.original_tool is None:
        lines.append(
            f"_(source message at index {r.truncate_at_message} is not an assistant tool_call — skipping)_"
        )
    else:
        lines.append(f"- original: `{r.original_tool}({json.dumps(r.original_args, sort_keys=True)})`")
        lines.append(f"- name match rate:  {r.name_match_rate:.1%}")
        lines.append(f"- exact match rate: {r.exact_match_rate:.1%}")
    lines.append("")

    lines.append("## Assistant text / reasoning divergence (top)")
    if not r.text_hist:
        lines.append("_(no assistant text content — pure tool-call emissions)_")
    else:
        for snippet, c in r.text_hist:
            pct = (c / r.n_epochs) * 100 if r.n_epochs else 0
            lines.append(f"\n### {c}× ({pct:.1f}%)")
            lines.append("```")
            lines.append(snippet[:text_chars])
            lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--resample-log", required=True)
    ap.add_argument("--source-log", required=True)
    ap.add_argument("--sample-id", required=True)
    ap.add_argument("--truncate-at-message", type=int, required=True)
    ap.add_argument("--source-epoch", type=int, default=1)
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--text-chars", type=int, default=500)
    ap.add_argument("--json", dest="json_out", default=None, help="Dump report JSON to this path")
    args = ap.parse_args()

    report = analyze(
        resample_log=args.resample_log,
        source_log=args.source_log,
        sample_id=args.sample_id,
        truncate_at_message=args.truncate_at_message,
        source_epoch=args.source_epoch,
        top_k=args.top_k,
        text_chars=args.text_chars,
    )
    print(format_report(report, text_chars=args.text_chars))

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(asdict(report), indent=2, default=str))
        print(f"\n(wrote JSON → {args.json_out})", file=sys.stderr)


if __name__ == "__main__":
    main()
