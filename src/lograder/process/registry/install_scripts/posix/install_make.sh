#!/usr/bin/env bash
set -euo pipefail

if ! command -v make &>/dev/null; then
    apt-get install -y make
fi
