# SPDX-FileCopyrightText: Copyright (C) 2026 unlucio and the Bespok3d contributors
# SPDX-License-Identifier: GPL-3.0-only
"""A Klipper bench with a stock SET_PURIFIER_MODE, a print file and the plugin connected."""

import pathlib
import sys

import pytest

KLIPPY_DIR = pathlib.Path(__file__).resolve().parent.parent / "files" / "klipper" / "klippy"
sys.path.insert(0, str(KLIPPY_DIR))

# The plugin module imports as Klipper loads it, from klippy/, so the path goes in first.
from extras import u1_chamber_cooling  # noqa: E402
from klipper_fakes import (  # noqa: E402
    FakeConfig,
    FakePrinter,
    FakeVirtualSdcard,
    StockPurifierMode,
)

DEFAULT_FAN_LEVEL = "0.5"


class ChamberCoolingBench:
    """One Klipper with purifier.py's SET_PURIFIER_MODE and [u1_chamber_cooling], before connect."""

    def __init__(self, fan_level=DEFAULT_FAN_LEVEL, print_file_path=None):
        self.printer = FakePrinter()
        self.stock_purifier_mode = StockPurifierMode(self.printer.gcode)
        self.printer.objects["virtual_sdcard"] = FakeVirtualSdcard(print_file_path)
        config = FakeConfig(self.printer, {"fan_level": fan_level})
        self.chamber_cooling = u1_chamber_cooling.load_config(config)

    def connect(self):
        self.printer.send_event("klippy:connect")
        return self

    def run_gcode(self, commandline):
        self.printer.gcode.run(commandline)

    @property
    def handled_params(self):
        return self.stock_purifier_mode.handled_params

    @property
    def responses(self):
        return self.printer.gcode.responses


def write_print_file(print_file_path, footer_text, filler_bytes=0):
    """A print file: G-code moves, then the slicer's footer at the end, as Orca writes it."""
    print_file_path.write_text("G1 X10 Y10\n" * (filler_bytes // 11) + footer_text)
    return str(print_file_path)


def connected_bench(**bench_state):
    return ChamberCoolingBench(**bench_state).connect()


@pytest.fixture
def make_bench():
    return connected_bench
