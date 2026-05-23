from __future__ import annotations

import math
import time

from config import DmxConfig
from state import Mode, State


def build_dmx_frame(state: State, config: DmxConfig, started_at: float) -> list[int]:
    channels = [0] * 512

    if not state.powered:
        return channels

    elapsed = time.monotonic() - started_at
    speed_factor = 0.08 + state.speed * 0.08

    if state.flash:
        red, green, blue = (255, 255, 255)
        strobe = 255
    elif state.mode == Mode.COLOR_CHANGE:
        red, green, blue = color_wheel(elapsed * speed_factor)
        strobe = 0
    else:
        pulse = int((math.sin(elapsed * speed_factor * math.tau) * 0.5 + 0.5) * 90)
        red, green, blue = color_wheel(elapsed * speed_factor * 0.6)
        red = min(255, red + pulse)
        green = min(255, green + pulse)
        blue = min(255, blue + pulse)
        strobe = 0

    set_channel(channels, config.master_channel, 255)
    set_channel(channels, config.red_channel, red)
    set_channel(channels, config.green_channel, green)
    set_channel(channels, config.blue_channel, blue)
    set_channel(channels, config.strobe_channel, strobe)
    return channels


def color_wheel(position: float) -> tuple[int, int, int]:
    position = position % 1.0
    red = int((math.sin(position * math.tau) * 0.5 + 0.5) * 255)
    green = int((math.sin((position + 1 / 3) * math.tau) * 0.5 + 0.5) * 255)
    blue = int((math.sin((position + 2 / 3) * math.tau) * 0.5 + 0.5) * 255)
    return red, green, blue


def set_channel(channels: list[int], channel: int, value: int) -> None:
    channels[channel - 1] = value
