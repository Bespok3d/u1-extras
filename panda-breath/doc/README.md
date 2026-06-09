# Panda Breath

Controls a [BIQU Panda Breath](https://github.com/justinh-rahb/pandabreath-klipper) chamber heater
from Klipper as a standard `heater_generic`. After installing, set the heater target from Fluidd or
Mainsail (or your slicer) like any other heater.

## What you need

- A Panda Breath device on your network (running stock OEM firmware). This plugin does not supply or
  flash the hardware; it teaches Klipper how to talk to a device you already have.
- Set **Panda Breath host** to its hostname or IP. If `.local` resolution fails, use the IP.

## Status

**Experimental.** The Klipper module is solid and stdlib-only, but this plugin has not yet been
verified against a physical Panda Breath. Treat it as a beta.

## Credits / license

The Klipper module `panda_breath.py` is vendored from
[justinh-rahb/pandabreath-klipper](https://github.com/justinh-rahb/pandabreath-klipper) at commit
`2fc8c03b918519060f0a2cc6b40a56fbc232e74f`, licensed **GPL-3.0**. The only change is normalizing a
few dash characters in comments to satisfy our linter; no code was changed.
