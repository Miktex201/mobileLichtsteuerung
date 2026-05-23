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
                port=1,
                cols=20,
                rows=4,
                charmap="A02",
                auto_linebreaks=False,
            )
            self.available = True
        except Exception as exc:
            self.lcd = None
            self.available = False
            print(f"Display nicht verfuegbar: {exc}")

    def show(self, state: State) -> None:
        lines = [
            "Bauwagen Licht",
            f"Status: {'AN' if state.powered else 'AUS'}",
            f"Modus : {state.mode.value}",
            f"Speed : {state.speed}/10" + (" FLASH" if state.flash else ""),
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
