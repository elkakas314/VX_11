"""REAPER Project Manager: Gestión de proyectos REAPER."""

from typing import Dict, List, Any, Optional
from pathlib import Path


class ProjectManager:
    """Gestor de proyectos REAPER."""

    def __init__(self, projects_path: str = None):
        self.projects_path = Path(projects_path) if projects_path else Path.home() / ".config" / "REAPER" / "Projects"

    async def list_projects(self) -> List[Dict[str, Any]]:
        """Listar proyectos REAPER disponibles."""
        projects = []
        
        if self.projects_path.exists():
            for rpp_file in self.projects_path.glob("*.rpp"):
                projects.append({
                    "name": rpp_file.stem,
                    "path": str(rpp_file),
                    "size_mb": rpp_file.stat().st_size / (1024 * 1024),
                    "modified": rpp_file.stat().st_mtime
                })

        return sorted(projects, key=lambda x: x["modified"], reverse=True)

    async def load_project(self, project_path: str) -> Dict[str, Any]:
        """Cargar proyecto REAPER."""
        try:
            path = Path(project_path)
            if not path.exists():
                return {"error": f"Project not found: {project_path}"}

            return {
                "status": "loaded",
                "path": project_path,
                "name": path.stem
            }
        except Exception as e:
            return {"error": str(e)}

    async def create_project(self, name: str, sample_rate: int = 48000,
                           bpm: float = 120.0) -> Dict[str, Any]:
        """Crear nuevo proyecto REAPER."""
        return {
            "status": "created",
            "name": name,
            "sample_rate": sample_rate,
            "bpm": bpm
        }

    async def save_project(self, project_path: str) -> bool:
        """Guardar proyecto REAPER."""
        # En producción: enviar comando a REAPER
        return True

    async def get_project_metadata(self, project_path: str) -> Dict[str, Any]:
        """Obtener metadata del proyecto."""
        return {
            "path": project_path,
            "sample_rate": 48000,
            "bpm": 120.0,
            "time_signature": "4/4",
            "tracks": 16,
            "length_seconds": 180.0
        }
