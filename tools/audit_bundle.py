#!/usr/bin/env python3
"""
Audit bundle ZIP creator.
Usage: python3 tools/audit_bundle.py <run_id> <output.zip>
Output: ZIP with docs/audit/<run_id>/* and VX11_STATUS_HANDOFF.md
"""
import sys
import zipfile
import os
from pathlib import Path


def create_audit_bundle(run_id: str, output_zip: str):
    """Create ZIP bundle of audit directory."""
    audit_dir = Path(f"docs/audit/{run_id}")

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as z:
        if audit_dir.exists():
            for file in audit_dir.rglob("*"):
                if file.is_file():
                    z.write(file, arcname=file.relative_to("docs/audit"))

        # Add status file
        if Path("docs/audit/VX11_STATUS_HANDOFF.md").exists():
            z.write(
                "docs/audit/VX11_STATUS_HANDOFF.md", arcname="VX11_STATUS_HANDOFF.md"
            )

    print(f"✓ Bundle created: {output_zip} ({os.path.getsize(output_zip)} bytes)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 tools/audit_bundle.py <run_id> <output.zip>")
        sys.exit(1)
    create_audit_bundle(sys.argv[1], sys.argv[2])
