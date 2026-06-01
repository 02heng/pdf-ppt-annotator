#!/usr/bin/env bash
# macOS 打包脚本（需在 Mac 上运行，无法跨平台编译）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> 项目目录: $ROOT"

echo "==> 安装打包依赖..."
python3 -m pip install -r requirements-build.txt -q

echo "==> PyInstaller 构建 .app ..."
python3 -m PyInstaller --noconfirm --clean packaging/TOPDFAnnotator.spec

APP_PATH="dist/TOPDFAnnotator.app"
if [[ ! -d "$APP_PATH" ]]; then
  echo "构建失败：未找到 $APP_PATH" >&2
  exit 1
fi

echo "==> 应用包: $APP_PATH"

OUTPUT_DIR="packaging/output"
mkdir -p "$OUTPUT_DIR"
DMG_NAME="TOPDFAnnotator-1.0.0-mac.dmg"
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
