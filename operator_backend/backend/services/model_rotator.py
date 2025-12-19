from typing import Dict


class ModelRotator:
    """Simple model selector placeholder."""

    def __init__(self):
        self.available = ["auto", "balanced", "eco"]
        self.default = "auto"

    def status(self) -> Dict[str, str]:
        return {"default": self.default, "available": self.available}
