"""Decision quality scanners — LLM analysis of strategic reasoning."""
from inspect_scout import Scanner, Transcript, llm_scanner, scanner


@scanner(messages="all")
def civ_kit_alignment() -> Scanner[Transcript]:
    """Rate 1-5 whether the agent leverages its civilization's unique abilities."""
    return llm_scanner(
        question="""\
This is a Civilization VI game transcript. Assess whether the agent
leverages its civilization's unique units, buildings, and abilities.

Examples:
- Babylon should trigger eurekas aggressively
- Kongo should build Theater Squares and Mbanza, not prioritize Campuses
- Sumeria should use War Carts early
- Korea should prioritize Seowon (unique Campus)
- Rome should leverage free monuments and roads

Did the agent's build orders and research path align with its
civilization's strengths? Rate 1-5:
1 = Completely ignored civ kit
3 = Partially used civ kit
5 = Excellent civ kit exploitation""",
        answer="number",
    )


@scanner(messages="all")
def victory_path_coherence() -> Scanner[Transcript]:
    """Assess whether build/research choices consistently support a victory path."""
    return llm_scanner(
        question="""\
Analyze this Civilization VI transcript for victory path coherence.

A coherent strategy maintains a consistent victory path (Science,
Culture, Domination, Religious, Diplomatic) through district choices,
research priorities, and military/civilian balance.

Signs of incoherence:
- Building Campuses but never starting space projects
- Building Holy Sites but never buying religious units
- Changing victory path mid-game without strategic reason
- Building districts that don't support any victory condition

What victory path is the agent pursuing and do its actions
consistently support it?""",
        answer="string",
    )
