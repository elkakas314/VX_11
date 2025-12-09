from pathlib import Path
import os
from typing import Dict


def _read_env_file(path: Path) -> Dict[str, str]:
    data = {}
    if not path.exists():
        return data
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                v = v.strip().strip('"').strip("'")
                data[k.strip()] = v
    return data


def load_tokens(repo_root: Path = None) -> Dict[str, str]:
    """
    Load tokens from environment. File-based tokens are deprecated and disabled by default.

    Behavior:
    - Reads existing environment variables only.
    - Optional fallback to tokens.env / tokens.env.master if
      VX11_ALLOW_TOKEN_FILES=true (for local dev only).
    """
    tokens: Dict[str, str] = {}

    # Opt-in file fallback for legacy dev flows (not for production)
    allow_files = os.environ.get("VX11_ALLOW_TOKEN_FILES", "").lower() in ("1", "true", "yes")
    if allow_files:
        if repo_root is None:
            repo_root = Path(__file__).resolve().parents[1]
        master_path = repo_root / "tokens.env.master"
        env_path = repo_root / "tokens.env"
        tokens.update(_read_env_file(master_path))
        tokens.update(_read_env_file(env_path))

    # Export to environment if not already set
    for k, v in tokens.items():
        if os.environ.get(k) is None and v != "":
            os.environ[k] = v

    return {k: os.environ.get(k, v) for k, v in tokens.items()}


def get_token(key: str, default: str = "") -> str:
    return os.environ.get(key, default)
