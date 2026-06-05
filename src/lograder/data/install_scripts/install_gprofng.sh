#!/usr/bin/env bash
set -euo pipefail

VERSION="2.42"
PREFIX="$PWD/.gprofng"

if [ ! -x "$PREFIX/bin/gprofng" ]; then
    wget -q "https://ftp.gnu.org/gnu/binutils/binutils-${VERSION}.tar.gz"
    tar -xzf "binutils-${VERSION}.tar.gz"
    cd "binutils-${VERSION}"
    ./configure \
        --prefix="${PREFIX}" \
        --enable-gprofng \
        --disable-gold \
        --disable-plugins \
        --disable-werror \
        > /dev/null
    make -C gprofng -j"$(getconf _NPROCESSORS_ONLN || echo 1)" > /dev/null
    make -C gprofng install > /dev/null
    cd ..
    rm -rf "binutils-${VERSION}" "binutils-${VERSION}.tar.gz"
fi
