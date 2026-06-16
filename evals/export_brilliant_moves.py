"""Export brilliant_move scanner findings to CSV.

Usage:
    python evals/export_brilliant_moves.py <scan_dir> [<output.csv>]
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from inspect_scout import scan_results_df


def export(scan_dir: str, out_path: str | None = None) -> str:
    results = scan_results_df(scan_dir)

    frames: list[pd.DataFrame] = []
    for name in ["brilliant_move", "move_37_candidate"]:
        if name not in results.scanners:
            continue
        df = results.scanners[name]
        if not len(df):
            continue

        # pull category / summary out of metadata if present
        def _get(md, key):
            if isinstance(md, dict):
                return md.get(key, "")
            return ""

        cat_col = (
            df["metadata.category"]
            if "metadata.category" in df.columns
            else df["metadata"].apply(lambda m: _get(m, "category"))
        )
        summary_col = (
            df["metadata.summary"]
            if "metadata.summary" in df.columns
            else df["metadata"].apply(lambda m: _get(m, "summary"))
        )

        out = pd.DataFrame(
            {
                "scanner": name,
                "transcript_id": df["transcript_id"],
                "model": df.get("transcript_model", ""),
                "task_id": df.get("transcript_task_id", ""),
                "message_id": df["input_ids"].apply(
                    lambda ids: ids[0] if isinstance(ids, list) and ids else ""
                ),
                "rating": df["value"],
                "category": cat_col,
                "summary": summary_col,
                "explanation": df.get("explanation", ""),
            }
        )
        frames.append(out)

    if not frames:
        raise SystemExit(f"No brilliant_move or move_37_candidate results in {scan_dir}")

    combined = pd.concat(frames, ignore_index=True)
    # sort highest-rated first, then by transcript
    combined["_sort"] = pd.to_numeric(combined["rating"], errors="coerce").fillna(0)
    combined = combined.sort_values(
        ["_sort", "scanner", "transcript_id"], ascending=[False, True, True]
    ).drop(columns=["_sort"])

    if out_path is None:
        out_path = str(Path(scan_dir).rstrip("/")) + "/brilliant_moves.csv"
    combined.to_csv(out_path, index=False)
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    scan_dir = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None
    written = export(scan_dir, out_path)
    print(f"wrote {written}")
