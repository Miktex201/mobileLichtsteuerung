from __future__ import annotations

import time

from dotenv import load_dotenv

from config import load_config
from dmx_output import make_dmx_output
from lighting import make_fixture, set_fixture


def main() -> int:
    load_dotenv()
    config = load_config()
    dmx = make_dmx_output(config.dmx)
    starts = config.dmx.outside_fixture_starts

    print(f"Teste DMX-Fixtures auf {starts}")
    print("Erst alle weiss, dann jede Lampe einzeln.")

    try:
        send_scene(dmx, starts, [make_fixture(255, 255, 255)] * len(starts), 4)

        colors = [
            make_fixture(255, 0, 0),
            make_fixture(0, 255, 0),
            make_fixture(0, 0, 255),
            make_fixture(255, 255, 255),
        ]
        for index, start in enumerate(starts):
            values = [make_fixture(0, 0, 0, master=0) for _ in starts]
            values[index] = colors[index % len(colors)]
            print(f"Lampe {index + 1} auf Startkanal {start}")
            send_scene(dmx, starts, values, 3)
    finally:
        dmx.send([0] * 512)
        time.sleep(0.2)
        dmx.close()

    return 0


def send_scene(dmx: object, starts: tuple[int, ...], values: list[tuple[int, ...]], seconds: float) -> None:
    frame = [0] * 512
    for start, fixture_values in zip(starts, values):
        set_fixture(frame, start, fixture_values)
    dmx.send(frame)
    time.sleep(seconds)


if __name__ == "__main__":
    raise SystemExit(main())
