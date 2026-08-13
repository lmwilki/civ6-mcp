# Changelog

## Unreleased

The focus shifted from running games to packaging the results. The dataset publisher pipeline exports all telemetry to HuggingFace with Croissant 1.1 metadata for the NeurIPS Evaluations & Datasets track submission. Several reliability features landed in parallel from ongoing eval runs across the fleet.

- **World Congress end-turn deadlock fixed**: The "hide the congress UI" Lua existed in five separate copies that had drifted — three knew only about `WorldCongressIntro`/`WorldCongressPopup`, so a turn blocked behind the Results, Proposals, or BetweenTurns screen could never be unblocked and `end_turn` looped forever. Consolidated into one `build_world_congress_dismiss()` covering all five contexts (plus `UIManager:DequeuePopup`, which `SetHide` alone omits). New `advance_world_congress` tool for the session blocker, surfaced in the blocker hint so agents can actually find it.
- **end_turn no longer latches on an aborted call**: `_pending_end_turn` was only cleared when a turn advanced, so a killed task, client timeout, or dropped connection left it stuck `True` — every later `end_turn` refused to send `ACTION_ENDTURN` and polled a request the game never received. Now escapes when the turn moved past the baseline or the marker exceeds `STALE_PENDING_SECS`, extracted into a pure `should_resend_end_turn()`.
- **HuggingFace dataset publisher**: End-to-end pipeline (`scripts/publish_hf/`) for staging, exporting parquet tables, generating Croissant 1.1 metadata, validating, and uploading to HuggingFace.
- **NeurIPS anonymization**: RAI metadata fields, identity redaction in parquet exports, anonymous HF account.
- **Game-over watchdog**: Detect victories even when the LLM stops calling tools — polls game state on a background timer.
- **Auto-resume on crash**: Increase max-retries to 20 for network resilience.
- **Admissibility badges**: Game IDs show admissibility status on game detail and benchmark pages.
- **8-dimension spider charts**: Model profile pages show radar charts with per-dimension scores, color-coded by domain.
- **Collaborator analysis toolkit**: `scripts/civbench_data.py` pandas library + SAS token generator for notebook-based analysis.
- **Advisor per-turn budget**: Soft warn at 10, hard cap at 20 calls across `get_district_advisor` + `get_wonder_advisor`. Fixes the 1,567-call loop that killed Gemini Pro at T136.
- **Save scumming detection**: Live deterrent during games + historical auditor for post-hoc analysis.
- **Single admissible boolean**: Precomputed on game doc — ELO query becomes one filter.
- **Game-over capture in end_turn**: `GameOverStatus` captured directly, eliminating fragile second Lua call.
- **Player elimination detection**: `IsAlive()` check when no winning team found.
- **Turn-limit detection**: `Game.GetMaxTurns()` check when no winner at game end.
- **Early diplomacy detection**: 45s threshold cuts 10-min dead wait per AI trade proposal.
- **10-min API timeout + 6 retries**: Prevents indefinite LLM hangs.
- **Live streaming**: In-progress games stream to Convex with quality gates.
- **Launch discipline**: Block dirty git tree + verify feature markers on remote machines.
- **Kimi-K2.5 support**: Register 256K context window with Inspect.
- **Sync safety**: Don't regress completed games to live when sync watcher delivers late rows.
- **Web**: Next.js 16.2.3, clickable model names, SEO (OG metadata, sitemap, llms.txt), UI polish (shimmer skeletons, victory glow, map playback 10x default).

## v1.1.10 — Orchestrator Hardening (2026-04-15)

Final round of stability fixes before handing the fleet over to unattended overnight runs. The main theme is making the orchestrator less aggressive — it now reports problems rather than trying to auto-fix them, which caused more damage than it prevented.

- **Orchestrator discovery**: Safer machine discovery, `needs_attention` status, no auto-kills.
- **Package verification**: Clear heartbeat and verify installed packages before dispatch.
- **Linux CONTINUE position**: Verified positional click for Linux windowed mode.
- **Disable GameCore pre-check on Linux**: Main menu has no Lua states — the pre-check was always failing and wasting 30s.

## v1.1.9 — Game-Over Detection (2026-04-14)

Multiple models were reaching game-over states that the server didn't detect — the agent would keep playing into a post-victory state, or the defeat screen would appear but the Lua query missed it. This release adds fallback detection paths for every game-over variant.

- **Defeat screen detection**: GameCore fallback + polling when standard detection fails.
- **Linux OCR geometry**: Use actual capture geometry for windowed click offset.
- **AI turn timeout**: Extended to 10 minutes (was 5). Some late-game turns with 8 AI civs genuinely take this long.
- **Game process timeout**: Increased to 60s for slow launches on underpowered machines.
- **Inspect eval fix**: Upgrade + compaction + stderr capture to prevent silent death.
- **Windows CMD fix**: Reverted `start /min` which prevented game from launching — the hidden window approach doesn't work with Steam's process model.

## v1.1.8 — Orchestrator v2 (2026-04-13)

Complete rewrite of the orchestrator's core loop. The v1 orchestrator was a flat script that dispatched jobs sequentially; v2 introduces a proper state machine with per-machine state files so multiple orchestrator instances (one per operator) can coordinate without overwriting each other.

- **Orchestrator v2**: Job matrix, state machine, resume-on-crash.
- **Per-machine state files**: Concurrent orchestrators no longer overwrite each other.
- **Windows CMD**: Hidden window for background launches.

## v1.1.7 — Scoring + Timeout (2026-04-10)

The big addition is the 8-dimension scoring rubric. Each completed game is automatically scored across Overall, Economic, Military, Scientific, Diplomatic, Spatial, Tool Fluency, and Coherence. These scores power the spider charts on the web dashboard and the `scorecard` CLI command for model comparison.

The AI turn timeout was also bumped from 40s to 5 minutes. The v1.0.3 post-mortem showed that T249 hangs were probabilistic, not deterministic — the AI just needed more time on complex late-game turns with 8 civilizations.

- **8-dimension scoring**: `score` and `scorecard` commands in analyze.py.
- **AI turn timeout**: Extended from 40s to 5 minutes (probabilistic hangs need more time).
- **Heartbeat threshold**: Unified 600s for boot and playing phases.
- **Victory type detection**: VP_DATA cross-check for Score victory fallback.
- **Linux autosave fix**: `Network.SaveGame` silently fails on Aspyr port — use GameCore path instead.
- **Inspect eval**: Fix silent death via upgrade + compaction + stderr.
- **Dependencies**: Upgrade google-genai 1.68→1.70, aiplatform 1.139→1.145.
- **Gemini 3 Flash**: Added ETA prior and model alias.

## v1.1.6 — World Congress + Provenance (2026-04-08)

The `vote_world_congress` tool was setting votes but never submitting them, which caused agents to get stuck in an infinite end_turn loop whenever the World Congress convened. Replaced with `queue_wc_votes` which batches votes and submits in a single call.

This release also adds `mcp_git_describe` to every diary row, so each data point is traceable to the exact server version that produced it — critical for data quality auditing.

- **Removed `vote_world_congress`**: Replaced by `queue_wc_votes` (old tool set votes but never submitted, causing infinite end_turn loops).
- **Provenance tagging**: `mcp_git_describe` added to playerRows schema.
- **Linux process cleanup**: Kill stale civ-mcp processes in kill_runner.
- **CONTINUE button**: Widen click grid for small windowed resolutions.
- **Heartbeat**: Handle non-integer turn values gracefully; bump playing threshold to 600s.
- **Flash Lite ETA**: Separate prior (was incorrectly using Gemini Pro's 5 min/turn).
- **Leader portraits**: Fix raw enum names like `LEADER_HAMMURABI`.
- **Stale games**: Add `markCompleted` Convex mutation.

## v1.1.5 — LOS + Space Projects (2026-04-05)

Two agent-facing bugs that caused repeated failures in specific game phases. Ranged units were trying to attack targets they couldn't see (the target list didn't check line of sight), and space projects showed `[READY]` even when prerequisite projects hadn't been completed — causing agents to queue unbuildable items and stall.

- **Ranged attack LOS check**: Add line-of-sight filter to ranged attack target list. Prevents `ERR:NO_LOS` errors that confused agents into retrying the same attack.
- **Space project UI**: Fix misleading `[READY]` on space projects that can't be built yet (missing prereq projects).
- **`_emitter` fix**: Resolve `UnboundLocalError` when telemetry emitter wasn't initialized.
- **Code formatting**: Bulk ruff format across src/, scripts/, evals/.

## v1.1.4 — Preflight + Web Polish (2026-04-03)

The fleet was experiencing too many silent failures — games that never started because Steam wasn't running, or packages weren't synced, or the telemetry bucket was unreachable. This release adds a comprehensive preflight check that catches all of these before wasting a 15-hour game slot.

- **Preflight checks**: Verify Steam running, no stale processes, telemetry bucket accessible, API credentials valid, uv packages synced.
- **Autosave fix**: Only clean autosaves on first attempt, not retries (retries were deleting the save they needed to load).
- **Web app**: Surface run IDs, data provenance, and eval track. Normalize design tokens, harden accessibility.
- **Heartbeat fixes**: Fix stale false-positive, TypeError in turn comparison.
- **Linux OCR**: Revert frame extent compensation and combined click chain.

## v1.1.3 — Orchestrator Observability (2026-04-01)

The orchestrator couldn't reliably tell whether a remote game was alive. Process detection via SSH was flaky (Windows `Get-Process` misses Session 1 processes, Linux `pgrep` races). The heartbeat file solves this: the MCP server writes its phase, turn, and PID on every tool call, and the orchestrator reads it via SSH.

- **Heartbeat file** (`~/.civ6-mcp/heartbeat.json`): MCP server writes phase, turn, PID on every tool call. Orchestrator reads via SSH instead of unreliable process detection.
- **Windows process killing**: PowerShell `Stop-Process` via EncodedCommand replaces `taskkill` (which can't reach Session 1 from SSH).
- **Autosave cleanup**: Clears both MCP autosaves and game `AutoSave_*` files before launch, preventing wrong-save loads. Fixed Linux path escaping for `Sid Meier's` apostrophe.
- **Phase-aware staleness**: Boot phases get 5 min threshold, playing gets 3 min.
- **Boot timeout**: 10 min hard limit for games that never reach gameplay.
- **Linux OCR**: Reverted frame extent compensation (xdotool already returns content area). Reverted combined click chain that broke GNOME input.

## v1.1.2 — Heartbeat System (2026-04-01)

- **Heartbeat file system**: Atomic JSON writes at `~/.civ6-mcp/heartbeat.json` with phase/turn/ts/pid.
- **Orchestrator reads heartbeat** instead of `Get-Process` on Windows (false negatives on schtasks sessions).
- **Status line** shows boot phase (`launching`, `connecting`, `loading`, `playing`).
- **Periodic status logging** to file every 5 minutes.

## v1.1.1 — Fleet Launch Fixes (2026-04-01)

The first batch of fleet runs exposed a long tail of platform-specific launch failures. Linux couldn't launch via Steam URI, killing the game also killed Steam, zombie processes blocked relaunch, and Windows PowerShell quoting broke the runner detection. Most of these were only visible when running headless via SSH — the local development path worked fine.

- **Linux game launch**: `steam -applaunch 289070` replaces unreliable URI scheme.
- **Kill game safety**: `pkill -x` exact match prevents killing Steam.
- **Stale process detection**: Kill zombie game processes that block relaunch.
- **Gemini 3.1 Flash Lite** added to model catalogue.
- **Menu audit script** for per-machine OCR calibration.
- **Crash recovery**: Connection-loss auto-restart after 5 consecutive failures; HANG recovery identity check retries.
- **Non-linear ETA**: Piecewise turn-time model with Bayesian blending.
- **Sleep detection**: Resets stall timers on host wake.
- **Sentinel safety**: Completion file only created on success.

## v1.1.0 — Orchestrator + Fleet Tooling (2026-03-31)

The transition from single-machine to multi-machine evaluation. The orchestrator dispatches (model, scenario) jobs to a fleet of machines via SSH, monitors health through heartbeat files, detects stalls, and auto-retries failed runs. Human-readable run IDs (`crimson-amber-falcon-47`) replaced hex hashes for easier debugging.

- **Orchestrator** (`scripts/orchestrator.py`): SSH-based fleet management with job dispatch, health monitoring, stall detection, auto-retry, and Convex sync.
- **Human-readable run IDs**: `adjective-color-noun-number` format (~34M unique IDs), deterministic from model+scenario+hour.
- **Data quality gates**: `should_sync_game()` skips <10 turns, `excludeReason` field for invalid games, Elo excludes development track.
- **CORRUPTED_QUEUE fix**: Auto-clear ghost queue entries, changed narration from "load autosave" to "set new production".
- **Wrong save loading**: Screen-aware detection, autosave cleanup, multi-position click grid, Lua reload fallback.

## v1.0.4 — Production Diagnostics (2026-03-30)

Small fixes that surfaced during the first real eval runs. Agents were confused by Great People showing 1 charge remaining after being consumed, by `set_research` silently accepting already-completed techs, and by opaque production failures.

- Great Person charges fix (consumed GP showed 1 remaining).
- Already-completed tech/civic detection in `set_research`.
- `CANNOT_PRODUCE` reasons in `set_city_production`.

## v1.0.3 — Crash Recovery (2026-03-30)

Post-mortem from the first GPT-5.4 eval run. A probabilistic hang at T249 wasted 2.1 hours because the single-retry recovery declared it "deterministic" after one attempt. The agent then loaded progressively older saves in a Groundhog Day loop. After relaunch, Civ 6 auto-loaded a Korea game from a different session because there was no post-load verification.

- Multi-retry hang recovery (3 attempts with escalating waits: 0s, 15s, 30s).
- Post-load civ identity verification (catches wrong-game-loaded after restart).
- Autosave retention increase (keep=5 → keep=8) for more fallback options.
- Fix SAVE_DIR → SINGLE_SAVE_DIR in save-existence check.

## v1.0.2 — Combat + Analysis (2026-03-30)

- **Combat followup fix**: Uses estimate as fallback (Lua state stale within same turn frame).
- **Promotion XP threshold fix**: `GetExperienceForNextLevel()` replaces double-counting formula.
- **City attack errors**: Split into `ERR:OUT_OF_RANGE`, `ERR:ALREADY_FIRED`, `ERR:NO_LOS`.
- **Builder tasks**: Filter by prerequisite tech (`_LOCKED` tag).
- **Analysis tools**: Sensorium metrics, reflection-action gap analysis.

## v1.0.1 — Combat Visibility (2026-03-29)

- Combat visibility improvements, movement diagnostics, trade reporting.

## v1.0.0 — Initial Release (2026-03-29)

The first tagged release. 76 MCP tools covering the full Civilization VI gameplay loop — units, cities, research, diplomacy, trade, government, religion, great people, world congress, and victory tracking. Eval infrastructure built on Inspect AI with three standardised scenarios (Ground Control, Snowflake, Cry Havoc). Real-time game dashboard on Convex with Elo rankings and strategic map replay. Telemetry pipeline to Azure Blob Storage. Cross-platform support for macOS, Windows, and Linux.

- MCP server with 76 tools for Civilization VI via FireTuner.
- CivBench eval infrastructure with Inspect AI integration.
- Convex dashboard with real-time game tracking, Elo rankings, strategic map replay.
- Azure Blob telemetry storage.
- Support for macOS, Windows, and Linux.
