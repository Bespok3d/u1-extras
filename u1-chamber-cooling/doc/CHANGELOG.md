# Changelog

## 0.1.0 (2026-11-22)

- First release. For PLA, PETG and TPU prints, the chamber cooling now follows the softening
  temperature of the materials the print uses, and the fan level you pick. Before, the start
  G-code cooled to a fixed 42 C for every material.
- ABS and ASA prints are left as they are.
- A print file without softening temperatures, or with one too low to leave a target above 0 C, keeps the stock cooling, and the console says so.
