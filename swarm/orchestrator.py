"""Swarm Orchestrator: Coordinates multi-agent collaboration and delegation."""

import asyncio
from typing import Dict, Any, List, Optional
from swarm.researcher import researcher
from swarm.coder import coder
from swarm.reviewer import reviewer

class SwarmOrchestrator:
    """Orchestrates specialist agents in autonomous pipelines or direct delegation."""

    def list_specialists(self) -> str:
        """Returns overview of available specialist agents."""
        return (
            f"1. Research Specialist ({researcher.role}): {researcher.expertise}\n"
            f"2. Software Engineer ({coder.role}): {coder.expertise}\n"
            f"3. QA Reviewer ({reviewer.role}): {reviewer.expertise}"
        )

    async def dispatch(self, domain: str, task_details: str, context: Optional[str] = None) -> str:
        """Dispatches a task to a single specialist agent based on domain keyword."""
        d = domain.strip().lower()
        agent = coder if ("code" in d or "eng" in d) else reviewer if ("rev" in d or "qa" in d) else researcher
        result = await agent.execute(task=task_details, context=context)
        return (
            f"=== [{agent.name.upper()} REPORT] ===\n"
            f"Role: {agent.role}\n\n"
            f"{result}\n"
            f"======================================"
        )

    async def run_collaborative_workflow(self, objective: str) -> str:
        """Runs a 3-stage collaborative workflow:
        1. Researcher investigates context and requirements.
        2. Coder designs and drafts technical implementation.
        3. Reviewer verifies accuracy, edge cases, and approves.
        """
        output_log = [f"=== SWARM WORKFLOW INITIATED ===", f"Objective: {objective}\n"]

        # Stage 1: Research
        output_log.append("[Stage 1/3] Research Specialist investigating...")
        research_notes = await researcher.execute(
            task=f"Investigate and extract key requirements, best practices, and risks for: {objective}"
        )
        output_log.append(f"[+] Research complete.\n")

        # Stage 2: Engineering
        output_log.append("[Stage 2/3] Coder Specialist engineering solution...")
        code_solution = await coder.execute(
            task=f"Design and engineer the implementation for: {objective}",
            context=f"Research Findings:\n{research_notes}"
        )
        output_log.append(f"[+] Engineering solution drafted.\n")

        # Stage 3: Review & Critique
        output_log.append("[Stage 3/3] Reviewer Specialist auditing solution...")
        critique = await reviewer.execute(
            task=f"Audit this proposed solution for errors, edge cases, and quality score:\n{code_solution}",
            context=f"Original Objective: {objective}"
        )
        output_log.append(f"[+] Review complete.\n")

        output_log.append("=== FINAL SYNTHESIZED DELIVERABLE ===")
        output_log.append(f"### IMPLEMENTATION:\n{code_solution}\n")
        output_log.append(f"### QA AUDIT & SCORE:\n{critique}")

        return "\n".join(output_log)

swarm = SwarmOrchestrator()
