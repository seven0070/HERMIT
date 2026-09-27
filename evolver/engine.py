"""Self-Evolver Engine orchestrating evaluation, mutation, and versioned evolution logs.

Persistence model (borrowed from AgentScope's workspace design: evolution
state lives in plain files on disk and is reloaded every run, so the agent
improves BETWEEN runs, not just within one session):

- data/evolution_log.json              versioned, append-only evolution history
- data/learned_skills/evolved_rules.md the ACTIVE rules overlay, injected into
                                       the system prompt at every startup
- data/learned_skills/rules_v<ver>.md  immutable snapshot per mutation

Mutations only fire on real failure signals (see evaluator) and never twice
in a row for the same issue signature - a loop guard against evolving over
noise.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from evolver.evaluator import evaluator, EvaluationReport
from evolver.mutator import mutator, rules_block

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EVOLUTION_LOG_FILE = DEFAULT_DATA_DIR / "evolution_log.json"
LEARNED_SKILLS_DIR = DEFAULT_DATA_DIR / "learned_skills"
ACTIVE_RULES_FILE = LEARNED_SKILLS_DIR / "evolved_rules.md"

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
                "total_evaluations": 0,
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
            return {"current_version": "1.0.0", "total_evolutions": 0, "total_evaluations": 0, "history": []}

    def save_log(self, data: Dict[str, Any]):
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # --- persistence: the active rules overlay -----------------------------

    def get_evolved_rules(self) -> str:
        """Returns the persisted operating-rules overlay, or "" if none exists."""
        try:
            if ACTIVE_RULES_FILE.exists():
                return ACTIVE_RULES_FILE.read_text(encoding="utf-8").strip()
        except Exception:
            pass
        return ""

    def get_evolved_rules_block(self) -> str:
        """Returns the prompt section to inject into the system prompt ("" if none)."""
        rules = self.get_evolved_rules()
        return rules_block(rules) if rules else ""

    def _save_rules(self, rules: str, version: str):
        ACTIVE_RULES_FILE.write_text(rules.strip() + "\n", encoding="utf-8")
        snapshot = LEARNED_SKILLS_DIR / f"rules_v{version}.md"
        snapshot.write_text(rules.strip() + "\n", encoding="utf-8")

    # --- the evolution loop ------------------------------------------------

    async def evolve(
        self,
        current_instructions: str,
        user_input: str,
        agent_output: str,
        tool_errors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Evaluates a turn and mutates the agent only on real failure signals."""
        report = evaluator.evaluate_turn(user_input, agent_output, tool_errors)

        log = self.load_log()
        log["total_evaluations"] = log.get("total_evaluations", 0) + 1

        if report.passed:
            self.save_log(log)
            return {
                "evolved": False,
                "score": report.score,
                "message": "No failure signals. No mutation needed.",
                "instructions": current_instructions
            }

        # Loop guard: never mutate twice in a row for the same issue signature.
        signature = report.issue_signature()
        history = log.get("history", [])
        last = history[-1] if history else {}
        if last.get("issue_signature") == signature and signature:
            self.save_log(log)
            return {
                "evolved": False,
                "score": report.score,
                "message": f"Same failure signature as the last mutation (v{last.get('version')}) - already addressed, skipping.",
                "instructions": current_instructions,
                "issues": report.issues,
                "strategy": report.recommended_strategy
            }

        existing_rules = self.get_evolved_rules()
        new_rules = await mutator.mutate_rules(existing_rules, report)

        cur_ver = log.get("current_version", "1.0.0")
        parts = cur_ver.split(".")
        new_ver = f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"

        self._save_rules(new_rules, new_ver)

        record = {
            "version": new_ver,
            "timestamp": datetime.now().isoformat(),
            "trigger": user_input[:100],
            "issues": report.issues,
            "issue_signature": signature,
            "strategy": report.recommended_strategy,
            "score_before": report.score,
            "notes": f"Mutation applied via strategy '{report.recommended_strategy}'; rules persisted to {ACTIVE_RULES_FILE.name}."
        }

        log["current_version"] = new_ver
        log["total_evolutions"] = log.get("total_evolutions", 0) + 1
        log["history"].append(record)
        self.save_log(log)

        # Return the live prompt: current instructions with the overlay refreshed.
        marker = "### SELF-EVOLVED OPERATING RULES"
        idx = current_instructions.find(marker)
        base = current_instructions[:idx].rstrip() if idx != -1 else current_instructions.rstrip()
        new_instructions = base + "\n\n" + rules_block(new_rules)

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
        persisted = "rules loaded from disk" if self.get_evolved_rules() else "no evolved rules yet"
        return (
            f"Self-Evolver Status: v{log.get('current_version', '1.0.0')} "
            f"({log.get('total_evolutions', 0)} mutations / {log.get('total_evaluations', 0)} turns evaluated, {persisted})."
        )

self_evolver = SelfEvolver()
