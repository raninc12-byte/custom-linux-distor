#!/usr/bin/env bash
# Boots the most recently built ISO in QEMU for a quick smoke test.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISO="$(ls -t "$PROJECT_ROOT"/out/*.iso | head -n1)"

if [[ -z "$ISO" ]]; then
    echo "No ISO found in $PROJECT_ROOT/out - run scripts/build-iso.sh first" >&2
    exit 1
fi

echo "Booting $ISO in QEMU (UEFI, 4GB RAM)..."
run_archiso -i "$ISO" -u -r 4096
