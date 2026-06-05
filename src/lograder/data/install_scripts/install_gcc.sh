#!/usr/bin/env bash
set -euo pipefail

if ! command -v gcc &>/dev/null; then
    apt-get install -y gcc
fi
