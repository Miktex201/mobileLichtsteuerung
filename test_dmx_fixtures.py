from __future__ import annotations

import time

from dotenv import load_dotenv

from config import load_config
from dmx_output import make_dmx_output
from lighting import make_fixture, make_lightbar, set_lightbar, set_par_fixture


def main() -> int:
    load_dotenv()
    config = load_config()
    dmx = make_dmx_output(config.dmx)
    par_starts = config.dmx.outside_fixture_starts
    lightbar_starts = config.dmx.outside_lightbar_starts
    elements = [("par", start) for start in par_starts] + [
        ("lightbar", start) for start in lightbar_starts
    ]
    elements.sort(key=lambda item: item[1])

    print(f"Teste PAR-Fixtures auf {par_starts}")
    print(f"Teste Lightbars auf {lightbar_starts}")
    print("Erst alle weiss, dann jedes Element einzeln.")

    try:
        send_scene(dmx, elements, [white_values(kind) for kind, _start in elements], 4)

        colors = [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 255, 255),
            (255, 0, 255),
        ]
        for index, (kind, start) in enumerate(elements):
            values = [off_values(element_kind) for element_kind, _start in elements]
            values[index] = color_values(kind, colors[index % len(colors)])
            print(f"Element {index + 1} ({kind}) auf Startkanal {start}")
            send_scene(dmx, elements, values, 3)
    finally:
        dmx.send([0] * 512)
        time.sleep(0.2)
        dmx.close()

    return 0


def white_values(kind: str) -> tuple[int, ...]:
    return color_values(kind, (255, 255, 255))


def off_values(kind: str) -> tuple[int, ...]:
    if kind == "lightbar":
        return make_lightbar(0, 0, 0, dimmer=0)
    return make_fixture(0, 0, 0, master=0)


def color_values(kind: str, color: tuple[int, int, int]) -> tuple[int, ...]:
    red, green, blue = color
    if kind == "lightbar":
        return make_lightbar(red, green, blue)
    return make_fixture(red, green, blue)


def send_scene(
    dmx: object,
    elements: list[tuple[str, int]],
    values: list[tuple[int, ...]],
    seconds: float,
) -> None:
    frame = [0] * 512
    for (kind, start), fixture_values in zip(elements, values):
        if kind == "lightbar":
            set_lightbar(frame, start, fixture_values)
        else:
            set_par_fixture(frame, start, fixture_values)
    dmx.send(frame)
    time.sleep(seconds)


if __name__ == "__main__":
    raise SystemExit(main())
