"""Evaluator for diagnosing agent failures and optimization opportunities."""

from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class EvaluationReport:
    score: float  # 0.0 to 1.0
    passed: bool
    issues: List[str]
    recommended_strategy: str

class AgentEvaluator:
    """Evaluates agent execution runs and identifies failure patterns."""

    def evaluate_turn(self, user_input: str, agent_output: str, tool_errors: List[str] = None) -> EvaluationReport:
        issues = []
        tool_errors = tool_errors or []

        # 1. Tool execution failures
        if tool_errors:
            for err in tool_errors:
                issues.append(f"Tool execution failure: {err}")

        # 2. Negative user feedback detection
        negative_signals = ["that's wrong", "incorrect", "you forgot", "not what i asked", "failed", "error"]
        if any(sig in user_input.lower() for sig in negative_signals):
            issues.append(f"User flagged dissatisfaction or correction: '{user_input}'")

        # 3. Model refusal / repetition checks
        if "as an ai model" in agent_output.lower() or "i cannot assist" in agent_output.lower():
            issues.append("Unhelpful refusal or generic disclaimer detected.")

        # Determine strategy
        if tool_errors:
            strategy = "add_tool_calling_constraint"
        elif any(sig in user_input.lower() for sig in negative_signals):
            strategy = "add_few_shot_example"
        elif len(issues) > 0:
            strategy = "restructure_instructions"
        else:
            strategy = "maintain"

        # Calculate score
        score = max(0.0, 1.0 - (len(issues) * 0.35))
        passed = len(issues) == 0

        return EvaluationReport(
            score=round(score, 2),
            passed=passed,
            issues=issues,
            recommended_strategy=strategy
        )

evaluator = AgentEvaluator()
