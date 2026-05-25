from __future__ import annotations

import math
import time

from config import DmxConfig
from state import Mode, State, Zone


ParFixtureValues = tuple[int, int, int, int, int, int, int]
LightbarValues = tuple[int, int, int, int, int, int, int]
DmxElement = tuple[str, int]


def build_dmx_frame(state: State, config: DmxConfig, started_at: float) -> list[int]:
    channels = [0] * 512

    if not state.powered:
        return channels

    elapsed = time.monotonic() - started_at
    par_starts, lightbar_starts = get_scene_starts(state, config)
    elements = build_visual_order(par_starts, lightbar_starts)

    if state.flash:
        apply_flash_scene(channels, par_starts, lightbar_starts)
    elif state.mode == Mode.COLOR_CHANGE:
        apply_color_change_scene(channels, state, elapsed, elements)
    else:
        apply_auto_scene(channels, state, elapsed, elements)

    return channels


def get_scene_starts(state: State, config: DmxConfig) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if state.zone == Zone.OUTSIDE:
        return config.outside_fixture_starts, config.outside_lightbar_starts
    if config.inside_fixture_starts:
        return config.inside_fixture_starts, ()
    return config.outside_fixture_starts, config.outside_lightbar_starts


def build_visual_order(par_starts: tuple[int, ...], lightbar_starts: tuple[int, ...]) -> list[DmxElement]:
    elements: list[DmxElement] = []
    elements.extend(("par", start) for start in par_starts)
    elements.extend(("lightbar", start) for start in lightbar_starts)
    return sorted(elements, key=lambda item: item[1])


def apply_flash_scene(
    channels: list[int],
    par_starts: tuple[int, ...],
    lightbar_starts: tuple[int, ...],
) -> None:
    for start in par_starts:
        set_par_fixture(channels, start, make_fixture(255, 255, 255, strobe=255))
    for start in lightbar_starts:
        set_lightbar(channels, start, make_lightbar(255, 255, 255, flash=255))


def apply_color_change_scene(
    channels: list[int],
    state: State,
    elapsed: float,
    elements: list[DmxElement],
) -> None:
    speed_factor = 0.005 + ((state.speed / 10) ** 1.7) * 0.10
    for index, (kind, start) in enumerate(elements):
        phase = index / max(1, len(elements)) * 0.35
        red, green, blue = color_wheel(elapsed * speed_factor + phase)
        set_element(channels, kind, start, red, green, blue, master=255)


def apply_auto_scene(
    channels: list[int],
    state: State,
    elapsed: float,
    elements: list[DmxElement],
) -> None:
    if not elements:
        return

    step_time = max(0.08, 0.78 - state.speed * 0.06)
    step = int(elapsed / step_time)
    pattern = auto_pattern(step, len(elements))
    red, green, blue = color_wheel(step * 0.19)

    for index, (kind, start) in enumerate(elements):
        if index in pattern:
            set_element(channels, kind, start, red, green, blue, master=255)
        else:
            set_element(channels, kind, start, 0, 0, 0, master=0)


def auto_pattern(step: int, element_count: int) -> set[int]:
    last = element_count - 1
    left_pair = [0, 1]
    right_pair = [max(0, last - 1), last]
    center = [element_count // 2]
    all_elements = list(range(element_count))

    patterns = [
        [0],
        [1],
        center,
        [max(0, last - 1)],
        [last],
        [last],
        [max(0, last - 1)],
        center,
        [1],
        [0],
        left_pair,
        right_pair,
        left_pair,
        right_pair,
        all_elements,
        [],
        all_elements,
        [],
        [index for index in all_elements if index % 2 == 0],
        [index for index in all_elements if index % 2 == 1],
        all_elements,
    ]
    return {index for index in patterns[step % len(patterns)] if index < element_count}


def set_element(
    channels: list[int],
    kind: str,
    start_channel: int,
    red: int,
    green: int,
    blue: int,
    *,
    master: int,
) -> None:
    if kind == "lightbar":
        set_lightbar(channels, start_channel, make_lightbar(red, green, blue, dimmer=master))
        return
    set_par_fixture(channels, start_channel, make_fixture(red, green, blue, master=master))


def make_fixture(
    red: int,
    green: int,
    blue: int,
    *,
    master: int = 255,
    strobe: int = 0,
    mode: int = 0,
    speed: int = 0,
) -> ParFixtureValues:
    return (
        clamp(master),
        clamp(red),
        clamp(green),
        clamp(blue),
        clamp(strobe),
        clamp(mode),
        clamp(speed),
    )


def make_lightbar(
    red: int,
    green: int,
    blue: int,
    *,
    dimmer: int = 255,
    program: int = 0,
    speed: int = 0,
    flash: int = 0,
) -> LightbarValues:
    return (
        clamp(red),
        clamp(green),
        clamp(blue),
        clamp(program),
        clamp(speed),
        clamp(flash),
        clamp(dimmer),
    )


def color_wheel(position: float) -> tuple[int, int, int]:
    position = position % 1.0
    red = int((math.sin(position * math.tau) * 0.5 + 0.5) * 255)
    green = int((math.sin((position + 1 / 3) * math.tau) * 0.5 + 0.5) * 255)
    blue = int((math.sin((position + 2 / 3) * math.tau) * 0.5 + 0.5) * 255)
    return red, green, blue


def set_fixture(channels: list[int], start_channel: int, values: ParFixtureValues) -> None:
    set_par_fixture(channels, start_channel, values)


def set_par_fixture(channels: list[int], start_channel: int, values: ParFixtureValues) -> None:
    for offset, value in enumerate(values):
        set_channel(channels, start_channel + offset, value)


def set_lightbar(channels: list[int], start_channel: int, values: LightbarValues) -> None:
    for offset, value in enumerate(values):
        set_channel(channels, start_channel + offset, value)


def set_channel(channels: list[int], channel: int, value: int) -> None:
    if 1 <= channel <= 512:
        channels[channel - 1] = clamp(value)


def clamp(value: int) -> int:
    return max(0, min(255, int(value)))
