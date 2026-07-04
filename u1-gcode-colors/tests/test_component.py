import asyncio
from copy import deepcopy

from gcode_preview_colors import GcodePreviewColors

# Obviously-fake patterned colors, never real device captures.
RED = "AA0000FF"
GREEN = "00BB00FF"
BLUE = "0000CCFF"
GREY = "DDDDDDFF"
IDENTITY_MAP = [0, 1, 2, 3] + [0] * 28

LIVE_STATUS = {
    "print_task_config": {
        "extruder_map_table": list(IDENTITY_MAP),
        "filament_color_rgba": [RED, GREEN, BLUE, GREY],
        "filament_exist": [True, True, True, True],
    }
}


class FakeMetadataStorage:
    def __init__(self, metadata):
        self.metadata = metadata

    def get(self, key, default=None):
        return deepcopy(self.metadata.get(key, default))

    def insert(self, key, value):
        self.metadata[key] = deepcopy(value)


class RaisingMetadataStorage(FakeMetadataStorage):
    def get(self, key, default=None):
        raise RuntimeError("klippy store exploded")


class FakeFileManager:
    def __init__(self, storage):
        self._storage = storage

    def get_metadata_storage(self):
        return self._storage


class FakeKlippyApis:
    def __init__(self, status=None, fail=False):
        self._status = status or {}
        self._fail = fail

    async def subscribe_objects(self, objects, callback=None):
        if self._fail:
            raise RuntimeError("subscribe failed")
        return self._status


class FakeServer:
    def __init__(self, components):
        self._components = components
        self.handlers = {}

    def lookup_component(self, name):
        if name not in self._components:
            raise KeyError(name)
        return self._components[name]

    def register_event_handler(self, event, handler):
        self.handlers.setdefault(event, []).append(handler)


class FakeConfig:
    def __init__(self, server, enabled=True):
        self._server = server
        self._enabled = enabled

    def get_server(self):
        return self._server

    def getboolean(self, key, default):
        return self._enabled


def _build(metadata, enabled=True, klippy=None, storage=None):
    store = storage if storage is not None else FakeMetadataStorage(metadata)
    components = {
        "klippy_apis": klippy or FakeKlippyApis(),
        "file_manager": FakeFileManager(store),
    }
    component = GcodePreviewColors(FakeConfig(FakeServer(components), enabled))
    return component, store


def test_fill_writes_filament_colors_that_the_metadata_endpoint_would_serve():
    entry = {"filament_colour": "#101010;#202020;#303030", "filament_type": "PLA"}
    metadata = {"model.gcode": entry}
    component, store = _build(metadata)
    component._merge_live_state(LIVE_STATUS)
    component._fill_all_files()
    # /server/files/metadata serves gcode_metadata.get(filename) verbatim, so asserting the store
    # entry is asserting exactly what Fluidd receives.
    served = store.get("model.gcode")
    assert served["filament_colors"] == ["#AA0000", "#00BB00", "#0000CC"]
    assert served["filament_colour"] == "#101010;#202020;#303030"


def test_toggle_off_never_writes():
    metadata = {"model.gcode": {"filament_colour": "#101010;#202020"}}
    component, store = _build(metadata, enabled=False)
    component._merge_live_state(LIVE_STATUS)
    component._fill_all_files()
    assert "filament_colors" not in store.get("model.gcode")


def test_filelist_changed_fills_the_added_gcode_file():
    metadata = {"added.gcode": {"filament_colour": "#101010;#202020;#303030;#404040"}}
    component, store = _build(metadata)
    component._merge_live_state(LIVE_STATUS)
    notify = {"action": "create_file", "item": {"root": "gcodes", "path": "added.gcode"}}
    component._handle_filelist_changed(notify)
    expected = ["#AA0000", "#00BB00", "#0000CC", "#DDDDDD"]
    assert store.get("added.gcode")["filament_colors"] == expected


def test_filelist_changed_ignores_non_gcode_roots():
    metadata = {"cfg.cfg": {"filament_colour": "#101010"}}
    component, store = _build(metadata)
    component._merge_live_state(LIVE_STATUS)
    component._handle_filelist_changed({"item": {"root": "config", "path": "cfg.cfg"}})
    assert "filament_colors" not in store.get("cfg.cfg")


def test_store_failure_is_swallowed_so_moonraker_is_never_broken():
    storage = RaisingMetadataStorage({"model.gcode": {"filament_colour": "#101010;#202020"}})
    component, _ = _build({}, storage=storage)
    component._merge_live_state(LIVE_STATUS)
    component._fill_all_files()  # must not raise


def test_klippy_subscribe_failure_is_swallowed():
    component, _ = _build({}, klippy=FakeKlippyApis(fail=True))
    asyncio.run(component._handle_klippy_ready())  # must not raise


def test_klippy_ready_subscribes_and_fills_from_returned_status():
    metadata = {"model.gcode": {"filament_colour": "#101010;#202020;#303030"}}
    component, store = _build(metadata, klippy=FakeKlippyApis(status=LIVE_STATUS))
    asyncio.run(component._handle_klippy_ready())
    assert store.get("model.gcode")["filament_colors"] == ["#AA0000", "#00BB00", "#0000CC"]


def test_status_update_refills_when_map_changes():
    metadata = {"model.gcode": {"filament_colour": "#101010;#202020;#303030;#404040"}}
    component, store = _build(metadata)
    component._merge_live_state(LIVE_STATUS)
    component._fill_all_files()
    remap = {"print_task_config": {"extruder_map_table": [3, 2, 1, 0] + [0] * 28}}
    component._handle_status_update(remap, 123.0)
    expected = ["#DDDDDD", "#0000CC", "#00BB00", "#AA0000"]
    assert store.get("model.gcode")["filament_colors"] == expected


def test_malformed_status_push_does_not_raise_into_moonraker():
    metadata = {"model.gcode": {"filament_colour": "#101010;#202020;#303030"}}
    component, store = _build(metadata)
    component._merge_live_state(LIVE_STATUS)
    component._fill_all_files()
    del store.metadata["model.gcode"]["filament_colors"]
    # A null or wrongly-shaped print_task_config value must be a no-op, never a TypeError escaping
    # the subscription callback.
    component._handle_status_update({"print_task_config": None}, 1.0)
    component._handle_status_update({"print_task_config": ["not", "a", "dict"]}, 1.0)
    assert "filament_colors" not in store.metadata["model.gcode"]


def test_malformed_filelist_event_does_not_raise_into_moonraker():
    component, _ = _build({"model.gcode": {"filament_colour": "#101010"}})
    component._merge_live_state(LIVE_STATUS)
    component._handle_filelist_changed({"item": None})  # must not raise
    component._handle_filelist_changed({})  # must not raise


def test_status_update_without_tracked_change_does_not_refill():
    metadata = {"model.gcode": {"filament_colour": "#101010;#202020;#303030"}}
    component, store = _build(metadata)
    component._merge_live_state(LIVE_STATUS)
    component._fill_all_files()
    del store.metadata["model.gcode"]["filament_colors"]
    component._handle_status_update({"print_task_config": {"filament_type": ["PLA"]}}, 1.0)
    assert "filament_colors" not in store.metadata["model.gcode"]
