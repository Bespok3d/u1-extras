from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

try:
    from .gcode_preview_color_map import (
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


class GcodePreviewColors:
    def __init__(self, config: ConfigHelper) -> None:
        self.server = config.get_server()
        self.enabled = config.getboolean("enabled", True)
        self.klippy_apis = self.server.lookup_component("klippy_apis")
        self.live_state: dict[str, Any] = {}
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
                {PRINT_TASK_OBJECT: None}, self._handle_status_update
            )
        except Exception:
            logging.exception("[gcode_preview_colors] print_task_config subscribe failed")
            return
        self._merge_live_state(status)
        self._fill_all_files()

    def _handle_status_update(
        self, status: dict[str, dict[str, Any]], eventtime: float
    ) -> None:
        # The launch-time remap on the printer screen writes extruder_map_table, so this update is
        # also the "print start" refill trigger: no separate print_stats subscription is needed.
        if self._merge_live_state(status):
            self._fill_all_files()

    def _merge_live_state(self, status: dict[str, Any]) -> bool:
        # Klippy drives this via the subscription callback, so a malformed push must not raise into
        # Moonraker: anything but a fields dict is simply "no update".
        fields = status.get(PRINT_TASK_OBJECT)
        if not isinstance(fields, dict):
            return False
        changed = False
        for field in TRACKED_FIELDS:
            if field in fields and fields[field] != self.live_state.get(field):
                self.live_state[field] = fields[field]
                changed = True
        return changed

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
            colors = self._colors_for_entry(entry)
            if colors is None or entry.get(COLORS_KEY) == colors:
                return
            entry[COLORS_KEY] = colors
            storage.insert(filename, entry)
        except Exception:
            logging.exception("[gcode_preview_colors] color fill failed for %s", filename)

    def _colors_for_entry(self, entry: Any) -> list[str] | None:
        if not isinstance(entry, dict):
            return None
        live = LiveFilamentState(
            extruder_map_table=self.live_state.get("extruder_map_table", []),
            rgba_by_extruder=self.live_state.get("filament_color_rgba", []),
            filament_exist_by_extruder=self.live_state.get("filament_exist", []),
        )
        sliced_colors = parse_sliced_colors(entry.get(SLICED_COLORS_KEY))
        return compute_filament_colors(sliced_colors, live)


def load_component(config: ConfigHelper) -> GcodePreviewColors:
    return GcodePreviewColors(config)
