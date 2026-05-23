from __future__ import annotations

import sys
import time


def try_display(address: int) -> bool:
    try:
        from RPLCD.i2c import CharLCD

        lcd = CharLCD(
            i2c_expander="PCF8574",
            address=address,
            port=1,
            cols=20,
            rows=4,
            charmap="A02",
            auto_linebreaks=False,
            backlight_enabled=True,
        )
        lcd.clear()
        lcd.write_string("Display Test")
        lcd.cursor_pos = (1, 0)
        lcd.write_string(f"Adresse: 0x{address:02x}")
        lcd.cursor_pos = (2, 0)
        lcd.write_string("Wenn du das siehst")
        lcd.cursor_pos = (3, 0)
        lcd.write_string("ist I2C korrekt.")
        time.sleep(5)
        lcd.close(clear=False)
        return True
    except Exception as exc:
        print(f"0x{address:02x} geht nicht: {exc}")
        return False


def main() -> int:
    for address in (0x27, 0x3F):
        print(f"Teste LCD-Adresse 0x{address:02x} ...")
        if try_display(address):
            print(f"Display erfolgreich auf 0x{address:02x} angesprochen.")
            return 0

    print("Kein Display auf 0x27 oder 0x3f erreicht.")
    print("Pruefe: I2C aktiviert, SDA GPIO2, SCL GPIO3, VCC/GND, RPLCD installiert.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
