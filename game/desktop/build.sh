#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# desktop/venv を有効化 (ursina, panda3d, pymunk が入っている環境)
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    echo "=== Activating desktop venv ==="
    source "$SCRIPT_DIR/venv/bin/activate"
fi

echo "=== Installing PyInstaller ==="
pip install pyinstaller

echo "=== Building BallGame.app ==="
pyinstaller ball_game.spec --noconfirm

# --- libintl.8.dylib を手動バンドル ---
# libpython3.11.dylib が @rpath/libintl.8.dylib を要求するが
# PyInstaller が自動収集しないため手動でコピーする
INTERNAL_DIR="$SCRIPT_DIR/dist/ball_game/_internal"
LIBINTL=""

# Homebrew の libintl を探す
for candidate in /opt/homebrew/lib/libintl.8.dylib /usr/local/lib/libintl.8.dylib; do
    if [ -f "$candidate" ]; then
        LIBINTL="$candidate"
        break
    fi
done

# brew --prefix で探す (フォールバック)
if [ -z "$LIBINTL" ] && command -v brew &>/dev/null; then
    GETTEXT_PREFIX="$(brew --prefix gettext 2>/dev/null || true)"
    if [ -n "$GETTEXT_PREFIX" ] && [ -f "$GETTEXT_PREFIX/lib/libintl.8.dylib" ]; then
        LIBINTL="$GETTEXT_PREFIX/lib/libintl.8.dylib"
    fi
fi

if [ -n "$LIBINTL" ]; then
    echo "=== Bundling libintl.8.dylib from $LIBINTL ==="
    cp "$LIBINTL" "$INTERNAL_DIR/libintl.8.dylib"
    chmod 755 "$INTERNAL_DIR/libintl.8.dylib"

    # libpython の @rpath を _internal 自身に向ける
    LIBPYTHON="$INTERNAL_DIR/libpython3.11.dylib"
    if [ -f "$LIBPYTHON" ]; then
        # 既存の @rpath に _internal が含まれていなければ追加
        install_name_tool -add_rpath @loader_path "$LIBPYTHON" 2>/dev/null || true
    fi

    # .app バンドル側にも同じ処理 (Frameworks/ に配置される)
    APP_FW="$SCRIPT_DIR/dist/BallGame.app/Contents/Frameworks"
    if [ -d "$APP_FW" ]; then
        cp "$LIBINTL" "$APP_FW/libintl.8.dylib"
        chmod 755 "$APP_FW/libintl.8.dylib"
        APP_LIBPYTHON="$APP_FW/libpython3.11.dylib"
        if [ -f "$APP_LIBPYTHON" ]; then
            install_name_tool -add_rpath @loader_path "$APP_LIBPYTHON" 2>/dev/null || true
        fi
    fi
else
    echo "WARNING: libintl.8.dylib not found. App may fail to launch."
    echo "Install gettext: brew install gettext"
fi

echo ""
echo "=== Build complete ==="
echo "Output: $SCRIPT_DIR/dist/BallGame.app"
echo "Run:    open dist/BallGame.app"
