#!/usr/bin/env python3
"""
DeepSeek R1 Optimization: power_manager.py for VX11

Rails (NON-NEGOTIABLE):
1. Container-level ONLY: docker compose, NO docker exec/kill
2. NO breaking changes to endpoints or function signatures
3. Keep CANONICAL_SERVICES, allowlist(), rate limiting intact
4. Preserve audit trail (OUTDIR logging)
5. Return PLAN + PATCH + VALIDATION in structured format
6. Economía: optimizar for <500ms latency, <$0.01 per operation
"""

import json
import sys
import os
from pathlib import Path

# Add repo to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from config.deepseek import call_deepseek_reasoner_async


def load_power_manager_context():
    """Load current power_manager.py for analysis."""
    pm_path = REPO_ROOT / "madre" / "power_manager.py"
    with open(pm_path) as f:
        content = f.read()
    return content


def build_r1_prompt(pm_content: str) -> str:
    """Build structured prompt for R1 optimization analysis."""
    return f"""
# VX11 Power Manager Optimization Task

## CONTEXT
File: madre/power_manager.py (container-level docker compose control)
Current stats: {len(pm_content.splitlines())} lines, subprocess-based commands

## RAILS (NON-NEGOTIABLE)
1. **Container-level ONLY**: Use `docker compose`, NEVER `docker exec` or process-level signals
2. **No breaking changes**: Endpoints /madre/power/* must remain stable
3. **Keep allowlist**: CANONICAL_SERVICES list is canonical, do not modify
4. **Audit trail**: docs/audit/ logging must remain
5. **Rate limits**: Keep token/rate limiting logic intact
6. **Return format**: PLAN (bottlenecks) + PATCH (code suggestions) + VALIDATION (how to verify)

## GOAL
Optimize for:
- **Speed**: Target <500ms per operation (docker compose commands async? caching?)
- **Economy**: <$0.01 per power operation (reduce I/O, batch operations)
- **Clarity**: Keep code readable, no over-optimization

## CODE TO ANALYZE
```python
{pm_content[:3000]}
...
```

## SPECIFIC QUESTIONS FOR R1 REASONING
1. **Bottlenecks**: Where are the slowest operations? (subprocess calls? DB writes? file I/O?)
2. **Batch opportunities**: Can we batch multiple docker compose commands? (e.g., stop all at once)
3. **Caching**: Can we cache allowlist or service status locally (with TTL)?
4. **Async**: Are subprocess calls blocking? Can we make them async?
5. **Economy**: Which operations cost most? How to optimize?

## OUTPUT FORMAT (REQUIRED)
Generate a JSON response with:
```json
{{
  "reasoning": "explanation of analysis and tradeoffs",
  "plan": [
    {{
      "priority": "high|medium|low",
      "bottleneck": "description of slowness/inefficiency",
      "estimated_speedup": "expected time reduction",
      "estimated_cost_savings": "economy improvement (percentage or %)"}},
    ...
  ],
  "patch_suggestions": [
    {{
      "function": "function_name",
      "current_issue": "what is slow/inefficient",
      "suggestion": "specific code change",
      "code_example": "before/after snippet",
      "breaking_risk": "high|medium|low|none",
      "estimated_impact": "time saved / requests reduced"}},
    ...
  ],
  "validation_steps": [
    "command or test to verify optimization",
    ...
  ],
  "warnings": ["any rail violations or risks"],
  "rails_compliance": "brief summary of how suggestions respect all rails"
}}
```

## CRITICAL: Respect Rails
- If any suggestion violates container-level-only, REJECT it
- If endpoint signature changes, REJECT it
- If audit trail is compromised, REJECT it
- If rate limiting is removed, REJECT it

Generate reasoning and structured response now.
"""


async def run_r1_optimization():
    """Invoke R1 for optimization analysis."""
    print("[*] Loading power_manager.py...")
    pm_content = load_power_manager_context()

    print("[*] Building R1 prompt...")
    prompt = build_r1_prompt(pm_content)

    print("[*] Calling DeepSeek R1 (may take 30-60 seconds)...")
    result, latency_ms, confidence = await call_deepseek_reasoner_async(
        prompt,
        task_type="optimization",
        max_reasoning_tokens=8000,
        temperature=0.7,
        timeout=60.0,
    )

    print(f"[+] R1 latency: {latency_ms:.0f}ms, confidence: {confidence:.2f}")

    content = result.get("text", result.get("result", ""))

    print("\n" + "=" * 80)
    print("DEEPSEEK R1 OPTIMIZATION ANALYSIS")
    print("=" * 80)
    print(content[:2000] if content else "(no output)")
    print("\n" + "-" * 80)

    # Try to parse as JSON
    try:
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            recommendations = json.loads(json_str)

            # Save to OUTDIR
            outdir = REPO_ROOT / "docs" / "audit" / "r1_power_manager_optimization"
            outdir.mkdir(parents=True, exist_ok=True)

            with open(outdir / "r1_recommendations.json", "w") as f:
                json.dump(recommendations, f, indent=2)

            print(
                f"\n[+] Saved recommendations to {outdir / 'r1_recommendations.json'}"
            )
            return recommendations
    except json.JSONDecodeError:
        print("[!] Could not parse JSON from R1 response")
        return None


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_r1_optimization())
