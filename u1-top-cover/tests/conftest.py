# SPDX-FileCopyrightText: Copyright (C) 2026 unlucio and the Bespok3d contributors
# SPDX-License-Identifier: GPL-3.0-only
"""A Klipper bench with a stock M106 and SET_PURIFIER_MODE, a top cover and the plugin connected."""

import pathlib
import sys

import pytest

KLIPPY_DIR = pathlib.Path(__file__).resolve().parent.parent / "files" / "klipper" / "klippy"
sys.path.insert(0, str(KLIPPY_DIR))

# The plugin module imports as Klipper loads it, from klippy/, so the path goes in first.
from extras import u1_top_cover  # noqa: E402
from klipper_fakes import (  # noqa: E402
    FakePrinter,
    FakePurifier,
    FakeVirtualSdcard,
    StockFan,
    StockPurifierMode,
)

DEFAULT_FAN_LEVEL = "Balanced"


class TopCoverBench:
    """One Klipper with fan.py's M106, a [purifier] and [u1_top_cover], before connect."""

    def __init__(
            self, power_detected=True, purifier_mode=u1_top_cover.PURIFIER_MODE_IDLE,
            stored_delay_seconds=0, fan_level=DEFAULT_FAN_LEVEL, print_file_path=None):
        self.printer = FakePrinter()
        self.stock_fan = StockFan(self.printer.gcode)
        self.stock_purifier_mode = StockPurifierMode(self.printer.gcode)
        self.purifier = FakePurifier(
            self.printer.reactor, power_detected, purifier_mode, stored_delay_seconds)
        self.printer.objects["purifier"] = self.purifier
        self.printer.objects["virtual_sdcard"] = FakeVirtualSdcard(print_file_path)
        top_cover_config = self.printer.config_for("u1_top_cover", {"fan_level": fan_level})
        self.top_cover = u1_top_cover.load_config(top_cover_config)

    def connect(self):
        self.printer.send_event("klippy:connect")
        return self

    def run_gcode(self, commandline):
        self.printer.gcode.run(commandline)

    def start_print(self):
        self.printer.send_event("print_stats:new_task_start")
        self.printer.send_event("print_stats:start")

    def resume_print(self):
        self.printer.send_event("print_stats:start")

    def end_print(self):
        self.printer.send_event("print_stats:stop")

    def advance(self, seconds):
        self.printer.reactor.advance(seconds)

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
    return TopCoverBench(**bench_state).connect()


@pytest.fixture
def make_bench():
    return connected_bench
