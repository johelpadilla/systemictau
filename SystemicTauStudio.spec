# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = []
binaries = []
hiddenimports = []

# Collect everything needed for streamlit + studio
for pkg in [
    'streamlit', 'tornado', 'pandas', 'numpy', 'matplotlib', 'click', 'pillow',
    'altair', 'pyarrow', 'pywebview', 'openpyxl', 'fpdf2', 'reportlab',
    'scipy', 'systemictau'   # ensure our package is fully collected
]:
    try:
        tmp_ret = collect_all(pkg)
        datas += tmp_ret[0]
        binaries += tmp_ret[1]
        hiddenimports += tmp_ret[2]
    except Exception:
        pass

hiddenimports += collect_submodules('streamlit')
hiddenimports += collect_submodules('scipy')
hiddenimports += ['streamlit', 'streamlit.web.cli', 'streamlit.runtime.scriptrunner', 'streamlit.web.server']
hiddenimports += ['systemictau.studio', 'systemictau.studio.app', 'systemictau.studio.analysis', 'systemictau.studio.viz']
hiddenimports += ['systemictau.exporter', 'systemictau.sensitivity']
# Extra for common silent failures
hiddenimports += ['pkg_resources', 'importlib.metadata', 'watchdog.observers', 'watchdog.events']

# pywebview (native window on macOS via WebKit / pyobjc)
hiddenimports += [
    'webview',
    'webview.platforms.cocoa',
    'webview.platforms',
    'webview.util',
    'objc',
    'PyObjCTools',
    'AppKit',
]
try:
    hiddenimports += collect_submodules('webview')
except Exception:
    pass

# Explicitly ensure DejaVu (and other matplotlib) fonts are bundled so font cache
# never depends on scanning the host system fonts inside the .app sandbox.
# This makes first-run + fontManager behavior consistent and fast.
try:
    import os as _os
    import matplotlib as _mpl
    _mpl_fonts = _os.path.join(_os.path.dirname(_mpl.__file__), 'mpl-data', 'fonts')
    if _os.path.isdir(_mpl_fonts):
        datas.append((_mpl_fonts, 'matplotlib/mpl-data/fonts'))
        print("Bundling matplotlib fonts from:", _mpl_fonts)
except Exception as _e:
    print("Note: could not add explicit matplotlib fonts:", _e)

# Include the studio code and launcher
a = Analysis(
    ['studio_launcher.py'],
    pathex=['src'],
    binaries=binaries,
    datas=datas + [
        ('src/systemictau/studio', 'systemictau/studio'),
        ('src/systemictau', 'systemictau'),
        ('.streamlit', '.streamlit'),  # config.toml (watcher disabled)
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SystemicTauStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,  # will match the architecture of the Python used to run PyInstaller (set in build script)
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SystemicTauStudio',
)
app = BUNDLE(
    coll,
    name='SystemicTauStudio.app',
    icon='icons/SystemicTau.icns',
    bundle_identifier='com.systemictau.studio',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleDisplayName': 'Systemic Tau Studio',
        'CFBundleName': 'SystemicTauStudio',
        'CFBundleVersion': '1.0',
        'CFBundleShortVersionString': '1.0',
        'LSMinimumSystemVersion': '11.0',
        'NSQuitAlwaysKeepsWindows': False,
        'ApplePersistenceIgnoreState': True,
    },
)