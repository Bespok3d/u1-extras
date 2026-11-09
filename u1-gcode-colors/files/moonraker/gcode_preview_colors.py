from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

try:
    from .gcode_preview_color_map import (
        NO_LIVE_FILAMENT,
        LiveFilamentState,
        compute_filament_colors,
        parse_sliced_colors,
    )
except ImportError:
    # Loaded outside the moonraker.components package: the unit tests put files/moonraker on
    # sys.path and import this module top-level, so the package-relative import above does not
    # resolve. On the printer Moonraker imports it as moonraker.components.gcode_preview_colors
    # and the relative import wins.
    from gcode_preview_color_map import (
        NO_LIVE_FILAMENT,
        LiveFilamentState,
        compute_filament_colors,
        parse_sliced_colors,
    )

if TYPE_CHECKING:
    from moonraker.components.file_manager.file_manager import MetadataStorage
    from moonraker.confighelper import ConfigHelper

PRINT_TASK_OBJECT = "print_task_config"
GCODE_ROOT = "gcodes"
COLORS_KEY = "filament_colors"
SLICED_COLORS_KEY = "filament_colour"
TRACKED_FIELDS = ("extruder_map_table", "filament_color_rgba", "filament_exist")
PRINT_STATS_OBJECT = "print_stats"
PRINT_STATS_FIELDS = ("state", "filename")
# The states in which print_stats names a file the printer feeds with the live map. A finished,
# cancelled or failed print keeps its filename, but the map then belongs to no print.
STATES_WITH_A_FILE_IN_PLAY = ("printing", "paused")


class GcodePreviewColors:
    def __init__(self, config: ConfigHelper) -> None:
        self.server = config.get_server()
        self.enabled = config.getboolean("enabled", True)
        self.klippy_apis = self.server.lookup_component("klippy_apis")
        self.live_state: dict[str, Any] = {}
        self.print_state: dict[str, Any] = {}
        self.server.register_event_handler(
            "server:klippy_ready", self._handle_klippy_ready
        )
        self.server.register_event_handler(
            "file_manager:filelist_changed", self._handle_filelist_changed
        )

    async def _handle_klippy_ready(self) -> None:
        if not self.enabled:
            return
        try:
            status = await self.klippy_apis.subscribe_objects(
                {PRINT_TASK_OBJECT: None, PRINT_STATS_OBJECT: list(PRINT_STATS_FIELDS)},
                self._handle_status_update,
            )
        except Exception:
            logging.exception("[gcode_preview_colors] printer state subscribe failed")
            return
        self._merge_live_state(status)
        self._fill_all_files()

    def _handle_status_update(
        self, status: dict[str, dict[str, Any]], eventtime: float
    ) -> None:
        # A print starting or ending moves the map onto or off a file, and the launch-time remap
        # on the printer screen writes extruder_map_table: either one refills the previews.
        if self._merge_live_state(status):
            self._fill_all_files()

    def _merge_live_state(self, status: dict[str, Any]) -> bool:
        map_changed = _merge_fields(status, PRINT_TASK_OBJECT, TRACKED_FIELDS, self.live_state)
        print_changed = _merge_fields(
            status, PRINT_STATS_OBJECT, PRINT_STATS_FIELDS, self.print_state
        )
        return map_changed or print_changed

    def _file_in_play(self) -> str | None:
        if self.print_state.get("state") not in STATES_WITH_A_FILE_IN_PLAY:
            return None
        filename = self.print_state.get("filename")
        return filename if isinstance(filename, str) and filename else None

    def _handle_filelist_changed(self, notify_info: dict[str, Any]) -> None:
        if not self.enabled:
            return
        item = notify_info.get("item") if isinstance(notify_info, dict) else None
        if not isinstance(item, dict) or item.get("root") != GCODE_ROOT:
            return
        filename = item.get("path")
        storage = self._metadata_storage()
        if not isinstance(filename, str) or storage is None:
            return
        self._fill_file(storage, filename)

    def _fill_all_files(self) -> None:
        if not self.enabled:
            return
        storage = self._metadata_storage()
        if storage is None:
            return
        for filename in list(storage.metadata.keys()):
            self._fill_file(storage, filename)

    def _metadata_storage(self) -> MetadataStorage | None:
        try:
            file_manager = self.server.lookup_component("file_manager")
            return file_manager.get_metadata_storage()
        except Exception:
            logging.exception("[gcode_preview_colors] file_manager unavailable")
            return None

    def _fill_file(self, storage: MetadataStorage, filename: str) -> None:
        try:
            entry = storage.get(filename)
            if not isinstance(entry, dict):
                return
            colors = self._colors_for_file(filename, entry)
            if entry.get(COLORS_KEY) == colors:
                return
            storage.insert(filename, _with_colors(entry, colors))
        except Exception:
            logging.exception("[gcode_preview_colors] color fill failed for %s", filename)

    def _colors_for_file(self, filename: str, entry: dict[str, Any]) -> list[str] | None:
        live = self._live_filament() if filename == self._file_in_play() else NO_LIVE_FILAMENT
        sliced_colors = parse_sliced_colors(entry.get(SLICED_COLORS_KEY))
        return compute_filament_colors(sliced_colors, live)

    def _live_filament(self) -> LiveFilamentState:
        return LiveFilamentState(
            extruder_map_table=self.live_state.get("extruder_map_table", []),
            rgba_by_extruder=self.live_state.get("filament_color_rgba", []),
            filament_exist_by_extruder=self.live_state.get("filament_exist", []),
        )


# A file with no colour to show carries none: a printed file whose slicer named no colour drops
# the loaded colours it showed during the print instead of keeping them for good.
def _with_colors(entry: dict[str, Any], colors: list[str] | None) -> dict[str, Any]:
    if colors is None:
        return {key: value for key, value in entry.items() if key != COLORS_KEY}
    return {**entry, COLORS_KEY: colors}


# Klippy drives this via the subscription callback, so a malformed push must not raise into
# Moonraker: anything but a fields dict is simply "no update".
def _merge_fields(
    status: dict[str, Any],
    object_name: str,
    tracked_fields: tuple[str, ...],
    merged_state: dict[str, Any],
) -> bool:
    fields = status.get(object_name)
    if not isinstance(fields, dict):
        return False
    changed_fields = [
        field
        for field in tracked_fields
        if field in fields and fields[field] != merged_state.get(field)
    ]
    merged_state.update({field: fields[field] for field in changed_fields})
    return bool(changed_fields)


def load_component(config: ConfigHelper) -> GcodePreviewColors:
    return GcodePreviewColors(config)
