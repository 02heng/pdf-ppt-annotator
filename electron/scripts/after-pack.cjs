'use strict';

/**
 * 打包后处理：
 * - Windows：rcedit 写入 exe 图标
 * - macOS：ad-hoc 签名内置 Python 后端，避免 Gatekeeper「已损坏」
 */
const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

function signMacBackend(context) {
  const product = context.packager.appInfo.productFilename;
  const appPath = path.join(context.appOutDir, `${product}.app`);
  const backendDir = path.join(appPath, 'Contents', 'Resources', 'backend-bin');
  if (!fs.existsSync(backendDir)) {
    console.warn('[after-pack] backend-bin not found:', backendDir);
    return;
  }
  console.log('[after-pack] ad-hoc signing embedded backend →', backendDir);
  execSync(
    `find "${backendDir}" -type f \\( -perm +111 -o -name '*.dylib' -o -name '*.so' \\) -print0 | while IFS= read -r -d '' f; do codesign --force --sign - "$f" 2>/dev/null || true; done`,
    { shell: '/bin/bash', stdio: 'inherit' },
  );
}

exports.default = async function afterPack(context) {
  if (process.platform === 'win32') {
    const { rcedit } = require('rcedit');
    const exeName = `${context.packager.appInfo.productFilename}.exe`;
    const exePath = path.join(context.appOutDir, exeName);
    const iconPath = path.resolve(__dirname, '..', 'assets', 'icon.ico');
    console.log('[after-pack] embedding icon →', exePath);
    await rcedit(exePath, { icon: iconPath });
    console.log('[after-pack] done');
    return;
  }

  if (process.platform === 'darwin') {
    signMacBackend(context);
  }
};
