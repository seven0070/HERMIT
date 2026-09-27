"""Research & Analysis Specialist Agent."""

from swarm.base import BaseSpecialistAgent
from rag.retriever import search_knowledge_base

class ResearcherAgent(BaseSpecialistAgent):
    """Deep research, synthesis, and domain fact-checking specialist."""

    def __init__(self):
        super().__init__(
            name="ResearchSpecialist",
            role="Lead Analyst & Information Synthesizer",
            expertise="Deep research, comparative analysis, factual synthesis, knowledge retrieval",
            system_instructions=(
                "You are an elite Research Specialist agent in an autonomous multi-agent swarm. "
                "Your objective is to provide deeply structured, evidence-backed, and exhaustive answers. "
                "When provided with knowledge base context, cite key details accurately. "
                "Structure your output with: Executive Summary, Key Findings, In-Depth Analysis, and Recommendations."
            )
        )

    async def execute(self, task: str, context: str = None) -> str:
        # Augment with RAG search automatically if query relates to knowledge base
        rag_context = search_knowledge_base(task, top_k=4)
        full_context = ""
        if "No relevant documents" not in rag_context and "empty" not in rag_context:
            full_context = f"[Knowledge Base Citations]:\n{rag_context}\n\n"
        if context:
            full_context += f"[Task Context]:\n{context}"

        return await super().execute(task, context=full_context.strip() or None)

researcher = ResearcherAgent()
