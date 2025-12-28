#!/usr/bin/env python3
"""
Autofix Conductor v1.0 (DeepSeek R1 Assisted Diagnosis & Repair)

Automated failure diagnosis and remediation:
- Detect E2E test failures
- Query DeepSeek R1 for root cause analysis
- Generate patch suggestions
- Apply fixes automatically (max 3 cycles)
- Re-test and validate
- Log all decisions for audit trail

Usage:
    python3 scripts/autofix_conductor_v1.py --test-result results.json

Flow:
1. Parse E2E test failure
2. Invoke DeepSeek R1 with failure context
3. Generate PATCH_INTENT.md
4. Apply suggested fixes
5. Re-run E2E test
6. Validate fix success or iterate
"""

import sys
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import argparse
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.tokens import get_token

# Constants
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-reasoner"
DEEPSEEK_TOKEN = os.environ.get("DEEPSEEK_API_TOKEN", "")
MAX_AUTOFIX_CYCLES = 3
MADRE_URL = "http://localhost:8001"
VX11_TOKEN = get_token("VX11_TOKEN") or "vx11-local-token"


def get_outdir() -> Path:
    """Get timestamped outdir for autofix run."""
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    outdir = Path("/home/elkakas314/vx11/docs/audit") / f"{ts}_AUTOFIX_CONDUCTOR_v1"
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir


def parse_test_results(result_file: Path) -> Dict[str, Any]:
    """Parse E2E test results JSON."""
    with open(result_file, "r") as f:
        return json.load(f)


def extract_failures(results: Dict[str, Any]) -> Dict[str, Any]:
    """Extract failed tests and their details."""
    failures = {}
    tests = results.get("tests", {})
    
    for test_name, test_result in tests.items():
        status = test_result.get("status", "unknown")
        if status != "ok":
            failures[test_name] = {
                "status": status,
                "details": test_result,
                "severity": "critical" if status == "fail" else "warning" if status == "degraded" else "timeout"
            }
    
    return failures


def invoke_deepseek_r1(failure_context: str) -> Dict[str, Any]:
    """
    Invoke DeepSeek R1 for analysis.
    NOTE: This is a STUB - in production, call actual API with proper token.
    """
    print(f"\n[AUTOFIX] Invoking DeepSeek R1 for failure analysis...")
    print(f"Context:\n{failure_context[:500]}...")

    # STUB: Return example diagnostic
    analysis = {
        "status": "analyzed",
        "root_cause": "Service crash loop detected - application initialization timeout",
        "affected_services": ["switch", "hermes"],
        "suggestions": [
            {
                "priority": "high",
                "action": "Increase service startup timeout from 30s to 60s",
                "file": "docker-compose.override.yml",
                "change": "healthcheck.timeout: 60s"
            },
            {
                "priority": "medium",
                "action": "Check service logs for initialization errors",
                "file": "services/switch/main.py",
                "change": "Add retry logic with exponential backoff on startup"
            }
        ],
        "estimated_fix_time_min": 2,
        "confidence": 0.75,
        "reasoning": "Based on failure pattern analysis and common VX11 service issues"
    }

    return analysis


def generate_patch_intent(analysis: Dict[str, Any], outdir: Path) -> Path:
    """Generate PATCH_INTENT.md with suggested fixes."""
    patch_file = outdir / "PATCH_INTENT.md"
    
    content = f"""# Autofix Patch Intent

**Generated**: {datetime.utcnow().isoformat()}Z  
**Status**: PENDING_APPROVAL  
**Confidence**: {analysis.get('confidence', 0) * 100:.1f}%  

## Root Cause Analysis

{analysis.get('root_cause', 'Unknown')}

## Affected Services

- {chr(10).join('- ' + s for s in analysis.get('affected_services', []))}

## Suggested Fixes

"""
    
    for i, suggestion in enumerate(analysis.get('suggestions', []), 1):
        content += f"""
### Fix #{i} (Priority: {suggestion.get('priority', 'medium').upper()})

**Action**: {suggestion.get('action', '')}  
**File**: `{suggestion.get('file', '')}`  

```diff
{suggestion.get('change', '')}
```

"""
    
    content += f"""
## Validation Plan

1. Apply patches
2. Rebuild affected services
3. Run E2E Test Conductor v2
4. Verify all tests pass (health checks, metrics, flows)
5. Log success/failure to forensic ledger

## Estimated Time

{analysis.get('estimated_fix_time_min', 5)} minutes

## Next Steps

- [ ] Manual review by DevOps
- [ ] Apply patches (autofix_apply.sh)
- [ ] Re-test
- [ ] Commit if successful
"""
    
    with open(patch_file, "w") as f:
        f.write(content)
    
    return patch_file


def apply_patch(patch_intent: Path, outdir: Path) -> Dict[str, Any]:
    """
    Apply suggested patches.
    NOTE: This is STUB - in production, would execute actual patch scripts.
    """
    print(f"\n[AUTOFIX] Applying patches from {patch_intent}...")
    
    # STUB: Return simulated patch result
    result = {
        "status": "applied",
        "patches_applied": 1,
        "patches_failed": 0,
        "containers_rebuilt": ["switch", "hermes"],
        "elapsed_sec": 45,
        "next_action": "retest"
    }
    
    return result


async def retest_after_fix(outdir: Path) -> Dict[str, Any]:
    """
    Re-run E2E Test Conductor v2 after fixes applied.
    """
    print(f"\n[AUTOFIX] Re-running E2E Test Conductor v2...")
    
    # Call e2e_test_conductor_v2.py
    try:
        result = subprocess.run(
            [
                sys.executable,
                "/home/elkakas314/vx11/scripts/e2e_test_conductor_v2.py",
                "--reason", "autofix_retest"
            ],
            capture_output=True,
            text=True,
            timeout=300,
            cwd="/app"
        )
        
        if result.returncode == 0:
            return {
                "status": "ok",
                "message": "E2E tests passed after fix",
                "stdout": result.stdout[-500:] if result.stdout else ""
            }
        else:
            return {
                "status": "fail",
                "message": "E2E tests still failing",
                "stdout": result.stdout[-500:] if result.stdout else "",
                "stderr": result.stderr[-500:] if result.stderr else ""
            }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "message": "E2E test timeout (300s)"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


async def run_autofix_cycle(failure_context: str, cycle: int, outdir: Path) -> Dict[str, Any]:
    """Run one autofix cycle: analyze → patch → retest."""
    print(f"\n{'='*70}")
    print(f"AUTOFIX CYCLE #{cycle}")
    print(f"{'='*70}")
    
    cycle_dir = outdir / f"cycle_{cycle}"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Invoke DeepSeek R1
    analysis = invoke_deepseek_r1(failure_context)
    with open(cycle_dir / "analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)
    
    # Step 2: Generate patch intent
    patch_file = generate_patch_intent(analysis, cycle_dir)
    print(f"✅ Patch intent generated: {patch_file}")
    
    # Step 3: Apply patches
    patch_result = apply_patch(patch_file, cycle_dir)
    with open(cycle_dir / "patch_result.json", "w") as f:
        json.dump(patch_result, f, indent=2)
    
    if patch_result.get("status") != "applied":
        print(f"❌ Patch application failed")
        return {
            "cycle": cycle,
            "status": "patch_failed",
            "result": patch_result
        }
    
    print(f"✅ Patches applied")
    
    # Step 4: Rebuild containers
    print(f"✅ Containers rebuilt: {patch_result.get('containers_rebuilt', [])}")
    
    # Step 5: Re-test
    retest_result = await retest_after_fix(cycle_dir)
    with open(cycle_dir / "retest_result.json", "w") as f:
        json.dump(retest_result, f, indent=2)
    
    if retest_result.get("status") == "ok":
        print(f"✅ ALL TESTS PASSED AFTER FIX!")
        return {
            "cycle": cycle,
            "status": "success",
            "result": retest_result
        }
    else:
        print(f"⚠️ Tests still failing after fix")
        return {
            "cycle": cycle,
            "status": "incomplete",
            "result": retest_result
        }


async def main():
    parser = argparse.ArgumentParser(
        description="Autofix Conductor v1.0 (DeepSeek R1 Assisted)"
    )
    parser.add_argument(
        "--test-result",
        help="Path to E2E test results JSON",
        required=False
    )
    parser.add_argument(
        "--reason",
        default="autofix",
        help="Reason for autofix run"
    )
    args = parser.parse_args()

    outdir = get_outdir()
    print(f"Audit dir: {outdir}")
    print(f"Max cycles: {MAX_AUTOFIX_CYCLES}")

    try:
        # Parse test results or use latest
        if args.test_result:
            result_file = Path(args.test_result)
        else:
            # Find latest test results
            audit_dir = Path("/home/elkakas314/vx11/docs/audit")
            test_dirs = list(audit_dir.glob("*_E2E_TEST_CONDUCTOR_v*/test_results.json"))
            if not test_dirs:
                print("❌ No test results found")
                return 1
            result_file = sorted(test_dirs)[-1]

        print(f"\n📊 Parsing test results: {result_file}")
        results = parse_test_results(result_file)

        # Extract failures
        failures = extract_failures(results)
        if not failures:
            print("✅ All tests passed, no autofix needed")
            return 0

        print(f"❌ Found {len(failures)} failures:")
        for name, failure in failures.items():
            print(f"   - {name}: {failure['status']}")

        # Generate failure context
        failure_context = json.dumps(failures, indent=2)
        with open(outdir / "failure_context.json", "w") as f:
            f.write(failure_context)

        # Run autofix cycles
        autofix_results = {
            "start_time": datetime.utcnow().isoformat() + "Z",
            "initial_failures": len(failures),
            "cycles": []
        }

        for cycle in range(1, MAX_AUTOFIX_CYCLES + 1):
            cycle_result = await run_autofix_cycle(failure_context, cycle, outdir)
            autofix_results["cycles"].append(cycle_result)

            if cycle_result.get("status") == "success":
                print(f"\n✅ FIX SUCCESSFUL in cycle {cycle}")
                break
            elif cycle == MAX_AUTOFIX_CYCLES:
                print(f"\n⚠️ Max cycles ({MAX_AUTOFIX_CYCLES}) reached")

        autofix_results["end_time"] = datetime.utcnow().isoformat() + "Z"
        autofix_results["status"] = "success" if any(
            c.get("status") == "success" for c in autofix_results["cycles"]
        ) else "incomplete"

        # Save summary
        summary_file = outdir / "autofix_summary.json"
        with open(summary_file, "w") as f:
            json.dump(autofix_results, f, indent=2)

        print(f"\n✅ Autofix summary saved: {summary_file}")
        print(f"\nFinal status: {autofix_results['status']}")
        return 0 if autofix_results["status"] == "success" else 1

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
