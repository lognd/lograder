#!/usr/bin/env bash
set -euo pipefail

if ! command -v ty &>/dev/null; then
    pip install ty
fi
