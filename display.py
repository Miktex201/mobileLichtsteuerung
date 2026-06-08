from __future__ import annotations

from config import DisplayConfig
from state import State


class Display:
    def __init__(self, config: DisplayConfig) -> None:
        try:
            from RPLCD.i2c import CharLCD

            self.lcd = CharLCD(
                i2c_expander=config.i2c_expander,
                address=config.i2c_address,
                port=config.i2c_port,
                cols=20,
                rows=4,
                charmap="A02",
                auto_linebreaks=False,
                backlight_enabled=True,
            )
            self.available = True
        except Exception as exc:
            self.lcd = None
            self.available = False
            print(f"Display nicht verfuegbar: {exc}")

    def show(self, state: State) -> None:
        bar = self._speed_bar(state.speed)
        lines = [
            self._zone_label(state),
            f"Status: {'AN' if state.powered else 'AUS'}",
            "Flash aktiv" if state.flash else f"Modus : {state.mode.value}",
            bar,
        ]
        if not self.available:
            print(" | ".join(lines))
            return

        assert self.lcd is not None
        self.lcd.clear()
        for row, line in enumerate(lines):
            self.lcd.cursor_pos = (row, 0)
            self.lcd.write_string(line[:20].ljust(20))

    def close(self) -> None:
        if self.available and self.lcd is not None:
            self.lcd.clear()
            self.lcd.close(clear=True)

    @staticmethod
    def _speed_bar(speed: int) -> str:
        filled = max(0, min(20, speed * 2))
        return "#" * filled + "-" * (20 - filled)

    @staticmethod
    def _zone_label(state: State) -> str:
        if state.dual:
            return "Buehne innen/aussen"
        return state.zone.value
