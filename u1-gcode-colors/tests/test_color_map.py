from gcode_preview_color_map import (
    LiveFilamentState,
    compute_filament_colors,
    is_loaded_rgba,
    parse_sliced_colors,
)

# Obviously-fake patterned colors (never real device captures): one per physical extruder.
RED = "AA0000FF"
GREEN = "00BB00FF"
BLUE = "0000CCFF"
GREY = "DDDDDDFF"
LOADED_FOUR = [RED, GREEN, BLUE, GREY]
EXIST_FOUR = [True, True, True, True]
SLICED_FOUR = ["#101010", "#202020", "#303030", "#404040"]
IDENTITY_MAP = [0, 1, 2, 3] + [0] * 28


def _state(table, rgba=None, exist=None):
    return LiveFilamentState(
        extruder_map_table=table,
        rgba_by_extruder=rgba if rgba is not None else list(LOADED_FOUR),
        filament_exist_by_extruder=exist if exist is not None else list(EXIST_FOUR),
    )


def test_identity_map_uses_loaded_color_per_tool():
    colors = compute_filament_colors(list(SLICED_FOUR), _state(list(IDENTITY_MAP)))
    assert colors == ["#AA0000", "#00BB00", "#0000CC", "#DDDDDD"]


def test_remapped_table_follows_the_physical_extruder():
    remap = [2, 0, 1, 3] + [0] * 28
    colors = compute_filament_colors(list(SLICED_FOUR), _state(remap))
    assert colors == ["#0000CC", "#AA0000", "#00BB00", "#DDDDDD"]


def test_more_than_four_logical_tools_collapse_onto_shared_physical_colors():
    sliced = SLICED_FOUR + ["#505050", "#606060"]
    table = [0, 1, 2, 3, 0, 1] + [0] * 26
    colors = compute_filament_colors(sliced, _state(table))
    assert colors == ["#AA0000", "#00BB00", "#0000CC", "#DDDDDD", "#AA0000", "#00BB00"]


def test_empty_extruder_falls_back_to_sliced_color():
    exist = [True, False, True, True]
    colors = compute_filament_colors(list(SLICED_FOUR), _state(list(IDENTITY_MAP), exist=exist))
    assert colors == ["#AA0000", "#202020", "#0000CC", "#DDDDDD"]


def test_default_white_rgba_falls_back_to_sliced_color():
    rgba = [RED, "FFFFFFFF", BLUE, GREY]
    colors = compute_filament_colors(list(SLICED_FOUR), _state(list(IDENTITY_MAP), rgba=rgba))
    assert colors == ["#AA0000", "#202020", "#0000CC", "#DDDDDD"]


def test_no_loaded_and_no_sliced_color_leaves_tool_unset():
    exist = [False, False, False, False]
    sliced = ["#101010", "", "#303030", ""]
    colors = compute_filament_colors(sliced, _state(list(IDENTITY_MAP), exist=exist))
    assert colors == ["#101010", "", "#303030", ""]


def test_no_sliced_colors_returns_none_so_the_component_skips_the_write():
    assert compute_filament_colors([], _state(list(IDENTITY_MAP))) is None


def test_all_tools_unresolved_returns_none():
    exist = [False, False, False, False]
    sliced = ["", "", "", ""]
    assert compute_filament_colors(sliced, _state(list(IDENTITY_MAP), exist=exist)) is None


def test_parse_sliced_colors_splits_on_semicolons():
    assert parse_sliced_colors("#101010;#202020;#303030") == ["#101010", "#202020", "#303030"]
    assert parse_sliced_colors("#101010 ; #202020") == ["#101010", "#202020"]
    assert parse_sliced_colors(None) == []
    assert parse_sliced_colors("") == []


def test_parse_sliced_colors_preserves_empty_slots_for_index_alignment():
    # An empty middle slot must stay in place so tool 2 keeps its own color instead of inheriting
    # tool 1's (a regression the naive "drop empty chunks" split introduced).
    assert parse_sliced_colors("#FF0000;;#0000FF") == ["#FF0000", "", "#0000FF"]


def test_empty_sliced_slot_does_not_shift_later_tool_colors():
    exist = [False, False, False]
    state = LiveFilamentState(
        extruder_map_table=[0, 1, 2] + [0] * 29,
        rgba_by_extruder=[RED, GREEN, BLUE],
        filament_exist_by_extruder=exist,
    )
    colors = compute_filament_colors(parse_sliced_colors("#FF0000;;#0000FF"), state)
    assert colors == ["#FF0000", "", "#0000FF"]


def test_is_loaded_rgba_rejects_empty_and_malformed():
    assert is_loaded_rgba("AA0000FF") is True
    assert is_loaded_rgba("FFFFFFFF") is False
    assert is_loaded_rgba("ffffffff") is False
    assert is_loaded_rgba("ABC") is False
    assert is_loaded_rgba(None) is False
