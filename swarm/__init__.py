"""Layer 4: Autonomous Multi-Agent Swarm package."""

from swarm.base import BaseSpecialistAgent
from swarm.researcher import researcher
from swarm.coder import coder
from swarm.reviewer import reviewer
from swarm.orchestrator import swarm

__all__ = ["BaseSpecialistAgent", "researcher", "coder", "reviewer", "swarm"]
