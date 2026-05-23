from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Mode(Enum):
    COLOR_CHANGE = "Farbwechsel"
    AUTO = "Automatik"


@dataclass
class State:
    powered: bool = True
    mode: Mode = Mode.AUTO
    speed: int = 5
    flash: bool = False
