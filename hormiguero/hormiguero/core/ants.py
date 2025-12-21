"""Ant definitions for Hormiguero."""

from dataclasses import dataclass
from typing import Callable, Dict


@dataclass
class Ant:
    ant_id: str
    name: str
    role: str
    scanner: Callable[[], Dict[str, object]]
