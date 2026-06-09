#!/bin/sh
# Cross-compile scross01/prometheus-klipper-exporter for the printer (arm64) and bake it into the
# package. Run in CI (needs Go); never on the printer. Pinned to a known-good commit. CGO off so the
# binary is fully static and portable across the printer's libc.
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
SRC_URL="https://github.com/scross01/prometheus-klipper-exporter.git"
SRC_SHA="9eacec280108a4da8156b47c01c2862219d86ecd"

WORK="$(mktemp -d)"
git clone --quiet "$SRC_URL" "$WORK"
git -C "$WORK" checkout --quiet "$SRC_SHA"

mkdir -p "$HERE/files/bin"
GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go -C "$WORK" build -o "$HERE/files/bin/prometheus-klipper-exporter" .
echo "built prometheus-klipper-exporter (linux/arm64) from ${SRC_SHA}"
