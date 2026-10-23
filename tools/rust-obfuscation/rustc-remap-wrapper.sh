#!/bin/bash
# rustc wrapper for the host std bootstrap build (wired via the
# build.rustc-wrapper bootstrap config key when this file exists).
# Remaps the CI workspace prefix so the sysroot's panic locations do not
# reveal the build environment in downstream binaries; remapped paths
# surface as /rustc/1.99.0/library/... exactly like official rustc std.
real="$1"
shift
exec "$real" "$@" --remap-path-prefix=/home/runner/work/llvm-project/llvm-project=/rustc/1.99.0
