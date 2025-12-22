#!/usr/bin/env python3
"""
Phase 4 Security Audit — VX11 Operator Backend
Validar:
1. No hardcoded secrets
2. Proxy architecture (TentaculoLinkClient as sole exit point)
3. Token secret rotation capability
"""

import os
import re
import sys
from pathlib import Path

# Color output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def check_hardcoded_secrets(root_dir):
    """Check for hardcoded secrets in Python files."""
    print(f"\n{YELLOW}🔍 Checking for hardcoded secrets...{RESET}")

    patterns = [
        r'password\s*=\s*["\'](?!os\.getenv|settings\.)[^"\']+["\']',
        r'secret\s*=\s*["\'](?!os\.getenv|settings\.)[^"\']+["\']',
        r'token\s*=\s*["\'](?!os\.getenv|settings\.)[^"\']+["\']',
        r'api_key\s*=\s*["\'](?!os\.getenv|settings\.)[^"\']+["\']',
        r"AWS_SECRET|DATABASE_URL|SLACK_TOKEN|GITHUB_TOKEN",
    ]

    issues = []

    for py_file in Path(root_dir).rglob("*.py"):
        # Skip venv, __pycache__, tests
        if any(
            skip in str(py_file) for skip in [".venv", "__pycache__", ".git", "tests/"]
        ):
            continue

        try:
            content = py_file.read_text()
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[: match.start()].count("\n") + 1
                    issues.append(
                        {
                            "file": py_file,
                            "line": line_num,
                            "match": match.group(),
                        }
                    )
        except Exception as e:
            print(f"{RED}  Error reading {py_file}: {e}{RESET}")

    if issues:
        print(
            f"{RED}  ❌ FAILED: Found {len(issues)} potential hardcoded secrets:{RESET}"
        )
        for issue in issues[:5]:  # Show first 5
            print(f"    {issue['file']}: line {issue['line']}")
            print(f"      {issue['match'][:80]}")
        return False
    else:
        print(f"{GREEN}  ✓ PASSED: No hardcoded secrets detected{RESET}")
        return True


def check_proxy_architecture(root_dir):
    """Check that TentaculoLinkClient is the sole proxy exit point."""
    print(f"\n{YELLOW}🔍 Checking proxy architecture...{RESET}")

    # Files that should NOT directly call external APIs
    restricted_files = [
        "operator_backend/backend/main_v7.py",
        "operator_backend/backend/routers/canonical_api.py",
    ]

    # Patterns that indicate direct API calls (forbidden)
    forbidden_patterns = [
        r"requests\.get|requests\.post|requests\.put|requests\.delete",
        r"urllib\.request\.",
        r"httpx\.get|httpx\.post",
        r"aiohttp\.",
        r"socket\.socket",
    ]

    issues = []

    for restricted_file in restricted_files:
        full_path = Path(root_dir) / restricted_file
        if not full_path.exists():
            continue

        try:
            content = full_path.read_text()
            # Exclude comments and imports
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                # Skip comments and imports
                if line.strip().startswith("#") or "import" in line:
                    continue

                for pattern in forbidden_patterns:
                    if re.search(pattern, line):
                        # Exception: if it's in a comment, skip
                        if "#" in line and line.index("#") < line.find(
                            pattern.split("|")[0]
                        ):
                            continue

                        issues.append(
                            {
                                "file": restricted_file,
                                "line": i,
                                "content": line.strip()[:80],
                            }
                        )
        except Exception as e:
            print(f"{RED}  Error reading {full_path}: {e}{RESET}")

    if issues:
        print(
            f"{RED}  ❌ FAILED: Found {len(issues)} direct API calls (not via TentaculoLinkClient):{RESET}"
        )
        for issue in issues[:5]:
            print(f"    {issue['file']}: line {issue['line']}")
            print(f"      {issue['content']}")
        return False
    else:
        print(f"{GREEN}  ✓ PASSED: All external calls go through proxy{RESET}")
        return True


def check_token_rotation(root_dir):
    """Check that token secrets can be rotated (from ENV, not hardcoded)."""
    print(f"\n{YELLOW}🔍 Checking token rotation capability...{RESET}")

    # Find where token secrets are used
    token_files = [
        "operator_backend/backend/routers/canonical_api.py",
        "config/tokens.py",
    ]

    issues = []

    for token_file in token_files:
        full_path = Path(root_dir) / token_file
        if not full_path.exists():
            continue

        try:
            content = full_path.read_text()

            # Check if TOKEN_SECRET is read from ENV
            if "OPERATOR_TOKEN_SECRET" in content or "TOKEN_SECRET" in content:
                if "os.getenv" in content or "settings." in content:
                    # Good: it's from environment
                    continue
                else:
                    issues.append(
                        {"file": token_file, "issue": "Token secret not from ENV"}
                    )
        except Exception as e:
            print(f"{RED}  Error reading {full_path}: {e}{RESET}")

    if issues:
        print(f"{RED}  ❌ FAILED: Token secrets may not be rotatable:{RESET}")
        for issue in issues:
            print(f"    {issue['file']}: {issue['issue']}")
        return False
    else:
        print(
            f"{GREEN}  ✓ PASSED: Token secrets are environment-based (rotatable){RESET}"
        )
        return True


def main():
    root_dir = Path("/home/elkakas314/vx11")

    print(
        f"""
╔════════════════════════════════════════════════════════════════╗
║        PHASE 4 SECURITY AUDIT — VX11 Operator Backend        ║
╚════════════════════════════════════════════════════════════════╝
"""
    )

    results = {
        "hardcoded_secrets": check_hardcoded_secrets(root_dir),
        "proxy_architecture": check_proxy_architecture(root_dir),
        "token_rotation": check_token_rotation(root_dir),
    }

    print(f"\n{YELLOW}📊 SUMMARY{RESET}")
    print("─" * 60)

    for check_name, passed in results.items():
        status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
        print(f"{check_name.replace('_', ' ').title():.<40} {status}")

    all_pass = all(results.values())

    print("─" * 60)
    if all_pass:
        print(f"\n{GREEN}✅ ALL SECURITY CHECKS PASSED{RESET}")
        print("\nRecommendation: Ready for production deployment")
        return 0
    else:
        print(f"\n{RED}❌ SOME SECURITY CHECKS FAILED{RESET}")
        print("\nAction required: Review and fix failures above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
