# U1 Smart Top Cover

Orca's filament profiles have an "Exhaust fan" setting (Cooling, "Activate air filtration"). Orca
sends it as `M106 P3 S<0 to 255>`. The stock U1 answers "Unsupported fan ID: 3", so the setting
does nothing. This plugin makes `M106 P3` drive the Snapmaker top cover's exhaust fan, so the
slicer controls the exhaust without any start G-code edits.

## What it does

- `M106 P3 S<n>` sets the top cover exhaust fan to n/255. 255 is full speed, 0 is off. A value
  above 255 runs at full speed. `M106 P3` with no S runs at full speed, as the stock M106 does.
- Every other M106 (no P, or any P other than 3) goes to the stock M106, unchanged.

## The rules

### End of print

The exhaust never stays on forever.

- Print finished: Orca sends its "complete print" exhaust speed after the end G-code. The exhaust
  runs at that speed for the purifier's stored turn-off delay, then turns off. The stock start
  G-code stores a delay of 0; then the exhaust runs for 180 seconds, the purifier's own default.
- Print cancelled or failed: the stock cancel sets the purifier to idle, and the exhaust turns off
  after the stored delay, as it does without this plugin.

`M106 P3 S0` during a print turns the exhaust off after the stored delay, the same way
`SET_PURIFIER FAN=exhaust SPEED=0` does.

### No top cover

With no top cover connected, `M106 P3` is ignored. The print keeps going with no error. The
console says so once per Klipper start.

### SET_PURIFIER_MODE and M106 P3

The purifier mode set by the start G-code (`SET_PURIFIER_MODE`) decides what Orca may do.

| Purifier mode | What M106 P3 does |
| --- | --- |
| 0, idle | Sets the exhaust to Orca's speed. |
| 1, cool chamber | Sets the exhaust to Orca's speed, and that speed becomes the lowest speed the cooling loop may use. The loop can still speed up the exhaust to cool the chamber, and its over-temperature alarm still works. `M106 P3 S0` sets that lowest speed to 0, so the loop may still start the exhaust if the chamber gets warm. |
| 2, preheat chamber, or 3, hot chamber | Ignored. These modes keep the exhaust off to hold the heat. The console says so once per Klipper start. |

A later `SET_PURIFIER_MODE` or `SET_PURIFIER` always wins over an earlier `M106 P3`: the last
command sent sets the fan.

## What it does not do

- It does not touch any other fan, nor the purifier's inner fan.
- It does not change the stock purifier, the start G-code or the end G-code.
- It adds no setting: install it and Orca's exhaust setting works.
- After a power-loss resume, the exhaust stays as the resume sets it until Orca's next `M106 P3`.

## Requirements

- A Snapmaker U1 on stock firmware. The top cover is needed for the exhaust to run, not for the
  plugin to load.
