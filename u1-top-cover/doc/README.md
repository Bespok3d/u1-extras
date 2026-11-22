# U1 Smart Top Cover

Lets your slicer run the exhaust fan of the Snapmaker U1 top cover.

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
- Nothing to set up. Install it and the slicer setting works.

## How to use it

1. In the slicer, open the filament profile, then the **Cooling** tab.
2. Under **Exhaust fan**, tick **Activate air filtration**.
3. Set **During print** (the speed while printing) and **Complete print** (the speed after the
   print ends), in percent.
4. Slice and print.

Snapmaker's own profiles have this off for PLA, PETG and TPU, and on for ABS and ASA. For ABS
and ASA the start G-code keeps the chamber warm, so the exhaust stays off while printing. The
"Complete print" speed still runs after the print ends.

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

## Requirements

- A Snapmaker U1 on stock firmware.
- The top cover, for the fan to run. The plugin loads without it.

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

### What it does not do

- It does not touch any other fan, nor the purifier's inner fan.
- It does not change the stock purifier, the start G-code or the end G-code.
- After a power-loss resume, the exhaust stays as the resume sets it until the slicer's next
  `M106 P3`.
