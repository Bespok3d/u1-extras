# Prometheus Exporter

Exposes Klipper and Moonraker metrics in Prometheus format so you can scrape them into a monitoring
stack (Prometheus + Grafana, Datadog, etc.). It runs
[scross01/prometheus-klipper-exporter](https://github.com/scross01/prometheus-klipper-exporter) as a
managed service.

## Use it

The exporter is multi-target (blackbox style), so it has two separate endpoints:

- `http://<printer>:9101/probe?target=127.0.0.1:7125` returns the printer's `klipper_*` metrics.
  `127.0.0.1:7125` is Moonraker on the U1. **This is the address you scrape.**
- `http://<printer>:9101/metrics` returns only the exporter's own runtime (`go_*`, `process_*`,
  `promhttp_*`) and no printer data. Do not point a dashboard at this one.

Quick check from any machine on the LAN:

```sh
curl "http://<printer>:9101/probe?target=127.0.0.1:7125"
```

You should see `klipper_*` series.

### Prometheus scrape config

Point Prometheus (or Grafana Agent / Datadog OpenMetrics) at the `/probe` endpoint, with the printer's
Moonraker as the target:

```yaml
  - job_name: "klipper"
    scrape_interval: 5s
    metrics_path: /probe
    static_configs:
      - targets: [ "127.0.0.1:7125" ]    # Moonraker, as reached from the exporter on the printer
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: "<printer>:9101"    # this plugin
```

This is for people who already run a metrics stack; if that means nothing to you, you do not need it.

## How the binary is built

The exporter is a small Go program. It is cross-compiled to a static arm64 binary in CI (pinned to a
known commit) and baked into the package; nothing is compiled on the printer.

## Status

Verified on a Snapmaker U1 (2026-07-23): the `/probe?target=127.0.0.1:7125` endpoint returns live
`klipper_*` metrics.
