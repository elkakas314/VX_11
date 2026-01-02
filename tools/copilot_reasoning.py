#!/usr/bin/env python3
"""
VX11 DeepSeek R1 Reasoning Oracle (COPILOT-ONLY)
─────────────────────────────────────────────────

Internal tool for GitHub Copilot automated reasoning.
Generates structured plans with VX11-specific guardrails.

WARNING: This script is for Copilot internal use only.
Direct human invocation is discouraged; use @vx11 commands instead.

Location: .github/deepseek_r1_reasoning.py
API: DeepSeek Reasoner (deepseek-reasoner model)
Audit Trail: docs/audit/r1/ (gitignored)
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from openai import OpenAI


class VX11DeepSeekReasoner:
    """
    VX11-specific reasoning oracle with safety guardrails.

    Rails (Constraints):
    ───────────────────
    1. Invariants: Preserve solo_madre runtime, tentaculo_link entrypoint, forense docs
    2. Scope: Only VX11 modules (madre, operator, switch, tentaculo, hormiguero)
    3. Safety: Never suggest deletion of docs/audit/**, forensic/** or canonical specs
    4. Atomicity: All changes must be git-atomic (one commit, clear purpose)
    5. Rollback: Every plan must include emergency recovery procedure
    6. Testing: Every plan must specify tests before production merge
    7. Audit: All outputs logged with timestamp, reasoning, risks
    """

    # VX11 SAFETY RAILS (non-negotiable)
    INVARIANTS = {
        "runtime_policy": "solo_madre (default), full-test temporary",
        "entrypoint": "tentaculo_link (single external entry)",
        "bd_default": "SQLite (data/runtime/vx11.db)",
        "canonical_specs": "docs/canon/** (immutable version control)",
        "forense_storage": "docs/audit/**, forensic/** (preserve always)",
        "git_remote": "vx_11_remote (authoritative), origin (mirror)",
    }

    PROTECTED_PATHS = [
        "docs/audit/**",
        "forensic/**",
        "docs/canon/**",
        "tokens.env*",
        ".env.deepseek",
        ".github/secrets/**",
    ]

    MODULES_ALLOWED = [
        "madre",
        "operator",
        "switch",
        "tentaculo_link",
        "hormiguero",
        "spawner",
        "redis",
    ]

    def __init__(self):
        self.api_key = self._load_api_key()
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY not found in .env.deepseek")

        self.client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")
        self.audit_dir = Path("docs/audit/r1")
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def _load_api_key(self):
        """Load DEEPSEEK_API_KEY from .env.deepseek (never print it)"""
        env_file = Path(".env.deepseek")
        if not env_file.exists():
            return None

        try:
            with open(env_file) as f:
                for line in f:
                    if line.startswith("DEEPSEEK_API_KEY"):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except:
            pass

        return None

    def _build_vx11_rails_prompt(self):
        """
        Construct the system rails to inject into every reasoning call.
        These enforce VX11 invariants and safety constraints.
        """
        rails = f"""
# VX11 REASONING ORACLE - SAFETY RAILS (ENFORCE STRICTLY)

## INVARIANTS (Non-negotiable)
- Runtime: solo_madre by default (only full-test profile allows all services)
- Entrypoint: ONLY tentaculo_link exposed externally (port 8000)
- Database: SQLite at data/runtime/vx11.db (canonical BD source)
- Canonical: docs/canon/** is version-controlled spec (never delete)
- Forense: docs/audit/**, forensic/** are immutable (preserve always)
- Git Remote: vx_11_remote is authoritative (origin is mirror)

## PROTECTED RESOURCES (Reject any plan that touches these)
{chr(10).join(f"- REJECT: {path}" for path in self.PROTECTED_PATHS)}

## ALLOWED MODULES (Only operate on these components)
{chr(10).join(f"✓ {mod}" for mod in self.MODULES_ALLOWED)}

## SAFETY GATES (Mandatory for all plans)
1. Risk Assessment: Identify severity (low/med/high)
2. Rollback: Every plan MUST include emergency recovery
3. Testing: Specify tests BEFORE production merge
4. Audit: All outputs logged with timestamp + reasoning
5. Atomicity: Each commit must be single-purpose and clear

## OUTPUT FORMAT (JSON ONLY - no markdown)
{{
  "tasks": [
    {{
      "id": "T1",
      "description": "Clear, single-purpose action",
      "files": ["file1.py", "file2.md"],
      "commands": ["cmd1", "cmd2"],
      "done_when": "Specific verification criteria",
      "rails_check": "Does NOT touch protected paths or invariants"
    }}
  ],
  "risks": [
    {{
      "risk": "Specific risk description",
      "severity": "low|med|high",
      "mitigation": "How we prevent/recover from this"
    }}
  ],
  "tests_to_run": ["test command 1", "test command 2"],
  "rollback_plan": ["emergency command 1", "emergency command 2"],
  "protected_resources_checked": true,
  "invariants_preserved": true,
  "definition_of_done": ["Specific success criteria"],
  "reasoning": "Brief explanation of decisions within VX11 constraints"
}}

## SAFETY CHECKLIST (answer before generating plan)
- All tasks within ALLOWED MODULES? YES/NO
- Any protected path touched? YES/NO  [If YES: REJECT]
- Rollback plan included? YES/NO  [If NO: REJECT]
- Tests specified? YES/NO  [If NO: REJECT]
- Invariants preserved? YES/NO  [If NO: REJECT]
"""
        return rails

    def reason(
        self,
        objective: str,
        context: str,
        task: str,
        format_json: bool = True,
        enforce_rails: bool = True,
    ) -> dict:
        """
        Call DeepSeek reasoner for structured planning with VX11 rails.

        Args:
            objective: What we're trying to achieve
            context: VX11 context (invariants, constraints)
            task: Specific task description
            format_json: If True, request JSON output
            enforce_rails: If True, inject safety guardrails (default: YES)

        Returns:
            Parsed response as dict with rails_enforced flag
        """

        # Build the system message with rails
        system_msg = self._build_vx11_rails_prompt() if enforce_rails else ""

        if format_json:
            prompt = f"""{system_msg}

---

## REASONING REQUEST

**OBJECTIVE**: {objective}

**CONTEXT & CONSTRAINTS**:
{context}

**SPECIFIC TASK**:
{task}

**OUTPUT**: JSON ONLY (valid, parseable, no markdown wrappers)

Generate a structured plan that:
1. Respects all VX11 invariants
2. Never touches protected resources
3. Includes emergency rollback
4. Specifies verification tests
5. Is atomic (single-purpose commits)"""
        else:
            prompt = f"""{system_msg}

---

OBJECTIVE: {objective}

CONTEXT: {context}

TASK: {task}

Provide detailed reasoning within VX11 safety constraints."""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[{"role": "user", "content": prompt}],
                temperature=1.0,
                max_tokens=4000,
            )

            content = response.choices[0].message.content

            if format_json:
                # Try to parse JSON from response
                try:
                    result = json.loads(content)
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown
                    if "```json" in content:
                        json_str = content.split("```json")[1].split("```")[0]
                        result = json.loads(json_str)
                    elif "```" in content:
                        json_str = content.split("```")[1].split("```")[0]
                        result = json.loads(json_str)
                    else:
                        result = {"error": "Invalid JSON response", "raw": content}
            else:
                result = {"response": content}

            # Add metadata
            result["_metadata"] = {
                "rails_enforced": enforce_rails,
                "timestamp": datetime.now().isoformat(),
                "model": "deepseek-reasoner",
            }

            # Save to audit
            self._save_audit(objective, result)

            return result

        except Exception as e:
            return {
                "error": str(e),
                "type": "deepseek_call_failed",
                "_metadata": {
                    "rails_enforced": enforce_rails,
                    "timestamp": datetime.now().isoformat(),
                },
            }

    def _save_audit(self, topic: str, result: dict):
        """Save reasoning output to audit trail (gitignored)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c if c.isalnum() else "_" for c in topic)[:30]
        filename = self.audit_dir / f"{timestamp}_{safe_topic}.json"

        try:
            with open(filename, "w") as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save audit: {e}", file=sys.stderr)

    @classmethod
    def verify_safety(cls, plan: dict) -> tuple[bool, list[str]]:
        """
        Verify that a generated plan respects all VX11 safety rails.

        Returns:
            (is_safe: bool, violations: list[str])
        """
        violations = []

        # Check invariants
        if not plan.get("invariants_preserved", False):
            violations.append("Plan does not preserve VX11 invariants")

        if not plan.get("rollback_plan"):
            violations.append("No rollback plan provided")

        if not plan.get("tests_to_run"):
            violations.append("No tests specified")

        # Check protected paths
        for task in plan.get("tasks", []):
            for file_path in task.get("files", []):
                for protected in cls.PROTECTED_PATHS:
                    if "*" in protected:
                        # Simple wildcard matching
                        base = protected.replace("**", "").replace("*", "")
                        if file_path.startswith(base):
                            violations.append(
                                f"Task touches protected path: {file_path}"
                            )
                    elif file_path == protected:
                        violations.append(f"Task touches protected path: {file_path}")

        return len(violations) == 0, violations


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python3 deepseek_r1_reasoning.py <objective> [context] [task]",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        reasoner = VX11DeepSeekReasoner()
        print("✅ DeepSeek R1 Oracle connected (VX11 rails active)\n", file=sys.stderr)
    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    objective = sys.argv[1]
    context = (
        sys.argv[2]
        if len(sys.argv) > 2
        else "VX11 default: solo_madre, tentaculo_link entrypoint, SQLite BD, forense immutable"
    )
    task = sys.argv[3] if len(sys.argv) > 3 else objective

    print(f"🧠 Reasoning about: {objective}", file=sys.stderr)
    print(f"⚙️  Rails: ENFORCED", file=sys.stderr)
    result = reasoner.reason(objective, context, task, enforce_rails=True)

    # Verify safety before returning
    if result.get("tasks"):
        is_safe, violations = VX11DeepSeekReasoner.verify_safety(result)
        if not is_safe:
            print(f"⚠️  SAFETY VIOLATIONS DETECTED:", file=sys.stderr)
            for v in violations:
                print(f"   - {v}", file=sys.stderr)
            result["_safety_violations"] = violations

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
