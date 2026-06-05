#!/usr/bin/env bash
set -euo pipefail

PREFIX="$PWD/.cmake"
VERSION="3.31.6"

if [ ! -x "$PREFIX/bin/cmake" ]; then
    wget "https://github.com/Kitware/CMake/releases/download/v${VERSION}/cmake-${VERSION}.tar.gz"
    tar -xzf "cmake-${VERSION}.tar.gz"
    cd cmake-3.31.6 > /dev/null
    ./bootstrap --prefix="$PREFIX" > /dev/null
    make -j"$(getconf _NPROCESSORS_ONLN || echo 1)" > /dev/null
    make install > /dev/null
    cd ..
fi
