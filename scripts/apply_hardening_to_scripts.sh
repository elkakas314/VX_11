#!/usr/bin/env bash
set -euo pipefail
# Apply basic hardening to shell and python scripts under scripts/
# - ensure shell scripts source cleanup_protect.sh
# - replace bare mv/rm -rf with safe_mv/safe_rm
# - for python, replace shutil.move/os.rename/shutil.rmtree with safe wrappers from cleanup_guard

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXCLUDES="$REPO_ROOT/docs/audit/CLEANUP_EXCLUDES_CORE.txt"

echo "Hardening scripts under $REPO_ROOT/scripts"

sh_files=$(find "$REPO_ROOT/scripts" -maxdepth 1 -type f -name "*.sh" ! -name "cleanup_protect.sh" ! -name "apply_hardening_to_scripts.sh")
py_files=$(find "$REPO_ROOT/scripts" -maxdepth 1 -type f -name "*.py")

for f in $sh_files; do
  echo "Processing shell script: $f"
  # insert source line after shebang if not present
  if ! rg -n "cleanup_protect.sh" -q "$f"; then
    awk 'NR==1{print;next} NR==2{print "source \"$(dirname \"${BASH_SOURCE[0]}\")/cleanup_protect.sh\""} {print}' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
  fi
  # replace rm -rf with safe_rm
  perl -0777 -pe 's/\brm -rf\b/safe_rm/g' -i.bak "$f" || true
  # replace bare mv with safe_mv (word boundaries)
  perl -0777 -pe 's/\bmv\b/safe_mv/g' -i.bak "$f" || true
done

for f in $py_files; do
  echo "Processing python script: $f"
  # add import for safe wrappers if needed
  if rg -n "from scripts.cleanup_guard import" -q "$f"; then
    echo "  import already present"
  else
    # add import after module docstring/shebang
    python3 - <<PY
import io,sys
fn="$f"
src=open(fn,'r',encoding='utf-8').read()
lines=src.splitlines()
insert_at=0
if lines and lines[0].startswith('#!'):
    insert_at=1
if len(lines)>insert_at and lines[insert_at].strip().startswith(('"""',"'''")):
    # find end of docstring
    ds=lines[insert_at].strip()[:3]
    i=insert_at+1
    while i<len(lines) and ds not in lines[i]:
        i+=1
    insert_at=i+1
imp='from scripts.cleanup_guard import safe_move_py, safe_rm_py\n'
lines.insert(insert_at, imp)
open(fn,'w',encoding='utf-8').write('\n'.join(lines)+('\n' if not src.endswith('\n') else ''))
print('  import inserted')
PY
  fi
  # replace calls
  perl -0777 -pe 's/shutil\.move\s*\(/safe_move_py(/g; s/os\.rename\s*\(/safe_move_py(/g; s/shutil\.rmtree\s*\(/safe_rm_py(/g; s/os\.remove\s*\(/safe_rm_py(/g' -i.bak "$f" || true
done

echo "Hardening applied. Backup files with .bak created where changes made."
