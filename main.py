from __future__ import annotations

import signal
import sys
import time

from dotenv import load_dotenv

from buttons import bind_button
from config import BUTTON_PINS, ROTARY_PINS, load_config
from display import Display
from dmx_output import make_dmx_output
from lighting import build_dmx_frame
from rotary_encoder import bind_rotary_button, bind_rotary_encoder
from state import Mode, State, Zone


def main() -> int:
    load_dotenv()

    config = load_config()
    state = State()
    display = Display(config.display)
    dmx = make_dmx_output(config.dmx)
    print(f"DMX backend: {config.dmx.backend}")
    print(f"DMX port: {config.dmx.port}")
    print(f"DMX aussen PAR fixtures: {config.dmx.outside_fixture_starts}")
    print(f"DMX aussen Lightbars: {config.dmx.outside_lightbar_starts}")
    print(f"DMX innen fixtures: {config.dmx.inside_fixture_starts or 'Fallback auf aussen'}")
    started_at = time.monotonic()
    running = True

    def refresh_display() -> None:
        display.show(state)

    def speed_up() -> None:
        state.speed = min(10, state.speed + 1)
        refresh_display()

    def speed_down() -> None:
        state.speed = max(1, state.speed - 1)
        refresh_display()

    def color_mode() -> None:
        state.mode = Mode.COLOR_CHANGE
        state.flash = False
        refresh_display()

    def auto_mode() -> None:
        state.mode = Mode.AUTO
        state.flash = False
        refresh_display()

    def power() -> None:
        state.powered = not state.powered
        refresh_display()

    def flash() -> None:
        state.flash = not state.flash
        if state.flash:
            state.powered = True
        refresh_display()

    def toggle_zone() -> None:
        state.zone = Zone.INSIDE if state.zone == Zone.OUTSIDE else Zone.OUTSIDE
        refresh_display()

    def stop(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    buttons = [
        bind_button(BUTTON_PINS["speed_up"], speed_up),
        bind_button(BUTTON_PINS["speed_down"], speed_down),
        bind_button(BUTTON_PINS["color_mode"], color_mode),
        bind_button(BUTTON_PINS["auto_mode"], auto_mode),
        bind_button(BUTTON_PINS["power"], power),
        bind_button(BUTTON_PINS["flash"], flash),
        bind_rotary_button(ROTARY_PINS["button"], toggle_zone),
        bind_rotary_encoder(
            ROTARY_PINS["a"],
            ROTARY_PINS["b"],
            clockwise=speed_up,
            counter_clockwise=speed_down,
        ),
    ]

    refresh_display()

    try:
        while running:
            dmx.send(build_dmx_frame(state, config.dmx, started_at))
            time.sleep(0.03)
    finally:
        dmx.send([0] * 512)
        dmx.close()
        display.close()
        for button in buttons:
            if button is not None and hasattr(button, "close"):
                button.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
