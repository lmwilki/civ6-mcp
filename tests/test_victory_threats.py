"""Tests for rival victory threat detection.

Regression coverage for the T337 loss: a rival won a Culture victory while
`get_victory_progress` reported Culture at "15% viability" and `end_turn`'s
victory scan emitted nothing at all. Both surfaces only ever described *our*
offense toward culture victory and had no defensive data path.
"""

from civ_mcp.end_turn import victory_events_from_lines
from civ_mcp.lua.models import SpaceProject, VictoryPlayerProgress, VictoryProgress
from civ_mcp.lua.victory import parse_victory_progress_response
from civ_mcp.narrate import narrate_victory_progress


def _player(name: str, pid: int = 0, **kw) -> VictoryPlayerProgress:
    base = dict(
        player_id=pid,
        name=name,
        score=800,
        science_vp=0,
        science_vp_needed=50,
        diplomatic_vp=5,
        tourism=10,
        military_strength=500,
        techs_researched=61,
        civics_completed=36,
        religion_cities=0,
    )
    base.update(kw)
    return VictoryPlayerProgress(**base)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# CULTURE line now carries the defensive direction
# ---------------------------------------------------------------------------


class TestCultureDefensiveParsing:
    def test_parses_defensive_fields(self):
        lines = ["CULTURE|Khmer|3|511|false|350|true"]
        vp = parse_victory_progress_response(lines)
        # offense (unchanged)
        assert vp.our_tourists_from["Khmer"] == 3
        assert vp.their_staycationers["Khmer"] == 511
        # defense (new)
        assert vp.their_tourists_from_us["Khmer"] == 350
        assert vp.they_dominate_us["Khmer"] is True

    def test_legacy_line_without_defensive_fields_still_parses(self):
        """Older Lua payloads must not crash the parser."""
        lines = ["CULTURE|Khmer|3|511|false"]
        vp = parse_victory_progress_response(lines)
        assert vp.our_tourists_from["Khmer"] == 3
        assert vp.their_tourists_from_us == {}
        assert vp.they_dominate_us == {}


# ---------------------------------------------------------------------------
# narrate_victory_progress surfaces the threat
# ---------------------------------------------------------------------------


class TestNarrateCultureThreat:
    def _vp(self, **kw) -> VictoryProgress:
        base = dict(
            players=[_player("Australia", 0, staycationers=260, culture_yield=111.0)],
            our_tourists_from={"Khmer": 3},
            their_staycationers={"Khmer": 511},
            enabled_victories={"VICTORY_CULTURE"},
        )
        base.update(kw)
        return VictoryProgress(**base)  # type: ignore[arg-type]

    def test_dominant_rival_is_flagged_critical(self):
        vp = self._vp(
            their_tourists_from_us={"Khmer": 350},
            they_dominate_us={"Khmer": True},
        )
        out = narrate_victory_progress(vp)
        assert "!!!" in out
        assert "Khmer" in out
        # the raw numbers must be visible, not just a verdict
        assert "350" in out and "260" in out

    def test_approaching_rival_is_flagged(self):
        vp = self._vp(
            their_tourists_from_us={"Khmer": 210},  # 210/260 = 81%
            they_dominate_us={"Khmer": False},
        )
        out = narrate_victory_progress(vp)
        assert "THREAT" in out

    def test_harmless_rival_not_flagged_as_threat(self):
        vp = self._vp(
            their_tourists_from_us={"Khmer": 10},
            they_dominate_us={"Khmer": False},
        )
        out = narrate_victory_progress(vp)
        assert "CULTURE VICTORY THREAT" not in out

    def test_defense_shown_even_though_our_offense_looks_hopeless(self):
        """The exact T337 shape: our offense is 3/511 (hopeless) while their
        offense against us is nearly complete. The old output showed only the
        former and read as 'no threat'."""
        vp = self._vp(
            their_tourists_from_us={"Khmer": 350},
            they_dominate_us={"Khmer": True},
        )
        out = narrate_victory_progress(vp)
        threat_section = out.split("CULTURE")[1]
        assert "THEM -> US" in threat_section


# ---------------------------------------------------------------------------
# end_turn per-turn victory scan
# ---------------------------------------------------------------------------


class TestVictoryProximityCultureEvents:
    def test_dominant_rival_emits_priority_1(self):
        lines = [
            "VENABLED|VICTORY_CULTURE",
            "CUL_THREAT|Khmer|350|260|true|482.0|111.0",
        ]
        events = victory_events_from_lines(lines)
        cul = [e for e in events if "CULTURE" in e.message.upper()]
        assert cul, "expected a culture threat event"
        assert cul[0].priority == 1
        assert "IMMINENT" in cul[0].message

    def test_approaching_rival_emits_threat(self):
        lines = [
            "VENABLED|VICTORY_CULTURE",
            "CUL_THREAT|Khmer|200|260|false|482.0|111.0",
        ]
        events = victory_events_from_lines(lines)
        assert any(
            "CULTURE VICTORY THREAT" in e.message and e.priority == 1 for e in events
        )

    def test_culture_output_gap_warns_early(self):
        """The leading indicator: tourists are still low, but their culture
        output is >=2x ours. This is the signal that existed for dozens of
        turns before the T337 loss and was never surfaced."""
        lines = [
            "VENABLED|VICTORY_CULTURE",
            "CUL_THREAT|Khmer|20|260|false|482.0|111.0",
        ]
        events = victory_events_from_lines(lines)
        assert any("culture output" in e.message.lower() for e in events)

    def test_no_warning_when_culture_victory_disabled(self):
        lines = [
            "VENABLED|VICTORY_TECHNOLOGY",
            "CUL_THREAT|Khmer|350|260|true|482.0|111.0",
        ]
        events = victory_events_from_lines(lines)
        assert not [e for e in events if "CULTURE" in e.message.upper()]

    def test_benign_rival_emits_nothing(self):
        lines = [
            "VENABLED|VICTORY_CULTURE",
            "CUL_THREAT|Canada|5|260|false|61.0|111.0",
        ]
        events = victory_events_from_lines(lines)
        assert events == []

    def test_existing_diplomatic_scan_still_works(self):
        lines = ["VENABLED|VICTORY_DIPLOMATIC", "DIPLO_THREAT|Aztec|14"]
        events = victory_events_from_lines(lines)
        assert any("14/20 DVP" in e.message for e in events)


# ---------------------------------------------------------------------------
# Space project completion must not depend on the science-VP counter
# ---------------------------------------------------------------------------


class TestSpaceProjectStatusRendering:
    def test_completed_project_has_no_misleading_hint(self):
        """A launched project used to render as [UNLOCKED] with the hint
        'need to complete prior projects first or build a Spaceport', because
        completion was inferred from GetScienceVictoryPoints() which reads 0.
        """
        vp = VictoryProgress(
            players=[_player("Australia", 0, spaceports=4)],
            space_projects=[
                SpaceProject(
                    project_type="PROJECT_LAUNCH_EARTH_SATELLITE",
                    name="Launch Earth Satellite",
                    status="completed",
                    progress_pct=0,
                    turns_remaining=0,
                    cost=900,
                    tech_prereq="TECH_ROCKETRY",
                    has_tech=True,
                    city_name="",
                )
            ],
            enabled_victories={"VICTORY_TECHNOLOGY"},
        )
        out = narrate_victory_progress(vp)
        assert "[DONE]" in out
        assert "need to complete prior projects" not in out

    def test_unlocked_hint_mentions_spaceport_only_when_relevant(self):
        vp = VictoryProgress(
            players=[_player("Australia", 0, spaceports=0)],
            space_projects=[
                SpaceProject(
                    project_type="PROJECT_LAUNCH_EARTH_SATELLITE",
                    name="Launch Earth Satellite",
                    status="unlocked",
                    progress_pct=0,
                    turns_remaining=0,
                    cost=900,
                    tech_prereq="TECH_ROCKETRY",
                    has_tech=True,
                    city_name="",
                )
            ],
            enabled_victories={"VICTORY_TECHNOLOGY"},
        )
        out = narrate_victory_progress(vp)
        assert "Spaceport" in out
