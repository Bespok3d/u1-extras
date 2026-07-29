# u1-extras

[![licence](https://img.shields.io/badge/licence-GPL--3.0-blue)](LICENSE)
[![release](https://img.shields.io/github/v/release/Bespok3d/u1-extras)](https://github.com/Bespok3d/u1-extras/releases)
![printer](https://img.shields.io/badge/printer-Snapmaker%20U1-informational)
![stock firmware](https://img.shields.io/badge/stock%20firmware-no%20flashing-brightgreen)

A co-repo of optional Bespok3d add-ons for the Snapmaker U1 (and Klipper printers), each installable
on its own from the store. A grab-bag of server-side extras and small U1 niceties: LED control, push
notifications, monitoring, handy system utilities, and G-code preview polish.

Plugins:

- **wled** - Drive WLED status LEDs from Moonraker's built-in `[wled]` (network-attached strips).
- **moonraker-notify** - Push print events (done / failed / error) to your phone or chat via Apprise.
- **klipper-hooks** - Prefix-named lifecycle hooks that run in sorted order.
- **prometheus-exporter** - A Prometheus metrics exporter (CI-built binary).
- **system-utils** - Static arm64 CLI utilities (curl, rsync).
- **u1-gcode-colors** - Color Fluidd's G-code preview by the filament actually loaded on each tool's extruder (U1-only).

(panda-breath and OctoEverywhere have moved to their own repos: `plugins/panda-breath-plugin` and
`plugins/octoeverywhere-plugin`.)

## Layout

```text
u1-extras/
  <plugin-id>/          # one plugin = one dir; its name is the manifest .name
    manifest.json
    files/              # payload the daemon places on the printer
    doc/README.md       # rendered in-app; not deployed
  .github/workflows/release.yml
  index.json            # the published sub-list (committed; referenced by main-index lists[])
  dist/                 # build output (gitignored)
```

Each plugin declares WHAT (a destination `class` + a `restart` hook), never a path or a raw command;
the printer-side adapter realizes it.

## Build locally

Needs Node.js 20+. Builds run through the shared `Bespok3d/b3-builder` tool:

```sh
npm install github:Bespok3d/b3-builder
npx b3-builder build --source ./moonraker-notify --atom-repo Bespok3d/u1-extras
# -> dist/moonraker-notify-<ver>.b3 + dist/moonraker-notify.atom.json
```

Drop `--source` to build every plugin in the repo at once.

The Action runs with `bake: 'true'`: a plugin that ships a `requirements.txt` or
`klipper_requirements.txt` at its root gets its Python deps downloaded for the printer platform
(aarch64, CPython 3.11) at build time. Pass `--bake` to do the same locally.

## Releasing

Bump a plugin's `manifest.json` `version` and push to `main`. CI runs the `Bespok3d/b3-builder`
Action over the whole repo, which packs each `.b3`, cuts a release per plugin, assembles this repo's
`index.json` sub-list as `U1 Extras`, and registers it in `Bespok3d/main-index`
(`lists/<repo>.json`). Secrets: `MAIN_INDEX_TOKEN` (contents:write on main-index) and
`REGISTRY_SIGNING_KEY` (the org registry key the `b3-builder` Action signs each `.b3` and atom
with).

## Composition

Bespok3d's own code in this repository is under the repository licence below. The third-party works
named here are separate works, aggregated with Bespok3d's code, each under its own licence. They are
not under the repository licence and Bespok3d does not relicense them. Each plugin's
`doc/ATTRIBUTIONS.md` names its upstreams and carries their copyright notices; the licence texts are
in [`LICENSES/`](LICENSES/).

**Stored in this repository.** The `moonraker-notify` plugin vendors Apprise 1.12.0 and its ten
runtime dependencies under `moonraker-notify/files/site-packages/`, because Moonraker's `[notifier]`
has to import them on a printer where pip cannot install anything. Every one of the eleven packages
carries its own licence file in its `dist-info`, and
[`moonraker-notify/doc/ATTRIBUTIONS.md`](moonraker-notify/doc/ATTRIBUTIONS.md) lists each with its
licence and copyright notice. Three of the vendored files are compiled extension modules, from
charset-normalizer and PyYAML, shipped as those projects publish them under the MIT licence.

**Fetched or built at package time.** These are not in the repository. Each plugin's `manifest.json`
carries a bake directive that fetches or builds them, so they enter only the built `.b3` package.

| Component                   | What it is                                                                              | Version                                           | Licence                                          |
| --------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------ |
| curl                        | the `system-utils` command, built by Bespok3d, statically linked against nine libraries | 8.17.0                                            | the curl licence, plus each linked library's own |
| rsync                       | the `system-utils` command                                                              | 3.4.4                                             | GPL-3.0-or-later                                 |
| prometheus-klipper-exporter | the `prometheus-exporter` binary                                                        | commit `9eacec280108a4da8156b47c01c2862219d86ecd` | MIT                                              |

### Corresponding Source

Bespok3d builds both `system-utils` binaries rather than fetching a built one, so the source that
corresponds to each shipped binary is upstream's source **plus** the configuration Bespok3d built it
with. All of it is public and is in every release of this repository:

- `rsync` 3.4.4, GPL-3.0-or-later: upstream
  `https://download.samba.org/pub/rsync/src/rsync-3.4.4.tar.gz`, sha256
  `bd88cf82fa653da32314fb229136407c5c90f80d1758d8f4b091767877d8fa96`, built by
  [`system-utils/toolchain/rsync.Dockerfile`](system-utils/toolchain/rsync.Dockerfile)
- `curl` 8.17.0: upstream `https://curl.se/download/curl-8.17.0.tar.xz`, sha256
  `955f6e729ad6b3566260e8fef68620e76ba3c31acf0a18524416a185acf77992`, built by
  [`system-utils/toolchain/curl.Dockerfile`](system-utils/toolchain/curl.Dockerfile)

Anyone who received a binary may take that source and rebuild it. If any part of it is unreachable,
ask the Bespok3d org and it will be provided.

Two of the libraries linked into `curl`, libidn2 and the libunistring it pulls in, are offered under
the LGPL, which entitles whoever received the binary to relink it against their own build of either
library. The Dockerfile above is that material: it names the pinned curl source and every library
package, and running it again with a substituted library produces a curl with that library in it. The
full inventory of every binary Bespok3d ships, with versions, checksums and build configuration, is
in `Bespok3d_history/doc/gpl-source-inventory.md`.

## Maintainership

These plugins are published and maintained by the Bespok3d org, and several repackage or build on
upstream source material. If you own the source material a plugin is based on and would rather manage
it yourself, you are welcome to contact the org to claim it back. The one condition is that it stays
actively maintained: a claimed plugin left to rot will be reclaimed so users are never stranded on an
abandoned package.

## Licence

Copyright (C) 2026 unlucio and the Bespok3d contributors

GPL version 3, for the code in this repository written by Bespok3d. See Composition above for the
rest.

This program is free software: you can redistribute it and/or modify it under the terms of version 3
of the GNU General Public License as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not,
see <https://www.gnu.org/licenses/>. The full text is in [LICENSE](LICENSE).

Bespok3d's own code elsewhere in the project is AGPL-3.0-or-later. The code here is GPL-3.0-only
instead because it has Extended Firmware lineage, which is GPL-3.0-only. Version 3 of the GPL and
version 3 of the AGPL may be combined in a single work, and section 13 of each licence says so; what
cannot happen is code offered under version 3 of the GPL alone being re-offered under the AGPL.

Bespok3d is a project of the Bespok3d Organisation, which is not a legal entity. Copyright is held by
the individual authors named above.

## Support this project

`u1-gcode-colors` are Bespok3d's own work. `moonraker-notify`,
`wled`, `klipper-hooks`, `prometheus-exporter` and `system-utils` package software written by other people, and a donation
here is not a donation to them.

If our part saved you an afternoon, you can [buy me a coffee](https://buymeacoffee.com/unlucio).
