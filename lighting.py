from __future__ import annotations

import math
import time

from config import DmxConfig
from state import Mode, State, ZoneState


ParFixtureValues = tuple[int, int, int, int, int, int, int]
LightbarValues = tuple[int, int, int, int, int, int, int]
DmxElement = tuple[str, int]
OUTSIDE_MAX_CHANNEL = 40


def build_dmx_frame(state: State, config: DmxConfig, started_at: float) -> list[int]:
    channels = [0] * 512

    elapsed = time.monotonic() - started_at
    outside_par, outside_lightbars, inside_par = get_configured_starts(config)
    render_zone(channels, state.outside, elapsed, outside_par, outside_lightbars)
    render_zone(channels, state.inside, elapsed, inside_par, ())

    return channels


def get_configured_starts(config: DmxConfig) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    outside_par = filter_start_channels(config.outside_fixture_starts, 1, OUTSIDE_MAX_CHANNEL)
    outside_lightbars = filter_start_channels(config.outside_lightbar_starts, 1, OUTSIDE_MAX_CHANNEL)
    inside_par = filter_start_channels(config.inside_fixture_starts, OUTSIDE_MAX_CHANNEL + 1, 512)
    return outside_par, outside_lightbars, inside_par


def render_zone(
    channels: list[int],
    zone_state: ZoneState,
    elapsed: float,
    par_starts: tuple[int, ...],
    lightbar_starts: tuple[int, ...],
) -> None:
    if not zone_state.powered:
        return

    elements = build_visual_order(par_starts, lightbar_starts)
    if zone_state.flash:
        apply_flash_scene(channels, zone_state, elapsed, par_starts, lightbar_starts)
    elif zone_state.mode == Mode.COLOR_CHANGE:
        apply_color_change_scene(channels, zone_state, elapsed, elements)
    else:
        apply_auto_scene(channels, zone_state, elapsed, elements)


def filter_start_channels(starts: tuple[int, ...], minimum: int, maximum: int) -> tuple[int, ...]:
    return tuple(start for start in starts if minimum <= start <= maximum)


def build_visual_order(par_starts: tuple[int, ...], lightbar_starts: tuple[int, ...]) -> list[DmxElement]:
    elements: list[DmxElement] = []
    elements.extend(("par", start) for start in par_starts)
    elements.extend(("lightbar", start) for start in lightbar_starts)
    return sorted(elements, key=lambda item: item[1])


def apply_flash_scene(
    channels: list[int],
    state: ZoneState,
    elapsed: float,
    par_starts: tuple[int, ...],
    lightbar_starts: tuple[int, ...],
) -> None:
    flash_value = flash_speed_to_dmx(state.speed)

    for start in par_starts:
        set_par_fixture(channels, start, make_fixture(255, 255, 255, strobe=flash_value))
    for start in lightbar_starts:
        set_lightbar(channels, start, make_lightbar(255, 255, 255, flash=flash_value))


def flash_speed_to_dmx(speed: int) -> int:
    speed = max(1, min(10, int(speed)))
    return round(8 + (speed - 1) * (247 / 9))


def apply_color_change_scene(
    channels: list[int],
    state: ZoneState,
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
    state: ZoneState,
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
