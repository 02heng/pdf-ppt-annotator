#!/usr/bin/env bash
# macOS 打包脚本（需在 Mac 上运行，无法跨平台编译）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

APP_VERSION="$(tr -d '\r\n' < VERSION)"
APP_VERSION="${APP_VERSION:-0.1.0}"

echo "==> 项目目录: $ROOT"
echo "==> 版本: v$APP_VERSION"

echo "==> 生成应用图标..."
python3 scripts/generate_app_icons.py

echo "==> 安装打包依赖..."
python3 -m pip install -r requirements-build.txt -q

ARCH="$(uname -m)"
echo "==> PyInstaller 构建 macOS ${ARCH} 版本 ..."
python3 -m PyInstaller --noconfirm --clean packaging/TOPDFAnnotator.spec

APP_PATH="dist/TOPDFAnnotator.app"
if [[ ! -d "$APP_PATH" ]]; then
  echo "构建失败：未找到 $APP_PATH" >&2
  exit 1
fi

# 验证架构
EXE_PATH="$APP_PATH/Contents/MacOS/TOPDFAnnotator"
if [[ -f "$EXE_PATH" ]]; then
  echo "==> 应用架构:"
  file "$EXE_PATH"
  lipo -info "$EXE_PATH" 2>/dev/null || echo "(lipo 不可用，跳过验证)"
fi

echo "==> 应用包: $APP_PATH"

OUTPUT_DIR="packaging/output"
mkdir -p "$OUTPUT_DIR"
DMG_NAME="TOPDFAnnotator-${APP_VERSION}-mac.dmg"
DMG_PATH="$OUTPUT_DIR/$DMG_NAME"

if command -v hdiutil >/dev/null 2>&1; then
  STAGING="$OUTPUT_DIR/dmg-staging"
  rm -rf "$STAGING"
  mkdir -p "$STAGING"
  cp -R "$APP_PATH" "$STAGING/"
  ln -sf /Applications "$STAGING/Applications"

  rm -f "$DMG_PATH"
  hdiutil create -volname "TO PDF 批注工具" -srcfolder "$STAGING" -ov -format UDZO "$DMG_PATH"
  rm -rf "$STAGING"
  echo "==> DMG 安装镜像: $DMG_PATH"
else
  echo "未找到 hdiutil，仅生成 .app，请手动压缩分发"
fi

echo ""
echo "完成。用户将 .app 拖入「应用程序」即可，无需安装 Python。"
