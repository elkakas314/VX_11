import os


def vx11_base_url():
    """Return the configured VX11 API base URL.

    Reads `VX11_API_BASE` environment variable. Defaults to
    `http://localhost:8000`. Always strips trailing slash.
    """
    url = os.getenv("VX11_API_BASE", "http://localhost:8000")
    return url.rstrip("/")
