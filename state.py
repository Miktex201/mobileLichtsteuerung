from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Mode(Enum):
    COLOR_CHANGE = "Farbwechsel"
    AUTO = "Automatik"


class Zone(Enum):
    OUTSIDE = "Buehne aussen"
    INSIDE = "Buehne innen"


@dataclass
class State:
    powered: bool = False
    mode: Mode = Mode.COLOR_CHANGE
    zone: Zone = Zone.OUTSIDE
    speed: int = 5
    flash: bool = False
