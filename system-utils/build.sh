#!/bin/sh
# Fetch static arm64 curl + rsync and bake them into files/bin. Run in CI; never on the printer.
# SHA-pinned against the upstream static-build releases. No compile, just download + verify + extract.
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="$HERE/files/bin"
WORK="$(mktemp -d)"
mkdir -p "$BIN"

CURL_URL="https://github.com/stunnel/static-curl/releases/download/8.17.0/curl-linux-aarch64-glibc-8.17.0.tar.xz"
CURL_SHA="3c6562544e1a21cd37e9dec7c48c7a6d9a2f64da42fde69ba79e54014b911abb"
RSYNC_URL="https://download.samba.org/pub/rsync/binaries/centos-8-aarch64/rsync-3.2.7.tar.gz"
RSYNC_SHA="2b8f21d006aaf94648bcc608717997cd34f27ba7f4b549f45d1a1dae63b78daa"

verify() { echo "$2  $1" | sha256sum -c - >/dev/null; }

curl -fsSL "$CURL_URL" -o "$WORK/curl.tar.xz"
verify "$WORK/curl.tar.xz" "$CURL_SHA"
tar -xJf "$WORK/curl.tar.xz" -C "$WORK"
install -m 0755 "$WORK/curl" "$BIN/curl"

curl -fsSL "$RSYNC_URL" -o "$WORK/rsync.tar.gz"
verify "$WORK/rsync.tar.gz" "$RSYNC_SHA"
tar -xzf "$WORK/rsync.tar.gz" -C "$WORK"
install -m 0755 "$WORK/usr/local/bin/rsync" "$BIN/rsync"

echo "baked static arm64 curl + rsync into files/bin"
