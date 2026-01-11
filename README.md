# Adamantite
A very simple build system.

- [x] Unsandboxed builds (uses the host environment)
- [ ] Sandboxed builds (sets up a more consistent temporary environment)

## Process
The build environment will have at least `bash`, `bzip2`, `coreutils`, `diffutils`, `findutils`, `gawk`, `gcc`, `grep`, `gzip`, `make`, `patch`, `sed`, `tar`, and `xz` available by default. The environment variable `$PACKAGE_OUT` will be set to the directory that the build step should install files to. The build step will start in a working directory containing the distfiles for the package. The build step will not be done as root.
