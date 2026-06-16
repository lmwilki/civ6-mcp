"""CivBench action-resampling task.

Takes a recorded `.eval` transcript, truncates its message history at a
chosen index, and asks the model "what would you do next?" many times from
that same context. Use `--epochs N` to control the sample count; Inspect
handles concurrency, retries, and storage.

No game engine is required — the MCP tool *schemas* are introspected
in-process from `civ_mcp.server`, and the resulting stub tools raise if
invoked. We use `generate(tool_calls='none')` so the model emits one
tool_call (or text) per epoch and we stop.

Usage:
    uv run --extra evals inspect eval evals/civbench_resample.py@civbench_resample \\
        --model openai/azure/gpt-5.2 \\
        --epochs 100 \\
        --max-connections 5 \\
        -T eval_log=logs/<source>.eval \\
        -T sample_id=ground_control \\
        -T truncate_at_message=42

Then analyse the output log:
    uv run --extra evals python scripts/inspect-log-analysis/analyze_resample.py \\
        --resample-log logs/<new>.eval \\
        --source-log logs/<source>.eval \\
        --sample-id ground_control \\
        --truncate-at-message 42
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.log import read_eval_log_sample
from inspect_ai.solver import chain, generate, use_tools
from inspect_ai.tool import ToolDef
from inspect_ai.tool._tool_params import ToolParam, ToolParams


def _make_named_stub(tool_name: str):
    """Stub function carrying the intended tool name. Must not be called —
    we use `generate(tool_calls='none')` so the model emits a tool_call but
    inspect never dispatches it. The per-tool name is required because some
    parts of inspect derive a tool's identity from `fn.__name__`, and sharing
    a single stub across all tools would collapse them to one entry."""

    async def _stub(**kwargs):
        raise RuntimeError(
            f"tool {tool_name!r} must not be executed in resample mode"
        )

    _stub.__name__ = tool_name
    _stub.__qualname__ = tool_name
    return _stub


def _mcp_tool_to_tooldef(mcp_tool) -> ToolDef:
    """Convert an MCP Tool (from FastMCP.list_tools()) to an inspect ToolDef."""
    schema = mcp_tool.inputSchema or {}
    props = schema.get("properties", {}) or {}
    required = schema.get("required", []) or []

    tparam_props: dict[str, ToolParam] = {}
    for name, prop in props.items():
        tparam_props[name] = ToolParam(
            type=prop.get("type"),
            # Inspect validates that every parameter has a non-empty
            # description; fall back to the param name when the MCP schema
            # omits one.
            description=prop.get("description") or name,
            default=prop.get("default"),
            enum=prop.get("enum"),
            items=prop.get("items"),
        )

    tparams = ToolParams(
        properties=tparam_props,
        required=list(required),
    )
    return ToolDef(
        tool=_make_named_stub(mcp_tool.name),
        name=mcp_tool.name,
        description=mcp_tool.description or "",
        parameters=tparams,
    )


def _load_mcp_tooldefs() -> list[ToolDef]:
    """Introspect the civ_mcp FastMCP server in-process and return ToolDefs."""
    import civ_mcp.server as server_mod

    mcp_tools = asyncio.run(server_mod.mcp.list_tools())
    return [_mcp_tool_to_tooldef(t) for t in mcp_tools]


def _load_prefix(
    eval_log: str, sample_id: str, truncate_at_message: int, epoch: int = 1
) -> list:
    """Load messages from a source .eval, truncated at `truncate_at_message`."""
    source = read_eval_log_sample(eval_log, id=sample_id, epoch=epoch)
    messages = list(source.messages)
    if truncate_at_message < 1 or truncate_at_message > len(messages):
        raise ValueError(
            f"truncate_at_message={truncate_at_message} out of range "
            f"(sample has {len(messages)} messages)"
        )
    return messages[:truncate_at_message]


@task
def civbench_resample(
    eval_log: str,
    sample_id: str,
    truncate_at_message: int,
    source_epoch: int = 1,
) -> Task:
    """Resample the next action at a fixed point in a recorded transcript.

    Args:
        eval_log: Path (or URI) to the source `.eval` log.
        sample_id: Sample id (scenario) within that log.
        truncate_at_message: Slice end (exclusive). Messages[:k] is the context
            shown to the model; messages[k] is what we're resampling against.
        source_epoch: Epoch of the source sample (default 1).
    """
    prefix = _load_prefix(eval_log, sample_id, truncate_at_message, source_epoch)
    tooldefs = _load_mcp_tooldefs()

    sample = Sample(
        id=f"{sample_id}@m{truncate_at_message}",
        input=prefix,
        metadata={
            "source_eval_log": str(eval_log),
            "source_sample_id": sample_id,
            "source_epoch": source_epoch,
            "truncate_at_message": truncate_at_message,
            "prefix_length": len(prefix),
            "n_tools": len(tooldefs),
        },
    )

    return Task(
        dataset=[sample],
        solver=chain(
            use_tools(*tooldefs, tool_choice="auto"),
            generate(tool_calls="none"),
        ),
        fail_on_error=False,
    )
