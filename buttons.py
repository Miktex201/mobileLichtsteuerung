from __future__ import annotations

from typing import Callable


def bind_button(pin: int, callback: Callable[[], None]) -> object | None:
    try:
        from gpiozero import Button

        button = Button(pin, pull_up=False, bounce_time=0.08)
        button.when_pressed = callback
        return button
    except Exception as exc:
        print(f"Button GPIO{pin} nicht verfuegbar: {exc}")
        return None
