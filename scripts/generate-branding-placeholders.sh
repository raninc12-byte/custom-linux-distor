#!/usr/bin/env bash
# Generates simple placeholder branding artwork (solid color + text) using
# ImageMagick, so Calamares/the desktop don't show broken image icons before
# real artwork is designed. Safe to re-run - skips files that already exist
# unless FORCE=1 is set.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRANDING_DIR="$PROJECT_ROOT/calamares-config/branding"
ICON_DIR="$PROJECT_ROOT/ai-assistant/packaging/icons"
PLYMOUTH_DIR="$PROJECT_ROOT/airootfs-profile/airootfs/usr/share/plymouth/themes/aibase"

if ! command -v convert >/dev/null 2>&1; then
    echo "ImageMagick 'convert' not found - install imagemagick to generate placeholders" >&2
    exit 1
fi

mkdir -p "$BRANDING_DIR" "$ICON_DIR" "$PLYMOUTH_DIR"

make_placeholder() {
    local path="$1" size="$2" bg="$3" label="$4"
    if [[ -f "$path" && "${FORCE:-0}" != "1" ]]; then
        echo "skip (exists): $path"
        return
    fi
    convert -size "$size" "xc:$bg" \
        -gravity center -fill white -pointsize 28 -font DejaVu-Sans-Bold \
        -annotate 0 "$label" \
        "$path"
    echo "generated: $path"
}

make_placeholder "$BRANDING_DIR/logo.png" 256x256 "#17151f" "AI-Base\nLinux"
make_placeholder "$BRANDING_DIR/welcome.png" 800x500 "#1d1b28" "AI-Base Linux\nLocal AI, built in."
make_placeholder "$ICON_DIR/aibase-assistant.png" 128x128 "#3daee9" "AI"
make_placeholder "$PLYMOUTH_DIR/logo.png" 256x256 "#17151f" "AI-Base\nLinux"

echo "Placeholder branding generated. Replace with real artwork before a public release."
