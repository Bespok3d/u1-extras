# Prometheus Exporter

Exposes Klipper and Moonraker metrics in Prometheus format so you can scrape them into a monitoring
stack (Prometheus + Grafana, Datadog, etc.). It runs
[scross01/prometheus-klipper-exporter](https://github.com/scross01/prometheus-klipper-exporter) as a
managed service.

## Use it

After installing, metrics are served at `http://<printer>:9101/metrics`. Point your Prometheus scrape
config (or Grafana Agent / Datadog OpenMetrics) at that endpoint.

This is for people who already run a metrics stack; if that means nothing to you, you do not need it.

## How the binary is built

The exporter is a small Go program. It is cross-compiled to a static arm64 binary in CI (pinned to a
known commit) and baked into the package; nothing is compiled on the printer.

## Status

**Experimental**, not yet verified on a physical printer.
