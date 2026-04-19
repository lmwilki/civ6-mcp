"""Brilliant moves scanner — per-message detection of Move 37 style plays.

Unlike the other scanners in this package which ingest the full Transcript,
this scanner operates on each ChatMessageAssistant independently. The goal
is to flag individual turns where the agent produced a creative, unexpected,
or uncommonly insightful strategic action — the Civ 6 analogue of AlphaGo's
Move 37 against Lee Sedol.

Running per-message keeps the judgement local: the model only sees the
single assistant turn (including its tool calls and diary reflections),
so we avoid diluting a rare spark across a 200-turn game. The tradeoff
is no cross-turn context — a move that was brilliant *because of* what
came five turns earlier will under-score here. For those patterns use
the transcript-level scanners.
"""

from collections.abc import AsyncIterator

from inspect_ai.model import ChatMessage, ChatMessageAssistant, ChatMessageTool
from inspect_scout import (
    AnswerStructured,
    Loader,
    Reference,
    Result,
    Scanner,
    Transcript,
    generate_answer,
    loader,
    parse_answer,
    scanner,
)
from pydantic import BaseModel, Field


BRILLIANT_MOVE_QUESTION = """\
You are reviewing a single turn from an LLM agent playing Civilization VI.
The message shows the agent's reasoning for the turn and the tool calls it
issued (moves, production, research, diplomacy, diary reflections).

Judge whether this single turn contains a "Move 37" — a creative,
unconventional, or structurally insightful play that a strong but
conventional player would be unlikely to make.

What counts as a brilliant move:
- Unusual synergy between civ unique abilities, terrain, and timing
  (e.g. Babylon chaining eurekas out of order; Maya offsetting a city
  to pull in a non-obvious luxury cluster; Khmer timing a flood for
  Holy Site food).
- Sacrificing an obvious short-term gain for a larger compounding
  advantage (e.g. razing a captured high-pop city to prevent a loyalty
  sink; passing on a Great Scientist to patronize a specific later one).
- Exploiting a subtle game mechanic the agent surfaces in its reasoning
  (e.g. declaring a protectorate war to avoid warmonger penalties;
  triggering a specific dedication window for a dark-age bonus; using
  trade routes to deliberately spread a rival religion *into* a hostile
  neighbor to weaken them).
- Unconventional district / wonder placement whose adjacency only pays
  off 30+ turns later.
- Diplomatic plays that are technically legal but read as clever —
  surplus-luxury trades priced above the AI's accept threshold, favor
  concentration on a single WC resolution, spy missions queued for a
  future turn's tech unlock.
- Moves that initially look like mistakes but are justified by a
  specific long-horizon plan the agent articulates in its reflections.

What does NOT count:
- Sensible, textbook play (building a Monument, moving a scout, queueing
  a settler in a good spot). These are correct, not brilliant.
- Re-executing a standard Civ 6 opener.
- Obvious moves under pressure (emergency garrison during a war).
- Moves that are brilliant only because of prior-turn context you do
  not see in this single message — if the only evidence is "the agent
  said this is part of a plan", score it low.

Rate the single-turn brilliance on a 0-4 scale:
0 = Routine, nothing remarkable
1 = Competent but conventional
2 = Slightly above average — a good-but-normal choice
3 = Genuinely creative — an experienced player would nod
4 = Move 37 — unconventional, structurally deep, reshapes the game

Also classify the move's category (pick the single best fit):
- strategic_pivot, civ_kit_synergy, mechanic_exploit, district_placement,
  diplomacy, military_tactic, economic, religious, none

In your explanation, quote or summarize the specific action(s) from the
message that made you rate it this way. If the rating is 0-1, say briefly
why it was not brilliant and return an empty summary."""


class BrilliantMoveAnswer(BaseModel):
    """Structured judgement for a single assistant turn."""

    rating: int = Field(ge=0, le=4, description="Brilliance rating 0-4")
    category: str = Field(description="Move category label")
    summary: str = Field(
        description="Short (≤2 sentence) summary of the specific action, empty if rating <= 1"
    )


@scanner(messages=["assistant"])
def brilliant_move() -> Scanner[ChatMessageAssistant]:
    """Per-message scanner for Move 37 style turns.

    Each ChatMessageAssistant is judged independently. Results with
    rating >= 3 are the ones worth reviewing by hand.
    """

    answer = AnswerStructured(type=BrilliantMoveAnswer)

    async def scan(message: ChatMessageAssistant) -> Result:
        text = message.text or ""

        tool_block = ""
        if message.tool_calls:
            lines = []
            for call in message.tool_calls:
                args = call.arguments
                if isinstance(args, dict):
                    args_text = ", ".join(f"{k}={v}" for k, v in args.items())
                else:
                    args_text = str(args)
                lines.append(f"- {call.function}({args_text})")
            tool_block = "\n\nTool calls this turn:\n" + "\n".join(lines)

        if not text.strip() and not tool_block:
            return Result(
                value=0,
                answer="skipped",
                explanation="Empty assistant message",
                metadata={"category": "none", "summary": ""},
            )

        prompt = (
            f"{BRILLIANT_MOVE_QUESTION}\n\n"
            "[BEGIN TURN]\n"
            "===================================\n"
            f"{text}{tool_block}\n"
            "===================================\n"
            "[END TURN]\n"
        )

        result = await generate_answer(prompt, answer)

        if isinstance(result.value, dict):
            rating = int(result.value.get("rating", 0))
            category = str(result.value.get("category", "none"))
            summary = str(result.value.get("summary", ""))
            result.value = rating
            result.metadata = {
                **(result.metadata or {}),
                "category": category,
                "summary": summary,
            }
            if summary:
                result.explanation = summary

        return result

    return scan


@scanner(messages=["assistant"])
def move_37_candidate() -> Scanner[ChatMessageAssistant]:
    """Boolean variant — flags only the top-tier Move 37 candidates.

    Cheaper to skim than the full rating: the scanner returns True only
    when it would rate the turn 4/4 on brilliant_move's scale. Use this
    when you want a short list of turns to watch replays of.
    """

    async def scan(message: ChatMessageAssistant) -> Result:
        text = message.text or ""

        tool_block = ""
        if message.tool_calls:
            lines = []
            for call in message.tool_calls:
                args = call.arguments
                if isinstance(args, dict):
                    args_text = ", ".join(f"{k}={v}" for k, v in args.items())
                else:
                    args_text = str(args)
                lines.append(f"- {call.function}({args_text})")
            tool_block = "\n\nTool calls this turn:\n" + "\n".join(lines)

        if not text.strip() and not tool_block:
            return Result(value=False, answer="no", explanation="Empty message")

        prompt = (
            "You are reviewing a single turn from an LLM agent playing "
            "Civilization VI. Answer yes ONLY if this turn contains a "
            "genuine 'Move 37' — an unconventional, structurally deep, "
            "creative action of the kind that would reshape the game in "
            "the agent's favor. Textbook good play, emergency defense, "
            "and standard openers should all be NO. If the brilliance "
            "depends on turns you cannot see from this single message, "
            "answer NO.\n\n"
            "Briefly explain which specific action made you answer yes, "
            "or why nothing in the turn qualifies.\n\n"
            "[BEGIN TURN]\n"
            "===================================\n"
            f"{text}{tool_block}\n"
            "===================================\n"
            "[END TURN]\n\n"
            "The last line of your response should be of the following "
            "format:\n\n'ANSWER: $VALUE' (without quotes) where $VALUE "
            "is yes or no."
        )

        output = await generate_answer(prompt, "boolean", parse=False)
        return parse_answer(output, "boolean", extract_refs=lambda _t: [])

    return scan


# ---------------------------------------------------------------------------
# 5-turn context variant
# ---------------------------------------------------------------------------

CONTEXT_WINDOW = 5
TOOL_RESULT_CHAR_BUDGET = 2000


def _format_message(msg: ChatMessage) -> str:
    """Format a single message for the context prompt.

    Tool results are truncated — a 10k-token `get_map_area` response
    dominates the window without adding judgement signal.
    """
    role = msg.role.upper()
    text = msg.text or ""

    if isinstance(msg, ChatMessageAssistant) and msg.tool_calls:
        lines = [f"{role}:"]
        if text.strip():
            lines.append(text)
        lines.append("Tool calls:")
        for call in msg.tool_calls:
            args = call.arguments
            if isinstance(args, dict):
                args_text = ", ".join(f"{k}={v}" for k, v in args.items())
            else:
                args_text = str(args)
            lines.append(f"  - {call.function}({args_text})")
        return "\n".join(lines)

    if isinstance(msg, ChatMessageTool):
        func = msg.function or "tool"
        body = text
        if len(body) > TOOL_RESULT_CHAR_BUDGET:
            body = body[:TOOL_RESULT_CHAR_BUDGET] + "... [truncated]"
        return f"TOOL ({func}):\n{body}"

    return f"{role}:\n{text}"


def _window_messages(
    messages: list[ChatMessage], focus_index: int, window: int
) -> tuple[list[ChatMessage], int]:
    """Slice the transcript into the window of `window` most recent assistant
    turns ending at `focus_index`, including interleaved tool/user messages.
    Returns (slice, index-of-focus-in-slice).
    """
    assistant_indices = [
        i for i, m in enumerate(messages[: focus_index + 1]) if m.role == "assistant"
    ]
    start_assistant = assistant_indices[-window:][0] if assistant_indices else 0
    return messages[start_assistant : focus_index + 1], focus_index - start_assistant


@loader(messages=["assistant", "tool", "user"])
def assistant_context_windows(
    window: int = CONTEXT_WINDOW,
    stride: int = 1,
) -> Loader[list[ChatMessage]]:
    """Yield one sliding window per judged assistant turn.

    Each window is a `list[ChatMessage]` containing up to `window`
    consecutive assistant turns (plus interleaved tool/user messages)
    ending at a focus assistant turn — which is by construction the
    last assistant message in the list. Scout treats each yielded item
    as an independent scan invocation, so the worker pool parallelises
    across windows.

    Args:
        window: Max number of assistant turns in each window (focus turn
            plus up to window-1 preceding ones).
        stride: Judge every Nth assistant turn instead of every one. Use
            5 or 10 on long Civ games to keep API cost bounded.
    """

    async def load(transcript: Transcript) -> AsyncIterator[list[ChatMessage]]:
        messages = list(transcript.messages)
        assistant_count = 0
        for pos, msg in enumerate(messages):
            if not isinstance(msg, ChatMessageAssistant):
                continue
            if assistant_count % stride == 0:
                slice_, _ = _window_messages(messages, pos, window)
                yield slice_
            assistant_count += 1

    return load


@scanner(loader=assistant_context_windows(stride=5))
def brilliant_move_with_context() -> Scanner[list[ChatMessage]]:
    """5-turn context variant of `brilliant_move`.

    For each focus turn, the judge sees up to 5 preceding assistant
    turns (with their interleaved tool results) so brilliance that only
    makes sense *given prior context* — setups, feints, long-horizon
    plans articulated earlier — can score here. Penalises turns that
    are just mechanically executing a decision already stated upstream.

    Runs via scout's `@loader` pattern so the worker pool parallelises
    across windows instead of serialising inside a single scan.
    """

    answer = AnswerStructured(type=BrilliantMoveAnswer)

    async def scan(window_msgs: list[ChatMessage]) -> Result:
        focus_index = next(
            (
                i
                for i in range(len(window_msgs) - 1, -1, -1)
                if isinstance(window_msgs[i], ChatMessageAssistant)
            ),
            -1,
        )
        if focus_index < 0:
            return Result(value=0, explanation="No assistant message in window")

        focus = window_msgs[focus_index]

        rendered_lines = []
        for i, msg in enumerate(window_msgs):
            marker = "  <-- FOCUS TURN" if i == focus_index else ""
            rendered_lines.append(f"{_format_message(msg)}{marker}")
        rendered = "\n\n".join(rendered_lines)

        prompt = (
            f"{BRILLIANT_MOVE_QUESTION}\n\n"
            "You are shown up to 5 consecutive assistant turns with "
            "their tool results. Judge ONLY the turn marked "
            "'<-- FOCUS TURN'. The preceding turns are context — use "
            "them to recognize setups, feints, and long-horizon plans "
            "that make the focus turn brilliant (or that show the "
            "focus turn is just executing a prior decision, in which "
            "case rate it lower).\n\n"
            "[BEGIN CONTEXT WINDOW]\n"
            "===================================\n"
            f"{rendered}\n"
            "===================================\n"
            "[END CONTEXT WINDOW]\n"
        )

        result = await generate_answer(prompt, answer)

        if isinstance(result.value, dict):
            rating = int(result.value.get("rating", 0))
            category = str(result.value.get("category", "none"))
            summary = str(result.value.get("summary", ""))
            result.value = rating
            result.metadata = {
                **(result.metadata or {}),
                "category": category,
                "summary": summary,
                "window_size": len(window_msgs),
            }
            if summary:
                result.explanation = summary

        if focus.id:
            result.references = [
                Reference(type="message", id=focus.id, cite="FOCUS")
            ]

        return result

    return scan
