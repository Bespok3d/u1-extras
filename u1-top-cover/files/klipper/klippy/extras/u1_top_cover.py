# SPDX-FileCopyrightText: Copyright (C) 2026 unlucio and the Bespok3d contributors
# SPDX-License-Identifier: GPL-3.0-only
"""Orca's exhaust fan command, M106 P3, drives the Snapmaker U1 top cover's exhaust fan."""

from typing import Any

from . import u1_top_cover_fan_level

EXHAUST_FAN_ID = 3
FULL_SPEED_S_VALUE = 255.
FULL_SPEED = 1.
# The purifier modes, as Snapmaker's extras/purifier.py numbers them.
PURIFIER_MODE_IDLE = 0
PURIFIER_MODE_COOL_CHAMBER = u1_top_cover_fan_level.PURIFIER_MODE_COOL_CHAMBER
MODES_THE_SLICER_DRIVES = (PURIFIER_MODE_IDLE, PURIFIER_MODE_COOL_CHAMBER)
# purifier.py switches the fan off at once for any delay below one second.
SHORTEST_TURN_OFF_DELAY_SECONDS = 1
# The stock start G-code stores a turn-off delay of 0, which would stop the complete-print speed
# the moment the print ends. purifier.py's own default delay is used then instead.
COMPLETE_PRINT_RUN_SECONDS = 180

NO_COVER_NOTICE = "u1_top_cover: no top cover found, M106 P3 ignored"
HEATING_MODE_NOTICE = (
    "u1_top_cover: the chamber is heating or kept warm, so the exhaust stays off and"
    " M106 P3 is ignored")


def exhaust_speed(s_value: float) -> float:
    """Turn M106's 0 to 255 S value into the purifier's 0 to 1 speed."""
    return min(s_value / FULL_SPEED_S_VALUE, FULL_SPEED)


def complete_print_run_seconds(stored_delay_seconds: int) -> int:
    """How long the exhaust keeps running after the print ends."""
    if stored_delay_seconds < SHORTEST_TURN_OFF_DELAY_SECONDS:
        return COMPLETE_PRINT_RUN_SECONDS
    return stored_delay_seconds


class U1TopCover:
    """Wraps the stock M106 and remembers the exhaust speed the slicer left on."""

    def __init__(self, config: Any) -> None:
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object("gcode")
        self.fan_level_cooling = u1_top_cover_fan_level.FanLevelCooling(config)
        self.purifier: Any = None
        self.stock_m106: Any = None
        # The speed the purifier reported right after the slicer set it; None when the slicer
        # left the exhaust off.
        self.slicer_exhaust_speed: float | None = None
        # print_stats:stop also fires with no print running, on a cancel or an error while idle.
        self.print_running = False
        self.notices_sent: set[str] = set()
        self.printer.register_event_handler("klippy:connect", self._handle_connect)
        self.printer.register_event_handler(
            "print_stats:new_task_start", self._handle_new_print)
        self.printer.register_event_handler("print_stats:stop", self._handle_print_stop)

    def _handle_connect(self) -> None:
        # Swapping the handler at connect is what gcode_macro's rename_existing does: every
        # section has registered its commands by then, so fan.py's M106 exists.
        self.purifier = self.printer.lookup_object("purifier")
        self.stock_m106 = self.gcode.register_command("M106", None)
        if self.stock_m106 is None:
            raise self.printer.config_error("u1_top_cover: no stock M106 to wrap")
        self.gcode.register_command("M106", self.cmd_M106)

    def cmd_M106(self, gcmd: Any) -> None:  # noqa: N802 - Klipper's cmd_<COMMAND> naming
        if gcmd.get_int("P", None) != EXHAUST_FAN_ID:
            self.stock_m106(gcmd)
            return
        speed = exhaust_speed(gcmd.get_float("S", FULL_SPEED_S_VALUE, minval=0.))
        self._apply_slicer_speed(speed, gcmd)

    def _apply_slicer_speed(self, speed: float, gcmd: Any) -> None:
        purifier_status = self.purifier.get_status(self.reactor.monotonic())
        if not purifier_status["power_detected"]:
            self._notice_once(NO_COVER_NOTICE, gcmd)
            return
        purifier_mode = purifier_status["mode"]
        if purifier_mode not in MODES_THE_SLICER_DRIVES:
            self._notice_once(HEATING_MODE_NOTICE, gcmd)
            return
        if purifier_mode == PURIFIER_MODE_COOL_CHAMBER:
            # The cooling loop never drops below this floor, so it can still speed up to cool
            # but never undercuts the slicer's speed.
            self.purifier.exhaust_fan_speed_threshold = speed
        self.purifier.set_exhaust_fan_speed(speed)
        self.slicer_exhaust_speed = self._print_owned_speed()

    def _print_owned_speed(self) -> float | None:
        """The speed the print's end turns off; None for an idle M106 P3 or a fan left off."""
        reported_speed = self._reported_exhaust_speed()
        if not self.print_running or reported_speed <= 0:
            return None
        return reported_speed

    def _handle_new_print(self) -> None:
        # print_stats:start would be wrong here: it also fires on every resume.
        self.print_running = True

    def _handle_print_stop(self) -> None:
        slicer_exhaust_speed = self.slicer_exhaust_speed
        self.slicer_exhaust_speed = None
        self.print_running = False
        if slicer_exhaust_speed is None or self.printer.is_shutdown():
            return
        if self._reported_exhaust_speed() != slicer_exhaust_speed:
            # The screen, SET_PURIFIER or the cooling loop changed the fan last: theirs wins.
            return
        stored_delay_seconds = self._exhaust_status()["delay"]
        self.purifier.set_exhaust_fan_delay_turn_off(
            complete_print_run_seconds(stored_delay_seconds))

    def _reported_exhaust_speed(self) -> float:
        return float(self._exhaust_status()["speed"])

    def _exhaust_status(self) -> Any:
        return self.purifier.get_status(self.reactor.monotonic())["exhaust_fan"]

    def _notice_once(self, notice: str, gcmd: Any) -> None:
        if notice in self.notices_sent:
            return
        self.notices_sent.add(notice)
        # respond_info also writes the notice to klippy.log.
        gcmd.respond_info(notice)


def load_config(config: Any) -> U1TopCover:
    return U1TopCover(config)
