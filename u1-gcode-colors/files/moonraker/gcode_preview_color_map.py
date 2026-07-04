"""Pure mapping from the U1 live filament state to Fluidd's per-tool preview colors.

This module has no Moonraker imports so it stays independently type-checked and unit-testable.
The Moonraker component (gcode_preview_colors.py) is the only caller: it reads the live
print_task_config state plus each gcode file's sliced colors and asks this module for the
filament_colors array Fluidd renders.

The mapping, settled in the u1-gcode-colors design: for each gcode tool index t,
filament_colors[t] = "#" + filament_color_rgba[extruder_map_table[t]][0:6]. The fallback ladder
per tool is: the real color loaded on the mapped physical extruder, else the file's own sliced
filament_colour[t], else unset (Fluidd's palette).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RGBA_LENGTH = 8
RGB_HEX_LENGTH = 6
# The firmware default for an extruder with no known filament. Treated as "not loaded" so a bare
# slot never overrides the file's own sliced color, even though it is technically opaque white.
EMPTY_EXTRUDER_RGBA = "FFFFFFFF"


@dataclass(frozen=True)
class LiveFilamentState:
    extruder_map_table: list[int]
    rgba_by_extruder: list[str]
    filament_exist_by_extruder: list[bool]


def is_loaded_rgba(rgba: Any) -> bool:
    if not isinstance(rgba, str) or len(rgba) != RGBA_LENGTH:
        return False
    return rgba.upper() != EMPTY_EXTRUDER_RGBA


def parse_sliced_colors(filament_colour: Any) -> list[str]:
    # Keep every ";"-separated slot, including empties, so the list stays aligned with the tool
    # index: an empty slot must map to tool t, not silently shift later colors down one.
    if not isinstance(filament_colour, str) or not filament_colour.strip():
        return []
    return [chunk.strip() for chunk in filament_colour.split(";")]


def _extruder_index_in_range(physical_extruder: int, live: LiveFilamentState) -> bool:
    within_colors = physical_extruder < len(live.rgba_by_extruder)
    within_exist = physical_extruder < len(live.filament_exist_by_extruder)
    return within_colors and within_exist


def loaded_tool_color(physical_extruder: int | None, live: LiveFilamentState) -> str | None:
    if physical_extruder is None or physical_extruder < 0:
        return None
    if not _extruder_index_in_range(physical_extruder, live):
        return None
    if not live.filament_exist_by_extruder[physical_extruder]:
        return None
    rgba = live.rgba_by_extruder[physical_extruder]
    return "#" + rgba[:RGB_HEX_LENGTH] if is_loaded_rgba(rgba) else None


def resolve_tool_color(
    tool_index: int, sliced_colors: list[str], live: LiveFilamentState
) -> str | None:
    physical_extruder = (
        live.extruder_map_table[tool_index]
        if tool_index < len(live.extruder_map_table)
        else None
    )
    loaded = loaded_tool_color(physical_extruder, live)
    if loaded is not None:
        return loaded
    if tool_index < len(sliced_colors) and sliced_colors[tool_index]:
        return sliced_colors[tool_index]
    return None


def compute_filament_colors(sliced_colors: list[str], live: LiveFilamentState) -> list[str] | None:
    if not sliced_colors:
        return None
    resolved = [
        resolve_tool_color(tool_index, sliced_colors, live)
        for tool_index in range(len(sliced_colors))
    ]
    if all(color is None for color in resolved):
        return None
    return [color if color is not None else "" for color in resolved]
