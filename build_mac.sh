#!/bin/bash
set -e

echo "======================================"
echo "    SYSTEMIC TAU - DMG BUILD SCRIPT   "
echo "======================================"

echo "1. Installing packaging dependencies..."
python3 -m pip install pyinstaller dmgbuild

echo "2. Building SystemicTau.app with PyInstaller..."
# We use --windowed to create a .app bundle (no terminal)
# We collect customtkinter and other tricky dependencies.
python3 -m PyInstaller --noconfirm \
    --name "SystemicTau" \
    --windowed \
    --collect-all customtkinter \
    --hidden-import "tkinterdnd2" \
    --hidden-import "scipy" \
    --hidden-import "numpy" \
    --hidden-import "pandas" \
    --hidden-import "google.genai" \
    --hidden-import "systemictau.core" \
    src/systemictau/desktop/app.py

echo "3. Cleaning up old DMG if it exists..."
rm -f dist/SystemicTau-Installer.dmg

echo "4. Creating DMG with dmgbuild..."
# Create a simple dmgbuild settings file on the fly
cat << 'EOF' > dmg_settings.py
format = 'UDBZ'
size = None
files = ['dist/SystemicTau.app']
symlinks = { 'Applications': '/Applications' }
badge_icon = None
icon_locations = {
    'SystemicTau.app': (140, 120),
    'Applications': (500, 120)
}
background = 'builtin-arrow'
show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False
window_rect = ((100, 100), (640, 280))
EOF

python3 -m dmgbuild -s dmg_settings.py "Systemic Tau Installation" dist/SystemicTau-Installer.dmg

echo "======================================"
echo " BUILD COMPLETE!"
echo " DMG is available at: dist/SystemicTau-Installer.dmg"
echo "======================================"
