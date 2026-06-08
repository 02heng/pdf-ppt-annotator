'use strict';

/** 将 pdf.js 复制到 electron/vendor，打包后主窗口预览可用 */
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..', '..');
const srcWeb = path.join(root, 'src', 'web');
const vendorDir = path.join(__dirname, '..', 'vendor', 'pdfjs');

const files = ['pdf.min.js', 'pdf.worker.min.js'];

fs.mkdirSync(vendorDir, { recursive: true });
for (const name of files) {
  const src = path.join(srcWeb, name);
  const dest = path.join(vendorDir, name);
  if (!fs.existsSync(src)) {
    console.error('[prepare-vendor] missing', src);
    process.exit(1);
  }
  fs.copyFileSync(src, dest);
  console.log('[prepare-vendor] OK →', dest);
}
