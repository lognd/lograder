#!/usr/bin/env bash
set -euo pipefail

if ! command -v curl &>/dev/null; then
    apt-get install -y curl
fi
