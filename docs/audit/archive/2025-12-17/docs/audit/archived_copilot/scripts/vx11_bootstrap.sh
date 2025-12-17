#!/usr/bin/env bash
set -euo pipefail
CD="$(pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel || echo "$CD")"
cd "$REPO_ROOT"

# Backups
mkdir -p docs/audit/backups
cp -v docs/audit/COPILOT_BOOTSTRAP.md docs/audit/COPILOT_BOOTSTRAP.md.bak 2>/dev/null || true
cp -v docs/audit/DB_MAP_v7_FINAL.md docs/audit/DB_MAP_v7_FINAL.md.bak 2>/dev/null || true
cp -v docs/audit/DB_SCHEMA_v7_FINAL.json docs/audit/DB_SCHEMA_v7_FINAL.json.bak 2>/dev/null || true

# 1) .github/agents/vx11.agent.md (reemplazo completo)
mkdir -p .github/agents
cat > .github/agents/vx11.agent.md <<'MD'
---
name: vx11
description: "Agente canónico VX11 — reglas quirúrgicas para intervenciones en repo."
rules:
  - "Antes de cualquier acción: localizar y validar DB_MAP*FINAL* y DB_SCHEMA*FINAL* en docs/audit."
  - "No preguntar salvo para acciones destructivas: rm, rmdir, mover fuera de docs/audit, tocar tokens, git reset/clean/push, docker compose up/down."
  - "Evidencia obligatoria: escribir outputs en docs/audit/."
  - "Preservar forense: forensic/crashes nunca se borra; archivar si se requiere reubicación."
---
MD

# 2) AGENTS.md (raíz) — contrato canónico
cat > AGENTS.md <<'TXT'
CONTRATO DE AGENTES VX11 (resumen)
- NO preguntar salvo acciones destructivas reales (rm, rmdir, mover fuera de docs/audit, tocar tokens/secrets, git reset/clean/push, docker compose up/down).
- Antes de actuar: consultar y validar la fuente de verdad:
  - docs/audit/DB_MAP_v7_FINAL.md
  - docs/audit/DB_SCHEMA_v7_FINAL.json
- Evidencia obligatoria: todo output relevante se escribe en docs/audit/.
- Forense: forensic/crashes NUNCA se borra; si es necesario, se ARCHIVA en docs/audit/archived_forensic/.
TXT

# 3) .github/copilot-instructions.md
cat > .github/copilot-instructions.md <<'MD'
- Modo cirujano: ejecutar en lotes sin preguntar.
- Antes de tocar BD o estructura: validar DB_MAP/DB_SCHEMA FINAL en docs/audit.
- Mantener evidencias y reportes en docs/audit/.
MD

# 4) .vscode/settings.json (validar JSON)
mkdir -p .vscode
cat > .vscode/settings.json <<'JSON'
{
  "vx11.agent.enabled": true,
  "vx11.agent.iterations": 5,
  "vx11.agent.autoApprove": {
    "allow": [
      "pwd",
      "ls",
      "find",
      "rg",
      "cat",
      "git status",
      "git diff",
      "git log",
      "git show",
      "git grep",
      "git ls-files",
      "python",
      "pytest",
      "docker ps",
      "docker compose config"
    ],
    "deny": [
      "rm",
      "rmdir",
      "mv",
      "cp",
      "chmod",
      "chown",
      "sudo",
      "git reset",
      "git clean",
      "git push",
      "docker compose up",
      "docker compose down"
    ]
  }
}
JSON

# Validate JSON
python3 -m json.tool .vscode/settings.json >/dev/null

# 5) Prepare docs/audit/COPILOT_BOOTSTRAP.md using live git info
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
REPO_PATH="$(pwd)"
BRANCH="$(git rev-parse --abbrev-ref HEAD || echo 'unknown')"
COMMIT_SHORT="$(git rev-parse --short HEAD || echo 'unknown')"
GIT_STATUS="$(git status -sb || true)"

DB_MAP_PATH="$(ls docs/audit/*DB_MAP*FINAL* 2>/dev/null | head -n1 || true)"
DB_SCHEMA_PATH="$(ls docs/audit/*DB_SCHEMA*FINAL* 2>/dev/null | head -n1 || true)"

if [ -z "$DB_MAP_PATH" ] || [ -z "$DB_SCHEMA_PATH" ]; then
  echo "BLOQUEO: DB_MAP/DB_SCHEMA FINAL no encontrados. Abortando."
  exit 2
fi

cat > docs/audit/COPILOT_BOOTSTRAP.md <<MD
# COPILOT_BOOTSTRAP
Generated: $TIMESTAMP
Repo: $REPO_PATH
Branch: $BRANCH
Commit: $COMMIT_SHORT

DB MAP (FUENTE DE VERDAD):
- $DB_MAP_PATH
DB SCHEMA (FUENTE DE VERDAD):
- $DB_SCHEMA_PATH

Git status:
$GIT_STATUS

Reglas:
- No crear duplicados ni archivos final_v2.
- Forense: forensic/crashes NUNCA borrar.

MD

# 6) FORENSE: detectar archivos borrados y restaurar o archivar
mkdir -p docs/audit/archived_forensic
# List deleted tracked files
DELETED="$(git ls-files --deleted || true)"
if [ -n "$DELETED" ]; then
  echo "Restaurando archivos rastreados borrados (git restore)..."
  echo "$DELETED" | xargs -r -n1 git restore --staged --worktree --
fi

# Archivar archivos no rastreados en forensic (si existen)
if [ -d forensic/crashes ]; then
  find forensic/crashes -type f -print0 | xargs -0 -I{} bash -c 'f="{}"; rel="${f#./}"; cp -v "$f" "docs/audit/archived_forensic/${rel//\//_}" || true'
fi

# 7) Regenerar DB map/schema (principal)
if [ -f scripts/generate_db_map.py ]; then
  python3 scripts/generate_db_map.py
else
  echo "scripts/generate_db_map.py no encontrado, intentando fallback..."
  python3 scripts/generate_db_map_from_db.py || true
fi

# Validate outputs exist
for f in docs/audit/DB_MAP_v7_FINAL.md docs/audit/DB_SCHEMA_v7_FINAL.json docs/audit/DB_MAP_v7_META.txt; do
  if [ -f "$f" ]; then
    echo "OK: $f"
  fi
done

# 8) Commit controlado (sin push)
git add \
  docs/audit/COPILOT_BOOTSTRAP.md \
  .github/agents/vx11.agent.md \
  AGENTS.md \
  .github/copilot-instructions.md \
  .vscode/settings.json \
  docs/audit/DB_MAP_v7_FINAL.md \
  docs/audit/DB_SCHEMA_v7_FINAL.json \
  docs/audit/DB_MAP_v7_META.txt || true

git commit -m "chore(vx11): cierre canónico copilot + bootstrap blindado + forense preservado" || echo "No changes to commit"

echo "TERMINADO: revisa git status y confirma (sin push)."
