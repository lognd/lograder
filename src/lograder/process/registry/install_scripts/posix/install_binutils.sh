#!/usr/bin/env bash
set -euo pipefail

if ! command -v ar &>/dev/null || ! command -v nm &>/dev/null; then
    apt-get install -y binutils
fi
