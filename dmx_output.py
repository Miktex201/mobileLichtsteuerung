from __future__ import annotations

import os
import threading
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


class SerialDmxOutput(DmxOutput):
    """Raw serial DMX output with a steady background send loop."""

    def __init__(self, port: str, channels: int = 512, fps: int = 44, enabled: bool | None = None) -> None:
        self.port = port
        self.channels = channels
        self.fps = max(1, min(44, int(fps)))
        self.frame_time = 1 / self.fps
        self.data = bytearray([0] * channels)
        self.lock = threading.Lock()
        self.serial = None
        self.thread: threading.Thread | None = None
        self.running = False

        if enabled is None:
            enabled = os.path.exists(port)
        self.enabled = enabled

        self.start()

    def start(self) -> None:
        if not self.enabled:
            print(f"DMX ist deaktiviert, {self.port} existiert nicht.")
            return

        import serial

        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=250000,
                bytesize=8,
                parity=serial.PARITY_NONE,
                stopbits=2,
            )
        except Exception as exc:
            self.enabled = False
            print(f"DMX konnte nicht gestartet werden: {exc}")
            return

        self.running = True
        self.thread = threading.Thread(target=self._send_loop, daemon=True)
        self.thread.start()
        print(f"DMX-Ausgabe gestartet auf {self.port} mit {self.fps} FPS")

    def send(self, channels: list[int]) -> None:
        with self.lock:
            self.data = bytearray(clamp_channels(channels, self.channels))

    def close(self) -> None:
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        if self.serial:
            self.serial.close()

    def _send_loop(self) -> None:
        while self.running:
            self.send_frame()
            time.sleep(self.frame_time)

    def send_frame(self) -> None:
        if not self.serial:
            return

        with self.lock:
            frame = bytes([0]) + bytes(self.data)

        self.serial.break_condition = True
        time.sleep(0.0001)
        self.serial.break_condition = False
        time.sleep(0.000012)
        self.serial.write(frame)
        self.serial.flush()


def clamp_channels(channels: list[int], size: int) -> list[int]:
    clipped = [max(0, min(255, int(value))) for value in channels[:size]]
    return clipped + [0] * (size - len(clipped))


def make_dmx_output(config: DmxConfig) -> DmxOutput:
    if config.backend == "log":
        return LogDmxOutput()
    try:
        if config.backend in ("open_dmx", "serial", "raw_serial"):
            return SerialDmxOutput(config.port)
        if config.backend == "enttec_pro":
            return EnttecProDmxOutput(config.port)
    except Exception as exc:
        print(f"DMX-Adapter nicht verfuegbar ({config.port}): {exc}")
        print("Starte ohne echten DMX-Ausgang. Setze DMX_BACKEND=log zum Testen.")
        return LogDmxOutput()

    raise ValueError(f"Unbekannter DMX_BACKEND: {config.backend}")
