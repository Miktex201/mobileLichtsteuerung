from __future__ import annotations

import math
import time

from config import DmxConfig
from state import Mode, State, Zone


FixtureValues = tuple[int, int, int, int, int, int, int]


def build_dmx_frame(state: State, config: DmxConfig, started_at: float) -> list[int]:
    channels = [0] * 512

    if not state.powered:
        return channels

    elapsed = time.monotonic() - started_at
    fixture_starts = get_fixture_starts(state, config)

    if state.flash:
        fixture_values = [make_fixture(255, 255, 255, strobe=255) for _ in fixture_starts]
    elif state.mode == Mode.COLOR_CHANGE:
        fixture_values = build_color_change_values(state, elapsed, len(fixture_starts))
    else:
        fixture_values = build_auto_values(state, elapsed, len(fixture_starts))

    for start_channel, values in zip(fixture_starts, fixture_values):
        set_fixture(channels, start_channel, values)
    return channels


def get_fixture_starts(state: State, config: DmxConfig) -> tuple[int, ...]:
    if state.zone == Zone.OUTSIDE:
        return config.outside_fixture_starts
    if config.inside_fixture_starts:
        return config.inside_fixture_starts
    return config.outside_fixture_starts


def build_color_change_values(state: State, elapsed: float, fixture_count: int) -> list[FixtureValues]:
    _ = elapsed
    speed = dmx_effect_speed(state.speed)
    return [
        make_fixture(0, 0, 0, master=255, strobe=0, mode=85, speed=speed)
        for _index in range(fixture_count)
    ]


def build_auto_values(state: State, elapsed: float, fixture_count: int) -> list[FixtureValues]:
    if fixture_count == 0:
        return []

    step_time = max(0.12, 1.25 - state.speed * 0.10)
    step = int(elapsed / step_time)
    pattern = auto_pattern(step, fixture_count)
    red, green, blue = color_wheel(step * 0.11)

    values = []
    for index in range(fixture_count):
        if index in pattern:
            values.append(make_fixture(red, green, blue, master=255, strobe=0, mode=0, speed=0))
        else:
            values.append(make_fixture(0, 0, 0, master=0, strobe=0, mode=0, speed=0))
    return values


def auto_pattern(step: int, fixture_count: int) -> set[int]:
    patterns = [
        [0],
        [1],
        [2],
        [3],
        [3],
        [2],
        [1],
        [0],
        [0, 1],
        [2, 3],
        [0, 1],
        [2, 3],
        [0, 1, 2, 3],
        [],
        [0, 2],
        [1, 3],
    ]
    return {index for index in patterns[step % len(patterns)] if index < fixture_count}


def make_fixture(
    red: int,
    green: int,
    blue: int,
    *,
    master: int = 255,
    strobe: int = 0,
    mode: int = 0,
    speed: int = 0,
) -> FixtureValues:
    return (
        clamp(master),
        clamp(red),
        clamp(green),
        clamp(blue),
        clamp(strobe),
        clamp(mode),
        clamp(speed),
    )


def color_wheel(position: float) -> tuple[int, int, int]:
    position = position % 1.0
    red = int((math.sin(position * math.tau) * 0.5 + 0.5) * 255)
    green = int((math.sin((position + 1 / 3) * math.tau) * 0.5 + 0.5) * 255)
    blue = int((math.sin((position + 2 / 3) * math.tau) * 0.5 + 0.5) * 255)
    return red, green, blue


def set_fixture(channels: list[int], start_channel: int, values: FixtureValues) -> None:
    for offset, value in enumerate(values):
        set_channel(channels, start_channel + offset, value)


def set_channel(channels: list[int], channel: int, value: int) -> None:
    if 1 <= channel <= 512:
        channels[channel - 1] = clamp(value)


def clamp(value: int) -> int:
    return max(0, min(255, int(value)))


def dmx_effect_speed(speed: int) -> int:
    return max(1, min(255, int(speed * 25.5)))
