# SPDX-FileCopyrightText: Copyright (C) 2026 unlucio and the Bespok3d contributors
# SPDX-License-Identifier: GPL-3.0-only
import json
import pathlib

import pytest
from conftest import ChamberCoolingBench, write_print_file
from extras import u1_chamber_cooling
from klipper_fakes import ConfigError

MANIFEST_PATH = pathlib.Path(__file__).resolve().parent.parent / "manifest.json"
# The stock start G-code's "strong cooling" line for PLA, PETG and TPU.
STOCK_COOL_CHAMBER = (
    "SET_PURIFIER_MODE MODE=1 DESIRE_TEMP=42 ALARM_TEMP=48 FAN_SPEED=0.6 DELAY_OFF=0")
STOCK_HOT_CHAMBER = "SET_PURIFIER_MODE MODE=3"
STOCK_IDLE = "SET_PURIFIER_MODE MODE=0"
# Orca's footer, in the order and spacing measured on real U1 print files.
PLA_AND_UNUSED_TPU_FOOTER = (
    "; filament used [mm] = 25086.98, 0.00, 0.00\n"
    "; CONFIG_BLOCK_START\n"
    "; filament_type = PLA;TPU;PLA\n"
    "; temperature_vitrification = 45,30,45\n"
    "; CONFIG_BLOCK_END\n")
PLA_AND_PETG_FOOTER = (
    "; CONFIG_BLOCK_START\n"
    "; temperature_vitrification = 70,45\n"
    "; CONFIG_BLOCK_END\n"
    "; filament used [mm] = 100.5, 2000.25\n")
NO_SOFTENING_TEMP_FOOTER = "; filament used [mm] = 25086.98\n"
MALFORMED_FOOTER = (
    "; filament used [mm] = 25086.98\n"
    "; temperature_vitrification = soft\n")
NOTHING_USED_FOOTER = (
    "; filament used [mm] = 0.00, 0.00\n"
    "; temperature_vitrification = 45,45\n")
SLOT_COUNT_MISMATCH_FOOTER = (
    "; filament used [mm] = 0.00, 1200.0\n"
    "; temperature_vitrification = 45\n")
TOO_LOW_SOFTENING_TEMP_FOOTER = (
    "; filament used [mm] = 1200.0\n"
    "; temperature_vitrification = 10\n")
LEVEL_HALF_PLA_PARAMS = {"DESIRE_TEMP": "35", "ALARM_TEMP": "43", "FAN_SPEED": "0.15"}


def print_bench(make_bench, tmp_path, footer_text, **bench_state):
    print_file_path = write_print_file(tmp_path / "print.gcode", footer_text)
    return make_bench(print_file_path=print_file_path, **bench_state)


def test_cool_chamber_takes_its_targets_from_the_softening_temp(make_bench, tmp_path):
    bench = print_bench(make_bench, tmp_path, PLA_AND_UNUSED_TPU_FOOTER)
    bench.run_gcode(STOCK_COOL_CHAMBER)
    assert bench.handled_params == [
        {"MODE": "1", "DELAY_OFF": "0", **LEVEL_HALF_PLA_PARAMS}]
    assert bench.responses == [
        "// u1_chamber_cooling: lowest softening temperature 45 C, fan level 0.5"]


def test_the_rewritten_commandline_carries_the_new_targets(make_bench, tmp_path):
    bench = print_bench(make_bench, tmp_path, PLA_AND_UNUSED_TPU_FOOTER)
    bench.run_gcode(STOCK_COOL_CHAMBER)
    assert bench.stock_purifier_mode.handled_commandlines == [
        "SET_PURIFIER_MODE MODE=1 DESIRE_TEMP=35 ALARM_TEMP=43 FAN_SPEED=0.15 DELAY_OFF=0"]


def test_the_lowest_used_softening_temp_wins(make_bench, tmp_path):
    bench = print_bench(make_bench, tmp_path, PLA_AND_PETG_FOOTER)
    bench.run_gcode(STOCK_COOL_CHAMBER)
    assert bench.handled_params[0]["DESIRE_TEMP"] == "35"


def test_the_footer_is_found_after_a_long_print_body(make_bench, tmp_path):
    print_file_path = write_print_file(
        tmp_path / "print.gcode", PLA_AND_UNUSED_TPU_FOOTER,
        filler_bytes=2 * u1_chamber_cooling.FOOTER_READ_BYTES)
    bench = make_bench(print_file_path=print_file_path)
    bench.run_gcode(STOCK_COOL_CHAMBER)
    assert bench.handled_params[0]["DESIRE_TEMP"] == "35"


@pytest.mark.parametrize(("fan_level", "level_params"), [
    ("0", {"DESIRE_TEMP": "30", "ALARM_TEMP": "43", "FAN_SPEED": "0.4"}),
    ("0.25", {"DESIRE_TEMP": "33", "ALARM_TEMP": "43", "FAN_SPEED": "0.25"}),
    ("0.5", LEVEL_HALF_PLA_PARAMS),
    ("0.75", {"DESIRE_TEMP": "38", "ALARM_TEMP": "43", "FAN_SPEED": "0.05"}),
    ("1", {"DESIRE_TEMP": "40", "ALARM_TEMP": "43", "FAN_SPEED": "0"}),
])
def test_each_fan_level_sets_its_targets(make_bench, tmp_path, fan_level, level_params):
    bench = print_bench(make_bench, tmp_path, PLA_AND_UNUSED_TPU_FOOTER, fan_level=fan_level)
    bench.run_gcode(STOCK_COOL_CHAMBER)
    assert bench.handled_params == [{"MODE": "1", "DELAY_OFF": "0", **level_params}]


@pytest.mark.parametrize("other_mode", [STOCK_HOT_CHAMBER, STOCK_IDLE])
def test_every_other_mode_goes_to_the_stock_command_unchanged(make_bench, tmp_path, other_mode):
    bench = print_bench(make_bench, tmp_path, PLA_AND_UNUSED_TPU_FOOTER)
    bench.run_gcode(other_mode)
    assert bench.stock_purifier_mode.handled_commandlines == [other_mode]
    assert bench.responses == []


def test_no_print_file_keeps_the_stock_targets(make_bench):
    bench = make_bench()
    bench.run_gcode(STOCK_COOL_CHAMBER)
    assert bench.stock_purifier_mode.handled_commandlines == [STOCK_COOL_CHAMBER]
    assert bench.responses == []


@pytest.mark.parametrize(
    "footer_text", [
        NO_SOFTENING_TEMP_FOOTER, MALFORMED_FOOTER, NOTHING_USED_FOOTER,
        SLOT_COUNT_MISMATCH_FOOTER, ""])
def test_no_usable_softening_temp_keeps_the_stock_targets_and_says_so(
        make_bench, tmp_path, footer_text):
    bench = print_bench(make_bench, tmp_path, footer_text)
    bench.run_gcode(STOCK_COOL_CHAMBER)
    assert bench.stock_purifier_mode.handled_commandlines == [STOCK_COOL_CHAMBER]
    assert bench.responses == ["// " + u1_chamber_cooling.NO_SOFTENING_TEMP_NOTICE]


def test_a_softening_temp_with_no_target_left_keeps_the_stock_targets_and_says_so(
        make_bench, tmp_path):
    bench = print_bench(make_bench, tmp_path, TOO_LOW_SOFTENING_TEMP_FOOTER)
    bench.run_gcode(STOCK_COOL_CHAMBER)
    assert bench.stock_purifier_mode.handled_commandlines == [STOCK_COOL_CHAMBER]
    assert bench.responses == ["// " + u1_chamber_cooling.too_low_notice(10., "0.5")]


def test_a_vanished_print_file_keeps_the_stock_targets_and_says_so(make_bench, tmp_path):
    bench = make_bench(print_file_path=str(tmp_path / "deleted.gcode"))
    bench.run_gcode(STOCK_COOL_CHAMBER)
    assert bench.stock_purifier_mode.handled_commandlines == [STOCK_COOL_CHAMBER]
    assert bench.responses == ["// " + u1_chamber_cooling.NO_SOFTENING_TEMP_NOTICE]


def test_connect_without_a_stock_set_purifier_mode_is_a_config_error():
    bench = ChamberCoolingBench()
    bench.printer.gcode.register_command("SET_PURIFIER_MODE", None)
    with pytest.raises(ConfigError):
        bench.connect()


def test_an_unknown_fan_level_is_a_config_error():
    with pytest.raises(ConfigError):
        ChamberCoolingBench(fan_level="2")


def test_the_config_tab_offers_exactly_the_plugin_fan_levels():
    manifest = json.loads(MANIFEST_PATH.read_text())
    fan_level_field = next(field for field in manifest["config"] if field["key"] == "FAN_LEVEL")
    assert fan_level_field["options"] == list(u1_chamber_cooling.FAN_LEVELS)
    assert fan_level_field["default"] in u1_chamber_cooling.FAN_LEVELS


@pytest.mark.parametrize("fan_level", u1_chamber_cooling.FAN_LEVELS.values())
@pytest.mark.parametrize("softening_temp", [30., 45., 70.])
def test_the_alarm_stays_above_the_target_at_every_level(fan_level, softening_temp):
    # purifier.py lifts an alarm below target + 1 up to target + 1; staying above keeps ours.
    targets = u1_chamber_cooling.cool_chamber_targets(softening_temp, fan_level)
    assert float(targets["ALARM_TEMP"]) >= float(targets["DESIRE_TEMP"]) + 1
