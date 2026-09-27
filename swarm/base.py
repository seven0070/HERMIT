"""Base class for Autonomous Specialist Agents in Layer 4 Swarm."""

from typing import Dict, Any, Optional
from gateway.router import gateway
from gateway.providers import GatewayResponse

class BaseSpecialistAgent:
    """Specialist subagent with distinct persona, goals, and domain tools."""

    def __init__(self, name: str, role: str, expertise: str, system_instructions: str):
        self.name = name
        self.role = role
        self.expertise = expertise
        self.system_instructions = system_instructions

    async def execute(self, task: str, context: Optional[str] = None) -> str:
        """Executes a domain-specific task using the Universal Gateway."""
        prompt = f"### TASK ASSIGNED TO {self.name.upper()} ({self.role}):\n{task}"
        if context:
            prompt += f"\n\n### ADDITIONAL CONTEXT:\n{context}"

        response: GatewayResponse = await gateway.complete(
            prompt=prompt,
            system_instruction=self.system_instructions
        )
        return response.text.strip()
