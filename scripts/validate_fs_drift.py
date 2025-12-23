import os
import sys

DRIFT_PATHS = ["hermes", "shubniggurath_legacy"]

def check_drift():
    found = []
    for path in DRIFT_PATHS:
        if os.path.exists(path):
            found.append(path)
    if found:
        print(f"❌ FS DRIFT DETECTED: {found}")
        return False
    print("✅ FS DRIFT CHECK: OK")
    return True

if __name__ == "__main__":
    if not check_drift():
        sys.exit(1)
