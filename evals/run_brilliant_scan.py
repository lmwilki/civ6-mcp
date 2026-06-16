"""Run brilliant_move / move_37_candidate directly against .eval transcripts
and stream results to a CSV as they complete.

Bypasses scout's supervisor (which crashes mid-scan on long Civ transcripts,
losing all in-memory results). Each row is written to disk immediately, so
a crash only loses the row currently in flight.

Usage:
    python evals/run_brilliant_scan.py --transcripts /tmp/scout_sweet --out /tmp/brilliant_moves.csv
    python evals/run_brilliant_scan.py --transcripts /path/to/evals --limit 2 --concurrency 8
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import os
import sys
import time
from pathlib import Path

from inspect_ai.log import read_eval_log, read_eval_log_samples
from inspect_ai.model import ChatMessageAssistant

# register scanners via module import side effects
sys.path.insert(0, str(Path(__file__).parent.parent))
from evals.scanners.brilliant_moves import (  # noqa: E402
    CONTEXT_WINDOW,
    _window_messages,
    brilliant_move,
    brilliant_move_with_context,
    move_37_candidate,
)

FIELDS = [
    "scanner",
    "eval_file",
    "transcript_id",
    "model",
    "task_id",
    "msg_idx",
    "message_id",
    "rating",
    "category",
    "summary",
    "explanation",
]


def scan_fns(include_context: bool = False):
    fns = {
        "brilliant_move": brilliant_move(),
        "move_37_candidate": move_37_candidate(),
    }
    if include_context:
        fns["brilliant_move_with_context"] = brilliant_move_with_context()
    return fns


async def _run_one(
    scanner_name,
    scan_fn,
    scan_input,
    writer,
    writer_lock,
    *,
    eval_file,
    transcript_id,
    model,
    task_id,
    msg_idx,
    message_id,
    sem,
):
    async with sem:
        try:
            result = await scan_fn(scan_input)
        except Exception as e:
            async with writer_lock:
                writer.writerow(
                    {
                        "scanner": scanner_name,
                        "eval_file": eval_file,
                        "transcript_id": transcript_id,
                        "model": model,
                        "task_id": task_id,
                        "msg_idx": msg_idx,
                        "message_id": message_id,
                        "rating": "",
                        "category": "",
                        "summary": "",
                        "explanation": f"ERR: {type(e).__name__}: {e}",
                    }
                )
            return

    md = result.metadata or {}
    async with writer_lock:
        writer.writerow(
            {
                "scanner": scanner_name,
                "eval_file": eval_file,
                "transcript_id": transcript_id,
                "model": model,
                "task_id": task_id,
                "msg_idx": msg_idx,
                "message_id": message_id,
                "rating": result.value,
                "category": md.get("category", ""),
                "summary": md.get("summary", ""),
                "explanation": (result.explanation or "").replace("\n", " "),
            }
        )


async def _process_eval_file(
    eval_path: Path,
    scanners: dict,
    writer,
    writer_lock,
    sem,
    *,
    stride: int,
):
    try:
        log = read_eval_log(str(eval_path), header_only=True)
    except Exception as e:
        print(f"  SKIP {eval_path.name}: {e}")
        return 0

    model = log.eval.model or "?"
    task_id = getattr(log.eval, "task_id", None) or log.eval.task

    count = 0
    for sample in read_eval_log_samples(str(eval_path)):
        transcript_id = sample.id or "?"
        all_messages = list(sample.messages)
        assistant_idx = 0
        tasks = []
        for i, msg in enumerate(all_messages):
            if not isinstance(msg, ChatMessageAssistant):
                continue
            if assistant_idx % stride == 0:
                msg_id = getattr(msg, "id", "") or ""
                for name, fn in scanners.items():
                    if name == "brilliant_move_with_context":
                        window, _ = _window_messages(
                            all_messages, i, CONTEXT_WINDOW
                        )
                        scan_input = window
                    else:
                        scan_input = msg
                    tasks.append(
                        _run_one(
                            name, fn, scan_input, writer, writer_lock,
                            eval_file=eval_path.name,
                            transcript_id=transcript_id,
                            model=model,
                            task_id=task_id,
                            msg_idx=i,
                            message_id=msg_id,
                            sem=sem,
                        )
                    )
            assistant_idx += 1
        count += len(tasks)
        if tasks:
            await asyncio.gather(*tasks)
    return count


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcripts", required=True, help="Directory of .eval files")
    ap.add_argument("--out", required=True, help="Output CSV path")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument(
        "--stride",
        type=int,
        default=1,
        help="Judge every Nth assistant turn (default 1)",
    )
    ap.add_argument("--limit", type=int, default=0, help="Max .eval files")
    ap.add_argument(
        "--with-context",
        action="store_true",
        help="Also run the 5-turn context variant (extra LLM call per judged turn)",
    )
    args = ap.parse_args()

    eval_files = sorted(Path(args.transcripts).glob("*.eval"))
    if args.limit:
        eval_files = eval_files[: args.limit]
    if not eval_files:
        sys.exit(f"No .eval files in {args.transcripts}")

    print(f"Scanning {len(eval_files)} eval files with concurrency={args.concurrency} stride={args.stride}")

    scanners = scan_fns(include_context=args.with_context)
    sem = asyncio.Semaphore(args.concurrency)
    writer_lock = asyncio.Lock()

    os.makedirs(Path(args.out).parent or ".", exist_ok=True)
    with open(args.out, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        fh.flush()

        class FlushingWriter:
            def __init__(self, w, fh):
                self.w = w
                self.fh = fh
                self.rows = 0

            def writerow(self, row):
                self.w.writerow(row)
                self.rows += 1
                if self.rows % 10 == 0:
                    self.fh.flush()

        fw = FlushingWriter(writer, fh)

        for ef in eval_files:
            t0 = time.time()
            n = await _process_eval_file(
                ef, scanners, fw, writer_lock, sem, stride=args.stride
            )
            fh.flush()
            dt = time.time() - t0
            print(f"  {ef.name}: {n} scans in {dt:.1f}s  (running total: {fw.rows} rows)")

    print(f"DONE. Wrote {fw.rows} rows to {args.out}")


if __name__ == "__main__":
    asyncio.run(main())
