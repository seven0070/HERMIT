"""Self-Evolver Engine orchestrating evaluation, mutation, and versioned evolution logs."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from evolver.evaluator import evaluator, EvaluationReport
from evolver.mutator import mutator

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EVOLUTION_LOG_FILE = DEFAULT_DATA_DIR / "evolution_log.json"
LEARNED_SKILLS_DIR = DEFAULT_DATA_DIR / "learned_skills"

class SelfEvolver:
    """Autonomous self-improvement engine for agent systems."""

    def __init__(self, log_path: Path = EVOLUTION_LOG_FILE):
        self.log_path = log_path
        self._ensure_storage()

    def _ensure_storage(self):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        LEARNED_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            initial_log = {
                "current_version": "1.0.0",
                "total_evolutions": 0,
                "history": [
                    {
                        "version": "1.0.0",
                        "timestamp": datetime.now().isoformat(),
                        "trigger": "Initial deployment",
                        "strategy": "bootstrap",
                        "score": 1.0,
                        "notes": "Baseline Layer 1 Personal Assistant configuration."
                    }
                ]
            }
            self.save_log(initial_log)

    def load_log(self) -> Dict[str, Any]:
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"current_version": "1.0.0", "total_evolutions": 0, "history": []}

    def save_log(self, data: Dict[str, Any]):
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    async def evolve(
        self,
        current_instructions: str,
        user_input: str,
        agent_output: str,
        tool_errors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Evaluates a turn and autonomously mutates the agent if shortcomings are found."""
        report = evaluator.evaluate_turn(user_input, agent_output, tool_errors)
        
        if report.passed:
            return {
                "evolved": False,
                "score": report.score,
                "message": "Performance optimal. No mutation needed.",
                "instructions": current_instructions
            }

        # Perform mutation
        new_instructions = await mutator.mutate_instructions(current_instructions, report)

        # Increment version
        log = self.load_log()
        cur_ver = log.get("current_version", "1.0.0")
        parts = cur_ver.split(".")
        new_ver = f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"
        
        record = {
            "version": new_ver,
            "timestamp": datetime.now().isoformat(),
            "trigger": user_input[:100],
            "issues": report.issues,
            "strategy": report.recommended_strategy,
            "score_before": report.score,
            "notes": f"Autonomous mutation applied via strategy '{report.recommended_strategy}'."
        }
        
        log["current_version"] = new_ver
        log["total_evolutions"] = log.get("total_evolutions", 0) + 1
        log["history"].append(record)
        self.save_log(log)

        # Save snapshot of new instructions
        snapshot_file = LEARNED_SKILLS_DIR / f"prompt_v{new_ver}.txt"
        with open(snapshot_file, "w", encoding="utf-8") as f:
            f.write(new_instructions)

        return {
            "evolved": True,
            "version": new_ver,
            "score": report.score,
            "issues": report.issues,
            "strategy": report.recommended_strategy,
            "instructions": new_instructions
        }

    def get_current_version(self) -> str:
        return self.load_log().get("current_version", "1.0.0")

    def get_history(self) -> List[Dict[str, Any]]:
        return self.load_log().get("history", [])

    def get_evolution_summary(self) -> str:
        log = self.load_log()
        history = log.get("history", [])
        return (
            f"Self-Evolver Status: v{log.get('current_version', '1.0.0')} "
            f"({log.get('total_evolutions', 0)} evolution cycles recorded)."
        )

self_evolver = SelfEvolver()
