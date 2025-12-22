"""
Manifestator v2: Auto-Patcher Inteligente con DeepSeek R1

Características:
- Auditoría de drift (archivos reales vs BD)
- Generación de patches con R1 reasoning
- Auto-aplicación de patches
- Validación con tests antes de commit
- Rollback automático si falla
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Tuple
import uuid
import asyncio
import logging
import json
import subprocess
import os
import hashlib
from datetime import datetime

from config.settings import settings
from config.db_schema import get_session, Report
from config.deepseek import call_deepseek_reasoner_async
import difflib

log = logging.getLogger("vx11.manifestator_v2")
app = FastAPI(title="VX11 Manifestator v2 AutoPatcher")

# =========== MODELS ===========

class DriftAuditRequest(BaseModel):
    """Request para auditar drift."""
    modules: Optional[List[str]] = None  # Si None, auditar todos
    include_tests: bool = True


class PatchRequest(BaseModel):
    """Request para generar patch."""
    module_name: str
    issue_description: str
    severity: str = "normal"  # low, normal, high, critical


class DriftItem(BaseModel):
    """Item de drift detectado."""
    module: str
    file_path: str
    drift_type: str  # missing, modified, extra, permission
    expected_hash: Optional[str] = None
    actual_hash: Optional[str] = None
    description: str


class PatchInfo(BaseModel):
    """Información de patch."""
    patch_id: str
    module: str
    timestamp: datetime
    status: str  # generated, validated, applied, rolled_back, failed
    drift_items: int
    files_modified: int
    lines_changed: int
    r1_reasoning: str
    test_result: Optional[str] = None


# =========== MANIFESTATOR V2 CORE ===========

class DriftAuditor:
    """Auditor de drift entre código real y BD."""
    
    def __init__(self):
        self.known_modules = [
            "tentaculo_link", "madre", "switch", "spawner", "hermes",
            "hormiguero", "manifestator", "mcp", "shubniggurath",
            "config"
        ]
    
    async def audit_all(self, include_tests: bool = True) -> List[DriftItem]:
        """Auditar todos los módulos."""
        drift_items = []
        
        for module in self.known_modules:
            module_path = f"/home/elkakas314/vx11/{module}"
            if os.path.exists(module_path):
                items = await self._audit_module(module, module_path, include_tests)
                drift_items.extend(items)
        
        return drift_items
    
    async def _audit_module(self, module_name: str, module_path: str, include_tests: bool) -> List[DriftItem]:
        """Auditar módulo individual."""
        drift_items = []
        
        try:
            # Listar archivos actuales
            actual_files = {}
            for root, dirs, files in os.walk(module_path):
                # Ignorar __pycache__, .tmp, etc
                dirs[:] = [d for d in dirs if d not in ["__pycache__", ".tmp_copilot", ".venv"]]
                
                for file in files:
                    if file.endswith((".py", ".yml", ".yaml", ".json", ".md")):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, module_path)
                        
                        with open(file_path, 'r') as f:
                            content = f.read()
                            file_hash = hashlib.md5(content.encode()).hexdigest()
                            actual_files[rel_path] = {
                                "hash": file_hash,
                                "size": len(content),
                            }
            
            # Detectar cambios (aquí simplemente reportamos qué encontramos)
            if not actual_files:
                drift_items.append(DriftItem(
                    module=module_name,
                    file_path=module_path,
                    drift_type="missing",
                    description=f"Module directory has no Python files",
                ))
        
        except Exception as e:
            drift_items.append(DriftItem(
                module=module_name,
                file_path=module_path,
                drift_type="error",
                description=f"Audit error: {e}",
            ))
        
        return drift_items


class PatchGenerator:
    """Generador de patches con R1."""
    
    async def generate_patch(self, module: str, issue: str, severity: str) -> Tuple[str, Dict[str, Any]]:
        """Generar patch usando R1 reasoning."""
        
        # 1. Leer módulo actual
        module_path = f"/home/elkakas314/vx11/{module}"
        main_file = os.path.join(module_path, "main.py")
        
        if not os.path.exists(main_file):
            raise HTTPException(status_code=404, detail=f"Module {module}/main.py not found")
        
        with open(main_file, 'r') as f:
            current_code = f.read()
        
        # 2. Usar R1 para generar patch
        reasoning = await call_deepseek_reasoner_async(
            prompt=f"""
Eres un experto en ingeniería de software. Analiza el siguiente código y el problema reportado:

MÓDULO: {module}
PROBLEMA: {issue}
SEVERIDAD: {severity}

CÓDIGO ACTUAL (primeras 1000 caracteres):
{current_code[:1000]}...

Genera una solución en formato JSON con:
1. diagnosis: Análisis del problema
2. root_cause: Causa raíz
3. proposed_fix: Descripción de la solución
4. code_changes: Array de cambios (oldCode, newCode, line_no)
5. test_commands: Array de comandos para validar
6. rollback_plan: Plan de rollback si falla

Responde SOLO con JSON válido.
""",
            max_tokens=2000,
        )
        
        try:
            patch_data = json.loads(reasoning.get("reasoning", "{}"))
        except:
            patch_data = {
                "diagnosis": "Parse error",
                "root_cause": "Unable to parse R1 response",
                "proposed_fix": "Manual review needed",
            }
        
        return reasoning.get("reasoning", ""), patch_data
    
    async def apply_patch(self, module: str, patch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Aplicar patch al código."""
        module_path = f"/home/elkakas314/vx11/{module}"
        main_file = os.path.join(module_path, "main.py")
        
        try:
            # Leer original
            with open(main_file, 'r') as f:
                original = f.read()
            
            # Aplicar cambios (simplificado: usar primer cambio si existe)
            patched = original
            changes = patch_data.get("code_changes", [])
            
            for change in changes[:1]:  # Limitar a un cambio por seguridad
                oldCode = change.get("oldCode", "")
                newCode = change.get("newCode", "")
                if oldCode and oldCode in patched:
                    patched = patched.replace(oldCode, newCode, 1)
            
            # Crear backup
            backup_file = f"{main_file}.backup"
            with open(backup_file, 'w') as f:
                f.write(original)
            
            # Aplicar
            with open(main_file, 'w') as f:
                f.write(patched)
            
            return {
                "status": "applied",
                "module": module,
                "backup": backup_file,
                "changes": len(changes),
            }
        
        except Exception as e:
            log.error(f"Patch apply error: {e}")
            return {
                "status": "failed",
                "error": str(e),
            }
    
    async def validate_patch(self, module: str) -> Dict[str, Any]:
        """Validar patch ejecutando tests."""
        try:
            result = subprocess.run(
                [
                    "python", "-m", "pytest",
                    f"tests/test_{module}.py",
                    "-q", "--tb=short"
                ],
                cwd="/home/elkakas314/vx11",
                capture_output=True,
                timeout=30,
            )
            
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "return_code": result.returncode,
                "stdout": result.stdout.decode()[:500],
                "stderr": result.stderr.decode()[:500],
            }
        
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "Tests took too long",
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }
    
    async def rollback_patch(self, module: str, backup_file: str) -> Dict[str, Any]:
        """Rollback de patch."""
        module_path = f"/home/elkakas314/vx11/{module}"
        main_file = os.path.join(module_path, "main.py")
        
        try:
            if os.path.exists(backup_file):
                with open(backup_file, 'r') as f:
                    original = f.read()
                
                with open(main_file, 'w') as f:
                    f.write(original)
                
                os.remove(backup_file)
                
                return {
                    "status": "rolled_back",
                    "module": module,
                }
            else:
                return {
                    "status": "error",
                    "error": "Backup file not found",
                }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }


class ManifestatorCore:
    """Core de Manifestator."""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.auditor = DriftAuditor()
        self.generator = PatchGenerator()
        self.patches: Dict[str, Dict[str, Any]] = {}
    
    async def run_drift_audit(self, modules: Optional[List[str]] = None) -> List[DriftItem]:
        """Ejecutar auditoría de drift."""
        if modules:
            drift_items = []
            for module in modules:
                module_path = f"/home/elkakas314/vx11/{module}"
                if os.path.exists(module_path):
                    items = await self.auditor._audit_module(module, module_path, True)
                    drift_items.extend(items)
            return drift_items
        else:
            return await self.auditor.audit_all()
    
    async def create_patch(self, module: str, issue: str, severity: str) -> PatchInfo:
        """Crear patch."""
        patch_id = str(uuid.uuid4())[:8]
        
        try:
            reasoning, patch_data = await self.generator.generate_patch(module, issue, severity)
            
            self.patches[patch_id] = {
                "module": module,
                "issue": issue,
                "severity": severity,
                "reasoning": reasoning,
                "data": patch_data,
                "status": "generated",
            }
            
            return PatchInfo(
                patch_id=patch_id,
                module=module,
                timestamp=datetime.utcnow(),
                status="generated",
                drift_items=0,
                files_modified=0,
                lines_changed=0,
                r1_reasoning=reasoning[:200],
            )
        
        except Exception as e:
            log.error(f"Patch creation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def apply_and_validate(self, patch_id: str) -> Dict[str, Any]:
        """Aplicar y validar patch."""
        if patch_id not in self.patches:
            raise HTTPException(status_code=404, detail="Patch not found")
        
        patch = self.patches[patch_id]
        module = patch["module"]
        patch_data = patch["data"]
        
        # Aplicar
        apply_result = await self.generator.apply_patch(module, patch_data)
        if apply_result["status"] != "applied":
            return apply_result
        
        # Validar
        test_result = await self.generator.validate_patch(module)
        
        if test_result["status"] != "passed":
            # Rollback
            await self.generator.rollback_patch(module, apply_result.get("backup", ""))
            patch["status"] = "rolled_back"
            return {
                "status": "rolled_back",
                "reason": "Tests failed",
                "test_result": test_result,
            }
        
        patch["status"] = "applied"
        return {
            "status": "applied",
            "patch_id": patch_id,
            "module": module,
            "test_result": test_result,
        }


# =========== ENDPOINTS ===========

_MANIFESTATOR_CORE: Optional[ManifestatorCore] = None


def get_manifestator_core(db_session = Depends(lambda: get_session("madre"))):
    """Dependency para manifestator core."""
    global _MANIFESTATOR_CORE
    if _MANIFESTATOR_CORE is None:
        _MANIFESTATOR_CORE = ManifestatorCore(db_session)
    return _MANIFESTATOR_CORE


@app.post("/manifestator/drift/audit")
async def audit_drift(
    req: DriftAuditRequest,
    core: ManifestatorCore = Depends(get_manifestator_core),
) -> Dict[str, Any]:
    """Ejecutar auditoría de drift."""
    try:
        items = await core.run_drift_audit(req.modules)
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "drift_items": len(items),
            "items": [
                {
                    "module": item.module,
                    "type": item.drift_type,
                    "description": item.description,
                }
                for item in items
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/manifestator/patch/create")
async def create_patch(
    req: PatchRequest,
    core: ManifestatorCore = Depends(get_manifestator_core),
) -> PatchInfo:
    """Generar patch con R1."""
    return await core.create_patch(req.module_name, req.issue_description, req.severity)


@app.post("/manifestator/patch/{patch_id}/apply")
async def apply_patch(
    patch_id: str,
    core: ManifestatorCore = Depends(get_manifestator_core),
) -> Dict[str, Any]:
    """Aplicar y validar patch."""
    return await core.apply_and_validate(patch_id)


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check."""
    return {"status": "ok", "module": "manifestator_v2"}


@app.post("/control")
async def control(action: str = "status") -> Dict[str, Any]:
    """Control actions."""
    return {
        "action": action,
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=52115, reload=True)
