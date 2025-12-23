"""Manifestator Drift Detection for Shubniggurath"""

import logging
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ShubDriftDetector:
    """Detect code drift in Shubniggurath modules"""
    
    def __init__(self):
        self.baseline_hashes: Dict[str, str] = {}
        self.drift_log: List[Dict[str, Any]] = []
        
    def compute_module_hash(self, module_path: str) -> str:
        """Compute SHA256 hash of module .py files"""
        hasher = hashlib.sha256()
        
        import os
        import glob
        
        py_files = glob.glob(f"{module_path}/**/*.py", recursive=True)
        
        for file_path in sorted(py_files):
            try:
                with open(file_path, "rb") as f:
                    hasher.update(f.read())
            except Exception as e:
                logger.error(f"Hash computation error: {e}")
        
        return hasher.hexdigest()
    
    def set_baseline(self, module_name: str, module_path: str):
        """Set baseline hash for module"""
        hash_value = self.compute_module_hash(module_path)
        self.baseline_hashes[module_name] = hash_value
        logger.info(f"Baseline set for {module_name}: {hash_value[:16]}...")
    
    def check_drift(self, module_name: str, module_path: str) -> bool:
        """Check if module has drifted from baseline"""
        if module_name not in self.baseline_hashes:
            logger.warning(f"No baseline for {module_name}")
            return False
        
        current_hash = self.compute_module_hash(module_path)
        baseline_hash = self.baseline_hashes[module_name]
        
        has_drift = current_hash != baseline_hash
        
        if has_drift:
            self.drift_log.append({
                "module": module_name,
                "timestamp": datetime.utcnow(),
                "previous_hash": baseline_hash[:16],
                "current_hash": current_hash[:16],
                "status": "drift_detected",
            })
            logger.warning(f"DRIFT DETECTED in {module_name}")
        
        return has_drift
    
    def get_drift_report(self) -> Dict[str, Any]:
        """Generate drift detection report"""
        return {
            "report_timestamp": datetime.utcnow().isoformat(),
            "total_modules": len(self.baseline_hashes),
            "drift_events": len(self.drift_log),
            "recent_drifts": self.drift_log[-10:],
        }


class ManifestatorShubBridge:
    """Bridge between Manifestator and Shub drift detection"""
    
    def __init__(self, config: Dict[str, Any]):
        self.detector = ShubDriftDetector()
        self.manifestator_url = config.get("manifestator_url", "http://manifestator:8005")
        self.token = config.get("token", "vx11_token")
        
    async def initialize_baselines(self, shub_path: str):
        """Initialize drift detection baselines for Shub"""
        modules = [
            "core",
            "engines",
            "api",
            "integrations",
            "database",
            "utils",
        ]
        
        for module in modules:
            module_path = f"{shub_path}/{module}"
            self.detector.set_baseline(f"shub.{module}", module_path)
            logger.info(f"Baseline set: shub.{module}")
    
    async def check_all_drift(self, shub_path: str) -> Dict[str, Any]:
        """Check drift for all Shub modules"""
        modules = ["core", "engines", "api", "integrations", "database", "utils"]
        
        drift_results = {}
        
        for module in modules:
            module_path = f"{shub_path}/{module}"
            has_drift = self.detector.check_drift(f"shub.{module}", module_path)
            drift_results[module] = has_drift
        
        report = self.detector.get_drift_report()
        report["module_status"] = drift_results
        
        return report
    
    async def report_to_manifestator(self, drift_report: Dict[str, Any]) -> bool:
        """Report drift to Manifestator for action"""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.manifestator_url}/drift/report",
                    headers={"X-VX11-Token": self.token},
                    json={"module": "shubniggurath", "report": drift_report},
                    timeout=30,
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Report error: {e}")
            return False
