"""Token-usage figures over `.eval` logs that completed
(`log.status == "success"`).

Reads a directory of Inspect `.eval` logs, keeps the ones whose harness
finished cleanly, and produces:

Caveat: `log.status == "success"` only means the Inspect harness exited
cleanly — **not** that the agent won the Civ game. `.eval` logs carry no
explicit win/loss signal; the civbench scorer emits dimensional scores
(overall_score, economic, etc.) rather than a binary outcome. Linking a
log to a game result (victory type, or "survived vs crashed in-game")
requires an external source: diary JSONL, the telemetry DB, or parsing
scorer output. Treat "completed runs" here as a token-accounting proxy,
not a win-rate proxy.

    1. token_composition_by_model.png
       Stacked bar of total tokens per model, split into fresh-input /
       cache-read / cache-write / output / reasoning.  Two panels: absolute
       totals and percent share.

    2. tokens_per_run_by_model.png
       One dot per completed run, x = model, y = total tokens (log).

    3. completed_runs.csv
       The underlying table (one row per (eval-file, model)).

Run:
    uv run --extra evals --extra analysis python \\
        scripts/inspect-log-analysis/figures.py <log_dir> [--out-dir <path>]
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from inspect_ai.log import list_eval_logs, read_eval_log


def _short(model: str) -> str:
    return model.split("/")[-1]


@dataclass
class RunUsage:
    eval_file: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cache_read: int
    cache_write: int
    reasoning_tokens: int


def collect(log_dir: Path) -> pd.DataFrame:
    rows: list[RunUsage] = []
    skipped_status: dict[str, int] = {}
    for info in list_eval_logs(str(log_dir)):
        try:
            log = read_eval_log(info, header_only=True)
        except Exception:
            skipped_status["read-error"] = skipped_status.get("read-error", 0) + 1
            continue
        if log.status != "success":
            skipped_status[log.status] = skipped_status.get(log.status, 0) + 1
            continue
        for model, u in (log.stats.model_usage or {}).items():
            rows.append(
                RunUsage(
                    eval_file=Path(info.name).name,
                    model=_short(model),
                    input_tokens=u.input_tokens or 0,
                    output_tokens=u.output_tokens or 0,
                    total_tokens=u.total_tokens or 0,
                    cache_read=u.input_tokens_cache_read or 0,
                    cache_write=u.input_tokens_cache_write or 0,
                    reasoning_tokens=u.reasoning_tokens or 0,
                )
            )
    df = pd.DataFrame([asdict(r) for r in rows])
    df.attrs["skipped"] = skipped_status
    return df


# ---- Figures ---------------------------------------------------------------

COMPONENTS = [
    ("input_tokens", "fresh input", "#3b82f6"),
    ("cache_read", "cache read", "#10b981"),
    ("cache_write", "cache write", "#14b8a6"),
    ("output_tokens", "output", "#f59e0b"),
    ("reasoning_tokens", "reasoning", "#a855f7"),
]


def fig_composition(df: pd.DataFrame, out: Path) -> None:
    cols = [c for c, _, _ in COMPONENTS]
    agg = df.groupby("model")[cols].sum().sort_index()
    counts = df.groupby("model").size()
    labels = [f"{m}\n(n={counts[m]})" for m in agg.index]

    totals = agg.sum(axis=1).replace(0, 1)
    pct = agg.div(totals, axis=0) * 100

    fig, (ax_abs, ax_pct) = plt.subplots(1, 2, figsize=(13, 5.5))

    for axis, frame, ylabel, fmt in [
        (ax_abs, agg, "tokens (summed across runs)", lambda v, _: f"{v/1e9:.1f}B"),
        (ax_pct, pct, "share of total tokens (%)", lambda v, _: f"{v:.0f}"),
    ]:
        bottom = [0.0] * len(labels)
        for col, name, c in COMPONENTS:
            vals = frame[col].to_list()
            axis.bar(labels, vals, bottom=bottom, label=name, color=c)
            bottom = [b + v for b, v in zip(bottom, vals)]
        axis.set_ylabel(ylabel)
        axis.tick_params(axis="x", labelrotation=15)
        axis.yaxis.set_major_formatter(plt.FuncFormatter(fmt))

    ax_abs.set_title("Absolute totals")
    ax_pct.set_title("Share by type")
    ax_pct.set_ylim(0, 100)
    ax_pct.legend(loc="center left", bbox_to_anchor=(1.02, 0.5))

    fig.suptitle("Token composition — .eval logs with status=success")
    fig.tight_layout()
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)


def fig_per_run(df: pd.DataFrame, out: Path) -> None:
    models = sorted(df["model"].unique())
    fig, ax = plt.subplots(figsize=(10, 5.5))

    for i, model in enumerate(models):
        sub = df[df["model"] == model]
        for _, row in sub.iterrows():
            jitter = i + (hash(row["eval_file"]) % 1000) / 2500 - 0.2
            ax.scatter(
                jitter,
                row["total_tokens"],
                color="#2563eb",
                s=90,
                alpha=0.8,
                edgecolor="black",
                linewidth=0.5,
                zorder=3,
            )

    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, rotation=15)
    ax.set_yscale("log")
    ax.set_ylabel("total tokens per run (log)")
    ax.set_title("Tokens per completed .eval run, by model")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)


def summarise(df: pd.DataFrame) -> str:
    lines = [
        f"Completed runs: {len(df)}",
        f"Models:         {', '.join(sorted(df['model'].unique()))}",
        "",
        f"{'Model':<42}  {'Runs':>4}  {'Σ tokens':>14}  {'Mean/run':>14}  {'Output/total %':>14}",
        "-" * 100,
    ]
    for model, sub in df.groupby("model"):
        out_share = sub["output_tokens"].sum() / max(sub["total_tokens"].sum(), 1) * 100
        lines.append(
            f"{model:<42}  {len(sub):>4}  {sub['total_tokens'].sum():>14,}  "
            f"{sub['total_tokens'].mean():>14,.0f}  {out_share:>14.2f}"
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("log_dir", help="Directory of .eval files")
    ap.add_argument(
        "--out-dir",
        default="scripts/inspect-log-analysis/figures",
        help="Where to write PNGs (default: %(default)s)",
    )
    args = ap.parse_args()

    df = collect(Path(args.log_dir))
    skipped = df.attrs.get("skipped", {})
    if skipped:
        print("Skipped non-success logs:", skipped)
    if df.empty:
        print("No completed .eval logs found — giving up.")
        return

    print(summarise(df))

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    fig_composition(df, out / "token_composition_by_model.png")
    fig_per_run(df, out / "tokens_per_run_by_model.png")
    df.to_csv(out / "completed_runs.csv", index=False)
    print(f"\nWrote 2 PNGs + completed_runs.csv to {out}/")


if __name__ == "__main__":
    main()
