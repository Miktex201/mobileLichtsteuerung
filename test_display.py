from __future__ import annotations

import sys
import os
import time


def try_display(port: int, address: int) -> bool:
    try:
        from RPLCD.i2c import CharLCD

        lcd = CharLCD(
            i2c_expander="PCF8574",
            address=address,
            port=port,
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
    port = int(os.getenv("LCD_I2C_PORT", "1"))
    addresses = list(range(0x20, 0x28)) + list(range(0x38, 0x40))
    print(f"Nutze I2C-Bus /dev/i2c-{port}")
    for address in addresses:
        print(f"Teste LCD-Adresse 0x{address:02x} ...")
        if try_display(port, address):
            print(f"Display erfolgreich auf 0x{address:02x} angesprochen.")
            return 0

    print("Kein Display auf den typischen PCF8574-Adressen erreicht.")
    print(f"Fuehre jetzt aus: i2cdetect -y {port}")
    print("Wenn dort keine Adresse erscheint: Verkabelung, VCC/GND oder I2C-Adapter pruefen.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
