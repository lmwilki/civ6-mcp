"""Tool misuse scanners — pattern-based detection of errors and stuck loops."""
from inspect_scout import Result, Scanner, Transcript, grep_scanner, scanner


@scanner(messages=["tool"])
def tool_errors() -> Scanner[Transcript]:
    """Count tool error responses (ERR:, Error:, Runtime Error)."""
    return grep_scanner([
        "ERR:",
        "Error:",
        "SILENT_FAILURE",
    ])


@scanner(messages=["tool"])
def repeated_failures() -> Scanner[Transcript]:
    """Detect 3+ consecutive errors to the same tool (stuck loops)."""

    async def scan(transcript: Transcript) -> Result:
        sequences: list[str] = []
        current_tool: str | None = None
        error_streak = 0

        for msg in transcript.messages:
            text = msg.text if hasattr(msg, "text") else ""
            is_error = text.startswith(("ERR:", "Error:"))
            tool_name = getattr(msg, "function", None) or ""

            if is_error and tool_name == current_tool:
                error_streak += 1
            elif is_error:
                if error_streak >= 3 and current_tool:
                    sequences.append(f"{current_tool} x{error_streak}")
                current_tool = tool_name
                error_streak = 1
            else:
                if error_streak >= 3 and current_tool:
                    sequences.append(f"{current_tool} x{error_streak}")
                current_tool = None
                error_streak = 0

        if error_streak >= 3 and current_tool:
            sequences.append(f"{current_tool} x{error_streak}")

        return Result(
            value=len(sequences),
            explanation=f"Stuck loops: {', '.join(sequences)}" if sequences else "No stuck loops",
        )

    return scan
