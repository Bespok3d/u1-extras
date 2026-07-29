# System Utilities (curl, rsync)

Installs static **arm64** builds of `curl` and `rsync` into `$BESPOK3D/bin` on the printer. Stock
Snapmaker firmware ships neither, so this is a convenience for shell scripting, backups, and transfers
when you SSH in.

Bespok3d itself does not need these (it reaches Moonraker over HTTP and moves files over SFTP) - they
are purely for your own use.

## Notes

- Binaries land in `$BESPOK3D/bin`. They are not yet added to your login `PATH`, so call them by full
  path (e.g. `$BESPOK3D/bin/curl ...`) or add that dir to your `PATH`. A base-layer `PATH` entry is a
  planned follow-up.
- Both binaries are compiled by Bespok3d in CI, from each project's own SHA-pinned source tarball, and
  baked into the package; nothing is downloaded or compiled on the printer.
- **Experimental.** Installed and running on a U1.
