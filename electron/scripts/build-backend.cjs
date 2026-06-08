'use strict';

/**
 * 发布：PyInstaller 冻结 Python 后端 → packaging/dist/topdf-backend/
 * 需已安装: pip install -r requirements-build.txt
 */
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..', '..');
const spec = path.join(root, 'packaging', 'topdf-backend.spec');
const outDir = path.join(root, 'packaging', 'dist', 'topdf-backend');
const win = process.platform === 'win32';

const candidates = [];
if (process.env.TOPDF_PYTHON) {
  candidates.push([process.env.TOPDF_PYTHON, []]);
}
if (win) {
  candidates.push(['python', []], ['py', ['-3']]);
} else {
  candidates.push(['python3', []], ['python', []]);
}

function pickPython() {
  for (const [cmd, prefix] of candidates) {
    const r = spawnSync(cmd, [...prefix, '-c', 'print(1)'], { encoding: 'utf8', shell: false });
    if (!r.error && r.status === 0) return [cmd, prefix];
  }
  return null;
}

if (!fs.existsSync(spec)) {
  console.error('[build-backend] Missing spec:', spec);
  process.exit(1);
}

const pyPair = pickPython();
if (!pyPair) {
  console.error('[build-backend] 找不到可用的 Python，请先安装 Python 3.10+');
  process.exit(1);
}

console.log('[build-backend] PyInstaller 打包 Electron 后端…');
const env = { ...process.env, PYTHONUTF8: '1' };
const pyCmd = pyPair[0];
const pyArgs = [...pyPair[1], '-m', 'PyInstaller', '--noconfirm', '--clean', '--distpath', path.join(root, 'packaging', 'dist'), spec];
const spawnPrefix =
  process.platform === 'darwin' && process.env.PYINSTALLER_TARGET_ARCH === 'x86_64'
    ? ['arch', '-x86_64']
    : [];
const r = spawnSync(
  spawnPrefix.length ? spawnPrefix[0] : pyCmd,
  spawnPrefix.length ? [...spawnPrefix.slice(1), pyCmd, ...pyArgs] : pyArgs,
  { cwd: root, stdio: 'inherit', env, shell: false },
);

if (r.error || r.status !== 0) {
  console.error('[build-backend] PyInstaller failed');
  process.exit(r.status || 1);
}

const exe = path.join(outDir, win ? 'topdf-backend.exe' : 'topdf-backend');
if (!fs.existsSync(exe)) {
  console.error('[build-backend] Expected binary missing:', exe);
  process.exit(1);
}
console.log('[build-backend] OK →', outDir);
