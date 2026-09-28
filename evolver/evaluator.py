"""Evaluator for diagnosing agent failures and optimization opportunities.

Trigger design: evolution fires on REAL failure signals only, never on
keyword coincidence. A user asking "search the logs for error codes" must
not mutate the agent. The signals below are deliberately narrow:

1. Tool execution errors that actually happened this turn.
2. Explicit user feedback phrases directed at the agent's previous reply
   (full phrases, not bare substrings like "error" or "failed").
3. The agent's own output showing a refusal, an empty answer, or the
   tool-loop cap being hit.
"""

from typing import List, Optional
from dataclasses import dataclass, field

# Full-phrase feedback signals. Bare words like "error"/"failed" are NOT here
# on purpose: they appear in ordinary requests ("check for errors in...").
NEGATIVE_FEEDBACK_PHRASES = [
    "that's wrong", "thats wrong", "that is wrong",
    "not what i asked", "you forgot", "you missed",
    "wrong answer", "that's incorrect", "thats incorrect",
    "still broken", "try again", "you didn't do", "you did not do",
    "that didn't work", "that did not work", "stop hallucinating",
]

REFUSAL_MARKERS = [
    "as an ai model", "as an ai language model", "i cannot assist with that",
]

LOOP_CAP_MARKER = "[Note: tool-call round limit reached]"
TOOL_ERROR_MARKER = "[TOOL ERROR]"

@dataclass
class EvaluationReport:
    score: float  # 0.0 to 1.0
    passed: bool
    issues: List[str]
    recommended_strategy: str
    signals: List[str] = field(default_factory=list)  # which signal classes fired

    def issue_signature(self) -> str:
        """Stable signature used to detect repeat failures on the same issue."""
        return "|".join(sorted(set(self.signals)))

class AgentEvaluator:
    """Evaluates agent execution runs and identifies failure patterns."""

    def evaluate_turn(
        self,
        user_input: str,
        agent_output: str,
        tool_errors: Optional[List[str]] = None,
    ) -> EvaluationReport:
        issues: List[str] = []
        signals: List[str] = []
        tool_errors = tool_errors or []
        user_lower = user_input.lower()
        output_lower = (agent_output or "").lower()

        # 1. Real tool execution failures observed this turn.
        real_errors = [e for e in tool_errors if e]
        if real_errors:
            signals.append("tool_error")
            for err in real_errors[:3]:
                issues.append(f"Tool execution failure: {err}")

        # 2. Explicit user feedback about the previous reply.
        matched = [p for p in NEGATIVE_FEEDBACK_PHRASES if p in user_lower]
        if matched:
            signals.append("negative_feedback")
            issues.append(
                f"User flagged dissatisfaction with the previous reply "
                f"({', '.join(matched[:2])}): '{user_input[:120]}'"
            )

        # 3. Refusal / generic disclaimer in the agent's own output.
        if any(m in output_lower for m in REFUSAL_MARKERS):
            signals.append("refusal")
            issues.append("Unhelpful refusal or generic disclaimer detected in the reply.")

        # 4. Tool-loop cap hit: the agent ran out of rounds mid-task.
        if LOOP_CAP_MARKER.lower() in output_lower:
            signals.append("loop_cap")
            issues.append("Agent hit the tool-call round limit before finishing the task.")

        # 5. Empty or whitespace reply to a non-empty request.
        if user_input.strip() and not (agent_output or "").strip():
            signals.append("empty_reply")
            issues.append("Agent returned an empty reply to a non-empty request.")

        # Strategy selection follows the strongest signal.
        if "tool_error" in signals:
            strategy = "add_tool_calling_constraint"
        elif "negative_feedback" in signals:
            strategy = "add_few_shot_example"
        elif "loop_cap" in signals:
            strategy = "add_tool_calling_constraint"
        elif signals:
            strategy = "restructure_instructions"
        else:
            strategy = "maintain"

        score = max(0.0, 1.0 - (len(issues) * 0.35))
        passed = len(issues) == 0

        return EvaluationReport(
            score=round(score, 2),
            passed=passed,
            issues=issues,
            recommended_strategy=strategy,
            signals=signals,
        )

evaluator = AgentEvaluator()
