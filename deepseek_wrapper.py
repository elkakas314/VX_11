#!/usr/bin/env python3
"""
VX11 DeepSeek R1 Reasoning Wrapper
Integrates DeepSeek with Copilot for structured planning
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from openai import OpenAI


class VX11DeepSeekReasoner:
    def __init__(self):
        self.api_key = self._load_api_key()
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY not found in .env.deepseek")

        self.client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")
        self.audit_dir = Path("docs/audit/r1")
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def _load_api_key(self):
        """Load DEEPSEEK_API_KEY from .env.deepseek"""
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

    def reason(
        self, objective: str, context: str, task: str, format_json: bool = True
    ) -> dict:
        """
        Call DeepSeek reasoner for structured planning

        Args:
            objective: What we're trying to achieve
            context: VX11 context (invariants, constraints)
            task: Specific task description
            format_json: If True, request JSON output

        Returns:
            Parsed response as dict
        """

        if format_json:
            prompt = f"""You are a reasoning assistant for VX11 (a containerized multi-service architecture).

**OBJECTIVE**: {objective}

**CONTEXT & INVARIANTS**:
{context}

**TASK**: {task}

**REQUIRED OUTPUT FORMAT** (JSON only, no markdown):
{{
  "tasks": [
    {{"id": "T1", "description": "...", "files": ["..."], "commands": ["..."], "done_when": "..."}}
  ],
  "risks": [
    {{"risk": "...", "severity": "low|med|high", "mitigation": "..."}}
  ],
  "tests_to_run": ["..."],
  "rollback_plan": ["..."],
  "definition_of_done": ["..."],
  "reasoning": "brief explanation of decisions"
}}

Output ONLY valid JSON. No explanations outside JSON."""
        else:
            prompt = f"""You are a reasoning assistant for VX11.

OBJECTIVE: {objective}

CONTEXT: {context}

TASK: {task}

Provide detailed reasoning and recommendations."""

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

            # Save to audit
            self._save_audit(objective, result)

            return result

        except Exception as e:
            return {"error": str(e), "type": "deepseek_call_failed"}

    def _save_audit(self, topic: str, result: dict):
        """Save reasoning output to audit trail"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c if c.isalnum() else "_" for c in topic)[:30]
        filename = self.audit_dir / f"{timestamp}_{safe_topic}.json"

        try:
            with open(filename, "w") as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save audit: {e}", file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 deepseek_wrapper.py <objective> [context] [task]")
        sys.exit(1)

    try:
        reasoner = VX11DeepSeekReasoner()
        print("✅ DeepSeek R1 connected\n")
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)

    objective = sys.argv[1]
    context = (
        sys.argv[2]
        if len(sys.argv) > 2
        else "VX11 default: solo_madre, tentaculo_link entrypoint"
    )
    task = sys.argv[3] if len(sys.argv) > 3 else objective

    print(f"🧠 Reasoning about: {objective}")
    result = reasoner.reason(objective, context, task)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
