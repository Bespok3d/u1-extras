# U1 Smart Top Cover

Lets your slicer run the exhaust fan of the Snapmaker U1 top cover, and cools the chamber to suit
the materials you print.

Orca and Snapmaker Orca have an exhaust fan setting in every filament profile. On a stock U1 that
setting does nothing: the printer answers "Unsupported fan ID: 3". With this plugin, the exhaust
fan runs at the speed you set in the slicer.

## What you get

- The exhaust fan follows the slicer's exhaust speed, during the print and after it.
- A speed the slicer sets never stays on forever. When a print ends, is cancelled or fails, the
  exhaust turns off by itself. A different speed you set yourself afterwards, on the screen or
  the console, is left alone, and so is an `M106 P3` you type while no print runs.
- No top cover? Nothing breaks. The print goes on, and the console says once that there is no
  top cover.
- When the printer keeps the chamber warm (for ABS or ASA), the exhaust stays off, as it should.
  The slicer's exhaust speed is skipped then.
- For PLA, PETG and TPU, the chamber is cooled to suit the lowest softening temperature of the
  materials the print uses, instead of the stock fixed 42 C. You pick how hard the fans work with
  **Fan level** (see below).
- One setting, **Fan level**, in the plugin's **Config** tab. **Balanced** is the default. Everything else
  works as soon as it is installed.

## How to use it

1. In the slicer, open the filament profile, then the **Cooling** tab.
2. Under **Exhaust fan**, tick **Activate air filtration**.
3. Set **During print** (the speed while printing) and **Complete print** (the speed after the
   print ends), in percent.
4. Slice and print.

Snapmaker's own profiles have this off for PLA, PETG and TPU, and on for ABS and ASA. For ABS
and ASA the start G-code keeps the chamber warm, so the exhaust stays off while printing. The
"Complete print" speed still runs after the print ends.

## Fan level

For PLA, PETG and TPU, the stock start G-code cools the chamber to a fixed 42 C, whatever the
material. The plugin reads the softening temperature of each material the print uses, takes the
lowest, and cools the chamber to a little below it. A spool that is loaded but not used is
ignored. ABS and ASA prints keep the chamber warm, as stock.

1. Open the plugin's **Config** tab and pick a **Fan level**. **Balanced** is the default.
2. Print as usual. The slicer writes each material's softening temperature into the print file;
   in Orca it is **Softening temperature** in the filament profile.

T is the lowest softening temperature among the materials the print uses.

| Fan level | Chamber target | Lowest exhaust speed | What you hear |
| --- | --- | --- | --- |
| Coolest chamber - loudest fan | T minus 15 C | 40 % | The exhaust runs all print, loudest. |
| Cool chamber - louder fan | T minus 12 C | 25 % | Always on, a bit quieter. |
| Balanced | T minus 10 C | 15 % | Always on, quiet. |
| Warmer chamber - quieter fan | T minus 7 C | 5 % | Barely audible, speeds up when the chamber warms. |
| Warmest chamber - quietest fan | T minus 5 C | off | Silent until the chamber passes the target. |

At every level the alarm is T minus 2 C. Above the target, the exhaust speeds up to cool.

Example, PLA with a softening temperature of 45 C, at **Balanced**: target 35 C, alarm 43 C, lowest
exhaust speed 15 %.

No usable softening temperature in the print file? The stock cooling runs, and the console says so.

### Know this before you print

- **The alarm pauses the print.** If the chamber stays above the alarm for 4 minutes, the printer
  pauses. Stock puts the alarm at 48 C. With a low softening temperature it comes much lower: TPU
  at 30 C gives an alarm at 28 C. In a warm room the chamber may not get that cool, and the
  print pauses. For a material like that, check its softening temperature in the filament
  profile, or pick a cooler fan level.
- **The slicer's exhaust speed wins over the level's lowest speed.** With **Activate air
  filtration** ticked, the slicer's "During print" speed becomes the lowest exhaust speed.
- **While a print file is loaded, a `SET_PURIFIER_MODE MODE=1` you type is changed too.** That includes a paused print and a print that failed. The plugin cannot
  tell it from the start G-code's line, so its own numbers replace yours.
- **Your filament profile decides.** The plugin uses the softening temperature the slicer wrote.
  If a profile has a wrong value, the target is wrong too.

## Check that it works

Type these in the Fluidd console, with the printer idle and the top cover on.

| Type this | What you should see |
| --- | --- |
| `M106 P3 S128` | No "Unsupported fan ID: 3" error. The exhaust fan starts at about half speed. |
| `GET_PURIFIER` | In the reply, `'mode': 'IDLE'`, and the exhaust fan `'speed'` at about 0.5. If you touched the fan on the screen in between, it shows the screen's speed. |
| `M106 P3 S0` | The exhaust fan turns off at once. |
| `SET_PURIFIER_MODE MODE=3` then `M106 P3 S255` | The first time since Klipper started, the console says "u1_top_cover: the chamber is heating or kept warm, so the exhaust stays off and M106 P3 is ignored". The exhaust stays off. |
| `SET_PURIFIER_MODE MODE=0` | Puts the purifier back to idle. The circulator (inner fan) stops after its own delay, 180 seconds by default. |
| `FIRMWARE_RESTART` | Puts back your saved exhaust turn-off delay. `MODE=3` set it to 0 until Klipper restarts. |

For the fan level, start a PLA, PETG or TPU print and look at the Fluidd console during the start
G-code.

| Look for | What it means |
| --- | --- |
| `u1_top_cover: lowest softening temperature 45 C, fan level Balanced` | The plugin read the print file. |
| `Purifier mode set to COOL CHAMBER` with `DESIRE_TEMP`, `ALARM_TEMP` and `FAN_SPEED` | These show the plugin's numbers, not 42 and 48. |
| `u1_top_cover: no softening temperature for the used materials in the print file, the start G-code's cooling is kept` | The plugin could not get a softening temperature from the print file: none written, unreadable, or no material used. The stock 42 C cooling runs. |
| `u1_top_cover: softening temperature 10 C is too low for fan level Balanced, the start G-code's cooling is kept` | The target would be 0 C or below, which turns the cooling off. The stock 42 C cooling runs. |

An ABS or ASA print, or a printer with no top cover, shows none of these lines.

## Requirements

- A Snapmaker U1 on stock firmware.
- The top cover, for the fan to run. The plugin loads without it.
- For the fan level: print files sliced with Orca or Snapmaker Orca.

## For the curious: how it works

The slicer sends the exhaust speed as `M106 P3 S<0 to 255>`. The plugin takes over `M106` and
handles only `P3`; every other `M106` goes to the stock command, unchanged.

- `M106 P3 S<n>` sets the exhaust to n/255. Above 255 runs at full speed. No `S` runs at full
  speed, as the stock `M106` does.
- `M106 P3 S0` turns the exhaust off at once, as the stock `M106 S0` does for any other fan.

### End of print

- Print finished: the slicer sends its "Complete print" speed after the end G-code. The exhaust
  runs at that speed for the stored turn-off delay, then turns off. The stock start G-code
  stores a delay of 0; then the exhaust runs for 180 seconds, the purifier's own default.
- Print cancelled: the stock cancel sets the purifier to idle, and the exhaust turns off after
  the stored delay, as it does without this plugin.
- Print failed: no stock macro runs, so the plugin turns the exhaust off itself, after the stored
  delay, or after 180 seconds when the stored delay is 0.

### The purifier mode decides

The start G-code sets the purifier mode with `SET_PURIFIER_MODE`. That mode decides what
`M106 P3` may do.

| Purifier mode | What `M106 P3` does |
| --- | --- |
| 0, idle | Sets the exhaust to the slicer's speed. |
| 1, cool chamber | Sets the exhaust to the slicer's speed, and that speed becomes the lowest speed the cooling loop may use. The loop can still speed up the exhaust to cool the chamber, and its over-temperature alarm still works. `M106 P3 S0` sets that lowest speed to 0, so the loop may still start the exhaust if the chamber gets warm. |
| 2, preheat chamber, or 3, hot chamber | Ignored. These modes keep the exhaust off to hold the heat. The console says so once per Klipper start. |

A later `SET_PURIFIER_MODE` or `SET_PURIFIER` always wins over an earlier `M106 P3`: the last
command sent sets the fan.

### Fan level

The plugin also takes over `SET_PURIFIER_MODE` and changes only `MODE=1`, the cool chamber mode.
It replaces `DESIRE_TEMP`, `ALARM_TEMP` and `FAN_SPEED`, keeps every other parameter, and hands
the command to the stock purifier. Every other mode goes to the stock command unchanged.

It reads the end of the print file for two lines the slicer writes:

- `; filament used [mm] = ...`: a material counts when its length is above 0.
- `; temperature_vitrification = ...`: the softening temperature of each material.

A `SET_PURIFIER_MODE MODE=1` typed in the console with no print file loaded goes to the stock
command unchanged.

### What it does not do

- It does not touch any other fan, nor the purifier's inner fan.
- It does not change the stock purifier, the start G-code or the end G-code files.
- After a power-loss resume, the exhaust stays as the resume sets it until the slicer's next
  `M106 P3`.
