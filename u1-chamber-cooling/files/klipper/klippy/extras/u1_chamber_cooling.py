# SPDX-FileCopyrightText: Copyright (C) 2026 unlucio and the Bespok3d contributors
# SPDX-License-Identifier: GPL-3.0-only
"""Chamber cooling targets from the print's softening temperature and the chosen fan level."""

import os
import pathlib
from dataclasses import dataclass
from typing import Any

# The purifier mode the stock start G-code picks for PLA, PETG and TPU, as purifier.py numbers it.
PURIFIER_MODE_COOL_CHAMBER = 1
# Orca writes both footer keys within 43 KB of the file's end on every print file measured.
FOOTER_READ_BYTES = 128 * 1024
FILAMENT_USED_KEY = "; filament used [mm] ="
SOFTENING_TEMP_KEY = "; temperature_vitrification ="
ALARM_BELOW_SOFTENING = 2.


@dataclass(frozen=True)
class FanLevel:
    target_below_softening: float
    lowest_fan_speed: float


# Keyed by the value the Config tab writes into the cfg; level 0 cools hardest, level 1 is quietest.
FAN_LEVELS = {
    "0": FanLevel(target_below_softening=15., lowest_fan_speed=.40),
    "0.25": FanLevel(target_below_softening=12., lowest_fan_speed=.25),
    "0.5": FanLevel(target_below_softening=10., lowest_fan_speed=.15),
    "0.75": FanLevel(target_below_softening=7., lowest_fan_speed=.05),
    "1": FanLevel(target_below_softening=5., lowest_fan_speed=0.),
}

NOTICE_PREFIX = "u1_chamber_cooling: "
STOCK_COOLING_KEPT = "the start G-code's cooling is kept"
NO_SOFTENING_TEMP_NOTICE = (
    f"{NOTICE_PREFIX}no softening temperature for the used materials in the print file,"
    f" {STOCK_COOLING_KEPT}")


def footer_values(footer_text: str, key: str) -> list[str]:
    """The comma-separated values of the last footer line that starts with key."""
    key_lines = [line for line in footer_text.splitlines() if line.startswith(key)]
    if not key_lines:
        return []
    return [value.strip() for value in key_lines[-1][len(key):].split(",")]


def lowest_used_softening_temp(footer_text: str) -> float | None:
    """The lowest softening temperature among the slots the print uses, or None if unknown."""
    used_lengths = footer_values(footer_text, FILAMENT_USED_KEY)
    softening_temps = footer_values(footer_text, SOFTENING_TEMP_KEY)
    try:
        used_slot_temps = [
            float(softening_temp)
            for used_length, softening_temp in zip(used_lengths, softening_temps, strict=True)
            if float(used_length) > 0]
    except ValueError:
        return None
    return min(used_slot_temps, default=None)


def cool_chamber_targets(softening_temp: float, fan_level: FanLevel) -> dict[str, str]:
    """The SET_PURIFIER_MODE MODE=1 parameters for this softening temperature and level."""
    return {
        "DESIRE_TEMP": f"{softening_temp - fan_level.target_below_softening:g}",
        "ALARM_TEMP": f"{softening_temp - ALARM_BELOW_SOFTENING:g}",
        "FAN_SPEED": f"{fan_level.lowest_fan_speed:g}",
    }


def leaves_a_cooling_target(softening_temp: float, fan_level: FanLevel) -> bool:
    # purifier.py runs neither its cooling loop nor its alarm for a target at or below 0 C.
    return softening_temp - fan_level.target_below_softening > 0


def too_low_notice(softening_temp: float, fan_level_name: str) -> str:
    return (
        f"{NOTICE_PREFIX}softening temperature {softening_temp:g} C is too low for fan level"
        f" {fan_level_name}, {STOCK_COOLING_KEPT}")


def read_footer(print_file_path: str) -> str:
    """The end of the print file, where the slicer writes its settings."""
    with pathlib.Path(print_file_path).open("rb") as print_file:
        file_size = print_file.seek(0, os.SEEK_END)
        print_file.seek(max(0, file_size - FOOTER_READ_BYTES))
        return print_file.read().decode("utf-8", errors="replace")


class U1ChamberCooling:
    """Wraps the stock SET_PURIFIER_MODE and rewrites its cool chamber targets."""

    def __init__(self, config: Any) -> None:
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object("gcode")
        self.fan_level_name = config.get("fan_level")
        self.fan_level = config.getchoice("fan_level", FAN_LEVELS)
        self.stock_set_purifier_mode: Any = None
        self.printer.register_event_handler("klippy:connect", self._handle_connect)

    def _handle_connect(self) -> None:
        # Swapping the handler at connect is what gcode_macro's rename_existing does: every
        # section has registered its commands by then, so purifier.py's command exists.
        self.stock_set_purifier_mode = self.gcode.register_command("SET_PURIFIER_MODE", None)
        if self.stock_set_purifier_mode is None:
            raise self.printer.config_error(
                f"{NOTICE_PREFIX}no stock SET_PURIFIER_MODE to wrap")
        self.gcode.register_command("SET_PURIFIER_MODE", self.cmd_SET_PURIFIER_MODE)

    def cmd_SET_PURIFIER_MODE(self, gcmd: Any) -> None:  # noqa: N802 - Klipper's cmd_<COMMAND> naming
        if gcmd.get_int("MODE", None) != PURIFIER_MODE_COOL_CHAMBER:
            self.stock_set_purifier_mode(gcmd)
            return
        print_file_path = self._print_file_path()
        if print_file_path is None:
            self.stock_set_purifier_mode(gcmd)
            return
        self._run_with_softening_targets(gcmd, print_file_path)

    def _run_with_softening_targets(self, gcmd: Any, print_file_path: str) -> None:
        softening_temp = self._print_softening_temp(print_file_path)
        if softening_temp is None:
            gcmd.respond_info(NO_SOFTENING_TEMP_NOTICE)
            self.stock_set_purifier_mode(gcmd)
            return
        if not leaves_a_cooling_target(softening_temp, self.fan_level):
            gcmd.respond_info(too_low_notice(softening_temp, self.fan_level_name))
            self.stock_set_purifier_mode(gcmd)
            return
        gcmd.respond_info(
            f"{NOTICE_PREFIX}lowest softening temperature {softening_temp:g} C,"
            f" fan level {self.fan_level_name}")
        self.stock_set_purifier_mode(self._rewritten_command(gcmd, softening_temp))

    def _print_softening_temp(self, print_file_path: str) -> float | None:
        try:
            footer_text = read_footer(print_file_path)
        except OSError:
            # The file went away mid-print; the stock cooling still runs, so nothing is lost.
            return None
        return lowest_used_softening_temp(footer_text)

    def _rewritten_command(self, gcmd: Any, softening_temp: float) -> Any:
        rewritten_params = {
            **gcmd.get_command_parameters(),
            **cool_chamber_targets(softening_temp, self.fan_level)}
        rewritten_commandline = " ".join(
            [gcmd.get_command()] + [f"{name}={value}" for name, value in rewritten_params.items()])
        return self.gcode.create_gcode_command(
            gcmd.get_command(), rewritten_commandline, rewritten_params)

    def _print_file_path(self) -> str | None:
        """The file the printer is printing, or None with no print loaded."""
        virtual_sdcard = self.printer.lookup_object("virtual_sdcard", None)
        if virtual_sdcard is None:
            return None
        print_file_path: str | None = virtual_sdcard.file_path()
        return print_file_path


def load_config(config: Any) -> U1ChamberCooling:
    return U1ChamberCooling(config)
