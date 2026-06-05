#!/usr/bin/env bash
set -euo pipefail

if ! command -v ld.lld &>/dev/null; then
    apt-get install -y lld
fi
