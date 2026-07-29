# Attributions - prometheus-exporter

**Plugin author:** Bespok3d, vendoring prometheus-klipper-exporter (Steve Cross, scross01); monitoring on the U1 was first done by @horzadome in the Extended Firmware overlay `67-app-monitoring`

Publishes printer metrics for Prometheus.

| Upstream project | Author | Licence | Needed at runtime | Code ships in this package |
| --- | --- | --- | --- | --- |
| prometheus-klipper-exporter | Steve Cross (scross01) | MIT | yes | yes |

The exporter is cross-compiled to a static arm64 binary at build time and shipped inside this
plugin. Upstream: https://github.com/scross01/prometheus-klipper-exporter

Ported from the Extended Firmware overlay `67-app-monitoring` (paxx12), GPL-3.0.

## Copyright notices

MIT requires the notice to travel with the binary this plugin ships. The full licence text is in
`LICENSES/MIT.txt` at the root of this repo.

| Component | Licence | Copyright notice, as the project states it |
| --- | --- | --- |
| prometheus-klipper-exporter | MIT | `Copyright 2022 Stephen Cross` |

Read from `LICENSE` in scross01/prometheus-klipper-exporter, retrieved 2026-07-28.
