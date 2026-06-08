#!/usr/bin/env bash
# macOS Electron 安装包（arm64 或 x86_64），需在 Mac 上运行
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ARCH="${1:-$(uname -m)}"
case "$ARCH" in
  arm64|aarch64) EB_ARCH="arm64" ;;
  x86_64|amd64) EB_ARCH="x64"; export PYINSTALLER_TARGET_ARCH=x86_64 ;;
  *) echo "Unsupported arch: $ARCH (use arm64 or x86_64)" >&2; exit 1 ;;
esac

APP_VERSION="$(tr -d '\r\n' < VERSION)"
APP_VERSION="${APP_VERSION:-0.2.0}"

echo "==> 项目目录: $ROOT"
echo "==> 版本: v$APP_VERSION"
echo "==> 目标架构: $EB_ARCH"

export CSC_IDENTITY_AUTO_DISCOVERY=false

echo "==> 安装 Python 打包依赖..."
grep -v '^crewai\|^-r' requirements.txt > /tmp/requirements-mac.txt
echo "pyinstaller>=6.3.0" >> /tmp/requirements-mac.txt
if [[ "$EB_ARCH" == "x64" ]]; then
  PY="/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
  export TOPDF_PYTHON="$PY"
  arch -x86_64 "$PY" -m pip install -r /tmp/requirements-mac.txt -q
else
  python3 -m pip install -r /tmp/requirements-mac.txt -q
fi

echo "==> 生成应用图标..."
if [[ "$EB_ARCH" == "x64" ]]; then
  arch -x86_64 "$PY" scripts/generate_app_icons.py
else
  python3 scripts/generate_app_icons.py
fi

echo "==> 构建 Electron DMG..."
pushd electron >/dev/null
npm install
npm run prepare-vendor
npm run build-backend
npx electron-builder --mac dmg "--$EB_ARCH" --publish never
popd >/dev/null

OUT="packaging/output/TOPDFAnnotator-${APP_VERSION}-mac-${EB_ARCH}.dmg"
DMG="$(find packaging/output -maxdepth 1 -name '*.dmg' -type f | head -1)"
if [[ -z "$DMG" ]]; then
  echo "构建失败：未找到 DMG" >&2
  exit 1
fi
cp "$DMG" "$OUT"
echo "==> 安装包: $OUT"
