# Changelog

## 0.1.1

- Docs fix: the printer's metrics come from the multi-target `/probe?target=127.0.0.1:7125` endpoint,
  not bare `/metrics` (which serves only the exporter's own runtime). README, manifest description, and
  the listed endpoint now point at the address that actually returns `klipper_*` series. Verified on a
  Snapmaker U1.

## 0.1.0

- First release. Runs prometheus-klipper-exporter as a managed service on :9101, exposing
  Klipper/Moonraker metrics in Prometheus format. Binary cross-compiled to arm64 in CI. Experimental.
