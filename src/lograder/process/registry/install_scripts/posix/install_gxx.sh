#!/usr/bin/env bash
set -euo pipefail

if ! command -v g++ &>/dev/null; then
    apt-get install -y g++
fi
