# U1 Chamber Cooling

Cools the Snapmaker U1 chamber to suit the materials you print.

For PLA, PETG and TPU, the stock start G-code cools the chamber to a fixed 42 C, whatever the
material. This plugin reads the softening temperature of each material the print uses, takes the
lowest, and cools the chamber to a little below it. You pick how hard the fans work.

## What you get

- The chamber target follows your materials: a PETG print may run warmer and quieter than a TPU
  print.
- Only the materials the print really uses count. A spool that is loaded but not used is ignored.
- One setting, **Fan level**, from 0 (coolest, loudest) to 1 (warmest, quietest).
- ABS and ASA prints keep the chamber warm, as stock. The plugin leaves them alone.
- No softening temperature in the print file? The stock cooling runs, and the console says so.

## How to use it

1. Install the plugin and open its **Config** tab.
2. Pick a **Fan level**. 0.5 is the default.
3. Print as usual. The slicer writes each material's softening temperature into the print file;
   in Orca it is **Softening temperature** in the filament profile.

## The fan levels

T is the lowest softening temperature among the materials the print uses.

| Fan level | Chamber target | Lowest exhaust speed | What you hear |
| --- | --- | --- | --- |
| 0 | T minus 15 C | 40 % | The exhaust runs all print, loudest. |
| 0.25 | T minus 12 C | 25 % | Always on, a bit quieter. |
| 0.5 | T minus 10 C | 15 % | Always on, quiet. |
| 0.75 | T minus 7 C | 5 % | Barely audible, speeds up when the chamber warms. |
| 1 | T minus 5 C | off | Silent until the chamber nears the target. |

At every level the alarm is T minus 2 C. Above the target, the exhaust speeds up to cool.

Example, PLA with a softening temperature of 45 C, at level 0.5: target 35 C, alarm 43 C, lowest
exhaust speed 15 %.

## Know this before you print

- **The alarm pauses the print.** If the chamber stays above the alarm for 4 minutes, the printer
  pauses. Stock puts the alarm at 48 C. With a low softening temperature it comes much lower: TPU
  at 30 C gives an alarm at 28 C. In a warm room the chamber may not get that cool, and the
  print pauses. For a material like that, check its softening temperature in the filament
  profile, or pick a lower fan level.
- **During a print, a `SET_PURIFIER_MODE MODE=1` you type is changed too.** The plugin cannot
  tell it from the start G-code's line, so its own numbers replace yours.
- **Your filament profile decides.** The plugin uses the softening temperature the slicer wrote.
  If a profile has a wrong value, the target is wrong too.

## Check that it works

Start a PLA, PETG or TPU print and look at the Fluidd console during the start G-code.

| Look for | What it means |
| --- | --- |
| `u1_chamber_cooling: lowest softening temperature 45 C, fan level 0.5` | The plugin read the print file. |
| `Purifier mode set to COOL CHAMBER` with `DESIRE_TEMP`, `ALARM_TEMP` and `FAN_SPEED` | These show the plugin's numbers, not 42 and 48. |
| `u1_chamber_cooling: no softening temperature for the used materials in the print file, the start G-code's cooling is kept` | The print file had no softening temperature. The stock 42 C cooling runs. |
| `u1_chamber_cooling: softening temperature 10 C is too low for fan level 0.5, the start G-code's cooling is kept` | The target would be 0 C or below, which turns the cooling off. The stock 42 C cooling runs. |

An ABS or ASA print shows neither plugin line.

## Requirements

- A Snapmaker U1 on stock firmware, with the top cover.
- Print files sliced with Orca or Snapmaker Orca.

## For the curious: how it works

The plugin takes over `SET_PURIFIER_MODE` and changes only `MODE=1`, the cool chamber mode. It
replaces `DESIRE_TEMP`, `ALARM_TEMP` and `FAN_SPEED`, keeps every other parameter, and hands the
command to the stock purifier. Every other mode goes to the stock command unchanged.

It reads the end of the print file for two lines the slicer writes:

- `; filament used [mm] = ...`: a material counts when its length is above 0.
- `; temperature_vitrification = ...`: the softening temperature of each material.

A `SET_PURIFIER_MODE MODE=1` typed in the console with no print loaded goes to the stock command
unchanged.
