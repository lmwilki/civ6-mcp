#!/usr/bin/env python3
"""Bulk runner for CivBench scenarios.

Runs scenarios sequentially (one game at a time) across one or more models.
Results are stored in Inspect's default log directory and viewable via
`inspect view`.

Usage:
    # Single model, all scenarios
    uv run python evals/runner.py --model openai/azure/gpt-5.2

    # Multiple models
    uv run python evals/runner.py \
        --models openai/azure/gpt-5.2,google/vertex/gemini-3.1-pro-preview

    # All default models
    uv run python evals/runner.py --all

    # Specific scenarios
    uv run python evals/runner.py \
        --model openai/azure/gpt-5.2 \
        --scenarios ground_control,deus_vult

    # Short test run (10 messages per sample)
    uv run python evals/runner.py \
        --model openai/azure/gpt-5.2 \
        --scenarios ground_control \
        --message-limit 10

Prerequisites:
    - Civilization VI running with FireTuner enabled (port 4318)
    - Benchmark save files in evals/saves/
    - evals/.env with API credentials (see evals/.env.example)
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Load credentials from evals/.env
# ---------------------------------------------------------------------------

EVALS_DIR = Path(__file__).parent
_ENV_FILE = EVALS_DIR / ".env"

if _ENV_FILE.exists():
    for line in _ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and value:
            os.environ.setdefault(key, value)

# ---------------------------------------------------------------------------
# Model catalogue — verified working models
# ---------------------------------------------------------------------------

# Azure OpenAI
AZURE_MODELS = [
    "openai/azure/gpt-5.2",
    "openai/azure/gpt-5.1",
    "openai/azure/gpt-5",
    "openai/azure/Kimi-K2.5",
    "openai/azure/Kimi-K2-Thinking",
    "openai/azure/DeepSeek-V3.2",
]

# Azure doesn't support the OpenAI Responses API — force chat completions
_NEEDS_CHAT_COMPLETIONS = {"gpt-5.2", "gpt-5.1", "gpt-5"}

# GCP Vertex AI
VERTEX_MODELS = [
    "google/vertex/gemini-3.1-pro-preview",
    "google/vertex/gemini-3-pro-preview",
    "google/vertex/gemini-3-flash-preview",
]

ALL_MODELS = AZURE_MODELS + VERTEX_MODELS

ALL_SCENARIOS = [
    "ground_control",
    "empty_canvas",
    "deus_vult",
    "snowflake",
    "cry_havoc",
]


def run_scenario(
    model: str,
    scenario: str,
    track: str = "civbench_standard",
    message_limit: int | None = None,
    extra_args: list[str] | None = None,
) -> int:
    """Run a single scenario and return the exit code."""
    cmd = [
        "inspect",
        "eval",
        f"evals/civbench.py@{track}",
        "--model",
        model,
        "-T",
        f"scenarios={scenario}",
        "--max-samples",
        "1",  # one game at a time
    ]
    # Azure doesn't support the OpenAI Responses API
    deployment = model.rsplit("/", 1)[-1]
    if deployment in _NEEDS_CHAT_COMPLETIONS:
        cmd.extend(["-M", "responses_api=false"])
    if message_limit is not None:
        cmd.extend(["--message-limit", str(message_limit)])
    if extra_args:
        cmd.extend(extra_args)

    print(f"\n{'=' * 60}")
    print(f"  {model} | {scenario}")
    print(f"  {' '.join(cmd)}")
    print(f"{'=' * 60}\n")

    result = subprocess.run(cmd, cwd=str(EVALS_DIR.parent))
    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Run CivBench scenarios across models."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--model",
        help="Single model to evaluate (e.g. openai/azure/gpt-5.2)",
    )
    group.add_argument(
        "--models",
        help="Comma-separated list of models to evaluate",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Run all default models",
    )
    parser.add_argument(
        "--scenarios",
        default=None,
        help="Comma-separated scenario IDs (default: all)",
    )
    parser.add_argument(
        "--track",
        default="civbench_standard",
        choices=["civbench_standard", "civbench_open"],
        help="Evaluation track (default: civbench_standard)",
    )
    parser.add_argument(
        "--message-limit",
        type=int,
        default=None,
        help="Override message limit (useful for test runs)",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="Print available models and exit",
    )
    args, extra = parser.parse_known_args()

    if args.list_models:
        print("Azure OpenAI:")
        for m in AZURE_MODELS:
            print(f"  {m}")
        print("\nGCP Vertex AI:")
        for m in VERTEX_MODELS:
            print(f"  {m}")
        return

    # Resolve models
    if args.all:
        models = ALL_MODELS
    elif args.models:
        models = [m.strip() for m in args.models.split(",")]
    elif args.model:
        models = [args.model]
    else:
        parser.error("Provide --model, --models, or --all")
        return

    # Resolve scenarios
    scenarios = (
        [s.strip() for s in args.scenarios.split(",")]
        if args.scenarios
        else ALL_SCENARIOS
    )

    # Run
    results: list[tuple[str, str, int]] = []
    total = len(models) * len(scenarios)
    current = 0

    for model in models:
        for scenario in scenarios:
            current += 1
            print(f"\n[{current}/{total}] Running {scenario} with {model}")
            rc = run_scenario(
                model=model,
                scenario=scenario,
                track=args.track,
                message_limit=args.message_limit,
                extra_args=extra if extra else None,
            )
            results.append((model, scenario, rc))
            if rc != 0:
                print(f"  WARNING: {scenario} exited with code {rc}")

    # Summary
    print(f"\n{'=' * 60}")
    print("  RESULTS SUMMARY")
    print(f"{'=' * 60}")
    for model, scenario, rc in results:
        status = "OK" if rc == 0 else f"FAIL (exit {rc})"
        print(f"  {model:45s} | {scenario:20s} | {status}")
    print()

    # Exit with non-zero if any scenario failed
    failures = sum(1 for _, _, rc in results if rc != 0)
    if failures:
        print(f"{failures}/{total} scenario(s) failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
