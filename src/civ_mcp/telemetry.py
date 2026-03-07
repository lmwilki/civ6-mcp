"""Telemetry emitter — decouples data production from storage backends.

The MCP server emits structured events (diary rows, tool calls, spatial
observations, map captures) through a TelemetryEmitter.  Pluggable sinks
handle where the data actually lands:

  * LocalSink  — writes JSONL files to ~/.civ6-mcp/ (always on, backward compat)
  * CloudSink  — writes to Azure Blob / GCS / S3 via fsspec (opt-in)

A manifest.json is written at startup and updated when the game identity is
discovered, solving the "orphaned game" problem (identity exists before
gameplay starts).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from civ_mcp.version import GIT_SHA, VERSION

log = logging.getLogger(__name__)

LOCAL_DIR = Path.home() / ".civ6-mcp"

# Event types emitted by the MCP server
EVENT_DIARY_ROW = "diary_row"
EVENT_CITY_ROW = "city_row"
EVENT_TOOL_CALL = "tool_call"
EVENT_SPATIAL = "spatial"
EVENT_MAP_STATIC = "map_static"
EVENT_MAP_DELTA = "map_delta"
EVENT_GAME_OVER = "game_over"


# ── Sink protocol ────────────────────────────────────────────────────────


@runtime_checkable
class TelemetrySink(Protocol):
    """Interface for telemetry storage backends."""

    def start(self, run_id: str, metadata: dict[str, Any]) -> None:
        """Called once at MCP startup with run_id and initial metadata."""
        ...

    def bind_game(self, civ: str, seed: int) -> None:
        """Called when game identity is discovered (civ type + random seed)."""
        ...

    async def emit(self, event_type: str, data: dict[str, Any]) -> None:
        """Write a single event to the sink."""
        ...

    async def close(self) -> None:
        """Flush and close the sink."""
        ...


# ── Local sink (always on) ───────────────────────────────────────────────


class LocalSink:
    """Writes JSONL files to ~/.civ6-mcp/, preserving existing file layout.

    File layout per game:
      diary_{civ}_{seed}_{run_id}.jsonl        — player rows per turn
      diary_{civ}_{seed}_{run_id}_cities.jsonl  — city rows per turn
      log_{civ}_{seed}_{run_id}.jsonl           — tool call events
      spatial_{civ}_{seed}_{run_id}.jsonl        — attention tracking
      mapstatic_{civ}_{seed}_{run_id}.json       — one-time terrain dump
      mapturns_{civ}_{seed}_{run_id}.jsonl       — per-turn ownership deltas
    """

    def __init__(self, directory: Path | None = None) -> None:
        self._dir = directory or LOCAL_DIR
        self._run_id: str = ""
        self._civ: str | None = None
        self._seed: int | None = None
        self._game_id: str | None = None
        self._lock = asyncio.Lock()
        # Buffered events received before bind_game()
        self._buffer: list[tuple[str, dict[str, Any]]] = []
        # Per-file open handles and sequence counters
        self._log_seq: int = 0
        self._has_map_static: bool = False

    def start(self, run_id: str, metadata: dict[str, Any]) -> None:
        self._run_id = run_id
        self._dir.mkdir(parents=True, exist_ok=True)

    def bind_game(self, civ: str, seed: int) -> None:
        game_id = f"{civ}_{seed}"
        if self._game_id == game_id:
            return
        self._civ = civ
        self._seed = seed
        self._game_id = game_id
        self._dir.mkdir(parents=True, exist_ok=True)

        # Seed log sequence from existing file
        log_path = self._path("log")
        if log_path.exists():
            with open(log_path, "rb") as f:
                self._log_seq = sum(1 for _ in f)
        else:
            self._log_seq = 0

        # Check if map static already captured
        static_path = self._dir / f"mapstatic_{self._game_id}_{self._run_id}.json"
        self._has_map_static = static_path.exists()

        # Flush buffered events
        if self._buffer:
            for event_type, data in self._buffer:
                self._write_sync(event_type, data)
            self._buffer.clear()

    async def emit(self, event_type: str, data: dict[str, Any]) -> None:
        async with self._lock:
            if self._game_id is None:
                # Buffer all events until game identity is known via bind_game()
                self._buffer.append((event_type, data))
                return
            self._write_sync(event_type, data)

    def _write_sync(self, event_type: str, data: dict[str, Any]) -> None:
        """Synchronous write — called under lock."""
        if event_type == EVENT_MAP_STATIC:
            if self._has_map_static:
                return  # Already captured (e.g. resumed session)
            path = self._dir / f"mapstatic_{self._game_id}_{self._run_id}.json"
            path.write_text(json.dumps(data, separators=(",", ":")))
            self._has_map_static = True
            return

        if event_type == EVENT_TOOL_CALL:
            data["seq"] = self._log_seq
            self._log_seq += 1
            path = self._path("log")
        elif event_type == EVENT_GAME_OVER:
            data["seq"] = self._log_seq
            self._log_seq += 1
            path = self._path("log")
        elif event_type == EVENT_DIARY_ROW:
            path = self._path("diary")
        elif event_type == EVENT_CITY_ROW:
            path = self._path("diary_cities")
        elif event_type == EVENT_SPATIAL:
            path = self._path("spatial")
        elif event_type == EVENT_MAP_DELTA:
            path = self._path("mapturns")
        else:
            log.warning("LocalSink: unknown event type %s", event_type)
            return

        with open(path, "a") as f:
            f.write(json.dumps(data, separators=(",", ":")) + "\n")

    def _path(self, file_type: str) -> Path:
        """Build the file path for a given type."""
        if file_type == "diary_cities":
            return self._dir / f"diary_{self._game_id}_{self._run_id}_cities.jsonl"
        if file_type == "mapturns":
            return self._dir / f"mapturns_{self._game_id}_{self._run_id}.jsonl"
        return self._dir / f"{file_type}_{self._game_id}_{self._run_id}.jsonl"

    async def close(self) -> None:
        pass  # JSONL files are flushed per-write


# ── Cloud sink (opt-in via CIV_MCP_TELEMETRY_BUCKET) ─────────────────────


class CloudSink:
    """Writes telemetry to a cloud bucket via fsspec (Azure Blob, GCS, S3).

    Async-buffered: flushes every ``flush_interval`` seconds or
    ``flush_count`` events, whichever comes first.

    Bucket layout:
      {bucket}/runs/{run_id}/manifest.json
      {bucket}/runs/{run_id}/diary.jsonl
      {bucket}/runs/{run_id}/cities.jsonl
      {bucket}/runs/{run_id}/log.jsonl
      {bucket}/runs/{run_id}/spatial.jsonl
      {bucket}/runs/{run_id}/map_static.json
      {bucket}/runs/{run_id}/map_turns.jsonl
    """

    def __init__(
        self,
        bucket_url: str,
        *,
        flush_interval: float = 5.0,
        flush_count: int = 10,
    ) -> None:
        # Normalise trailing slash
        self._bucket = bucket_url.rstrip("/")
        self._flush_interval = flush_interval
        self._flush_count = flush_count
        self._run_id: str = ""
        self._metadata: dict[str, Any] = {}
        self._civ: str | None = None
        self._seed: int | None = None
        self._lock = asyncio.Lock()
        self._buffer: dict[str, list[str]] = {}  # filename -> list of JSON lines
        self._flush_task: asyncio.Task[None] | None = None
        self._fs: Any = None  # fsspec filesystem instance
        self._closed = False

    def _get_fs(self) -> Any:
        """Lazy-init fsspec filesystem from the bucket URL scheme."""
        if self._fs is not None:
            return self._fs
        import fsspec

        self._fs = fsspec.filesystem(
            self._bucket.split("://")[0],
            # Let fsspec pick up credentials from environment
        )
        return self._fs

    def _run_prefix(self) -> str:
        return f"{self._bucket}/runs/{self._run_id}"

    def start(self, run_id: str, metadata: dict[str, Any]) -> None:
        self._run_id = run_id
        self._metadata = dict(metadata)
        # Write initial manifest (blocking — runs once at startup)
        manifest = {
            "run_id": run_id,
            "start_ts": time.time(),
            "mcp_version": VERSION,
            "git_sha": GIT_SHA,
            "metadata": self._metadata,
        }
        self._write_cloud_json(f"{self._run_prefix()}/manifest.json", manifest)
        # Periodic flush task is started lazily on first emit()

    def bind_game(self, civ: str, seed: int) -> None:
        self._civ = civ
        self._seed = seed
        # Update manifest with game identity (blocking — runs once per game)
        manifest_path = f"{self._run_prefix()}/manifest.json"
        try:
            fs = self._get_fs()
            existing = json.loads(fs.cat_file(manifest_path))
        except Exception:
            existing = {"run_id": self._run_id, "metadata": self._metadata}
        existing["civ"] = civ
        existing["seed"] = seed
        existing["game_id"] = f"{civ}_{seed}"
        self._write_cloud_json(manifest_path, existing)

    async def emit(self, event_type: str, data: dict[str, Any]) -> None:
        filename = self._event_to_filename(event_type)
        if filename is None:
            return

        # Start periodic flush on first emit (deferred from start() to
        # guarantee we're inside an active event loop)
        if self._flush_task is None:
            self._flush_task = asyncio.create_task(self._periodic_flush())

        async with self._lock:
            if event_type == EVENT_MAP_STATIC:
                # Write immediately (single JSON file, not JSONL)
                path = f"{self._run_prefix()}/{filename}"
                await asyncio.to_thread(self._write_cloud_json, path, data)
                return

            line = json.dumps(data, separators=(",", ":"))
            self._buffer.setdefault(filename, []).append(line)

            # Check flush threshold
            total = sum(len(v) for v in self._buffer.values())
            if total >= self._flush_count:
                await self._flush()

    async def close(self) -> None:
        self._closed = True
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        async with self._lock:
            await self._flush()

    async def _flush(self) -> None:
        """Append buffered lines to cloud files."""
        if not self._buffer:
            return
        fs = self._get_fs()
        flushed: list[str] = []
        for filename, lines in self._buffer.items():
            if not lines:
                flushed.append(filename)
                continue
            path = f"{self._run_prefix()}/{filename}"
            payload = "\n".join(lines) + "\n"
            try:
                await asyncio.to_thread(self._append_cloud, fs, path, payload)
                flushed.append(filename)
            except Exception:
                log.warning("CloudSink: failed to flush %s", path, exc_info=True)
        for k in flushed:
            del self._buffer[k]

    async def _periodic_flush(self) -> None:
        """Background task: flush buffer at regular intervals."""
        try:
            while not self._closed:
                await asyncio.sleep(self._flush_interval)
                async with self._lock:
                    await self._flush()
        except asyncio.CancelledError:
            pass

    def _write_cloud_json(self, path: str, data: dict[str, Any]) -> None:
        """Write a single JSON object to cloud (blocking)."""
        try:
            fs = self._get_fs()
            content = json.dumps(data, separators=(",", ":"))
            with fs.open(path, "w") as f:
                f.write(content)
        except Exception:
            log.warning("CloudSink: failed to write %s", path, exc_info=True)

    @staticmethod
    def _append_cloud(fs: Any, path: str, payload: str) -> None:
        """Append text to a cloud file (create if missing)."""
        with fs.open(path, "ab") as f:
            f.write(payload.encode("utf-8"))

    @staticmethod
    def _event_to_filename(event_type: str) -> str | None:
        return {
            EVENT_DIARY_ROW: "diary.jsonl",
            EVENT_CITY_ROW: "cities.jsonl",
            EVENT_TOOL_CALL: "log.jsonl",
            EVENT_GAME_OVER: "log.jsonl",
            EVENT_SPATIAL: "spatial.jsonl",
            EVENT_MAP_STATIC: "map_static.json",
            EVENT_MAP_DELTA: "map_turns.jsonl",
        }.get(event_type)


# ── Emitter (fan-out to sinks) ───────────────────────────────────────────


class TelemetryEmitter:
    """Fan-out emitter that routes events to all registered sinks.

    Usage in server lifespan:

        emitter = TelemetryEmitter()
        emitter.add_sink(LocalSink())
        if cloud_bucket:
            emitter.add_sink(CloudSink(cloud_bucket))
        emitter.start()

    Then throughout the server:

        await emitter.emit("diary_row", row_dict)
    """

    def __init__(self) -> None:
        self._sinks: list[TelemetrySink] = []
        self._run_id: str = ""
        self._metadata: dict[str, Any] = {}
        self._started: bool = False

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def metadata(self) -> dict[str, Any]:
        """Eval metadata from CIV_MCP_METADATA env var (or start() arg)."""
        return self._metadata

    def add_sink(self, sink: TelemetrySink) -> None:
        self._sinks.append(sink)

    def start(
        self,
        run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize all sinks with run_id and metadata.

        If run_id is None, reads CIV_MCP_RUN_ID env var or generates a UUID.
        If metadata is None, reads CIV_MCP_METADATA env var (JSON) or {}.
        """
        self._run_id = (
            run_id or os.environ.get("CIV_MCP_RUN_ID") or uuid.uuid4().hex[:8]
        )
        if metadata is not None:
            self._metadata = metadata
        else:
            raw = os.environ.get("CIV_MCP_METADATA", "")
            if raw:
                try:
                    self._metadata = json.loads(raw)
                except json.JSONDecodeError:
                    log.warning("Invalid CIV_MCP_METADATA JSON: %s", raw)
                    self._metadata = {}
            else:
                self._metadata = {}
        # Always include MCP version info — used by diary rows and manifest
        self._metadata.setdefault("mcp_version", VERSION)
        self._metadata.setdefault("mcp_git_sha", GIT_SHA)

        for sink in self._sinks:
            try:
                sink.start(self._run_id, self._metadata)
            except Exception:
                log.warning("Failed to start sink %s", sink, exc_info=True)
        self._started = True

    def bind_game(self, civ: str, seed: int) -> None:
        """Propagate game identity to all sinks."""
        for sink in self._sinks:
            try:
                sink.bind_game(civ, seed)
            except Exception:
                log.warning("Failed to bind game on sink %s", sink, exc_info=True)

    async def emit(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit an event to all sinks. Non-blocking; errors are logged."""
        for sink in self._sinks:
            try:
                await sink.emit(event_type, data)
            except Exception:
                log.warning("Sink %s failed on %s", sink, event_type, exc_info=True)

    async def close(self) -> None:
        """Flush and close all sinks."""
        for sink in self._sinks:
            try:
                await sink.close()
            except Exception:
                log.warning("Failed to close sink %s", sink, exc_info=True)
