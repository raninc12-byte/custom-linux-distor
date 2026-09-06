#!/usr/bin/env bash
# Full ISO build: local repo -> service symlinks -> mkarchiso.
# Must be run on an Arch Linux host/container with archiso installed.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$PROJECT_ROOT/out"
WORK_DIR="/tmp/aibase-archiso-work"

"$PROJECT_ROOT/scripts/generate-branding-placeholders.sh"
"$PROJECT_ROOT/scripts/build-local-repo.sh"
"$PROJECT_ROOT/scripts/enable-services.sh"

mkdir -p "$OUT_DIR"
sudo mkarchiso -v -r -w "$WORK_DIR" -o "$OUT_DIR" "$PROJECT_ROOT/airootfs-profile"

echo "ISO built in $OUT_DIR"
