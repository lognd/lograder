#!/usr/bin/env bash
set -euo pipefail

if ! command -v clang &>/dev/null; then
    apt-get install -y clang
fi
