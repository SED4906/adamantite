# Adamantite
A very simple build system. For example, `cd pkgs` and `python ../adamantite.py libjpeg-turbo`

- [x] Unsandboxed builds (uses the host environment)
- [x] Sandboxed builds (sets up a more consistent temporary environment)

A sandboxed build is used for the specified package and its explicit dependencies, unsandboxed builds are used to bootstrap the build environment.

## Schema
- `version` The package version, which will be included in the output filename.
- `build` Bash script that will be run with `$PACKAGE_OUT` set to the output directory to install files to, and the working directory containing only the `distfiles` to start with.
- `depends` Optional list of explicit dependencies, as package names.
- `distfiles` Optional list of tables:
 - `uri` URL to download package from
 - `blake2b` BLAKE2B checksum, allows any length.
 - `name` Optional file name, if the one implied by `uri` is insufficient.
