#!/usr/bin/env bash
set -euo pipefail

VERSION="3.22.0"
PREFIX="$PWD/.valgrind"

if [ ! -x "$PREFIX/bin/valgrind" ]; then
    wget "https://sourceware.org/pub/valgrind/valgrind-${VERSION}.tar.bz2"
    tar -xjf "valgrind-${VERSION}.tar.bz2"
    cd "valgrind-${VERSION}"
    ./configure --prefix="${PREFIX}" > /dev/null
    make -j"$(getconf _NPROCESSORS_ONLN || echo 1)" > /dev/null
    make install > /dev/null
fi
