#!/usr/bin/env bash
set -euo pipefail

if ! command -v mypy &>/dev/null; then
    pip install mypy
fi
