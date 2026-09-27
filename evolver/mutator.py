"""Prompt and skill mutator for self-evolving agents."""

from typing import List, Dict, Any
from evolver.evaluator import EvaluationReport
from gateway.router import gateway

MUTATION_PROMPT = """You are an expert AI Prompt & Agent Architecture Optimizer.
Analyze the following agent evaluation report and current instructions, then produce ONE targeted, surgical improvement.

### CURRENT SYSTEM INSTRUCTIONS:
{current_instructions}

### EVALUATION ISSUES DETECTED:
{issues}

### RECOMMENDED STRATEGY:
{strategy}

### RULES:
1. Make surgical, concise changes (do not bloat the prompt).
2. Clearly solve the root cause identified in the issues.
3. Return the entire improved system instructions, ready to deploy.
"""

class AgentMutator:
    """Applies surgical prompt mutations based on diagnosed failure modes."""

    async def mutate_instructions(
        self,
        current_instructions: str,
        report: EvaluationReport
    ) -> str:
        if report.passed:
            return current_instructions

        formatted_issues = "\n".join(f"- {i}" for i in report.issues)
        prompt = MUTATION_PROMPT.format(
            current_instructions=current_instructions,
            issues=formatted_issues,
            strategy=report.recommended_strategy
        )

        try:
            # Use Layer 2 Universal Gateway to perform the self-evolution rewrite
            response = await gateway.complete(
                prompt=prompt,
                system_instruction="You are an autonomous AI Agent System Mutator that specializes in optimizing agent instructions."
            )
            return response.text.strip()
        except Exception as e:
            # Fallback local mutation rule if all external models are unreachable
            fallback_rule = f"\n\n### SELF-EVOLVED RULE ({report.recommended_strategy}):\n"
            for issue in report.issues:
                fallback_rule += f"- Address issue: {issue}\n"
            return current_instructions + fallback_rule

mutator = AgentMutator()
