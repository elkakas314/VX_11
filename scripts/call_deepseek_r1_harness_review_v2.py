#!/usr/bin/env python3
"""
DeepSeek R1 Review Caller for VX11 Stability P0 Harness (FASE 3).

Reviews the harness design and provides recommendations for:
- Bug detection
- Performance optimization
- Scalability improvements
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Load env for tokens
env_file = Path("/home/elkakas314/vx11/tokens.env")
if env_file.exists():
    try:
        import dotenv

        dotenv.load_dotenv(env_file)
        print(f"[LOAD] Loaded tokens from {env_file}")
    except ImportError:
        print(f"[WARN] python-dotenv not available, loading manually")
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ[key] = val

sys.path.insert(0, str(Path("/home/elkakas314/vx11")))

try:
    from config.deepseek import call_deepseek_reasoner

    print("[✓] DeepSeek config loaded")
except ImportError as e:
    print(f"[ERROR] Failed to import DeepSeek config: {e}")
    print(f"[ERROR] Make sure DEEPSEEK_API_KEY is set in tokens.env")
    sys.exit(1)


def main():
    """Run DeepSeek R1 review on harness design."""

    # Read harness script
    harness_file = Path("/home/elkakas314/vx11/scripts/vx11_stability_p0.py")
    if not harness_file.exists():
        print(f"[ERROR] Harness file not found: {harness_file}")
        return 1

    harness_code = harness_file.read_text()[:6000]

    # Comprehensive review prompt
    prompt = """# VX11 Stability P0 Harness - DeepSeek R1 Review (FASE 3)

## System Context
VX11 is a microservices system with 9+ modules testing stability metrics (RAM/CPU/OOM/restarts/latency).

## Harness Features (Current)
1. Topological sort for module dependencies
2. Health checks with exponential backoff (2^n seconds)
3. Docker stats/inspect parsing (JSON-based, robust)
4. Stability_P0_pct formula: 40% tests + 20% health + 15% restarts + 15% OOM + 10% memory
5. Flow checks: endpoint testing with HTTP code, latency, payload hash
6. Per-module pytest integration
7. Reports: JSON + Markdown with cost table and rankings

## Harness Limitations & Questions
1. **Bug Risk:** Health check returncode logic—are we parsing HTTP codes correctly from curl?
2. **Robustness:** docker_down_services now uses stop/rm per service. Will this handle timing issues?
3. **Metric Collection:** docker stats --format json—what if service not running? Graceful fallback?
4. **Flow Checks:** Payload hash—useful signal or unnecessary overhead?
5. **Stability Formula:** Are weights (40/20/15/15/10) appropriate? Should critical modules weight more?
6. **Performance:** Starting/stopping each module sequentially—any opportunity for parallelization?
7. **Scalability:** If modules grow to 20+, auto-discovery from docker-compose.yml vs hardcoded map?
8. **Memory Leak Detection:** Current design doesn't track deltas across cycles. Should we?

## Request for Review

Please provide a JSON response with:
{
  "critical_bugs": [
    {"issue": "...", "impact": "high/medium", "fix": "..."},
    ...
  ],
  "recommended_improvements": [
    {"title": "...", "benefit": "...", "effort": "low/medium/high"},
    ...
  ],
  "scalability_recommendations": ["...", "..."],
  "architectural_strengths": ["...", "..."],
  "architectural_weaknesses": ["...", "..."],
  "confidence_score_pct": 75,
  "summary": "..."
}

Be concise, focus on actionable recommendations.
"""

    print("[DEEPSEEK R1] Starting review of VX11 Stability P0 harness...")
    print(f"[DEEPSEEK R1] Prompt: {len(prompt)} chars")
    print()

    # Call DeepSeek R1
    try:
        result, latency_ms, confidence = call_deepseek_reasoner(
            prompt=prompt,
            task_type="architecture_review",
            max_reasoning_tokens=8000,
            temperature=0.5,
            timeout=120.0,
        )
        print(
            f"[✓] DeepSeek R1 Response received in {latency_ms:.1f}ms (confidence: {confidence:.1%})"
        )
    except Exception as e:
        print(f"[ERROR] DeepSeek API call failed: {e}")
        print(f"[ERROR] Check DEEPSEEK_API_KEY in tokens.env")
        return 1

    # Save output
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    audit_dir = Path(f"/home/elkakas314/vx11/docs/audit/vx11_stability_{ts}")
    audit_dir.mkdir(parents=True, exist_ok=True)

    output_file = audit_dir / "DEEPSEEK_R1_REVIEW.md"

    # Format review
    review_text = f"""# DeepSeek R1 Harness Design Review

**Generated:** {datetime.utcnow().isoformat()}
**Model:** deepseek-reasoner
**Latency:** {latency_ms:.1f}ms
**Confidence:** {confidence:.1%}

## API Response

```json
{json.dumps(result, indent=2) if isinstance(result, dict) else result}
```

## Summary

DeepSeek R1 has reviewed the VX11 Stability P0 harness design and provided recommendations.
See JSON response above for:
- Critical bugs to fix
- Performance improvements to implement
- Scalability recommendations for growth
- Architectural strengths and weaknesses
- Overall confidence score

**Next Steps:**
1. Review critical_bugs array and prioritize fixes
2. Evaluate recommended_improvements based on effort/benefit
3. Consider scalability changes if growing beyond 10 modules
4. Incorporate approved changes and re-run review
"""

    output_file.write_text(review_text)
    print(f"[✓] Review saved: {output_file}")
    print()
    print("[DeepSeek R1 Findings]")
    print("=" * 80)
    if isinstance(result, dict):
        print(json.dumps(result, indent=2))
    else:
        print(result)
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
