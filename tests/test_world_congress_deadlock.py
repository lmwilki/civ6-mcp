"""Tests for World Congress end-turn deadlock and the end_turn in-flight guard.

Two failure modes are covered:

1. World Congress screens hold the end-turn lock. The "hide the congress UI"
   Lua existed in four separate copies that had drifted apart -- three hid
   only WorldCongressIntro/Popup while a fourth knew about three more
   full-screen contexts. Whichever screen was left up kept blocking, and
   end_turn looped forever.

2. `_pending_end_turn` latches True when an end_turn call is aborted
   (killed task, client timeout, dropped connection). Every later call then
   refuses to send ACTION_ENDTURN and polls a request the game never
   received -- a permanent hang with no recovery path.
"""

from unittest.mock import MagicMock

from civ_mcp.end_turn import STALE_PENDING_SECS, should_resend_end_turn
from civ_mcp.game_state import GameState
from civ_mcp.lua.congress import (
    WORLD_CONGRESS_CONTEXTS,
    build_congress_submit,
    build_world_congress_dismiss,
    parse_world_congress_dismiss,
)
from civ_mcp.lua.notifications import BLOCKING_TOOL_MAP


# ---------------------------------------------------------------------------
# All World Congress screens must be hidden, everywhere
# ---------------------------------------------------------------------------


class TestCongressScreenCoverage:
    def test_context_list_covers_known_blocking_screens(self):
        for name in (
            "WorldCongressPopup",
            "WorldCongressIntro",
            "WorldCongressBetweenTurns",
            "WorldCongressResults",
            "WorldCongressProposals",
        ):
            assert name in WORLD_CONGRESS_CONTEXTS

    def test_dismiss_query_hides_every_context(self):
        lua = build_world_congress_dismiss()
        for name in WORLD_CONGRESS_CONTEXTS:
            assert name in lua, f"{name} not hidden by dismiss query"

    def test_dismiss_query_dequeues_popup(self):
        """SetHide alone leaves the popup queued in UIManager."""
        assert "DequeuePopup" in build_world_congress_dismiss()

    def test_submit_query_hides_every_context(self):
        """Regression: build_congress_submit was the fourth drifted copy and
        hid only two of the five screens."""
        lua = build_congress_submit()
        for name in WORLD_CONGRESS_CONTEXTS:
            assert name in lua, f"{name} not hidden by submit query"

    def test_scoped_dismiss_filters_to_one_blocker_type(self):
        lua = build_world_congress_dismiss(
            only_type="ENDTURN_BLOCKING_WORLD_CONGRESS_LOOK"
        )
        assert "ENDTURN_BLOCKING_WORLD_CONGRESS_LOOK" in lua

    def test_unscoped_dismiss_matches_any_world_congress_blocker(self):
        lua = build_world_congress_dismiss()
        assert 'k:find("WORLD_CONGRESS")' in lua

    def test_emits_machine_readable_counts(self):
        assert "WC_DISMISSED|" in build_world_congress_dismiss()

    def test_dismiss_popup_covers_every_context(self):
        """dismiss_popup's Phase 1 list was the fifth drifted copy — it named
        only Popup/Intro, so a turn stuck behind the Results screen survived
        a dismiss_popup() call."""
        import inspect

        from civ_mcp import game_lifecycle

        src = inspect.getsource(game_lifecycle.dismiss_popup)
        assert "WORLD_CONGRESS_CONTEXTS" in src


class TestParseDismiss:
    def test_parses_counts(self):
        assert parse_world_congress_dismiss(["WC_DISMISSED|2|3"]) == (2, 3)

    def test_missing_line_returns_zeros(self):
        assert parse_world_congress_dismiss(["something else"]) == (0, 0)

    def test_malformed_line_returns_zeros(self):
        assert parse_world_congress_dismiss(["WC_DISMISSED|x|y"]) == (0, 0)


# ---------------------------------------------------------------------------
# The agent must be told the remedy exists
# ---------------------------------------------------------------------------


class TestBlockerHint:
    def test_session_blocker_mentions_advance_tool(self):
        """The session blocker is deliberately never auto-resolved, so the
        hint is the only way an agent learns advance_world_congress exists.
        Without it the agent just calls end_turn() again and loops."""
        hint = BLOCKING_TOOL_MAP["ENDTURN_BLOCKING_WORLD_CONGRESS_SESSION"]
        assert "queue_wc_votes" in hint
        assert "advance_world_congress" in hint


# ---------------------------------------------------------------------------
# end_turn in-flight guard
# ---------------------------------------------------------------------------


class TestShouldResendEndTurn:
    def test_sends_when_nothing_pending(self):
        resend, _ = should_resend_end_turn(
            pending=False, pending_from=None, pending_at=0.0, turn_before=100, now=50.0
        )
        assert resend is True

    def test_suppresses_genuine_in_flight_request(self):
        """Double-sending ACTION_ENDTURN makes turns skip (412 -> 415)."""
        resend, reason = should_resend_end_turn(
            pending=True, pending_from=100, pending_at=100.0, turn_before=100, now=102.0
        )
        assert resend is False
        assert "flight" in reason.lower()

    def test_resends_when_pending_flag_is_stale(self):
        """The aborted-call case: flag stuck True, turn never moved."""
        resend, reason = should_resend_end_turn(
            pending=True,
            pending_from=100,
            pending_at=100.0,
            turn_before=100,
            now=100.0 + STALE_PENDING_SECS + 1,
        )
        assert resend is True
        assert "stale" in reason.lower()

    def test_resends_when_turn_already_advanced_past_baseline(self):
        """The previous request completed; this is a fresh turn."""
        resend, reason = should_resend_end_turn(
            pending=True, pending_from=100, pending_at=100.0, turn_before=101, now=101.0
        )
        assert resend is True
        assert "completed" in reason.lower()

    def test_stale_threshold_is_generous_enough_to_keep_double_send_guard(self):
        """The double-send hazard only exists for a few seconds after the
        original request, so the threshold must be well above that."""
        assert STALE_PENDING_SECS >= 15.0

    def test_unknown_baseline_does_not_wedge_forever(self):
        resend, _ = should_resend_end_turn(
            pending=True,
            pending_from=None,
            pending_at=0.0,
            turn_before=None,
            now=STALE_PENDING_SECS + 1,
        )
        assert resend is True


# ---------------------------------------------------------------------------
# GameState pending-flag invariant
# ---------------------------------------------------------------------------


class TestPendingFlagInvariant:
    def _gs(self) -> GameState:
        return GameState(MagicMock())

    def test_declared_wc_blocker_fields(self):
        """server.py reads these; they were only ever set dynamically."""
        gs = self._gs()
        assert gs._wc_blocker_turn == -1
        assert gs._wc_blocker_count == 0

    def test_mark_sets_all_three_fields_together(self):
        gs = self._gs()
        gs.mark_pending_end_turn(turn=137, now=1234.0)
        assert gs._pending_end_turn is True
        assert gs._pending_end_turn_from == 137
        assert gs._pending_end_turn_at == 1234.0

    def test_clear_resets_all_three_fields_together(self):
        """The timestamp used to be left behind on every clear path. Harmless
        today only because one call site sets it; a second would inherit a
        stale timestamp and mis-classify a fresh request as stale."""
        gs = self._gs()
        gs.mark_pending_end_turn(turn=137, now=1234.0)
        gs.clear_pending_end_turn()
        assert gs._pending_end_turn is False
        assert gs._pending_end_turn_from is None
        assert gs._pending_end_turn_at == 0.0
