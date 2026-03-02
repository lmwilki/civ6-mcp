#!/usr/bin/env python3
"""Install CivBench eval saves into the Civ 6 save directory.

Copies .Civ6Save files from evals/saves/ into the platform-specific
Civilization VI save directory so they can be loaded via load_game_save().

Usage:
    uv run python scripts/install_saves.py            # copy missing saves
    uv run python scripts/install_saves.py --force     # overwrite existing
    uv run python scripts/install_saves.py --dry-run   # show what would happen
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, "src")
from civ_mcp.game_launcher import SINGLE_SAVE_DIR

SAVES_SRC = Path(__file__).resolve().parent.parent / "evals" / "saves"


def main() -> None:
    parser = argparse.ArgumentParser(description="Install CivBench saves into Civ 6")
    parser.add_argument(
        "--force", action="store_true", help="Overwrite saves that already exist"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would happen without copying"
    )
    args = parser.parse_args()

    if not SINGLE_SAVE_DIR:
        print("Error: Could not determine Civ 6 save directory for this platform.")
        sys.exit(1)

    dest = Path(SINGLE_SAVE_DIR)
    saves = sorted(SAVES_SRC.glob("*.Civ6Save"))

    if not saves:
        print(f"No .Civ6Save files found in {SAVES_SRC}")
        sys.exit(1)

    print(f"Source:      {SAVES_SRC}")
    print(f"Destination: {dest}")
    print(f"Saves found: {len(saves)}")
    print()

    if not args.dry_run:
        os.makedirs(dest, exist_ok=True)

    copied = 0
    skipped = 0

    for src in saves:
        dst = dest / src.name
        if dst.exists() and not args.force:
            print(f"  SKIP  {src.name}  (already exists)")
            skipped += 1
        elif args.dry_run:
            print(f"  COPY  {src.name}  (dry run)")
            copied += 1
        else:
            shutil.copy2(src, dst)
            print(f"  COPY  {src.name}")
            copied += 1

    print()
    print(f"Done: {copied} copied, {skipped} skipped, {len(saves)} total")
    if args.dry_run:
        print("(dry run — no files were actually copied)")


if __name__ == "__main__":
    main()
