# Changelog

## 0.1.2 (2026-07-28)

- `curl` is now built by Bespok3d from curl's own SHA-pinned source tarball, the same way `rsync`
  already was, instead of being fetched as a prebuilt static release. Two of the libraries it links
  statically are LGPL, and that licence entitles whoever received the binary to relink it against
  their own build of those libraries; a binary someone else compiled left nothing to hand over.
- The build drops two components the fetched binary carried: the c-ares resolver, which curl replaces
  with its own threaded resolver, and HTTP/3. Both are still available to the build, so either can be
  added back if something on the printer turns out to want it.
- `doc/ATTRIBUTIONS.md` now carries the copyright notice of every library linked into `curl`, and of
  the musl C library that both `curl` and `rsync` are statically linked against.

## 0.1.0

- First release. Ships SHA-pinned static arm64 `curl` and `rsync` into `$BESPOK3D/bin` via the new
  `system-bin` placement class. Experimental.
