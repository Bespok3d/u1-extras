# U1 G-code Preview Colors

**Status: verified on a real Snapmaker U1.** The Moonraker component that fills the preview colors
is complete, unit-tested, and confirmed on real hardware, including the tricky case of a
tool-to-extruder remap made on the printer's screen at launch.

Fluidd's G-code preview colors each tool's lines from the file's Moonraker metadata array
`filament_colors`. On the Snapmaker U1 that array is always empty (the firmware stores a
different, singular field), so every print shows the same fallback palette regardless of what
is actually loaded. This plugin fills that array from the printer's live filament state, so the
preview matches what will actually print.

## What it does

- Reads the U1's live tool to extruder mapping and each extruder's loaded filament color.
- Writes a `filament_colors` array into each G-code file's Moonraker metadata, one entry per
  tool, so Fluidd's preview (legend and lines) shows the real loaded color.
- Tracks changes: a remap on the printer's screen at launch, or a color change, refreshes the
  preview to match.
- Falls back to the file's own sliced color when a tool has no real loaded color, and leaves
  Fluidd's default palette in place when neither is available.
- Works automatically with the Spoolman helper plugin if installed: no separate setup, no
  coupling between the two plugins.

## What it does not do

- It never changes Fluidd itself. Only the metadata Fluidd already reads is filled in.
- It never edits the G-code file's own sliced color comment.

## Requirements

- A Snapmaker U1 (this plugin depends on U1-specific firmware state and does nothing on other
  printers).

## Configuration

- **Fill real per-tool colors** (toggle, on by default): turn off to stop filling new G-code
  files. A file already filled while the toggle was on keeps its colors until Moonraker
  recomputes that file's metadata (a rescan or re-add); it is not stripped immediately.

## Setup

1. Install this plugin from the Bespok3d store.
2. No further configuration is required; colors fill in automatically for every print.
