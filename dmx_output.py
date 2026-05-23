from __future__ import annotations

import time

from config import DmxConfig


class DmxOutput:
    def send(self, channels: list[int]) -> None:
        raise NotImplementedError

    def close(self) -> None:
        pass


class LogDmxOutput(DmxOutput):
    def __init__(self) -> None:
        self._last = 0.0

    def send(self, channels: list[int]) -> None:
        now = time.monotonic()
        if now - self._last >= 1.0:
            print("DMX:", channels[:8])
            self._last = now


class EnttecProDmxOutput(DmxOutput):
    """ENTTEC DMX USB Pro compatible packet protocol."""

    START = 0x7E
    END = 0xE7
    SEND_DMX_PACKET = 6

    def __init__(self, port: str) -> None:
        import serial

        self.serial = serial.Serial(port=port, baudrate=57600, timeout=0.05)

    def send(self, channels: list[int]) -> None:
        data = bytes([0] + clamp_channels(channels, 512))
        size = len(data)
        packet = bytes(
            [self.START, self.SEND_DMX_PACKET, size & 0xFF, (size >> 8) & 0xFF]
        ) + data + bytes([self.END])
        self.serial.write(packet)

    def close(self) -> None:
        self.serial.close()


class OpenDmxOutput(DmxOutput):
    """Simple FTDI/Open DMX style output."""

    def __init__(self, port: str) -> None:
        import serial

        self.serial = serial.Serial(
            port=port,
            baudrate=250000,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            timeout=0.05,
        )

    def send(self, channels: list[int]) -> None:
        data = bytes([0] + clamp_channels(channels, 512))
        try:
            self.serial.break_condition = True
            time.sleep(0.00012)
            self.serial.break_condition = False
            time.sleep(0.000012)
            self.serial.write(data)
        except OSError:
            self.serial.close()
            raise

    def close(self) -> None:
        self.serial.close()


def clamp_channels(channels: list[int], size: int) -> list[int]:
    clipped = [max(0, min(255, int(value))) for value in channels[:size]]
    return clipped + [0] * (size - len(clipped))


def make_dmx_output(config: DmxConfig) -> DmxOutput:
    if config.backend == "log":
        return LogDmxOutput()
    try:
        if config.backend == "open_dmx":
            return OpenDmxOutput(config.port)
        if config.backend == "enttec_pro":
            return EnttecProDmxOutput(config.port)
    except Exception as exc:
        print(f"DMX-Adapter nicht verfuegbar ({config.port}): {exc}")
        print("Starte ohne echten DMX-Ausgang. Setze DMX_BACKEND=log zum Testen.")
        return LogDmxOutput()

    raise ValueError(f"Unbekannter DMX_BACKEND: {config.backend}")
