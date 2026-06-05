#!/usr/bin/env bash
set -euo pipefail

if ! command -v nasm &>/dev/null; then
    apt-get install -y nasm
fi
