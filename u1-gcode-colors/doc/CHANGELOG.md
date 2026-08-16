# Changelog

## 0.1.2 (2026-08-16)

U1 G-code Preview Colors is now a stable plugin. Before, it only showed up in the store if you had set your
plugin channel to testing; now it shows for everyone. Nothing about the plugin itself changed.

## 0.1.1 (2026-07-04)

- Verified on a real Snapmaker U1: the G-code preview now shows each tool's actually loaded
  filament color, confirmed against a live print with a tool-to-extruder remap made on the
  printer's screen at launch.

## 0.1.0

- Plugin skeleton: manifest, config toggle, Moonraker component load hook.
- Moonraker component that fills each G-code file's `filament_colors` metadata array from the
  U1's live `print_task` state, with a per-tool fallback to the file's sliced color and then
  Fluidd's palette.
