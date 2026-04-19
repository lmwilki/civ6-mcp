"""Analysis over a directory of Inspect `.eval` logs.

Run:
    uv run --extra evals python scripts/inspect-log-analysis/analysis.py <log_dir>

`inspect-ai` lives in the `evals` / `scout` optional-dependency groups in
pyproject.toml, so select one with `--extra`.

`log_dir` is any path `inspect_ai.log.list_eval_logs` accepts — a local directory
of `.eval` files, or an `s3://` / `az://` URI.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log


@dataclass
class UsageTotals:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cache_read: int = 0
    cache_write: int = 0
    reasoning_tokens: int = 0
    total_cost: float = 0.0
    samples: int = 0

    def add(self, usage) -> None:
        self.input_tokens += usage.input_tokens or 0
        self.output_tokens += usage.output_tokens or 0
        self.total_tokens += usage.total_tokens or 0
        self.cache_read += usage.input_tokens_cache_read or 0
        self.cache_write += usage.input_tokens_cache_write or 0
        self.reasoning_tokens += usage.reasoning_tokens or 0
        self.total_cost += usage.total_cost or 0.0


@dataclass
class Report:
    files_read: int = 0
    files_skipped: int = 0
    by_model: dict[str, UsageTotals] = field(default_factory=dict)

    def model_totals(self, model: str) -> UsageTotals:
        return self.by_model.setdefault(model, UsageTotals())

    def grand_total(self) -> UsageTotals:
        grand = UsageTotals()
        for m in self.by_model.values():
            grand.input_tokens += m.input_tokens
            grand.output_tokens += m.output_tokens
            grand.total_tokens += m.total_tokens
            grand.cache_read += m.cache_read
            grand.cache_write += m.cache_write
            grand.reasoning_tokens += m.reasoning_tokens
            grand.total_cost += m.total_cost
            grand.samples += m.samples
        return grand


def token_usage(log_dir: str | Path) -> Report:
    """Aggregate token usage across every `.eval` log under `log_dir`.

    Uses `header_only=True` — stats live in the log header, so we don't pay to
    deserialise samples.
    """
    report = Report()
    infos = list_eval_logs(str(log_dir))

    for info in infos:
        try:
            log = read_eval_log(info, header_only=True)
        except Exception:
            report.files_skipped += 1
            continue

        report.files_read += 1

        for model, usage in (log.stats.model_usage or {}).items():
            totals = report.model_totals(model)
            totals.add(usage)
            totals.samples += 1

    return report


def format_report(report: Report) -> str:
    rows = []
    rows.append(f"Files read:    {report.files_read}")
    rows.append(f"Files skipped: {report.files_skipped}")
    rows.append("")
    header = f"{'Model':<48}  {'Samples':>7}  {'Input':>14}  {'Output':>12}  {'Total':>14}  {'CacheRead':>12}  {'CacheWrite':>12}  {'Reasoning':>12}  {'Cost($)':>10}"
    rows.append(header)
    rows.append("-" * len(header))

    for model in sorted(report.by_model):
        t = report.by_model[model]
        rows.append(
            f"{model:<48}  {t.samples:>7,}  {t.input_tokens:>14,}  {t.output_tokens:>12,}  "
            f"{t.total_tokens:>14,}  {t.cache_read:>12,}  {t.cache_write:>12,}  "
            f"{t.reasoning_tokens:>12,}  {t.total_cost:>10,.2f}"
        )

    grand = report.grand_total()
    rows.append("-" * len(header))
    rows.append(
        f"{'TOTAL':<48}  {grand.samples:>7,}  {grand.input_tokens:>14,}  {grand.output_tokens:>12,}  "
        f"{grand.total_tokens:>14,}  {grand.cache_read:>12,}  {grand.cache_write:>12,}  "
        f"{grand.reasoning_tokens:>12,}  {grand.total_cost:>10,.2f}"
    )
    return "\n".join(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("log_dir", help="Directory (or URI) containing .eval files")
    args = ap.parse_args()

    report = token_usage(args.log_dir)
    print(format_report(report))


if __name__ == "__main__":
    main()
