from __future__ import annotations

from config import DmxConfig
from lighting import build_dmx_frame
from state import Mode, State, Zone, ZoneState


def make_test_config() -> DmxConfig:
    return DmxConfig(
        backend="log",
        port="/dev/null",
        outside_fixture_starts=(1, 9, 25, 33),
        outside_lightbar_starts=(17,),
        inside_fixture_starts=(41, 49),
        master_channel=1,
        red_channel=2,
        green_channel=3,
        blue_channel=4,
        strobe_channel=5,
    )


def test_color_change_all_outside_fixtures_are_on() -> None:
    state = State(powered=True, mode=Mode.COLOR_CHANGE, zone=Zone.OUTSIDE, speed=5)
    frame = build_dmx_frame(state, make_test_config(), started_at=0)

    for start_channel in (1, 9, 25, 33):
        assert frame[start_channel - 1] == 255
        assert any(frame[start_channel + offset - 1] > 0 for offset in (1, 2, 3))
        assert frame[start_channel + 4 - 1] == 0
        assert frame[start_channel + 5 - 1] == 0
        assert frame[start_channel + 6 - 1] == 0

    assert any(frame[17 + offset - 1] > 0 for offset in (0, 1, 2))
    assert frame[17 + 3 - 1] == 0
    assert frame[17 + 4 - 1] == 0
    assert frame[17 + 5 - 1] == 0
    assert frame[17 + 6 - 1] == 255


def test_auto_mode_uses_manual_rgb_without_strobe() -> None:
    state = State(powered=True, mode=Mode.AUTO, zone=Zone.OUTSIDE, speed=5)
    frame = build_dmx_frame(state, make_test_config(), started_at=0)

    for start_channel in (1, 9, 25, 33):
        assert frame[start_channel + 4 - 1] == 0
        assert frame[start_channel + 5 - 1] == 0
        assert frame[start_channel + 6 - 1] == 0

    assert frame[17 + 3 - 1] == 0
    assert frame[17 + 4 - 1] == 0
    assert frame[17 + 5 - 1] == 0
    assert frame[17 + 6 - 1] in (0, 255)


def test_inside_only_uses_inside_addresses() -> None:
    state = State(powered=True, mode=Mode.COLOR_CHANGE, zone=Zone.INSIDE, speed=5)
    frame = build_dmx_frame(state, make_test_config(), started_at=0)

    assert frame[0] == 0
    assert frame[8] == 0
    assert frame[16] == 0
    assert frame[24] == 0
    assert frame[32] == 0
    assert frame[40] == 255
    assert frame[48] == 255


def test_switching_to_inside_keeps_outside_running() -> None:
    state = State(powered=True, mode=Mode.COLOR_CHANGE, zone=Zone.OUTSIDE, speed=5)
    state.zone = Zone.INSIDE
    frame = build_dmx_frame(state, make_test_config(), started_at=0)

    assert frame[0] == 255
    assert frame[8] == 255
    assert frame[24] == 255
    assert frame[32] == 255
    assert frame[40] == 0
    assert frame[48] == 0


def test_inside_and_outside_can_have_separate_modes() -> None:
    state = State(zone=Zone.OUTSIDE)
    state.outside = ZoneState(powered=True, mode=Mode.COLOR_CHANGE, speed=5, flash=False)
    state.inside = ZoneState(powered=True, mode=Mode.AUTO, speed=5, flash=False)
    frame = build_dmx_frame(state, make_test_config(), started_at=0)

    assert frame[0] == 255
    assert frame[40] in (0, 255)
    assert any(frame[:40])
    assert any(frame[40:])


def test_dual_uses_inside_and_outside_addresses() -> None:
    state = State(powered=True, mode=Mode.COLOR_CHANGE, zone=Zone.OUTSIDE, speed=5)
    state.set_dual(True)
    frame = build_dmx_frame(state, make_test_config(), started_at=0)

    assert frame[0] == 255
    assert frame[8] == 255
    assert any(frame[17 + offset - 1] > 0 for offset in (0, 1, 2))
    assert frame[17 + 6 - 1] == 255
    assert frame[24] == 255
    assert frame[32] == 255
    assert frame[40] == 255
    assert frame[48] == 255


def test_flash_is_continuous_and_speed_controlled() -> None:
    slow_state = State(powered=True, mode=Mode.AUTO, zone=Zone.OUTSIDE, speed=1, flash=True)
    fast_state = State(powered=True, mode=Mode.AUTO, zone=Zone.OUTSIDE, speed=10, flash=True)

    slow_frame = build_dmx_frame(slow_state, make_test_config(), started_at=0)
    fast_frame = build_dmx_frame(fast_state, make_test_config(), started_at=0)
    later_frame = build_dmx_frame(fast_state, make_test_config(), started_at=-10)

    assert slow_frame[0] == 255
    assert slow_frame[16] == 255
    assert slow_frame[4] == 8
    assert slow_frame[21] == 8
    assert fast_frame[0] == 255
    assert fast_frame[16] == 255
    assert fast_frame[4] == 255
    assert fast_frame[21] == 255
    assert later_frame[0] == 255
    assert later_frame[16] == 255
