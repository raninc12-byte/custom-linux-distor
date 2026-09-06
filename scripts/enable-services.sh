#!/usr/bin/env bash
# Run once before mkarchiso, on the Arch Linux build host, to create the
# systemd enable symlinks. Kept as a script (not committed symlinks) because
# git-on-Windows checkouts can't reliably store real symlinks.
set -euo pipefail

PROFILE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../airootfs-profile" && pwd)"
AIROOTFS="$PROFILE_DIR/airootfs"

enable() {
    local unit="$1" target="$2"
    mkdir -p "$AIROOTFS/etc/systemd/system/${target}.wants"
    ln -sf "/usr/lib/systemd/system/${unit}" \
        "$AIROOTFS/etc/systemd/system/${target}.wants/${unit}"
}

enable_local() {
    local unit="$1" target="$2"
    mkdir -p "$AIROOTFS/etc/systemd/system/${target}.wants"
    ln -sf "/etc/systemd/system/${unit}" \
        "$AIROOTFS/etc/systemd/system/${target}.wants/${unit}"
}

# Core services for the live/installed system.
enable NetworkManager.service multi-user.target
enable lightdm.service graphical.target

# Our own first-boot units (files live directly under etc/systemd/system/).
enable_local aibase-plymouth-setup.service multi-user.target
enable_local aibase-gpu-detect.service multi-user.target
enable_local aibase-first-boot-setup.service multi-user.target

echo "Service symlinks created under $AIROOTFS/etc/systemd/system/"
