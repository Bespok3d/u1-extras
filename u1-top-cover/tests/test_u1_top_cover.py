# SPDX-FileCopyrightText: Copyright (C) 2026 unlucio and the Bespok3d contributors
# SPDX-License-Identifier: GPL-3.0-only
import pytest
from conftest import TopCoverBench
from extras import u1_top_cover
from klipper_fakes import CommandError, ConfigError

PURIFIER_MODE_PREHEAT_CHAMBER = 2
PURIFIER_MODE_HOT_CHAMBER = 3
STORED_DELAY_SECONDS = 60
ORCA_SPEED_70_PERCENT = 178
ORCA_SLICER_SPEED = pytest.approx(ORCA_SPEED_70_PERCENT / u1_top_cover.FULL_SPEED_S_VALUE)
EXHAUST_FULL_SPEED = u1_top_cover.FULL_SPEED
EXHAUST_OFF = 0.


def test_every_other_m106_goes_to_the_stock_fan(make_bench):
    bench = make_bench()
    other_fan_commands = ["M106 S255", "M106 P0 S128", "M106 P2 S100", "M106"]
    for commandline in other_fan_commands:
        bench.run_gcode(commandline)
    assert bench.stock_fan.handled_commandlines == other_fan_commands
    assert bench.purifier.exhaust_speed == EXHAUST_OFF


def test_m106_p3_sets_the_exhaust_to_s_over_255(make_bench):
    bench = make_bench()
    bench.run_gcode(f"M106 P3 S{ORCA_SPEED_70_PERCENT}")
    assert bench.purifier.exhaust_speed == ORCA_SLICER_SPEED
    assert bench.stock_fan.handled_commandlines == []


def test_m106_p3_above_255_runs_at_full_speed(make_bench):
    bench = make_bench()
    bench.run_gcode("M106 P3 S300")
    assert bench.purifier.exhaust_speed == EXHAUST_FULL_SPEED


def test_m106_p3_without_s_runs_at_full_speed_like_stock_m106(make_bench):
    bench = make_bench()
    bench.run_gcode("M106 P3")
    assert bench.purifier.exhaust_speed == EXHAUST_FULL_SPEED


def test_m106_p3_with_a_negative_s_is_refused_like_stock_m106(make_bench):
    bench = make_bench()
    with pytest.raises(CommandError):
        bench.run_gcode("M106 P3 S-5")


def test_m106_p3_s0_turns_off_at_once_like_stock_m106(make_bench):
    bench = make_bench(stored_delay_seconds=STORED_DELAY_SECONDS)
    bench.run_gcode("M106 P3 S255")
    bench.run_gcode("M106 P3 S0")
    assert bench.purifier.exhaust_speed == EXHAUST_OFF


def test_no_top_cover_ignores_m106_p3_and_says_so_once(make_bench):
    bench = make_bench(power_detected=False)
    bench.run_gcode("M106 P3 S255")
    bench.run_gcode("M106 P3 S128")
    assert bench.purifier.exhaust_speed == EXHAUST_OFF
    assert bench.responses == ["// " + u1_top_cover.NO_COVER_NOTICE]


def test_cool_chamber_mode_takes_the_slicer_speed_as_its_floor(make_bench):
    bench = make_bench(purifier_mode=u1_top_cover.PURIFIER_MODE_COOL_CHAMBER)
    bench.run_gcode(f"M106 P3 S{ORCA_SPEED_70_PERCENT}")
    assert bench.purifier.exhaust_speed == ORCA_SLICER_SPEED
    assert bench.purifier.exhaust_fan_speed_threshold == ORCA_SLICER_SPEED


def test_cool_chamber_mode_s0_drops_the_floor_and_turns_off_at_once(make_bench):
    bench = make_bench(
        purifier_mode=u1_top_cover.PURIFIER_MODE_COOL_CHAMBER,
        stored_delay_seconds=STORED_DELAY_SECONDS)
    bench.run_gcode("M106 P3 S255")
    bench.run_gcode("M106 P3 S0")
    assert bench.purifier.exhaust_fan_speed_threshold == EXHAUST_OFF
    assert bench.purifier.exhaust_speed == EXHAUST_OFF


@pytest.mark.parametrize(
    "heating_mode", [PURIFIER_MODE_PREHEAT_CHAMBER, PURIFIER_MODE_HOT_CHAMBER])
def test_heating_modes_keep_the_exhaust_off_and_say_so_once(make_bench, heating_mode):
    bench = make_bench(purifier_mode=heating_mode)
    bench.run_gcode("M106 P3 S255")
    bench.run_gcode("M106 P3 S128")
    assert bench.purifier.exhaust_speed == EXHAUST_OFF
    assert bench.purifier.exhaust_fan_speed_threshold == 0
    assert bench.responses == ["// " + u1_top_cover.HEATING_MODE_NOTICE]


def test_print_end_runs_the_complete_print_speed_then_turns_it_off(make_bench):
    bench = make_bench(stored_delay_seconds=0)
    bench.start_print()
    bench.run_gcode(f"M106 P3 S{ORCA_SPEED_70_PERCENT}")
    bench.end_print()
    bench.advance(u1_top_cover.COMPLETE_PRINT_RUN_SECONDS - 1)
    assert bench.purifier.exhaust_speed == ORCA_SLICER_SPEED
    bench.advance(1)
    assert bench.purifier.exhaust_speed == EXHAUST_OFF


def test_finished_print_runs_orca_complete_print_speed_after_the_stock_print_end(make_bench):
    # Orca writes its complete-print M106 P3 after the end G-code, so it lands after the stock
    # PRINT_END has already sent SET_PURIFIER_MODE MODE=0.
    bench = make_bench(purifier_mode=u1_top_cover.PURIFIER_MODE_COOL_CHAMBER)
    bench.start_print()
    bench.run_gcode("M106 P3 S255")
    bench.purifier.setup_idle_mode()
    bench.run_gcode(f"M106 P3 S{ORCA_SPEED_70_PERCENT}")
    bench.end_print()
    bench.advance(u1_top_cover.COMPLETE_PRINT_RUN_SECONDS - 1)
    assert bench.purifier.exhaust_speed == ORCA_SLICER_SPEED
    bench.advance(1)
    assert bench.purifier.exhaust_speed == EXHAUST_OFF


def test_cancelled_print_follows_the_stock_cancel(make_bench):
    # The stock CANCEL_PRINT sends SET_PURIFIER_MODE MODE=0 after the print has stopped.
    bench = make_bench(stored_delay_seconds=0)
    bench.start_print()
    bench.run_gcode(f"M106 P3 S{ORCA_SPEED_70_PERCENT}")
    bench.end_print()
    bench.purifier.setup_idle_mode()
    assert bench.purifier.exhaust_speed == EXHAUST_OFF


def test_print_end_uses_the_stored_delay_when_there_is_one(make_bench):
    bench = make_bench(stored_delay_seconds=STORED_DELAY_SECONDS)
    bench.start_print()
    bench.run_gcode("M106 P3 S255")
    bench.end_print()
    bench.advance(STORED_DELAY_SECONDS)
    assert bench.purifier.exhaust_speed == EXHAUST_OFF


def test_print_end_leaves_an_exhaust_the_slicer_did_not_start(make_bench):
    bench = make_bench()
    bench.purifier.set_exhaust_fan_speed(1.)
    bench.end_print()
    bench.advance(u1_top_cover.COMPLETE_PRINT_RUN_SECONDS)
    assert bench.purifier.exhaust_speed == EXHAUST_FULL_SPEED


def test_print_end_leaves_a_speed_set_after_the_slicer(make_bench):
    # The touchscreen or SET_PURIFIER FAN=exhaust SPEED=... changed the fan: the last command wins.
    bench = make_bench()
    bench.start_print()
    bench.run_gcode(f"M106 P3 S{ORCA_SPEED_70_PERCENT}")
    bench.purifier.set_exhaust_fan_speed(EXHAUST_FULL_SPEED)
    bench.end_print()
    bench.advance(u1_top_cover.COMPLETE_PRINT_RUN_SECONDS)
    assert bench.purifier.exhaust_speed == EXHAUST_FULL_SPEED


def test_print_end_after_the_slicer_turned_it_off_changes_nothing(make_bench):
    bench = make_bench(stored_delay_seconds=STORED_DELAY_SECONDS)
    bench.start_print()
    bench.run_gcode("M106 P3 S255")
    bench.run_gcode("M106 P3 S0")
    bench.end_print()
    bench.advance(STORED_DELAY_SECONDS)
    assert bench.purifier.exhaust_speed == EXHAUST_OFF


def test_print_end_leaves_an_exhaust_set_before_the_print_started(make_bench):
    bench = make_bench()
    bench.run_gcode("M106 P3 S255")
    bench.start_print()
    bench.end_print()
    bench.advance(u1_top_cover.COMPLETE_PRINT_RUN_SECONDS)
    assert bench.purifier.exhaust_speed == EXHAUST_FULL_SPEED


def test_a_resume_keeps_the_exhaust_orca_started(make_bench):
    bench = make_bench()
    bench.start_print()
    bench.run_gcode("M106 P3 S255")
    bench.resume_print()
    bench.end_print()
    bench.advance(u1_top_cover.COMPLETE_PRINT_RUN_SECONDS)
    assert bench.purifier.exhaust_speed == EXHAUST_OFF


def test_a_stop_with_no_print_running_leaves_an_idle_m106_p3(make_bench):
    # print_stats:stop also fires for a CANCEL_PRINT or an error while the printer is idle.
    bench = make_bench()
    bench.run_gcode(f"M106 P3 S{ORCA_SPEED_70_PERCENT}")
    bench.end_print()
    bench.advance(u1_top_cover.COMPLETE_PRINT_RUN_SECONDS)
    assert bench.purifier.exhaust_speed == ORCA_SLICER_SPEED


def test_print_end_after_a_klipper_shutdown_arms_no_timer(make_bench):
    bench = make_bench()
    bench.start_print()
    bench.run_gcode("M106 P3 S255")
    bench.printer.shut_down = True
    bench.end_print()
    bench.advance(u1_top_cover.COMPLETE_PRINT_RUN_SECONDS)
    assert bench.purifier.exhaust_speed == EXHAUST_FULL_SPEED


def test_connect_without_a_stock_m106_is_a_config_error():
    bench = TopCoverBench()
    bench.printer.gcode.register_command("M106", None)
    with pytest.raises(ConfigError):
        bench.connect()


def test_complete_print_run_falls_back_only_below_one_second():
    assert u1_top_cover.complete_print_run_seconds(0) == u1_top_cover.COMPLETE_PRINT_RUN_SECONDS
    assert u1_top_cover.complete_print_run_seconds(1) == 1
