from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Mode(Enum):
    COLOR_CHANGE = "Farbwechsel"
    AUTO = "Automatik"


class Zone(Enum):
    OUTSIDE = "Buehne aussen"
    INSIDE = "Buehne innen"


@dataclass
class ZoneState:
    powered: bool = False
    mode: Mode = Mode.COLOR_CHANGE
    speed: int = 5
    flash: bool = False


@dataclass(init=False)
class State:
    zone: Zone = Zone.OUTSIDE
    dual: bool = False
    outside: ZoneState = field(default_factory=ZoneState)
    inside: ZoneState = field(default_factory=ZoneState)

    def __init__(
        self,
        powered: bool = False,
        mode: Mode = Mode.COLOR_CHANGE,
        zone: Zone = Zone.OUTSIDE,
        dual: bool = False,
        speed: int = 5,
        flash: bool = False,
    ) -> None:
        self.zone = zone
        self.dual = dual
        self.outside = ZoneState()
        self.inside = ZoneState()

        for target in self._targets():
            target.powered = powered
            target.mode = mode
            target.speed = speed
            target.flash = flash

    @property
    def current(self) -> ZoneState:
        return self.outside if self.zone == Zone.OUTSIDE else self.inside

    def _targets(self) -> tuple[ZoneState, ...]:
        if self.dual:
            return self.outside, self.inside
        return (self.current,)

    def set_dual(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled and not self.dual:
            source = self.current
            for target in (self.outside, self.inside):
                target.powered = source.powered
                target.mode = source.mode
                target.speed = source.speed
                target.flash = source.flash
        self.dual = enabled

    @property
    def powered(self) -> bool:
        return self.current.powered

    @powered.setter
    def powered(self, value: bool) -> None:
        for target in self._targets():
            target.powered = bool(value)

    @property
    def mode(self) -> Mode:
        return self.current.mode

    @mode.setter
    def mode(self, value: Mode) -> None:
        for target in self._targets():
            target.mode = value

    @property
    def speed(self) -> int:
        return self.current.speed

    @speed.setter
    def speed(self, value: int) -> None:
        speed = max(1, min(10, int(value)))
        for target in self._targets():
            target.speed = speed

    @property
    def flash(self) -> bool:
        return self.current.flash

    @flash.setter
    def flash(self, value: bool) -> None:
        for target in self._targets():
            target.flash = bool(value)
