# Attributions - system-utils

**Plugin author:** Bespok3d, vendoring curl and rsync; `curl` on the U1 was first added by @horzadome in the Extended Firmware overlay `01-system-utils`

Adds `curl` and `rsync` to the printer.

| Upstream project | Author | Licence | Needed at runtime | Code ships in this package |
| --- | --- | --- | --- | --- |
| curl | Daniel Stenberg and the curl contributors | curl licence (MIT-like) | yes | yes |
| rsync | Wayne Davison and the rsync contributors | GPL-3.0-or-later | yes | yes |

Both are static arm64 binaries built by Bespok3d from each project's own source tarball, with the
Dockerfiles in `toolchain/`, so Bespok3d's build configuration is part of the source that corresponds
to each shipped binary.

Both binaries are statically linked against musl libc 1.2.5, Alpine's C library, so a copy of musl is
inside each one and its MIT notice travels with them.

`curl` is statically linked, so nine further libraries are compiled into the binary that reaches the
printer and their notices travel with it:

| Library linked into curl | Version | Licence |
| --- | --- | --- |
| OpenSSL | 3.3.7 | Apache-2.0 |
| zlib | 1.3.2 | Zlib |
| brotli | 1.1.0 | MIT |
| zstd | 1.5.6 | BSD-3-Clause |
| libidn2 | 2.3.7 | LGPL-3.0-or-later, the arm Bespok3d takes of its dual licence |
| libunistring | 1.2 | LGPL-3.0-or-later, the arm Bespok3d takes of its dual licence |
| libpsl | 0.21.5 | MIT |
| libssh2 | 1.11.1 | BSD-3-Clause |
| nghttp2 | 1.69.0 | MIT |

Ported from the Extended Firmware overlay `01-system-utils`, GPL-3.0, with commits by @horzadome,
liberodark and paxx12.

## Copyright notices

Reproduced because these licences require the notice to travel with the binaries this plugin ships.
The full licence texts are in `LICENSES/` at the root of this repo.

| Component | Licence | Copyright notice, as the project states it |
| --- | --- | --- |
| musl libc 1.2.5 | MIT | `Copyright © 2005-2020 Rich Felker, et al.` |
| curl 8.17.0 | curl licence (MIT-like) | `Copyright (c) 1996 - 2025, Daniel Stenberg, <daniel@haxx.se>, and many contributors, see the THANKS file.` |
| rsync 3.4.4 | GPL-3.0-or-later | `Copyright (C) 1996 Andrew Tridgell`, `Copyright (C) 1996 Paul Mackerras`, `Copyright (C) 2003-2022 Wayne Davison` |
| OpenSSL 3.3.7 | Apache-2.0 | `Copyright (c) 1998-2026 The OpenSSL Project Authors`, `Copyright (c) 1995-1998 Eric A. Young, Tim J. Hudson` |
| zlib 1.3.2 | Zlib | `(C) 1995-2026 Jean-loup Gailly and Mark Adler` |
| brotli 1.1.0 | MIT | `Copyright (c) 2009, 2010, 2013-2016 by the Brotli Authors.` |
| zstd 1.5.6 | BSD-3-Clause | `Copyright (c) Meta Platforms, Inc. and affiliates. All rights reserved.` |
| libidn2 2.3.7 | LGPL-3.0-or-later | `Copyright (C) 2011-2024 Simon Josefsson` |
| libunistring 1.2 | LGPL-3.0-or-later | `Copyright (C) 2001-2002, 2005-2024 Free Software Foundation, Inc.` |
| libpsl 0.21.5 | MIT | `Copyright (C) 2014-2024 Tim Rühsen` |
| libssh2 1.11.1 | BSD-3-Clause | `Copyright (C) 2004-2007 Sara Golemon <sarag@libssh2.org>`, `Copyright (C) 2005,2006 Mikhail Gusarov <dottedmag@dottedmag.net>`, `Copyright (C) 2006-2007 The Written Word, Inc.`, `Copyright (C) 2007 Eli Fant <elifantu@mail.ru>`, `Copyright (C) 2009-2023 Daniel Stenberg`, `Copyright (C) 2008, 2009 Simon Josefsson`, `Copyright (C) 2000 Markus Friedl`, `Copyright (C) 2015 Microsoft Corp.` |
| nghttp2 1.69.0 | MIT | `Copyright (c) 2012, 2014, 2015, 2016 Tatsuhiro Tsujikawa`, `Copyright (c) 2012, 2014, 2015, 2016 nghttp2 contributors` |

Read from each project's own file at the version shipped, retrieved 2026-07-28: `COPYING` at curl tag
`curl-8_17_0`, the header of `rsync.c` at rsync tag `v3.4.4`, `README.md` at OpenSSL tag
`openssl-3.3.7`, `LICENSE` at zlib tag `v1.3.2`, brotli tag `v1.1.0`, zstd tag `v1.5.6` and libpsl tag
`0.21.5`, `COPYING` at libssh2 tag `libssh2-1.11.1` and nghttp2 tag `v1.69.0`, `lib/idn2.h.in` at
libidn2 tag `v2.3.7`, `lib/unistr.in.h` in the libunistring 1.2 release tarball, and `COPYRIGHT` at
musl tag `v1.2.5`.

Both binaries ship compiled, so their licences entitle a user to the source of the exact version
shipped: rsync 3.4.4 and curl 8.17.0 as those projects publish them, plus the Dockerfiles in
`toolchain/` that build them. libidn2 and libunistring are LGPL and are linked statically into
`curl`, so a user is also entitled to relink that binary against their own build of either library;
`toolchain/curl.Dockerfile` names every source and package the binary is built from and is exactly
that material. The full inventory, with checksums, is in
`Bespok3d_history/doc/gpl-source-inventory.md`.
