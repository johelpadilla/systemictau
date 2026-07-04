#!/bin/bash
set -euo pipefail

echo "========================================"
echo "   SYSTEMIC TAU - macOS DMG BUILDER    "
echo "========================================"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Detect architecture early
ARCH=$(uname -m)
echo "Building on architecture: $ARCH"
if [ "$ARCH" = "arm64" ]; then
    echo "⚠️  This will produce an Apple Silicon (arm64) binary."
    echo "   It will NOT run on Intel Macs (x86_64)."
    echo "   If your target Mac is Intel, build on that machine or use a x86_64 Python."
elif [ "$ARCH" = "x86_64" ]; then
    echo "✓ Building for Intel (x86_64)."
else
    echo "Unknown arch: $ARCH"
fi

# Prefer venv
if [ -x ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
    echo "✓ Using venv: $PYTHON"
else
    echo "⚠️  .venv not found. Creating with uv..."
    if command -v uv >/dev/null 2>&1; then
        uv venv --python 3.12 .venv
        PYTHON=".venv/bin/python"
    else
        PYTHON="python3"
        echo "⚠️  Falling back to system python3"
    fi
fi

# Install build tools robustly
echo "1. Installing build tools..."
if command -v uv >/dev/null 2>&1; then
    uv pip install --python "$PYTHON" pyinstaller dmgbuild --quiet 2>/dev/null || \
    "$PYTHON" -m pip install pyinstaller dmgbuild --quiet
else
    "$PYTHON" -m pip install pyinstaller dmgbuild --quiet
fi

# For Studio builds we also need the runtime packages + pywebview in the build env
# (so PyInstaller can discover and bundle them correctly).
MODE_CHECK="${1:-desktop}"
if [[ "$MODE_CHECK" == "--studio" || "$MODE_CHECK" == "studio" ]]; then
    echo "   Installing Studio + pywebview runtime packages (robust build)..."
    if command -v uv >/dev/null 2>&1; then
        uv pip install --python "$PYTHON" pywebview streamlit matplotlib pandas openpyxl scipy --quiet 2>/dev/null || \
        "$PYTHON" -m pip install pywebview streamlit matplotlib pandas openpyxl scipy --quiet
    else
        "$PYTHON" -m pip install pywebview streamlit matplotlib pandas openpyxl scipy --quiet
    fi
fi

# Ensure icon
ICON="icons/SystemicTau.icns"
if [ ! -f "$ICON" ]; then
    echo "2. Creating placeholder icon..."
    mkdir -p icons build/icons.iconset
    if [ -f "dev_dual_final_global.png" ]; then
        sips -z 1024 1024 dev_dual_final_global.png --out build/icons.iconset/icon_512x512@2x.png >/dev/null 2>&1 || true
        iconutil -c icns build/icons.iconset -o "$ICON" 2>/dev/null || cp build/icons.iconset/icon_512x512@2x.png icons/SystemicTau.png || true
    fi
fi

if [ ! -f "$ICON" ]; then
    ICON=""
    echo "   (no custom icon)"
fi

# Clean
echo "3. Cleaning..."
rm -rf build/SystemicTau* dist/SystemicTau* dist/*Installer.dmg 2>/dev/null || true

MODE="${1:-desktop}"

if [[ "$MODE" == "--studio" || "$MODE" == "studio" ]]; then
    echo "4. Building Studio app..."
    "$PYTHON" -m PyInstaller --noconfirm --clean SystemicTauStudio.spec

    echo "5. Building Studio DMG..."
    cat > /tmp/dmg_studio.py << EOF
format = 'UDBZ'
files = ['dist/SystemicTauStudio.app']
symlinks = {'Applications': '/Applications'}
icon_locations = {'SystemicTauStudio.app': (140, 120), 'Applications': (500, 120)}
background = 'builtin-arrow'
window_rect = ((100, 100), (640, 280))
EOF
    "$PYTHON" -m dmgbuild -s /tmp/dmg_studio.py "Systemic Tau Studio" dist/SystemicTauStudio-Installer.dmg

    echo "✅ Done: dist/SystemicTauStudio-Installer.dmg"
else
    echo "4. Building Desktop app..."
    "$PYTHON" -m PyInstaller --noconfirm --clean SystemicTau.spec

    echo "5. Building Desktop DMG..."
    if [ -n "$ICON" ]; then
        cat > /tmp/dmg_desktop.py << EOF
format = 'UDBZ'
files = ['dist/SystemicTau.app']
symlinks = {'Applications': '/Applications'}
icon_locations = {'SystemicTau.app': (140, 120), 'Applications': (500, 120)}
background = 'builtin-arrow'
window_rect = ((100, 100), (640, 280))
EOF
        "$PYTHON" -m dmgbuild -s /tmp/dmg_desktop.py "Systemic Tau" dist/SystemicTau-Installer.dmg
    else
        "$PYTHON" -m dmgbuild -s dmg_settings.py "Systemic Tau" dist/SystemicTau-Installer.dmg
    fi

    echo "✅ Done: dist/SystemicTau-Installer.dmg"
fi

ls -lh dist/*Installer.dmg 2>/dev/null || true
echo "========================================"