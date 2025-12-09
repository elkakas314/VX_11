"""
DNS Resolver with Docker fallback
Handles DNS resolution for inter-module communication in Docker networks
"""

import socket
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def resolve_module_url(
    module_name: str,
    port: int,
    protocol: str = "http",
    fallback_localhost: bool = False,
) -> str:
    """
    Resolve module URL with Docker DNS and fallback to localhost.
    
    Args:
        module_name: Name of the module (e.g., 'switch', 'hermes')
        port: Port number
        protocol: 'http' or 'https'
        fallback_localhost: If True, try localhost fallback if Docker DNS fails
    
    Returns:
        Full URL string
    """
    # Primary: Docker service name
    docker_name = f"{module_name}:{port}"
    docker_url = f"{protocol}://{module_name}:{port}"
    
    # Try to resolve Docker DNS
    try:
        socket.gethostbyname(module_name)
        logger.debug(f"✓ Docker DNS resolved: {module_name}")
        return docker_url
    except socket.gaierror:
        logger.warning(f"⚠ Docker DNS failed for {module_name}, trying fallback...")
    
    # Fallback 1: localhost (for local development)
    if fallback_localhost:
        localhost_url = f"{protocol}://localhost:{port}"
        try:
            socket.gethostbyname("localhost")
            logger.info(f"✓ Using localhost fallback: {localhost_url}")
            return localhost_url
        except socket.gaierror:
            pass
    
    # Fallback 2: 127.0.0.1
    logger.warning(f"⚠ Docker DNS failed for {module_name}, using 127.0.0.1 fallback")
    return f"{protocol}://127.0.0.1:{port}"


def test_module_connectivity(url: str, timeout: int = 5) -> bool:
    """
    Test if a module is reachable via HTTP health check.
    
    Args:
        url: Base URL of module
        timeout: Timeout in seconds
    
    Returns:
        True if reachable, False otherwise
    """
    import httpx
    
    try:
        health_url = f"{url}/health"
        response = httpx.get(health_url, timeout=timeout)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"✗ Module unreachable at {url}: {e}")
        return False
