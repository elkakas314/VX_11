"""Utility functions for Shub"""

import logging
import asyncio
import hashlib
from typing import Callable, Any

logger = logging.getLogger(__name__)


def async_retry(max_attempts: int = 3, delay: float = 1.0):
    """Async retry decorator"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay)
            raise last_error
        return wrapper
    return decorator


def compute_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """Compute file hash"""
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()


def format_loudness(lufs: float) -> str:
    """Format loudness value for display"""
    return f"{lufs:.2f} LUFS"


def format_frequency(freq: float) -> str:
    """Format frequency with unit"""
    if freq < 1000:
        return f"{freq:.1f} Hz"
    elif freq < 1_000_000:
        return f"{freq/1000:.2f} kHz"
    else:
        return f"{freq/1_000_000:.2f} MHz"
