# Builds a genuinely static aarch64 rsync from rsync's own release tarball.
#
# Why we compile instead of pinning a prebuilt: nobody ships one that runs here. rsync's upstream
# (download.samba.org) publishes exactly one aarch64 build, centos-8-aarch64, and it dynamically links
# OpenSSL 1.1 -- the U1 carries only libcrypto.so.3 and has no /etc/ld.so.conf to bridge it, so that
# binary cannot start at all. The one third-party static-aarch64 project (jbruechert/rsync-static) froze
# its asset in 2020. Building from source is the only option that leaves us pinned to rsync itself.
#
# Alpine is the toolchain because its libc IS musl: an arm64 image under QEMU links static natively, with
# no cross-compiler to configure. Targets linux/arm64 (Rockchip U1).
FROM --platform=linux/arm64 alpine:3.21

RUN apk add --no-cache build-base curl

WORKDIR /build

# Pinned to the release tarball + its sha256. This is the whole external dependency: rsync's own source.
ARG RSYNC_VERSION=3.4.4
ARG RSYNC_SHA256=bd88cf82fa653da32314fb229136407c5c90f80d1758d8f4b091767877d8fa96

RUN curl -fsSL -o rsync.tar.gz "https://download.samba.org/pub/rsync/src/rsync-${RSYNC_VERSION}.tar.gz" \
    && echo "${RSYNC_SHA256}  rsync.tar.gz" | sha256sum -c - \
    && tar -xzf rsync.tar.gz

# Every --disable here drops a shared library rsync would otherwise link. openssl is the one that broke
# the old binary; zstd/lz4/xxhash/iconv/acl/xattr would each reintroduce the same class of failure. zlib
# and popt come from rsync's own bundled copies, so they link in rather than being looked up at runtime.
WORKDIR /build/rsync-${RSYNC_VERSION}
RUN ./configure \
      --disable-openssl \
      --disable-xxhash \
      --disable-zstd \
      --disable-lz4 \
      --disable-iconv \
      --disable-acl-support \
      --disable-xattr-support \
      --disable-md2man \
      --with-included-zlib=yes \
      --with-included-popt=yes \
      LDFLAGS=-static \
    && make -j"$(nproc)"

# Prove it before it can ever reach a printer: a dynamic section here means some --disable above stopped
# working, which is exactly how the current broken rsync shipped.
RUN ldd rsync 2>&1 | grep -q "Not a valid dynamic program\|not a dynamic executable\|statically linked" \
    && ./rsync --version

# /out holds exactly the members manifest.json declares: the bake fails on anything else left here.
# Stripped because a static link pulls musl's debug_info in with it, tripling the size of a binary that
# ships to a printer with a small flash.
RUN mkdir -p /out && install -m 0755 rsync /out/rsync && strip /out/rsync
