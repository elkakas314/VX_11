#!/usr/bin/env python3
"""
Hermes CLI Discovery with Playwright (Phase 3)
Discovers available CLIs and validates their accessibility.
Runs in --dry-run by default; requires --apply to make changes.
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Logging setup
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)


def check_window(force: bool = False) -> bool:
    """Check if current time is within off-hours window."""
    window_env = os.getenv("VX11_PLAYWRIGHT_WINDOW", "02:00-06:00")
    if force or not window_env:
        return True

    start_h, end_h = window_env.split("-")
    start_h = int(start_h.split(":")[0])
    end_h = int(end_h.split(":")[0])

    now_h = datetime.now().hour

    # If start < end (e.g., 02:00-06:00), check if now is in range
    if start_h < end_h:
        return start_h <= now_h < end_h
    # If start > end (e.g., 22:00-06:00), wrap around midnight
    else:
        return now_h >= start_h or now_h < end_h


def discover_cli_providers() -> dict:
    """
    Discover available CLI providers on system.

    Returns:
        {
            "providers": [
                {"name": "...", "available": bool, "path": "..."},
                ...
            ],
            "timestamp": datetime,
        }
    """
    import subprocess

    providers_to_check = [
        "copilot-cli",
        "curl",
        "wget",
        "python3",
        "node",
        "bash",
        "sh",
        "jq",
        "git",
    ]

    discovered = []
    for provider in providers_to_check:
        try:
            result = subprocess.run(
                ["which", provider],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                discovered.append(
                    {
                        "name": provider,
                        "available": True,
                        "path": result.stdout.strip(),
                    }
                )
            else:
                discovered.append(
                    {
                        "name": provider,
                        "available": False,
                        "path": None,
                    }
                )
        except Exception as e:
            discovered.append(
                {
                    "name": provider,
                    "available": False,
                    "path": None,
                    "error": str(e),
                }
            )

    return {
        "providers": discovered,
        "timestamp": datetime.utcnow().isoformat(),
    }


def validate_with_playwright(dry_run: bool = True) -> dict:
    """
    Validate CLI accessibility using Playwright (headless).
    NOTE: Only attempts accessibility checks; never runs captchas or automated signups.
    """
    if not os.getenv("VX11_ENABLE_PLAYWRIGHT", "0") == "1":
        log.warning(
            "Playwright disabled (VX11_ENABLE_PLAYWRIGHT=0). Skipping validation."
        )
        return {"skipped": True, "reason": "playwright_disabled"}

    try:
        import asyncio
        from playwright.async_api import async_playwright
    except ImportError:
        log.warning("Playwright not installed. Skipping validation.")
        return {"skipped": True, "reason": "playwright_not_installed"}

    async def validate_cli_pages():
        """Async validation of free CLI service pages."""
        results = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            # Example: check if Copilot CLI is accessible
            test_urls = [
                ("copilot_cli", "https://github.com/features/copilot/cli"),
            ]

            for name, url in test_urls:
                try:
                    page = await context.new_page()
                    await asyncio.sleep(0.5)  # Small delay
                    await page.goto(url, wait_until="load", timeout=10000)
                    results.append(
                        {
                            "cli": name,
                            "url": url,
                            "accessible": page.url == url,
                            "status": "ok",
                        }
                    )
                    await page.close()
                except Exception as e:
                    results.append(
                        {
                            "cli": name,
                            "url": url,
                            "accessible": False,
                            "status": "error",
                            "error": str(e),
                        }
                    )

            await browser.close()
            return results

    try:
        results = asyncio.run(validate_cli_pages())
        return {"validated": results, "dry_run": dry_run}
    except Exception as e:
        log.error(f"Playwright validation failed: {e}")
        return {"error": str(e)}


def generate_report(
    discovery_result: dict, validation_result: dict, apply: bool = False
) -> str:
    """Generate CLI discovery report."""
    report_lines = [
        "# CLI Discovery Report (Phase 3)",
        f"**Timestamp**: {datetime.utcnow().isoformat()}",
        f"**Mode**: {'APPLY' if apply else 'DRY-RUN'}",
        "",
        "## Discovered Providers",
        "",
    ]

    providers = discovery_result.get("providers", [])
    available_count = sum(1 for p in providers if p["available"])

    report_lines.append(
        f"**Found {available_count}/{len(providers)} available providers**"
    )
    report_lines.append("")

    for p in providers:
        status = "✓" if p["available"] else "✗"
        path = p.get("path", "N/A")
        report_lines.append(f"- {status} **{p['name']}** ({path})")

    report_lines.append("")
    report_lines.append("## Playwright Validation (Accessibility)")
    report_lines.append("")

    if validation_result.get("skipped"):
        report_lines.append(f"⚠️ **Skipped**: {validation_result['reason']}")
    elif validation_result.get("error"):
        report_lines.append(f"❌ **Error**: {validation_result['error']}")
    else:
        validated = validation_result.get("validated", [])
        for v in validated:
            status = "✓" if v["accessible"] else "✗"
            report_lines.append(f"- {status} {v['cli']} ({v['status']})")

    report_lines.append("")
    report_lines.append("## Integration")
    report_lines.append("")
    report_lines.append(
        "Discovered CLIs can be registered in `config/db_schema.py` table `cli_providers`."
    )
    report_lines.append(
        "Validation ensures accessibility for automated discovery (no signups)."
    )

    return "\n".join(report_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Hermes CLI Discovery with Playwright (Phase 3)"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes (default: dry-run)"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force run outside off-hours window"
    )
    parser.add_argument(
        "--no-playwright", action="store_true", help="Skip Playwright validation"
    )
    args = parser.parse_args()

    log.info("Phase 3: Hermes CLI Discovery starting...")

    # Check window
    if not check_window(force=args.force):
        log.warning("Outside off-hours window. Use --force to override.")
        sys.exit(1)

    # Discover CLIs
    log.info("Discovering available CLI providers...")
    discovery = discover_cli_providers()

    available = [p for p in discovery["providers"] if p["available"]]
    log.info(f"Found {len(available)} available providers")

    # Validate (if Playwright enabled)
    validation = {}
    if not args.no_playwright:
        log.info("Running Playwright accessibility validation...")
        validation = validate_with_playwright(dry_run=not args.apply)
    else:
        validation = {"skipped": True, "reason": "playwright_disabled_by_user"}

    # Generate report
    report = generate_report(discovery, validation, apply=args.apply)

    # Write report
    report_path = Path("docs/audit/CLI_DISCOVERY_REPORT.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    log.info(f"Report written to {report_path}")

    if args.apply:
        log.info("APPLY mode: Would register providers in DB (stub)")
        log.info("Actual registration to be implemented")
    else:
        log.info("DRY-RUN: No changes made")

    log.info("Phase 3: CLI Discovery completed.")


if __name__ == "__main__":
    main()
