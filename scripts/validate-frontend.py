#!/usr/bin/env python3
"""
Frontend validation script - verifies:
1. No hardcoded internal ports in source
2. Vite config base path alignment
3. API paths consistency
4. Build artifact correctness
"""

import os
import json
import re
import subprocess
from pathlib import Path

FRONTEND_ROOT = Path(__file__).parent.parent / "operator" / "frontend"
SOURCE_DIR = FRONTEND_ROOT / "src"
VITE_CONFIG = FRONTEND_ROOT / "vite.config.ts"

INTERNAL_PORTS = [
    r":\s*8001\b",
    r":\s*8002\b",
    r":\s*8003\b",
    r":\s*8011\b",
    r"localhost:8001",
    r"localhost:8002",
    r"localhost:8003",
    r"localhost:8011",
    r"127\.0\.0\.1:8001",
    r"127\.0\.0\.1:8002",
    r"127\.0\.0\.1:8003",
    r"127\.0\.0\.1:8011",
]

VALID_API_PREFIXES = [
    "/operator/api",
    "/operator/ui",
    "/health",
    "/v1",
    "/vx11",
]


def check_hardcoded_ports():
    """Scan source files for hardcoded internal ports"""
    violations = []

    for tsx_file in SOURCE_DIR.rglob("*.ts*"):
        if "node_modules" in str(tsx_file):
            continue
        try:
            with open(tsx_file, "r") as f:
                content = f.read()
                for pattern in INTERNAL_PORTS:
                    if re.search(pattern, content, re.IGNORECASE):
                        # Check if it's not in a comment
                        lines = content.split("\n")
                        for i, line in enumerate(lines):
                            if re.search(pattern, line, re.IGNORECASE):
                                if not line.strip().startswith("//"):
                                    violations.append(
                                        {
                                            "file": str(
                                                tsx_file.relative_to(FRONTEND_ROOT)
                                            ),
                                            "line": i + 1,
                                            "pattern": pattern,
                                        }
                                    )
        except Exception as e:
            print(f"Warning: Could not read {tsx_file}: {e}")

    return violations


def check_vite_config():
    """Verify Vite configuration"""
    issues = []

    try:
        with open(VITE_CONFIG, "r") as f:
            content = f.read()

        checks = {
            "base path": ("base:", "/operator/ui"),
            "proxy endpoint": ("/operator/api", "localhost:8000"),
            "port config": ("port:", "5173"),
        }

        for check_name, (pattern, expected) in checks.items():
            if pattern not in content:
                issues.append(
                    {
                        "check": check_name,
                        "found": False,
                        "pattern": pattern,
                        "expected": expected,
                    }
                )
    except Exception as e:
        issues.append({"error": str(e)})

    return issues


def check_api_paths():
    """Verify all API paths use correct prefix"""
    invalid_paths = []

    for ts_file in SOURCE_DIR.rglob("*.ts*"):
        if "node_modules" in str(ts_file):
            continue
        try:
            with open(ts_file, "r") as f:
                content = f.read()

            # Find all string paths that look like URLs
            path_pattern = r"""["'`]/([\w/-]*?)["'`]"""
            matches = re.findall(path_pattern, content)

            for match in matches:
                full_path = "/" + match
                valid = any(
                    full_path.startswith(prefix) for prefix in VALID_API_PREFIXES
                )

                if not valid and match and not match.startswith("images"):
                    invalid_paths.append(
                        {
                            "file": str(ts_file.relative_to(FRONTEND_ROOT)),
                            "path": full_path,
                        }
                    )
        except Exception as e:
            pass

    return invalid_paths


def check_build_artifacts():
    """Verify build output"""
    dist_dir = FRONTEND_ROOT / "dist"
    issues = []

    if not dist_dir.exists():
        issues.append("dist/ does not exist (run `npm run build` first)")
        return issues

    index_html = dist_dir / "index.html"
    if not index_html.exists():
        issues.append("dist/index.html missing")
        return issues

    try:
        with open(index_html, "r") as f:
            content = f.read()

        # Check for localhost hardcoding in built HTML
        if "localhost:8011" in content or "127.0.0.1:8011" in content:
            issues.append("Built HTML contains hardcoded localhost:8011")

        # Check for correct base path
        if 'href="/operator/ui/"' not in content:
            issues.append("Base path not correctly set in built HTML")
    except Exception as e:
        issues.append(f"Error reading dist/index.html: {e}")

    return issues


def generate_report():
    """Generate comprehensive validation report"""
    report = {
        "timestamp": subprocess.run(
            ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True
        ).stdout.strip(),
        "frontend_root": str(FRONTEND_ROOT),
        "checks": {},
    }

    print("🔍 Frontend Validation Report")
    print("=" * 60)

    # 1. Hardcoded ports
    print("\n1️⃣  Checking for hardcoded internal ports...")
    violations = check_hardcoded_ports()
    report["checks"]["hardcoded_ports"] = {
        "status": "PASS" if not violations else "FAIL",
        "violations": violations,
    }
    if violations:
        print(f"   ❌ FAILED: Found {len(violations)} violation(s)")
        for v in violations:
            print(f"      {v['file']}:{v['line']} - {v['pattern']}")
    else:
        print("   ✅ PASS: No hardcoded internal ports found")

    # 2. Vite config
    print("\n2️⃣  Checking Vite configuration...")
    vite_issues = check_vite_config()
    report["checks"]["vite_config"] = {
        "status": "PASS" if not vite_issues else "FAIL",
        "issues": vite_issues,
    }
    if vite_issues:
        print(f"   ❌ FAILED: {len(vite_issues)} issue(s)")
        for issue in vite_issues:
            print(f"      {issue}")
    else:
        print("   ✅ PASS: Vite config correct")

    # 3. API paths
    print("\n3️⃣  Checking API path consistency...")
    invalid = check_api_paths()
    report["checks"]["api_paths"] = {
        "status": "PASS" if not invalid else "WARN",
        "invalid_paths": invalid[:10],  # Limit to first 10
    }
    if invalid:
        print(
            f"   ⚠️  WARN: {len(invalid)} potentially invalid path(s) (showing first 10)"
        )
        for item in invalid[:10]:
            print(f"      {item['file']}: {item['path']}")
    else:
        print("   ✅ PASS: All API paths valid")

    # 4. Build artifacts
    print("\n4️⃣  Checking build artifacts...")
    build_issues = check_build_artifacts()
    report["checks"]["build_artifacts"] = {
        "status": "PASS" if not build_issues else "FAIL",
        "issues": build_issues,
    }
    if build_issues:
        print(f"   ⚠️  WARN: {len(build_issues)} issue(s)")
        for issue in build_issues:
            print(f"      {issue}")
    else:
        print("   ✅ PASS: Build artifacts OK")

    # Overall status
    print("\n" + "=" * 60)
    all_pass = all(
        check["status"] == "PASS"
        for check in report["checks"].values()
        if isinstance(check, dict) and "status" in check
    )
    report["overall_status"] = "PASS" if all_pass else "WARN"
    print(f"\n📊 Overall: {report['overall_status']}")
    print("=" * 60)

    # Save report
    report_file = FRONTEND_ROOT / "validation-report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n💾 Report saved to: {report_file}")

    return report


if __name__ == "__main__":
    try:
        report = generate_report()
        exit(0 if report["overall_status"] == "PASS" else 1)
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        exit(1)
