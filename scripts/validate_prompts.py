#!/usr/bin/env python3
"""
validate_prompts.py — Valida agentes, prompts y instrucciones de Copilot.
Estado: AUTO-GENERATED (safe).
"""

import sys
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
AGENTS_DIR = REPO_ROOT / ".github" / "agents"
COPILOT_AGENTS_DIR = REPO_ROOT / ".github" / "copilot-agents"
INSTRUCTIONS_FILE = REPO_ROOT / ".github" / "copilot-instructions.md"

# Frontmatter keys válidas para agents (VS Code standard)
VALID_KEYS = {
    "name", "description", "argument-hint", "target", "infer",
    "tools", "handoffs", "model", "version", "updated"
}

# Tools válidas actualizadas (no usar runSubagent, fetch obsoleto, etc)
VALID_TOOLS = {
    "search/usages", "read/problems", "search/changes",
    "execute/testFailure", "web/fetch", "web/githubRepo",
    "agent"
}

# Tools OBSOLETAS (deben ser migradas)
OBSOLETE_TOOLS = {
    "runSubagent", "fetch", "githubRepo", "usages", "problems",
    "changes", "testFailure", "terminal",
    "github/github-mcp-server/get_issue",
    "github/github-mcp-server/get_issue_comments",
    "github.vscode-pull-request-github/issue_fetch",
    "github.vscode-pull-request-github/activePullRequest"
}

def validate_agent_file(path):
    """Valida frontmatter de un .agent.md."""
    errors = []
    # Ignorar Plan.agent.md (es ejemplo externo de VS Code)
    if path.name == "Plan.agent.md":
        print(f"  ⊘ {path.name} (VS Code example, skipped)")
        return errors
    
    try:
        content = path.read_text(encoding="utf-8")
        # Buscar frontmatter (líneas entre --- y ---)
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not match:
            errors.append(f"  ✗ {path.name}: Sin frontmatter válido")
            return errors
        
        frontmatter = match.group(1)
        
        # Detectar keys inválidas (ignorar keys dentro de handoffs)
        in_handoffs = False
        for line in frontmatter.split("\n"):
            if line.strip() == "handoffs:":
                in_handoffs = True
                continue
            if in_handoffs and not line.startswith("  "):
                in_handoffs = False
            if in_handoffs or not line or line.startswith(" "):
                continue
            if ":" not in line:
                continue
            key = line.split(":")[0].strip()
            if key not in VALID_KEYS and not key.startswith("-"):
                errors.append(f"  ⚠ {path.name}: Key no estándar '{key}' (vs Code no reconoce)")
        
        # Detectar tools obsoletas
        if "tools:" in frontmatter:
            tools_match = re.search(r"tools:\s*\[(.*?)\]", frontmatter)
            if tools_match:
                tools_str = tools_match.group(1)
                for obsolete in OBSOLETE_TOOLS:
                    if obsolete in tools_str:
                        errors.append(f"  ⚠ {path.name}: Tool OBSOLETA '{obsolete}' (migrar a válida)")
        
        # Check: infer o model (no ambos)
        has_infer = "infer:" in frontmatter
        has_model = "model:" in frontmatter
        if has_infer and has_model:
            errors.append(f"  ⚠ {path.name}: Tiene AMBOS 'infer' y 'model' (VS Code usará infer)")
        
        # Check: model = gpt-5-mini (inválido, VS Code no lo reconoce)
        if 'model: "gpt-5-mini"' in frontmatter or "model: 'gpt-5-mini'" in frontmatter:
            errors.append(f"  ✗ {path.name}: model 'gpt-5-mini' no existe en VS Code (usar infer: true)")
        
        if not errors:
            print(f"  ✓ {path.name}")
    except Exception as e:
        errors.append(f"  ✗ {path.name}: Error reading ({e})")
    
    return errors

def check_instructions_links():
    """Valida que los links en copilot-instructions.md existan."""
    errors = []
    try:
        content = INSTRUCTIONS_FILE.read_text(encoding="utf-8")
        
        # Buscar patrones [path](path) y [file](path)
        pattern = r"\[([^\]]+)\]\(([^\)]+)\)"
        for match in re.finditer(pattern, content):
            link_text, link_path = match.groups()
            
            # Si es URL (http/https), ignorar
            if link_path.startswith("http"):
                continue
            
            # Si es fragmento (#), ignorar
            if link_path.startswith("#"):
                continue
            
            # Resolver ruta (relativa a REPO_ROOT, no a .github/)
            # Soportar: ../../docs/file.md, ../docs/file.md
            if link_path.startswith("../../"):
                resolved = REPO_ROOT / link_path[6:]  # Quitar "../../"
            elif link_path.startswith("../"):
                resolved = REPO_ROOT / link_path[3:]  # Quitar "../"
            else:
                resolved = REPO_ROOT / link_path
            
            # Chequear si archivo existe
            if not resolved.exists():
                errors.append(f"  ✗ Link roto en copilot-instructions.md: [{link_text}]({link_path})")
    except Exception as e:
        errors.append(f"  ✗ Error reading copilot-instructions.md: {e}")
    
    return errors

def main():
    print("=" * 70)
    print("VALIDACIÓN: Agentes, Prompts e Instrucciones de Copilot")
    print("=" * 70)
    
    all_errors = []
    
    # Validar .agent.md files
    print("\n1. Validando .github/agents/*.agent.md...")
    if AGENTS_DIR.exists():
        for agent_file in sorted(AGENTS_DIR.glob("*.agent.md")):
            errors = validate_agent_file(agent_file)
            all_errors.extend(errors)
    else:
        print(f"  ⚠ Directorio {AGENTS_DIR} no existe")
    
    # Validar .prompt.md files (estructura básica)
    print("\n2. Validando .github/copilot-agents/*.prompt.md...")
    if COPILOT_AGENTS_DIR.exists():
        for prompt_file in sorted(COPILOT_AGENTS_DIR.glob("*.prompt.md")):
            # Solo chequeo básico: que exista y tenga contenido
            try:
                content = prompt_file.read_text(encoding="utf-8")
                if len(content.strip()) > 0:
                    print(f"  ✓ {prompt_file.name}")
                else:
                    all_errors.append(f"  ✗ {prompt_file.name}: Archivo vacío")
            except Exception as e:
                all_errors.append(f"  ✗ {prompt_file.name}: Error ({e})")
    else:
        print(f"  ⚠ Directorio {COPILOT_AGENTS_DIR} no existe")
    
    # Validar links en copilot-instructions.md
    print("\n3. Validando links en .github/copilot-instructions.md...")
    link_errors = check_instructions_links()
    if link_errors:
        all_errors.extend(link_errors)
    else:
        print("  ✓ Todos los links existen")
    
    # Resumen
    print("\n" + "=" * 70)
    if all_errors:
        print(f"❌ ERRORES ENCONTRADOS ({len(all_errors)}):\n")
        for error in all_errors:
            print(error)
        return 1
    else:
        print("✅ VALIDACIÓN OK: 0 errores detectados")
        return 0

if __name__ == "__main__":
    sys.exit(main())
