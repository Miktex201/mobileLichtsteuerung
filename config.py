from __future__ import annotations

import os
from dataclasses import dataclass


BUTTON_PINS = {
    "speed_up": 25,      # Button 1, rot
    "speed_down": 24,    # Button 2, lila
    "color_mode": 23,    # Button 3, blau
    "auto_mode": 22,     # Button 4, grau
    "power": 17,         # Button 5, schwarz
    "flash": 27,         # Button 6, weiss
}


ROTARY_PINS = {
    "button": 4,   # Lila, Drehgeber-Druckknopf
    "a": 5,        # Grau
    "b": 6,        # Schwarz
}


@dataclass(frozen=True)
class DisplayConfig:
    i2c_address: int
    i2c_expander: str
    i2c_port: int


@dataclass(frozen=True)
class DmxConfig:
    backend: str
    port: str
    outside_fixture_starts: tuple[int, ...]
    outside_lightbar_starts: tuple[int, ...]
    inside_fixture_starts: tuple[int, ...]
    master_channel: int
    red_channel: int
    green_channel: int
    blue_channel: int
    strobe_channel: int


@dataclass(frozen=True)
class AppConfig:
    display: DisplayConfig
    dmx: DmxConfig


def load_config() -> AppConfig:
    return AppConfig(
        display=DisplayConfig(
            i2c_address=int(os.getenv("LCD_I2C_ADDRESS", "0x27"), 0),
            i2c_expander=os.getenv("LCD_I2C_EXPANDER", "PCF8574"),
            i2c_port=int(os.getenv("LCD_I2C_PORT", "1")),
        ),
        dmx=DmxConfig(
            backend=os.getenv("DMX_BACKEND", "enttec_pro").lower(),
            port=os.getenv("DMX_PORT", "/dev/ttyUSB0"),
            outside_fixture_starts=read_dmx_channel_list("DMX_OUTSIDE_PAR_FIXTURES", "1,9,25,33"),
            outside_lightbar_starts=read_dmx_channel_list("DMX_OUTSIDE_LIGHTBARS", "17"),
            inside_fixture_starts=read_dmx_channel_list("DMX_INSIDE_FIXTURES", ""),
            master_channel=read_dmx_channel("DMX_CHANNEL_MASTER", 1),
            red_channel=read_dmx_channel("DMX_CHANNEL_RED", 2),
            green_channel=read_dmx_channel("DMX_CHANNEL_GREEN", 3),
            blue_channel=read_dmx_channel("DMX_CHANNEL_BLUE", 4),
            strobe_channel=read_dmx_channel("DMX_CHANNEL_STROBE", 5),
        ),
    )


def read_dmx_channel(env_name: str, default_channel: int) -> int:
    channel = int(os.getenv(env_name, str(default_channel)))
    if channel < 1 or channel > 512:
        raise ValueError(f"{env_name} muss zwischen 1 und 512 liegen")
    return channel


def read_dmx_channel_list(env_name: str, default_value: str) -> tuple[int, ...]:
    raw_value = os.getenv(env_name, default_value).strip()
    if not raw_value:
        return ()

    channels = tuple(int(part.strip()) for part in raw_value.split(",") if part.strip())
    for channel in channels:
        if channel < 1 or channel > 506:
            raise ValueError(f"{env_name} enthaelt ungueltigen Startkanal {channel}")
    return channels
