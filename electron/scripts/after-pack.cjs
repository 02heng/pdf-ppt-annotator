'use strict';

/**
 * Windows 打包后把品牌 ICO 写入 exe（与 AI-writer 相同做法）。
 * 仅用 PNG 作 win.icon 时，任务栏仍可能显示 Electron 默认图标。
 */
const path = require('path');
const { rcedit } = require('rcedit');

exports.default = async function afterPack(context) {
  if (process.platform !== 'win32') return;

  const exeName = `${context.packager.appInfo.productFilename}.exe`;
  const exePath = path.join(context.appOutDir, exeName);
  const iconPath = path.resolve(__dirname, '..', 'assets', 'icon.ico');

  console.log('[after-pack] embedding icon →', exePath);
  await rcedit(exePath, { icon: iconPath });
  console.log('[after-pack] done');
};
