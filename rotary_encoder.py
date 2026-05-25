from __future__ import annotations

from typing import Callable


def bind_rotary_encoder(
    pin_a: int,
    pin_b: int,
    clockwise: Callable[[], None],
    counter_clockwise: Callable[[], None],
) -> object | None:
    try:
        from gpiozero import RotaryEncoder

        encoder = RotaryEncoder(pin_a, pin_b, max_steps=100000, wrap=True)
        encoder.when_rotated_clockwise = clockwise
        encoder.when_rotated_counter_clockwise = counter_clockwise
        return encoder
    except Exception as exc:
        print(f"Drehgeber GPIO{pin_a}/GPIO{pin_b} nicht verfuegbar: {exc}")
        return None


def bind_rotary_button(pin: int, callback: Callable[[], None]) -> object | None:
    try:
        from gpiozero import Button

        button = Button(pin, pull_up=True, bounce_time=0.08)
        button.when_pressed = callback
        return button
    except Exception as exc:
        print(f"Drehgeber-Knopf GPIO{pin} nicht verfuegbar: {exc}")
        return None
