# Changelog

## 0.1.0 (2026-11-21)

- First release. The exhaust fan setting in Orca's filament profile now drives the top cover's
  exhaust fan. Orca sends it as `M106 P3`; before, the U1 answered "Unsupported fan ID: 3" and the
  setting did nothing.
- When a print ends, is cancelled or fails, the exhaust turns off by itself. A finished print
  first runs Orca's "complete print" exhaust speed.
- A printer with no top cover ignores the command, says so once, and keeps printing.
