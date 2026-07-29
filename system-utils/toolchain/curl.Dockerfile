# Builds a genuinely static aarch64 curl from curl's own release tarball.
#
# Why Bespok3d builds curl rather than shipping a published static binary: curl links libidn2, and
# libidn2 is LGPL. Anyone who receives a static LGPL link is entitled to the material needed to relink
# the binary against their own build of that library. A binary someone else compiled leaves us with
# nothing to hand over. Building it here puts the whole build configuration in our hands, and this
# file plus the pinned sources below reproduce the shipped binary from source.
#
# The libraries are Alpine's own static packages. The base image tag fixes the Alpine branch, not the
# library versions: a rebuild draws whatever v3.21 currently carries. That is why the `apk info -v`
# step below prints the versions into the build log, and why the GPL source inventory names the exact
# versions the shipped binary was linked against rather than pointing at this package list.
#
# Two components the previously shipped binary carried are absent here: c-ares, so curl uses its own
# threaded resolver, and nghttp3, so there is no HTTP/3. Alpine 3.21 carries both, static archives
# included, so either can be added back by installing its -dev package and dropping the matching
# --without flag below.

FROM --platform=linux/arm64 alpine:3.21

RUN apk add --no-cache build-base curl \
      openssl-dev openssl-libs-static \
      zlib-dev zlib-static \
      brotli-dev brotli-static \
      zstd-dev zstd-static \
      libidn2-dev libidn2-static \
      libunistring-dev libunistring-static \
      libpsl-dev libpsl-static \
      libssh2-dev libssh2-static \
      nghttp2-dev nghttp2-static

# The exact library versions this build links in, printed into the build log so the GPL source
# inventory can name them without anyone guessing from the package list above.
RUN apk info -v | grep -E "^(openssl|zlib|brotli|zstd|libidn2|libunistring|libpsl|libssh2|nghttp2)" | sort

WORKDIR /build

ARG CURL_VERSION=8.17.0
ARG CURL_SHA256=955f6e729ad6b3566260e8fef68620e76ba3c31acf0a18524416a185acf77992

RUN curl -fsSL -o curl.tar.xz "https://curl.se/download/curl-${CURL_VERSION}.tar.xz" \
    && echo "${CURL_SHA256}  curl.tar.xz" | sha256sum -c - \
    && tar -xJf curl.tar.xz

WORKDIR /build/curl-${CURL_VERSION}

# Two flags earn their place. Alpine's gcc defaults to PIE, which quietly produces a dynamic binary,
# so the objects are compiled -fno-PIE. And libtool consumes a bare -static as one of its own options
# instead of passing it to the linker, so the fully static link is asked for at make time with
# libtool's own -all-static. Without both, this builds a dynamic curl and says nothing.
RUN PKG_CONFIG="pkg-config --static" ./configure \
      --disable-shared --enable-static \
      --with-openssl --with-brotli --with-zstd --with-libidn2 --with-libssh2 \
      --with-nghttp2 --with-libpsl \
      --without-ngtcp2 --without-nghttp3 \
      --disable-ldap --disable-ldaps --disable-manual \
      CFLAGS=-fno-PIE LDFLAGS=-no-pie \
    && make -j"$(nproc)" LDFLAGS="-all-static -no-pie"

RUN ldd src/curl 2>&1 | grep -q "Not a valid dynamic program\|not a dynamic executable\|statically linked" \
    && ./src/curl --version

RUN mkdir -p /out && install -m 0755 src/curl /out/curl && strip /out/curl
