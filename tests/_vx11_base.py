import os


def vx11_base_url():
    """Return the configured VX11 API base URL.

    Reads `VX11_API_BASE` environment variable. Defaults to
    `http://localhost:8000`. Always strips trailing slash.
    """
    url = os.getenv("VX11_API_BASE", "http://localhost:8000")
    return url.rstrip("/")


def vx11_auth_headers():
    """Return authorization headers for frontdoor requests.

    Priority of env vars:
    - `VX11_TENTACULO_LINK_TOKEN` (explicit)
    - `VX11_TOKEN` (general)
    Header name can be overridden with `VX11_TOKEN_HEADER` (default `X-VX11-Token`).
    """
    # Prefer explicit env vars; fall back to common test tokens for local runs.
    token = (
        os.getenv("VX11_TENTACULO_LINK_TOKEN")
        or os.getenv("VX11_TOKEN")
        or os.getenv("VX11_TEST_TOKEN")
        or "vx11-test-token"
    )
    header_name = os.getenv("VX11_TOKEN_HEADER") or "X-VX11-Token"
    # Include both token header variants commonly used in repo.
    return {header_name: token, "X-VX11-GW-TOKEN": token}
