import httpx
from typing import Dict, Any
from config.settings import settings
from config.tokens import get_token

VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}


class HealthAggregator:
    """
    Recolector simple de health across VX11 módulos vía Tentáculo Link.
    """

    def __init__(self):
        self.power_mode = "balanced"
        self.modules = {
            "tentaculo_link": (getattr(settings, "tentaculo_link_url", "") or f"http://tentaculo_link:{getattr(settings, 'tentaculo_link_port', settings.gateway_port)}").rstrip("/"),
            "madre": (getattr(settings, "madre_url", "") or f"http://madre:{settings.madre_port}").rstrip("/"),
            "switch": (getattr(settings, "switch_url", "") or f"http://switch:{settings.switch_port}").rstrip("/"),
            "hermes": (getattr(settings, "hermes_url", "") or f"http://hermes:{settings.hermes_port}").rstrip("/"),
            "hormiguero": (getattr(settings, "hormiguero_url", "") or f"http://hormiguero:{settings.hormiguero_port}").rstrip("/"),
            "manifestator": (getattr(settings, "manifestator_url", "") or f"http://manifestator:{settings.manifestator_port}").rstrip("/"),
            "mcp": (getattr(settings, "mcp_url", "") or f"http://mcp:{settings.mcp_port}").rstrip("/"),
            "shub": (getattr(settings, "shub_url", "") or f"http://shubniggurath:{settings.shub_port}").rstrip("/"),
            "spawner": (getattr(settings, "spawner_url", "") or f"http://spawner:{settings.spawner_port}").rstrip("/"),
        }

    async def collect(self) -> Dict[str, Any]:
        results = {}
        async with httpx.AsyncClient(timeout=3.0, headers=AUTH_HEADERS) as client:
            for name, base_url in self.modules.items():
                try:
                    resp = await client.get(f"{base_url}/health")
                    results[name] = {
                        "ok": resp.status_code == 200,
                        "status": resp.json() if resp.status_code == 200 else {},
                    }
                except Exception as e:
                    results[name] = {"ok": False, "error": str(e)}
        return {"power_mode": self.power_mode, "services": results}
