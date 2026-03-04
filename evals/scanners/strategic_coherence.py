"""Strategic coherence scanner — threat detection and response."""
from inspect_scout import Scanner, Transcript, llm_scanner, scanner


@scanner(messages="all")
def threat_response() -> Scanner[Transcript]:
    """Rate 1-5 how quickly the agent detects and responds to the primary threat."""
    return llm_scanner(
        question="""\
This Civilization VI transcript is from a benchmark scenario designed
to test specific blind spots. Analyze whether:

1. The agent discovered the primary threat (religious victory push,
   military invasion, rival science lead, etc.)
2. How quickly it responded after discovery
3. Whether the response was appropriate and sufficient

Rate the agent's threat response 1-5:
1 = Never detected the threat
2 = Detected late, inadequate response
3 = Detected with moderate delay, partial response
4 = Detected reasonably quickly, good response
5 = Early detection, strong proactive response""",
        answer="number",
    )
