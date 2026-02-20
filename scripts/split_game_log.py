#!/usr/bin/env python3
"""One-off script to split game_log.jsonl into per-session files.

Reads the monolithic game_log.jsonl, groups entries by session ID,
and writes each session to game_log_{session_id}.jsonl. Skips
sessions that already have a per-session file.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

LOG_DIR = Path.home() / ".civ6-mcp"
CENTRAL_LOG = LOG_DIR / "game_log.jsonl"


def main():
    if not CENTRAL_LOG.exists():
        print(f"No log file found at {CENTRAL_LOG}")
        sys.exit(1)

    lines_by_session: dict[str, list[str]] = defaultdict(list)
    malformed = 0

    print(f"Reading {CENTRAL_LOG}...")
    with open(CENTRAL_LOG) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                sid = entry.get("session")
                if not sid:
                    malformed += 1
                    continue
                # Keep the raw line to preserve exact formatting
                lines_by_session[sid].append(line)
            except json.JSONDecodeError:
                malformed += 1

    total = sum(len(v) for v in lines_by_session.values())
    print(f"Found {total} entries across {len(lines_by_session)} sessions ({malformed} malformed lines skipped)")

    written = 0
    skipped = 0
    for sid, lines in sorted(lines_by_session.items(), key=lambda x: -len(x[1])):
        path = LOG_DIR / f"game_log_{sid}.jsonl"
        if path.exists():
            skipped += 1
            continue
        with open(path, "w") as f:
            f.write("\n".join(lines) + "\n")
        written += 1
        print(f"  {path.name}: {len(lines)} entries")

    print(f"\nDone. Wrote {written} session files, skipped {skipped} (already exist)")


if __name__ == "__main__":
    main()
