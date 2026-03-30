#!/usr/bin/env bash
set -euo pipefail

VERSION="9.0.2"

if [ ! -x "pytest" ]; then
    python3 -m pip install "pytest==${VERSION}"
fi
