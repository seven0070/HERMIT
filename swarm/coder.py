"""Multi-Model & Multi-Modal Software Engineering Agent."""

from typing import Optional
from swarm.base import BaseSpecialistAgent
from mcp_hub.client import mcp_hub
from gateway.router import gateway

class MultiModelCoderAgent(BaseSpecialistAgent):
    """Staff engineer supporting multi-model routing and multimodal vision analysis."""

    def __init__(self):
        super().__init__(
            name="MultiModelCoder",
            role="Staff Software Engineer & Multimodal Code Architect",
            expertise="Polyglot coding, architecture, multimodal UI-to-code, debugging across model tiers",
            system_instructions=(
                "You are an elite Staff Software Engineer in an autonomous swarm. "
                "Write clean, modular, production-ready code with defensive error handling. "
                "Output complete runnable code blocks without placeholders."
            )
        )

    async def execute(self, task: str, context: Optional[str] = None, model: Optional[str] = None, image_url: Optional[str] = None) -> str:
        # Augment with local workspace snapshot if relevant
        mcp_context = ""
        lower = task.lower()
        if any(w in lower for w in ["file", "dir", "code", "repo", "tree"]):
            mcp_context = mcp_hub.execute_tool("filesystem", "list_directory", {"path": "."})

        full_prompt = f"### TASK:\n{task}\n"
        if image_url:
            full_prompt += f"\n[Multimodal Vision Input]: Diagram/Image URL: {image_url}\n"
        if mcp_context:
            full_prompt += f"\n[Local Workspace Tree]:\n{mcp_context}\n"
        if context:
            full_prompt += f"\n[Context]:\n{context}\n"

        # Dispatch via Universal Gateway with optional targeted model override
        kwargs = {"model": model} if model else {}
        resp = await gateway.complete(
            prompt=full_prompt,
            system_instruction=self.system_instructions,
            **kwargs
        )
        return resp.text.strip()

coder = MultiModelCoderAgent()
