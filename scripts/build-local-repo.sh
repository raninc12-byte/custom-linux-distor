#!/usr/bin/env bash
# Builds the ai-assistant pacman package and drops it into a local repo that
# the archiso build's pacman.conf points to (see airootfs-profile/pacman.conf).
set -euo pipefail

REPO_DIR="/tmp/aibase-local-repo"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$REPO_DIR"

pushd "$PROJECT_ROOT/ai-assistant/packaging" >/dev/null
makepkg -si --noconfirm --needed
cp -f ./*.pkg.tar.zst "$REPO_DIR/"
popd >/dev/null

repo-add "$REPO_DIR/aibase-local.db.tar.gz" "$REPO_DIR"/*.pkg.tar.zst

echo "Local repo ready at $REPO_DIR"
