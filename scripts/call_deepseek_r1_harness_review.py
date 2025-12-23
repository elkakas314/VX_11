#!/usr/bin/env python3
"""
DeepSeek R1 Review Caller for VX11 Stability P0 Harness Design.

Reads the harness design from scripts/vx11_stability_p0.py and sends it to
DeepSeek R1 for architectural review + stability recommendations.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Load env for tokens
env_file = Path("/home/elkakas314/vx11/tokens.env")
if env_file.exists():
    import dotenv

    dotenv.load_dotenv(env_file)
    print(f"[LOAD] Loaded tokens from {env_file}")

sys.path.insert(0, str(Path("/home/elkakas314/vx11")))

from config.deepseek import call_deepseek_reasoner
from config.settings import settings


def main():
    # Read harness script
    harness_file = Path("/home/elkakas314/vx11/scripts/vx11_stability_p0.py")
    if not harness_file.exists():
        print(f"[ERROR] Harness file not found: {harness_file}")
        return 1

    harness_code = harness_file.read_text()[:5000]  # First 5000 chars for token budget

    # Prepare prompt for DeepSeek R1
    prompt = f"""
# VX11 Stability P0 Harness Design Review

## Current Harness Design (first 5000 chars):

```python
{harness_code}
```

## Prompt for Architecture Review:

Please perform a thorough stability and reliability review of this harness design. Focus on:

1. **Dependency Order Correctness**:
   - Is the module startup order (switch→hermes→spawner→hormiguero→mcp→manifestator→operator→shubniggurath) correct?
   - Are there any circular dependencies or missing prerequisite services?
   - Should operator-frontend really depend on operator-backend?

2. **Metric Collection Robustness**:
   - The current docker_stats() and docker_inspect() parsing is crude. Will it handle edge cases (multiple containers, no-stream format variations)?
   - Should we add memory leak detection with delta tracking across cycles?
   - Is OOMKilled detection sufficient, or should we also check exit codes?

3. **Health Check Strategy**:
   - Using simple HTTP GET with curl —is this resilient to slow startups?
   - Should we add retry logic with exponential backoff?
   - Current timeout is 5s—is this too short for slow services?

4. **Test Integration**:
   - The pytest pattern matching (test_switch_*.py, test_hermes_*.py, etc.) assumes test file naming. Will this work reliably?
   - Should we add a fallback "smoke test" when no pattern matches?
   - The limit to 2 test files per pattern—should this be configurable?

5. **Failure Handling**:
   - Current design: module fails individually, suite continues. Is this correct, or should we abort on core failures?
   - Should we implement automatic log collection when a module fails?
   - Is the 20s timeout sufficient for all services?

6. **Scalability & Extensibility**:
   - The MODULE_DEPENDENCY_MAP is hardcoded. Should we auto-discover from docker-compose.yml?
   - How would this harness scale to 15-20 modules?
   - Can we make metric thresholds (OOM, latency p95 < 500ms) configurable?

7. **Performance & Efficiency**:
   - Current design starts/stops each module individually. Should we batch operations?
   - Are docker API calls (stats, inspect) efficient, or should we cache results?
   - The sleep(2) after docker up—is 2 seconds always sufficient?

8. **Security & Isolation**:
   - Should we isolate metrics/logs per cycle to prevent cross-contamination?
   - Any risk of port conflicts if services fail to shut down cleanly?

## Deliverables:

Please provide:
1. **Top 3-5 Critical Issues** that could cause test failures
2. **Top 3 Performance Improvements** to make the harness faster/more efficient
3. **Top 2 Scalability Recommendations** for when VX11 grows
4. **Confidence Score** (0-100%) that this harness is production-ready as-is
5. **One-sentence summary** of the main architectural strength and one weakness

Format your response as JSON for easy parsing.
"""

    print("[DEEPSEEK] Sending harness design to DeepSeek R1 for review...")
    print(f"[DEEPSEEK] Prompt length: {len(prompt)} chars")
    print(f"[DEEPSEEK] Model: deepseek-reasoner")
    print()

    # Call DeepSeek R1
    result, latency_ms, confidence = call_deepseek_reasoner(
        prompt=prompt,
        task_type="architecture_review",
        max_reasoning_tokens=8000,
        temperature=0.5,
        timeout=120.0,
    )

    # Prepare output
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    audit_dir = Path(f"/home/elkakas314/vx11/docs/audit/vx11_stability_{ts}")
    audit_dir.mkdir(parents=True, exist_ok=True)

    output_file = audit_dir / "DEEPSEEK_R1_REVIEW.md"

    # Format review
    review_text = f"""# DeepSeek R1 Harness Design Review

**Generated:** {datetime.utcnow().isoformat()}
**Latency:** {latency_ms:.1f}ms
**Confidence:** {confidence:.1%}

## API Response

```json
{json.dumps(result, indent=2)}
```

## Summary

The DeepSeek R1 review has been completed. See JSON above for detailed recommendations.

### Key Insights

1. **Prompt Sent:** {len(prompt)} characters
2. **Response Time:** {latency_ms:.1f}ms
3. **Model Confidence:** {confidence:.1%}
4. **Status:** ✅ Review Complete

## Recommendations to Accept/Implement

- [TODO: Extract and list recommendations]

## Recommendations to Defer

- [TODO: Note any deferred items]

---

**Next Steps:**
1. Review JSON response above
2. Extract critical issues
3. Update harness accordingly
4. Re-run unit tests to validate

"""

    output_file.write_text(review_text)

    print(f"\n[DEEPSEEK] Review saved to: {output_file}")
    print(f"[DEEPSEEK] Latency: {latency_ms:.1f}ms")
    print(f"[DEEPSEEK] Confidence: {confidence:.1%}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
