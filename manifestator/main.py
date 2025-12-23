"""
Manifestator: Drift detection, validation, patch generation for VX11 blueprint.
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
import json
import hashlib
from datetime import datetime
import httpx
import logging

from config.tokens import load_tokens, get_token
from config.settings import settings
from config.forensics import write_log
from .dsl import ManifestatorDSL, ConfigBlock
from config import deepseek

log = logging.getLogger("vx11.manifestator")
load_tokens()

VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)


def check_token(x_vx11_token: str = Header(None)):
    if settings.enable_auth:
        if not x_vx11_token or x_vx11_token != VX11_TOKEN:
            raise HTTPException(status_code=401, detail="auth_required")
    return True


# CPU gate: shared state with Hormiguero (ALWAYS-OFF by default)
# Can be updated by Hormiguero via callback or polled from env var
_cpu_sustained_high = False


def set_cpu_sustained_high(state: bool) -> None:
    """
    Called by Hormiguero to update CPU pressure state.
    If True, /patchplan and /builder/spec return 429 (Too Many Requests).
    """
    global _cpu_sustained_high
    _cpu_sustained_high = state


def get_cpu_sustained_high() -> bool:
    """Check if CPU is sustained high. Polls env var or internal state."""
    import os

    # Env var takes precedence (for mocking/testing)
    env_val = os.getenv("MANIFESTATOR_CPU_SUSTAINED_HIGH", "0")
    if env_val == "1":
        return True
    return _cpu_sustained_high


app = FastAPI(title="VX11 manifestator")

REPO_ROOT = Path(__file__).resolve().parents[1]
# Prefer canonical blueprint if present
CANONICAL_BLUEPRINT = REPO_ROOT / "docs" / "VX11_v6.3_CANONICAL.json"
LEGACY_BLUEPRINT = REPO_ROOT / ".tmp_copilot" / "vx11_union"
BLUEPRINT_PATH = (
    CANONICAL_BLUEPRINT if CANONICAL_BLUEPRINT.exists() else LEGACY_BLUEPRINT
)
PATCHES_DIR = REPO_ROOT / ".tmp_copilot" / "manifestator" / "patches"
PATCHES_DIR.mkdir(parents=True, exist_ok=True)

# DSL instance
dsl = ManifestatorDSL(storage_dir=str(PATCHES_DIR.parent))

# Global state for metrics tracking
_GLOBAL_STATE = {
    "active_patches": [],
    "patches_applied": 0,
}


def parse_blueprint_modules(blueprint_path: Path) -> List[str]:
    """Parse blueprint to extract expected modules."""
    if not blueprint_path.exists():
        return []

    try:
        text = blueprint_path.read_text(encoding="utf-8")
        modules = set()

        # Extract module names (carpeta/archivo patterns)
        for m in re.findall(r"\b([a-zA-Z0-9_\-]+)/", text):
            name = m.strip()
            if name == "gateway":
                # Legacy alias: map gateway -> tentaculo_link (frontdoor único)
                modules.add("tentaculo_link")
            else:
                modules.add(name)

        # Filter known modules
        known = {
            "tentaculo_link",
            "madre",
            "switch",
            "hermes",
            "hormiguero",
            "manifestator",
            "mcp",
            "shubniggurath",
            "spawner",
            "config",
            "scripts",
            "tests",
            "docs",
        }
        return sorted([m for m in modules if m in known])
    except Exception:
        return []


def compute_module_hash(module_path: Path) -> str:
    """Compute SHA256 hash of module files."""
    h = hashlib.sha256()
    for f in sorted(module_path.glob("**/*.py")):
        try:
            h.update(f.read_bytes())
        except Exception:
            pass
    return h.hexdigest()[:12]


async def probe_service_health(url: str, timeout: float = 2.0) -> Dict[str, Any]:
    """Probe service health endpoint."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(f"{url}/health")
            return {
                "url": url,
                "reachable": True,
                "status_code": resp.status_code,
                "health": resp.json() if resp.status_code == 200 else None,
            }
    except Exception as e:
        return {
            "url": url,
            "reachable": False,
            "error": str(e),
        }


def port_for_module(module: str) -> Optional[int]:
    """Get port for module from settings."""
    mapping = {
        "tentaculo_link": getattr(
            settings, "tentaculo_link_port", settings.gateway_port
        ),
        "gateway": settings.gateway_port,
        "madre": settings.madre_port,
        "switch": settings.switch_port,
        "hermes": settings.hermes_port,
        "hormiguero": settings.hormiguero_port,
        "manifestator": settings.manifestator_port,
        "mcp": settings.mcp_port,
        "shubniggurath": settings.shub_port,
        "spawner": settings.spawner_port,
    }
    return mapping.get(module)


# ============ CANONICAL MINIMUM CONTRACT ENDPOINTS ============


@app.post("/manifestator/validate")
async def manifestator_validate(body: Dict[str, Any] = None):
    """
    Validate drift evidence or state snapshot (CANONICAL minimal contract).

    Request:
    {
        "drift_evidence": {"missing": [...], "extra": [...]},
        "state": {...}
    }

    Response:
    {
        "valid": bool,
        "issues": [],
        "risk": "low|mid|high",
        "hash": "sha256"
    }
    """
    if not body:
        body = {}

    drift = body.get("drift_evidence", {})
    state = body.get("state", {})

    issues = []
    if drift.get("missing"):
        issues.append(f"Missing {len(drift['missing'])} files")
    if drift.get("extra"):
        issues.append(f"Extra {len(drift['extra'])} files")

    risk = "low" if not issues else ("mid" if len(issues) < 3 else "high")
    h = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:12]

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "risk": risk,
        "hash": h,
    }


@app.post("/manifestator/patchplan")
async def manifestator_patchplan(body: Dict[str, Any] = None):
    """
    Generate minimal patchplan from drift evidence (CANONICAL minimal contract).

    **CPU Gate:** Returns 429 if CPU is sustained high.

    Request:
    {
        "drift_evidence": {"missing": [...], "extra": [...]},
        "scope": "local|global" (optional)
    }

    Response:
    {
        "plan_id": "uuid",
        "actions": [
            {"action": "add|remove|verify", "target": "path", "reason": "..."}
        ],
        "risk": "low|mid|high",
        "estimated_time_sec": int,
        "notes": "..."
    }
    """
    # CPU gate: block if sustained high
    if get_cpu_sustained_high():
        raise HTTPException(
            status_code=429,
            detail="CPU sustained high; patchplan generation temporarily blocked",
        )

    if not body:
        body = {}

    import uuid

    plan_id = str(uuid.uuid4())
    drift = body.get("drift_evidence", {})
    scope = body.get("scope", "local")

    actions = []

    # Build actions from drift
    for missing in drift.get("missing", []):
        actions.append(
            {"action": "add", "target": missing, "reason": "missing_from_canonical"}
        )

    for extra in drift.get("extra", []):
        actions.append(
            {"action": "remove", "target": extra, "reason": "extra_not_in_canonical"}
        )

    risk = "low" if len(actions) < 3 else ("mid" if len(actions) < 10 else "high")
    estimated_time = len(actions) * 2  # rough estimate

    return {
        "plan_id": plan_id,
        "actions": actions,
        "risk": risk,
        "estimated_time_sec": estimated_time,
        "notes": f"Plan for {scope} scope with {len(actions)} actions",
    }


@app.get("/health", dependencies=[])
def health():
    return {"status": "healthy", "service": "manifestator"}


@app.post("/control")
def control(action: Optional[str] = None):
    """Control endpoint (start/stop/restart/status)."""
    return {"module": "manifestator", "action": action or "status", "status": "ok"}


# Metrics endpoints (adaptive optimization)
@app.get("/metrics/cpu")
async def metrics_cpu():
    """CPU metrics for manifestator module."""
    try:
        import psutil

        cpu_percent = psutil.cpu_percent(interval=0.1)
        return {"metric": "cpu", "value": cpu_percent, "unit": "percent"}
    except:
        return {"metric": "cpu", "value": 0, "unit": "percent"}


@app.get("/metrics/memory")
async def metrics_memory():
    """Memory metrics for manifestator module."""
    try:
        import psutil

        memory = psutil.virtual_memory()
        return {
            "metric": "memory",
            "value": memory.percent,
            "unit": "percent",
            "available_mb": memory.available / (1024 * 1024),
        }
    except:
        return {"metric": "memory", "value": 0, "unit": "percent"}


@app.get("/metrics/queue")
async def metrics_queue():
    """Active patch operations metric."""
    return {
        "metric": "queue",
        "value": len(_GLOBAL_STATE.get("active_patches", [])),
        "unit": "patches",
    }


@app.get("/metrics/throughput")
async def metrics_throughput():
    """Patches applied throughput."""
    return {
        "metric": "throughput",
        "value": _GLOBAL_STATE.get("patches_applied", 0),
        "unit": "patches",
    }


@app.get("/drift")
async def drift():
    """Detect drift between repo and blueprint."""
    # Parse blueprint
    expected_modules = parse_blueprint_modules(BLUEPRINT_PATH)

    # Scan repo
    real_modules = [
        p.name for p in REPO_ROOT.iterdir() if p.is_dir() and not p.name.startswith(".")
    ]
    # Ignorar duplicados
    real_modules = list(set(real_modules))

    # Evitar duplicados en expected también
    expected_modules = list(set(expected_modules))
    missing = [m for m in expected_modules if m not in real_modules]
    extra = [
        p
        for p in real_modules
        if p not in expected_modules and p not in {".venv", ".git"}
    ]

    # Probe health
    probe_results = {}
    for module in expected_modules:
        port = port_for_module(module)
        if port is None:
            probe_results[module] = {"error": "no_port_mapping"}
            continue

        # Use hostname from settings instead of localhost
        module_hostname = getattr(settings, f"{module}_url", None)
        if module_hostname:
            health = await probe_service_health(module_hostname, timeout=2.0)
        else:
            # Fallback to hostname from docker-compose DNS
            hostname = module.replace("_", "_")
            health = await probe_service_health(
                f"http://{hostname}:{port}", timeout=2.0
            )
        probe_results[module] = health

    # Compute hashes
    module_hashes = {}
    for module in real_modules:
        module_path = REPO_ROOT / module
        if module_path.is_dir():
            module_hashes[module] = compute_module_hash(module_path)

    write_log("manifestator", f"drift_report:missing={len(missing)}:extra={len(extra)}")

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "expected_modules": expected_modules,
        "real_modules": real_modules,
        "missing": missing,
        "extra": extra,
        "probes": probe_results,
        "module_hashes": module_hashes,
    }


@app.post("/generate-patch")
async def generate_patch(module: str, issue: str, proposed_fix: Optional[str] = None):
    """Generate a patch for a module."""
    patch_id = f"patch-{module}-{int(datetime.utcnow().timestamp())}"

    patch_data = {
        "id": patch_id,
        "module": module,
        "timestamp": datetime.utcnow().isoformat(),
        "issue": issue,
        "proposed_fix": proposed_fix or "auto",
        "status": "proposed",
    }

    patch_file = PATCHES_DIR / f"{patch_id}.json"
    with patch_file.open("w") as f:
        json.dump(patch_data, f, indent=2)

    write_log("manifestator", f"patch_generated:{patch_id}:{module}")

    return {
        "patch_id": patch_id,
        "file": str(patch_file),
        "status": "generated",
    }


@app.post("/validate-patch")
async def validate_patch(patch_id: str):
    """Validate a patch before application."""
    patch_file = PATCHES_DIR / f"{patch_id}.json"
    if not patch_file.exists():
        raise HTTPException(status_code=404, detail="patch_not_found")

    try:
        patch_data = json.loads(patch_file.read_text())

        # Basic validation
        validations = {
            "has_id": "id" in patch_data,
            "has_module": "module" in patch_data,
            "has_issue": "issue" in patch_data,
            "valid_json": True,
        }

        is_valid = all(validations.values())
        write_log("manifestator", f"patch_validated:{patch_id}:valid={is_valid}")

        return {
            "patch_id": patch_id,
            "valid": is_valid,
            "validations": validations,
        }

    except Exception as e:
        return {
            "patch_id": patch_id,
            "valid": False,
            "error": str(e),
        }


@app.get("/patches")
def list_patches(limit: int = 50):
    """List generated patches."""
    patches = sorted(
        PATCHES_DIR.glob("patch-*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:limit]

    return {
        "patches": [
            {
                "id": p.stem,
                "file": str(p),
                "created": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
            }
            for p in patches
        ]
    }


@app.post("/apply-patch")
async def apply_patch(patch_id: str):
    """Apply a validated patch."""
    patch_file = PATCHES_DIR / f"{patch_id}.json"
    if not patch_file.exists():
        raise HTTPException(status_code=404, detail="patch_not_found")

    try:
        patch_data = json.loads(patch_file.read_text())

        # Mark as applied
        patch_data["status"] = "applied"
        patch_data["applied_at"] = datetime.utcnow().isoformat()

        with patch_file.open("w") as f:
            json.dump(patch_data, f, indent=2)

        # Update global state
        _GLOBAL_STATE["patches_applied"] += 1

        write_log("manifestator", f"patch_applied:{patch_id}")

        return {
            "patch_id": patch_id,
            "status": "applied",
        }

    except Exception as e:
        write_log(
            "manifestator", f"patch_apply_failed:{patch_id}:{str(e)}", level="ERROR"
        )
        return {
            "patch_id": patch_id,
            "status": "error",
            "error": str(e),
        }


# ========== DSL ENDPOINTS (Declarative Configuration) ==========


class BlockDefinition(BaseModel):
    target: str
    operation: str
    key: str
    value: Any
    depends_on: Optional[List[str]] = None


class CreatePlanRequest(BaseModel):
    blocks: List[BlockDefinition]


@app.post("/manifestator/dsl/plan")
async def dsl_create_plan(req: CreatePlanRequest):
    """
    Create deployment plan from block definitions.
    """
    try:
        blocks = [
            dsl.create_block(
                target=b.target,
                operation=b.operation,
                key=b.key,
                value=b.value,
                depends_on=b.depends_on,
            )
            for b in req.blocks
        ]

        plan = dsl.create_plan(blocks)
        write_log(
            "manifestator", f"dsl_plan_created:{plan.plan_id}:blocks={len(blocks)}"
        )

        return {
            "status": "created",
            "plan_id": plan.plan_id,
            "blocks_count": len(blocks),
        }
    except Exception as e:
        write_log("manifestator", f"dsl_create_plan_error:{e}", level="ERROR")
        return {"status": "error", "error": str(e)}


@app.post("/manifestator/dsl/simulate/{plan_id}")
async def dsl_simulate(plan_id: str):
    """
    Simulate plan without making changes.
    """
    try:
        result = await dsl.simulate(plan_id)
        write_log("manifestator", f"dsl_simulate:{plan_id}:ok={result.get('ok')}")
        return {"status": "ok", **result}
    except Exception as e:
        write_log("manifestator", f"dsl_simulate_error:{plan_id}:{e}", level="ERROR")
        return {"status": "error", "error": str(e)}


@app.post("/manifestator/dsl/apply/{plan_id}")
async def dsl_apply(plan_id: str, force: bool = False):
    """
    Apply plan: commit changes and record rollback info.
    """
    try:
        result = await dsl.apply(plan_id, force=force)
        write_log("manifestator", f"dsl_apply:{plan_id}:ok={result.get('ok')}")
        return {"status": "ok" if result.get("ok") else "error", **result}
    except Exception as e:
        write_log("manifestator", f"dsl_apply_error:{plan_id}:{e}", level="ERROR")
        return {"status": "error", "error": str(e)}


@app.post("/manifestator/dsl/rollback/{plan_id}")
async def dsl_rollback(plan_id: str):
    """
    Rollback applied plan to previous state.
    """
    try:
        result = await dsl.rollback(plan_id)
        write_log("manifestator", f"dsl_rollback:{plan_id}:ok={result.get('ok')}")
        return {"status": "ok" if result.get("ok") else "error", **result}
    except Exception as e:
        write_log("manifestator", f"dsl_rollback_error:{plan_id}:{e}", level="ERROR")
        return {"status": "error", "error": str(e)}


@app.get("/manifestator/dsl/audit/{plan_id}")
async def dsl_audit(plan_id: str):
    """
    Audit plan: check current state vs applied state.
    """
    try:
        result = await dsl.audit(plan_id)
        write_log("manifestator", f"dsl_audit:{plan_id}")
        return {"status": "ok", **result}
    except Exception as e:
        write_log("manifestator", f"dsl_audit_error:{plan_id}:{e}", level="ERROR")
        return {"status": "error", "error": str(e)}


@app.get("/manifestator/dsl/plans")
async def dsl_list_plans(status: Optional[str] = None):
    """
    List deployment plans, optionally filtered by status.
    """
    plans = dsl.list_plans(status=status)
    return {"status": "ok", "count": len(plans), "plans": plans}


@app.post("/manifestator/semantic-validate")
async def semantic_validate(body: Dict[str, Any]):
    """
    Validación semántica opcional usando DeepSeek R1 (si hay clave).
    """
    try:
        manifest = body.get("manifest", "")
        result, latency_ms, confidence = await deepseek.call_deepseek_reasoner_async(
            manifest, task_type="manifest_validation", max_reasoning_tokens=2000
        )
        return {
            "status": "ok",
            "provider": result.get("provider"),
            "latency_ms": latency_ms,
            "confidence": confidence,
            "analysis": result,
        }
    except Exception as e:
        write_log("manifestator", f"semantic_validate_error:{e}", level="ERROR")
        return {"status": "error", "error": str(e)}


# ========== PATCH BUILDER & REPAIR ==========


class PatchBuilder:
    """Genera parches para arreglar drift detec tado."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.patches = []

    def add_patch(
        self, patch_type: str, target: str, action: str, details: Optional[Dict] = None
    ):
        """Registra un parche."""
        patch = {
            "type": patch_type,
            "target": target,
            "action": action,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.patches.append(patch)
        write_log("manifestator", f"patch_generated:{patch_type}:{target}:{action}")
        return patch

    def fix_missing_files(self, missing_files: List[str]) -> List[Dict]:
        """Genera parches para archivos faltantes."""
        patches = []
        for file_path in missing_files:
            patch = self.add_patch(
                "file_creation",
                file_path,
                "create",
                {"reason": "missing_file"},
            )
            patches.append(patch)
        return patches

    def fix_extra_files(self, extra_files: List[str]) -> List[Dict]:
        """Genera parches para archivos extra."""
        patches = []
        for file_path in extra_files:
            if file_path.endswith((".tmp", ".log", ".cache", ".pyc")):
                patch = self.add_patch(
                    "file_removal",
                    file_path,
                    "rm",
                    {"reason": "garbage_file"},
                )
                patches.append(patch)
        return patches

    def fix_import_errors(self, module: str, errors: List[str]) -> List[Dict]:
        """Genera parches para errores de import."""
        patches = []
        for error in errors:
            patch = self.add_patch(
                "import_fix",
                module,
                "fix_imports",
                {"error": error},
            )
            patches.append(patch)
        return patches

    def get_patches(self) -> List[Dict]:
        return self.patches


async def comprehensive_drift_detection() -> Dict[str, Any]:
    """Detección completa de drift: archivos, estructura, imports, canonicalidad."""
    from config.db_schema import DriftReport, get_session

    report = {
        "files_missing": [],
        "files_extra": [],
        "import_errors": [],
        "structure_issues": [],
        "timestamp": datetime.utcnow().isoformat(),
    }

    # 1. Archivos faltantes vs canonical
    expected_modules = parse_blueprint_modules(BLUEPRINT_PATH)
    real_modules = [
        p.name for p in REPO_ROOT.iterdir() if p.is_dir() and not p.name.startswith(".")
    ]
    report["modules_missing"] = [m for m in expected_modules if m not in real_modules]
    report["modules_extra"] = [
        m
        for m in real_modules
        if m not in expected_modules and m not in {".venv", ".git", "__pycache__"}
    ]

    # 2. Archivos basura
    runtime_path = REPO_ROOT / "data" / "runtime"
    if runtime_path.exists():
        for item in runtime_path.iterdir():
            if item.is_file() and item.suffix in [".tmp", ".cache", ".log"]:
                if item.stat().st_size > 1024 * 10:  # > 10 KB
                    report["files_extra"].append(str(item.relative_to(REPO_ROOT)))

    # 3. Validar imports en módulos
    for module in real_modules[:5]:  # Limitar a 5 módulos para rapidez
        module_path = REPO_ROOT / module
        if module_path.is_dir():
            for py_file in module_path.glob("*.py"):
                try:
                    content = py_file.read_text()
                    # Buscar imports mal formados
                    bad_imports = re.findall(r"from\s+\d+|import\s+\d+", content)
                    if bad_imports:
                        report["import_errors"].append(
                            {
                                "file": str(py_file.relative_to(REPO_ROOT)),
                                "errors": bad_imports,
                            }
                        )
                except Exception:
                    pass

    # Guardar en BD
    db = get_session("vx11")
    try:
        drift_rec = DriftReport(
            module="manifestator",
            details=json.dumps(report),
            severity=(
                "medium" if report["modules_extra"] or report["files_extra"] else "low"
            ),
        )
        db.add(drift_rec)
        db.commit()
    except Exception as e:
        write_log("manifestator", f"drift_report_db_error:{e}", level="WARNING")
    finally:
        db.close()

    return report


# ============ PASO 6: Real Patch Generation (Manifestator v7.1) ============


@app.post("/manifestator/scan-drift")
async def scan_drift_v2(req: Dict[str, Any] = None):
    """
    Detectar drift en sistema (PASO 6).

    Input:
      {
        "scope": "sistema"  // "sistema", "config", "data"
      }

    Output:
      {
        "status": "ok",
        "drift_id": "drift_...",
        "files_changed": 5,
        "severity": 0.4,
        "diffs": [...]
      }
    """
    from manifestator.patch_generator_v2 import get_drift_scanner

    try:
        scope = (req or {}).get("scope", "sistema") if req else "sistema"
        scanner = get_drift_scanner()
        drift_report = await scanner.scan_drift(scope=scope)

        write_log(
            "manifestator", f"scan_drift_api:{drift_report.drift_id}:scope={scope}"
        )
        return {
            "status": "ok",
            "drift": drift_report.to_dict(),
        }
    except Exception as e:
        write_log("manifestator", f"scan_drift_error:{e}", level="ERROR")
        return {"status": "error", "error": str(e)}


@app.post("/manifestator/generate-patch")
async def generate_patch_v2(req: Dict[str, Any]):
    """
    Generar patch desde reporte de drift (PASO 6).

    Input:
      {
        "drift_id": "drift_...",
        "diffs": [...]
      }

    Output:
      {
        "status": "ok",
        "patch_id": "patch_...",
        "operations": [...]
      }
    """
    from manifestator.patch_generator_v2 import (
        DriftScanner,
        DriftReport,
        FileDiff,
        PatchGenerator,
    )

    try:
        # Reconstruir drift report desde input
        diffs = []
        for diff_data in req.get("diffs", []):
            diffs.append(
                FileDiff(
                    file_path=diff_data.get("file"),
                    operation=diff_data.get("op"),
                    old_hash=diff_data.get("old_hash"),
                    new_hash=diff_data.get("new_hash"),
                )
            )

        drift_report = DriftReport(
            drift_id=req.get("drift_id", "drift_unknown"),
            detected_at=datetime.utcnow().isoformat(),
            scope="sistema",
            diffs=diffs,
            total_files_changed=len(diffs),
            severity=0.5,
        )

        # Generar patch
        patch = PatchGenerator.generate_patch(drift_report)

        write_log(
            "manifestator",
            f"generate_patch_api:{patch['patch_id']}:ops={patch['operation_count']}",
        )
        return {
            "status": "ok",
            "patch": patch,
        }
    except Exception as e:
        write_log("manifestator", f"generate_patch_error:{e}", level="ERROR")
        return {"status": "error", "error": str(e)}


@app.post("/manifestator/validate-patch")
async def validate_patch_v2(req: Dict[str, Any]):
    """
    Validar integridad de patch (PASO 6).

    Input:
      {
        "patch_id": "patch_...",
        "operations": [...]
      }
    """
    from manifestator.patch_generator_v2 import PatchValidator

    try:
        is_valid, errors = await PatchValidator.validate_patch(req)

        write_log(
            "manifestator", f"validate_patch_api:{req.get('patch_id')}:valid={is_valid}"
        )
        return {
            "status": "ok",
            "patch_id": req.get("patch_id"),
            "valid": is_valid,
            "errors": errors,
        }
    except Exception as e:
        write_log("manifestator", f"validate_patch_error:{e}", level="ERROR")
        return {"status": "error", "error": str(e)}


@app.post("/manifestator/apply-patch-v2")
async def apply_patch_v2(req: Dict[str, Any]):
    """
    Aplicar patch generado (PASO 6).

    Input:
      {
        "patch_id": "patch_...",
        "operations": [...]
      }
    """
    from manifestator.patch_generator_v2 import PatchGenerator, PatchValidator

    try:
        # Validar primero
        is_valid, errors = await PatchValidator.validate_patch(req)
        if not is_valid:
            return {"status": "error", "errors": errors}

        # Aplicar
        result = await PatchGenerator.apply_patch(req)

        write_log(
            "manifestator",
            f"apply_patch_api:{req.get('patch_id')}:applied={result['applied']}:failed={result['failed']}",
        )
        return {
            "status": "ok",
            "patch_id": req.get("patch_id"),
            "result": result,
        }
    except Exception as e:
        write_log("manifestator", f"apply_patch_error:{e}", level="ERROR")
        return {"status": "error", "error": str(e)}


@app.post("/detect-drift")
async def detect_drift_advanced():
    """Detección avanzada de drift."""
    return await comprehensive_drift_detection()


@app.post("/repair")
async def repair_endpoint(module: Optional[str] = None):
    """Repara drift detectado automáticamente."""
    drift = await comprehensive_drift_detection()
    builder = PatchBuilder(REPO_ROOT)

    # Generar parches
    builder.fix_missing_files(drift.get("files_missing", []))
    builder.fix_extra_files(drift.get("files_extra", []))
    builder.fix_import_errors(module or "all", drift.get("import_errors", []))

    patches = builder.get_patches()
    write_log("manifestator", f"repair:generated_{len(patches)}_patches")

    return {
        "status": "ok",
        "patches_count": len(patches),
        "patches": patches,
        "drift": drift,
    }


@app.post("/manifestator/builder/spec")
async def manifestator_builder_spec(body: Dict[str, Any] = None):
    """
    Generate builder specification (CANONICAL planning-only endpoint).

    **CPU Gate:** Returns 429 if CPU is sustained high.

    Request:
    {
        "module": "string",
        "canonical_manifest": {...} | null,
        "patchplan": {...} | null,
        "constraints": {
            "max_cpu_pct": 5,
            "max_mem_mb": 256,
            "concurrency": 1,
            "background_only": true
        },
        "context": {"correlation_id": "..."}
    }

    Response:
    {
        "builder_id": "uuid-or-stable-id",
        "module": "...",
        "actions": [...],  # Recipe steps (NO execution)
        "artifacts": [...],  # Suggested paths (NO writes)
        "risk": "low|mid|high",
        "estimated_time_sec": int,
        "notes": [...],
        "hash": "sha256-of-response"
    }
    """
    # CPU gate: block if sustained high
    if get_cpu_sustained_high():
        raise HTTPException(
            status_code=429,
            detail="CPU sustained high; builder spec generation temporarily blocked",
        )

    if not body:
        body = {}

    import uuid

    builder_id = str(uuid.uuid4())
    module = body.get("module", "unknown")
    constraints = body.get("constraints", {})
    patchplan = body.get("patchplan", {})
    context = body.get("context", {})
    correlation_id = context.get("correlation_id", "N/A")

    # Generate recipe from patchplan (if present)
    actions = []
    if patchplan and patchplan.get("actions"):
        for patch_action in patchplan["actions"]:
            action_type = patch_action.get("action", "unknown")
            target = patch_action.get("target", "")

            # Map patch actions to builder recipe steps
            if action_type == "add":
                actions.append(
                    {
                        "step": f"create_{len(actions)}",
                        "type": "add",
                        "target": target,
                        "reason": patch_action.get("reason", ""),
                        "executable": False,
                    }
                )
            elif action_type == "remove":
                actions.append(
                    {
                        "step": f"remove_{len(actions)}",
                        "type": "remove",
                        "target": target,
                        "reason": patch_action.get("reason", ""),
                        "executable": False,
                    }
                )

    # Proposed artifacts (sandbox, not written unless explicitly approved by Madre)
    artifacts = [
        f"/tmp/vx11_builder/{module}/artifacts",
        f"/tmp/vx11_builder/{module}/logs",
    ]

    # Risk assessment
    risk = "low"
    if len(actions) > 5:
        risk = "mid"
    if len(actions) > 10 or constraints.get("concurrency", 1) > 1:
        risk = "high"

    # Estimated time based on action count
    estimated_time = len(actions) * 2 + 5  # base 5s + 2s per action

    notes = [
        f"Recipe for module: {module}",
        f"Constraints: {constraints}",
        f"Correlation ID: {correlation_id}",
        "Action list is PLANNING ONLY; no writes to filesystem unless explicitly approved by Madre",
        f"Artifacts directory (NOT CREATED unless builder is executed): {artifacts[0]}",
    ]

    # Hash of response (stable, deterministic)
    response_dict = {
        "builder_id": builder_id,
        "module": module,
        "actions": actions,
        "artifacts": artifacts,
        "risk": risk,
        "estimated_time_sec": estimated_time,
        "notes": notes,
    }
    response_hash = hashlib.sha256(
        json.dumps(response_dict, sort_keys=True).encode()
    ).hexdigest()[:16]

    return {
        "builder_id": builder_id,
        "module": module,
        "actions": actions,
        "artifacts": artifacts,
        "risk": risk,
        "estimated_time_sec": estimated_time,
        "notes": notes,
        "hash": response_hash,
    }


@app.post("/apply-patch")
async def apply_patch_endpoint(patch_id: str):
    """Aplica un parche específico."""
    # Mock: en producción integraría con Madre
    return {
        "status": "ok",
        "patch_id": patch_id,
        "applied": True,
        "message": "Patch applied (mock)",
    }


# ========== RAILS ORCHESTRATOR ENDPOINTS ==========
# New endpoints for RailsMap planning (added FASE 3)

from .rails import create_rails_router

rails_router = create_rails_router()
app.include_router(rails_router)
