#!/usr/bin/env bash
set -euo pipefail

if ! command -v perf &>/dev/null; then
    KERNEL="$(uname -r)"
    apt-get install -y "linux-tools-${KERNEL}" linux-tools-generic 2>/dev/null \
        || apt-get install -y linux-perf 2>/dev/null \
        || { echo "Could not install perf for kernel ${KERNEL}"; exit 1; }
fi
