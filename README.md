# u1-extras

A co-repo of optional Bespok3d add-ons for the Snapmaker U1 (and Klipper printers), each installable
on its own from the store. A grab-bag of server-side extras ported from the extended firmware: LED
control, push notifications, monitoring, cloud access, and handy system utilities.

Plugins:

- **wled** - Drive WLED status LEDs from Moonraker's built-in `[wled]` (network-attached strips).
- **moonraker-notify** - Push print events (done / failed / error) to your phone or chat via Apprise.
- **panda-breath** - Connect a Panda Breath chamber-heating device (experimental).

(Build-heavier add-ons - a Prometheus exporter, OctoEverywhere cloud, and static CLI utilities - land
in this same list as their build pipelines come online.)

## Layout

```text
u1-extras/
  <plugin-id>/          # one plugin = one dir; its name is the manifest .name
    manifest.json
    files/              # payload the daemon places on the printer
    doc/README.md       # rendered in-app; not deployed
  scripts/{pack.sh,generate-atom.mjs,assemble-list.mjs}
  .github/workflows/release.yml
  index.json            # the published sub-list (committed; referenced by main-index lists[])
  dist/                 # build output (gitignored)
```

Each plugin declares WHAT (a destination `class` + a `restart` hook), never a path or a raw command;
the printer-side adapter realizes it. See `Bespok3d/doc/anatomy-of-a-plugin.md`.

## Releasing

Bump a plugin's `manifest.json` `version` and push to `main`. CI packs each `.b3`, cuts a release per
plugin, regenerates this repo's `index.json` sub-list, and registers it in `Bespok3d/main-index`.
Secret: `MAIN_INDEX_TOKEN` (contents:write on main-index). Signing deferred.

## Maintainership

These plugins are published and maintained by the Bespok3d org, and several repackage or build on
upstream source material. If you own the source material a plugin is based on and would rather manage
it yourself, you are welcome to contact the org to claim it back. The one condition is that it stays
actively maintained: a claimed plugin left to rot will be reclaimed so users are never stranded on an
abandoned package.
