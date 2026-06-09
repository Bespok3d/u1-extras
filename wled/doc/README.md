# WLED Status Lights

Connects a network-attached [WLED](https://kno.wled.ge/) LED strip to your printer through
Moonraker's built-in `[wled]` support. Once installed you can control the strip from Fluidd or
Mainsail and from Klipper macros (`WLED_ON`, `WLED_OFF`, `SET_WLED`).

## What you need

- A WLED device on the same network (an ESP running WLED, wired to your LED strip). This plugin does
  not flash or supply hardware; it only tells Moonraker how to reach a WLED device you already have.

## Configuration

| Setting | Meaning |
| --- | --- |
| Strip name | The name you reference in macros, e.g. `WLED_ON STRIP=status`. |
| WLED address | Hostname or IP of the WLED device (e.g. `wled.local` or `192.168.1.50`). |
| LED count | Number of LEDs on the strip. |
| Color order | Match your strip's wiring (most are `GRB`). |

After installing, restart is automatic. Set a preset in the WLED app and Moonraker can switch to it.
