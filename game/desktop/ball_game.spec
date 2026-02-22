# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for BallGame macOS app bundle.
Usage: pyinstaller ball_game.spec
"""

import shutil
import subprocess

from PyInstaller.utils.hooks import collect_all, collect_submodules

# --- libintl (gettext) を明示的にバンドル ---
# libpython が @rpath/libintl.8.dylib を要求するが PyInstaller が自動収集しない
def _find_libintl():
    """Homebrew の libintl.8.dylib パスを返す"""
    candidates = [
        '/opt/homebrew/lib/libintl.8.dylib',       # Apple Silicon
        '/usr/local/lib/libintl.8.dylib',           # Intel
    ]
    for p in candidates:
        import os
        if os.path.exists(p):
            return p
    # brew --prefix で探す
    try:
        prefix = subprocess.check_output(
            ['brew', '--prefix', 'gettext'], text=True
        ).strip()
        p = os.path.join(prefix, 'lib', 'libintl.8.dylib')
        if os.path.exists(p):
            return p
    except Exception:
        pass
    return None

_libintl_path = _find_libintl()
_extra_binaries = [(_libintl_path, '.')] if _libintl_path else []

# --- 依存パッケージの収集 ---
panda3d_datas, panda3d_binaries, panda3d_hiddenimports = collect_all('panda3d')
ursina_datas, ursina_binaries, ursina_hiddenimports = collect_all('ursina')
pymunk_datas, pymunk_binaries, pymunk_hiddenimports = collect_all('pymunk')

# direct3d_tools は macOS では不要だが collect_all で拾われるので除外しない
# (PyInstaller が自動的に不要プラットフォームのものをスキップする)

all_datas = panda3d_datas + ursina_datas + pymunk_datas + [
    ('assets', 'assets'),
    ('stages', 'stages'),
]

# panda3d.rocket は x86_64 のみで arm64 非対応 → 除外
panda3d_binaries = [b for b in panda3d_binaries if 'rocket' not in b[0]]

all_binaries = panda3d_binaries + ursina_binaries + pymunk_binaries + _extra_binaries

all_hiddenimports = (
    panda3d_hiddenimports
    + ursina_hiddenimports
    + pymunk_hiddenimports
    + collect_submodules('panda3d')
    + [
        'websockets',
        'zoneinfo',
    ]
)

# --- 除外モジュール ---
excludes = [
    'tkinter',
    'matplotlib',
    'scipy',
    'numpy.testing',
    'pytest',
    'IPython',
    'notebook',
    'PIL.ImageTk',
    'panda3d.rocket',
]

a = Analysis(
    ['ball_game.py'],
    pathex=[],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=all_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ball_game',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # macOS の dylib 破損防止
    console=False,        # ターミナル非表示
    target_arch=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='ball_game',
)

app = BUNDLE(
    coll,
    name='BallGame.app',
    icon='assets/icon.icns',
    bundle_identifier='com.watnow.ballgame',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleName': 'BallGame',
        'NSHighResolutionCapable': True,
    },
)
