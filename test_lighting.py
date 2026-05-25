from __future__ import annotations

from config import DmxConfig
from lighting import build_dmx_frame
from state import Mode, State, Zone


def make_test_config() -> DmxConfig:
    return DmxConfig(
        backend="log",
        port="/dev/null",
        outside_fixture_starts=(1, 9, 17, 25),
        inside_fixture_starts=(),
        master_channel=1,
        red_channel=2,
        green_channel=3,
        blue_channel=4,
        strobe_channel=5,
    )


def test_color_change_all_outside_fixtures_are_on() -> None:
    state = State(powered=True, mode=Mode.COLOR_CHANGE, zone=Zone.OUTSIDE, speed=5)
    frame = build_dmx_frame(state, make_test_config(), started_at=0)

    for start_channel in (1, 9, 17, 25):
        assert frame[start_channel - 1] == 255
        assert frame[start_channel + 1 - 1] == 0
        assert frame[start_channel + 2 - 1] == 0
        assert frame[start_channel + 3 - 1] == 0
        assert frame[start_channel + 4 - 1] == 0
        assert frame[start_channel + 5 - 1] == 85
        assert frame[start_channel + 6 - 1] == 127


def test_auto_mode_uses_manual_rgb_without_strobe() -> None:
    state = State(powered=True, mode=Mode.AUTO, zone=Zone.OUTSIDE, speed=5)
    frame = build_dmx_frame(state, make_test_config(), started_at=0)

    for start_channel in (1, 9, 17, 25):
        assert frame[start_channel + 4 - 1] == 0
        assert frame[start_channel + 5 - 1] == 0
        assert frame[start_channel + 6 - 1] == 0


def test_inside_without_addresses_falls_back_to_outside_fixtures() -> None:
    state = State(powered=True, mode=Mode.COLOR_CHANGE, zone=Zone.INSIDE, speed=5)
    frame = build_dmx_frame(state, make_test_config(), started_at=0)

    assert frame[0] == 255
    assert frame[8] == 255
    assert frame[16] == 255
    assert frame[24] == 255
