"""Prompt mutator for self-evolving agents.

The mutator no longer rewrites the entire system prompt. It produces a short
overlay of operating rules (markdown bullets) that address the diagnosed
issues. The overlay is persisted by the engine and injected on top of the
fresh base prompt on every start, so evolved behavior survives restarts
without freezing the rest of the prompt (memory block, tool list, ...).
"""

from typing import List
from evolver.evaluator import EvaluationReport
from gateway.router import gateway

MUTATION_PROMPT = """You are an expert AI Agent Behavior Optimizer.
An agent evaluation detected real failures. Write or refine the agent's
EVOLVED OPERATING RULES: a short markdown bullet list of behavioral rules
that prevent these failures from happening again.

### EXISTING EVOLVED RULES (refine, keep what still applies):
{existing_rules}

### ISSUES DETECTED (real signals from the last run):
{issues}

### RECOMMENDED STRATEGY:
{strategy}

### RULES:
1. Output ONLY the bullet list of operating rules (markdown "- " bullets, no headers, no commentary).
2. Be surgical: 1 rule per root cause, max 6 rules total. No bloat.
3. Rules must be actionable instructions to the agent (e.g. "Always verify X before Y").
4. Merge with the existing rules instead of duplicating them.
"""

class AgentMutator:
    """Produces surgical operating-rule mutations from diagnosed failure modes."""

    async def mutate_rules(
        self,
        existing_rules: str,
        report: EvaluationReport
    ) -> str:
        """Returns the refined operating-rules overlay (markdown bullets)."""
        if report.passed:
            return existing_rules

        formatted_issues = "\n".join(f"- {i}" for i in report.issues)
        prompt = MUTATION_PROMPT.format(
            existing_rules=existing_rules.strip() or "(none yet)",
            issues=formatted_issues,
            strategy=report.recommended_strategy,
        )

        try:
            response = await gateway.complete(
                prompt=prompt,
                system_instruction="You are an autonomous AI Agent System Mutator that specializes in concise behavioral rules."
            )
            rules = response.text.strip()
            if rules:
                return rules
        except Exception:
            pass

        # Offline fallback: append deterministic rules for the new issues.
        lines = [existing_rules.strip()] if existing_rules.strip() else []
        for issue in report.issues:
            lines.append(f"- Address this observed failure: {issue}")
        return "\n".join(lines)

    async def mutate_instructions(
        self,
        current_instructions: str,
        report: EvaluationReport
    ) -> str:
        """Backwards-compatible wrapper: returns base instructions + overlay."""
        existing = self._extract_overlay(current_instructions)
        base = current_instructions[: len(current_instructions) - len(existing)].rstrip() if existing else current_instructions
        rules = await self.mutate_rules(existing, report)
        if not rules.strip():
            return current_instructions
        return base.rstrip() + "\n\n" + rules_block(rules)

    @staticmethod
    def _extract_overlay(instructions: str) -> str:
        marker = "### SELF-EVOLVED OPERATING RULES"
        idx = instructions.find(marker)
        if idx == -1:
            return ""
        return instructions[idx:]

def rules_block(rules: str) -> str:
    """Wraps raw rules markdown in the prompt section the base prompt injects."""
    return (
        "### SELF-EVOLVED OPERATING RULES (learned from real failures, persist across restarts):\n"
        + rules.strip()
    )

mutator = AgentMutator()
