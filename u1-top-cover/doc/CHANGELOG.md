# Changelog

## 0.2.0 (2026-11-22)

- New **Fan level** setting in the Config tab: 0, 0.25, 0.5, 0.75 or 1. For PLA, PETG and TPU, the
  chamber is now cooled to suit the lowest softening temperature of the materials the print uses,
  instead of the stock fixed 42 C. 0 cools hardest and is loudest, 1 is quietest. The default is
  0.5.
- A print file with no usable softening temperature keeps the stock cooling, and the console says
  so.

## 0.1.0 (2026-11-21)

- First release. The exhaust fan setting in Orca's filament profile now drives the top cover's
  exhaust fan. Orca sends it as `M106 P3`; before, the U1 answered "Unsupported fan ID: 3" and the
  setting did nothing.
- When a print ends, is cancelled or fails, the exhaust turns off by itself. A finished print
  first runs Orca's "complete print" exhaust speed.
- A printer with no top cover ignores the command, says so once, and keeps printing.
