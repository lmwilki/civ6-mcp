#!/usr/bin/env bash
# Copy fixture data to ~/.civ6-mcp so the web dashboard can display it.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="${CIV6_DIARY_DIR:-$HOME/.civ6-mcp}"

mkdir -p "$TARGET"
cp "$DIR"/*.jsonl "$TARGET"/
echo "Loaded $(ls "$DIR"/*.jsonl | wc -l) fixture files into $TARGET"
