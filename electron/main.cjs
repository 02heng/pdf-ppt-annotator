const { app, BrowserWindow, shell, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn, spawnSync } = require('child_process');
const http = require('http');
const os = require('os');

// #region agent log
/** @param {string} hypothesisId H1=PATH/py missing H2=cmd fallback H3=scan misses D/custom H4=exe rejects --version H5=parse */
function dbgLog(location, message, data, hypothesisId) {
  const row = {
    sessionId: '374c21',
    timestamp: Date.now(),
    location,
    message,
    data: data || {},
    hypothesisId: hypothesisId || 'H0',
  };
  const body = JSON.stringify(row);
  fetch('http://127.0.0.1:7858/ingest/bb32bb00-ef93-4ab3-ac30-fccdd1a96431', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': '374c21' },
    body,
  }).catch(() => {});
  try {
    fs.appendFileSync(path.join(__dirname, '..', 'debug-374c21.log'), `${body}\n`, 'utf8');
  } catch (_) {}
  try {
    fs.appendFileSync(path.join(os.tmpdir(), 'slide-annotate-debug-374c21.log'), `${body}\n`, 'utf8');
  } catch (_) {}
}
// #endregion

const API_PORT = process.env.SLIDE_ANNOTATE_PORT || '8765';
process.env.SLIDE_ANNOTATE_PORT = String(API_PORT);
const API_HOST = '127.0.0.1';

let mainWindow = null;
let pythonProcess = null;

function serverRoot() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'server');
  }
  return path.join(__dirname, '..', 'server');
}

/** 图形界面进程在 Windows 上常缺少用户 PATH；补全常见 Python 安装目录 */
function widenedPathEnv() {
  const env = { ...process.env };
  if (process.platform !== 'win32') {
    return env;
  }
  const extras = [];
  const win = env.SystemRoot || 'C:\\Windows';
  extras.push(path.join(win), path.join(win, 'System32'));
  const la = env.LOCALAPPDATA;
  if (la) {
    const base = path.join(la, 'Programs', 'Python');
    try {
      const dirs = fs
        .readdirSync(base, { withFileTypes: true })
        .filter((d) => d.isDirectory() && /^Python\d+$/i.test(d.name))
        .map((d) => path.join(base, d.name));
      for (const d of dirs) {
        extras.push(path.join(d, 'Scripts'), d);
      }
    } catch {
      /* ignore */
    }
  }
  env.PATH = [...extras, env.PATH || ''].filter(Boolean).join(path.delimiter);
  return env;
}

/** Windows：直接找 python.exe，避免 PATH 里没有 python/py 时出现 ENOENT */
function listWindowsPythonExes() {
  const out = [];
  const push = (p) => {
    if (p && fs.existsSync(p)) {
      out.push(p);
    }
  };
  const la = process.env.LOCALAPPDATA;
  if (la) {
    const root = path.join(la, 'Programs', 'Python');
    try {
      for (const name of fs.readdirSync(root)) {
        push(path.join(root, name, 'python.exe'));
      }
    } catch {
      /* ignore */
    }
  }
  const pf = process.env.ProgramFiles;
  if (pf) {
    for (const v of ['Python312', 'Python311', 'Python310', 'Python39']) {
      push(path.join(pf, v, 'python.exe'));
    }
  }
  const pf86 = process.env['ProgramFiles(x86)'];
  if (pf86) {
    for (const v of ['Python312', 'Python311', 'Python310']) {
      push(path.join(pf86, v, 'python.exe'));
    }
  }
  const home = process.env.USERPROFILE || process.env.HOME;
  if (home) {
    push(path.join(home, 'anaconda3', 'python.exe'));
    push(path.join(home, 'miniconda3', 'python.exe'));
    push(path.join(home, 'mambaforge', 'python.exe'));
  }
  try {
    const devTools = path.join('D:', 'DevTools');
    if (fs.existsSync(devTools)) {
      for (const name of fs.readdirSync(devTools)) {
        push(path.join(devTools, name, 'python.exe'));
      }
    }
  } catch {
    /* ignore */
  }
  return [...new Set(out)];
}

/** Python.org 安装器写入注册表：InstallPath 默认值为安装目录。 */
function getWindowsPythonFromRegistry() {
  const exes = [];
  const versions = ['3.14', '3.13', '3.12', '3.11', '3.10', '3.9'];
  const hives = ['HKCU', 'HKLM'];
  for (const hive of hives) {
    for (const ver of versions) {
      const regKey = `${hive}\\Software\\Python\\PythonCore\\${ver}\\InstallPath`;
      const r = spawnSync('reg', ['query', regKey, '/ve'], {
        encoding: 'utf-8',
        windowsHide: true,
      });
      if (r.error || r.status !== 0) {
        continue;
      }
      const line = String(r.stdout || '')
        .split(/\r?\n/)
        .find((l) => l.includes('REG_SZ'));
      if (!line) {
        continue;
      }
      const i = line.indexOf('REG_SZ');
      let dir = line.slice(i + 6).trim().replace(/^"+|"+$/g, '');
      if (!dir) {
        continue;
      }
      const exe = path.join(dir, 'python.exe');
      if (fs.existsSync(exe)) {
        exes.push(exe);
      }
    }
  }
  return [...new Set(exes)];
}

/**
 * 通过 cmd.exe 调用 py / where：与「用户双击启动」的 Electron 相比，能拿到更接近终端的 PATH。
 * @returns {string|null} python.exe 绝对路径
 */
function resolvePythonViaWindowsCmd(env) {
  const comspec = env.ComSpec || path.join(env.SystemRoot || 'C:\\Windows', 'System32', 'cmd.exe');
  const run = (script) => {
    const r = spawnSync(comspec, ['/d', '/s', '/c', script], {
      env,
      encoding: 'utf-8',
      windowsHide: true,
    });
    // #region agent log
    dbgLog(
      'resolvePythonViaCmd:run',
      script.slice(0, 100),
      {
        status: r.status,
        errCode: r.error ? r.error.code : undefined,
        outFirst: String(r.stdout || '')
          .split(/\r?\n/)[0]
          ?.slice(0, 220),
        errTail: String(r.stderr || '').slice(-320),
      },
      'H2'
    );
    // #endregion
    if (r.error || r.status !== 0 || !r.stdout) {
      return '';
    }
    return String(r.stdout).trim();
  };

  const firstLine = (s) => (s ? s.split(/\r?\n/)[0].trim() : '');

  let exe = firstLine(run('py -3 -c "import sys; print(sys.executable)"'));
  if (exe && fs.existsSync(exe)) {
    return exe;
  }
  exe = firstLine(run('py -c "import sys; print(sys.executable)"'));
  if (exe && fs.existsSync(exe)) {
    return exe;
  }
  const whereOut = run('where python');
  if (whereOut) {
    const lines = whereOut.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    for (const line of lines) {
      if (line.toLowerCase().endsWith('.exe') && fs.existsSync(line)) {
        return line;
      }
    }
  }
  return null;
}

function resolvePythonLauncher() {
  const env = widenedPathEnv();
  const tries = [];

  const slidePy = (process.env.SLIDE_ANNOTATE_PYTHON || '').trim();
  if (slidePy) {
    tries.push([slidePy, []]);
  }
  if (process.env.PYTHON) {
    tries.push([process.env.PYTHON, []]);
  }

  const discovered = process.platform === 'win32' ? listWindowsPythonExes() : [];
  // #region agent log
  dbgLog(
    'resolvePythonLauncher:enter',
    'start',
    {
      platform: process.platform,
      hasSLIDE_ANNOTATE_PYTHON: Boolean(slidePy),
      hasPYTHON: Boolean(process.env.PYTHON),
      pathHead: (env.PATH || '').slice(0, 200),
      discoveredN: discovered.length,
      discoveredSample: discovered.slice(0, 4).map((p) => p.slice(-60)),
    },
    'H1'
  );
  // #endregion

  if (process.platform === 'win32') {
    const regExes = getWindowsPythonFromRegistry();
    // #region agent log
    dbgLog(
      'resolvePythonLauncher:registry',
      'registry exes',
      { n: regExes.length, sample: regExes.slice(0, 2).map((e) => e.slice(-55)) },
      'H1'
    );
    // #endregion
    for (const exe of regExes) {
      tries.push([exe, []]);
    }
    for (const exe of discovered) {
      tries.push([exe, []]);
    }
    tries.push(['py', ['-3']], ['py', []], ['python', []], ['python3', []]);
  } else {
    tries.push(['python3', []], ['python', []]);
  }

  for (const [command, prefix] of tries) {
    if (!command) {
      continue;
    }
    const r = spawnSync(command, [...prefix, '--version'], {
      env,
      encoding: 'utf-8',
      windowsHide: true,
    });
    // #region agent log
    dbgLog(
      'resolvePythonLauncher:try',
      String(command).slice(-80),
      {
        prefix,
        status: r.status,
        errCode: r.error ? r.error.code : undefined,
        verrTail: String(r.stderr || '').slice(-180),
      },
      'H4'
    );
    // #endregion
    if (!r.error && r.status === 0) {
      // #region agent log
      dbgLog('resolvePythonLauncher:pick', 'spawnSync ok', { picked: String(command).slice(-100), prefix }, 'H5');
      // #endregion
      return { command, prefix, env };
    }
  }

  if (process.platform === 'win32') {
    const exeFromCmd = resolvePythonViaWindowsCmd(env);
    if (exeFromCmd) {
      const r = spawnSync(exeFromCmd, ['--version'], {
        env,
        encoding: 'utf-8',
        windowsHide: true,
      });
      // #region agent log
      dbgLog(
        'resolvePythonLauncher:cmdExe',
        String(exeFromCmd).slice(-100),
        {
          status: r.status,
          errCode: r.error ? r.error.code : undefined,
        },
        'H2'
      );
      // #endregion
      if (!r.error && r.status === 0) {
        // #region agent log
        dbgLog('resolvePythonLauncher:pick', 'from cmd path', { picked: String(exeFromCmd).slice(-100) }, 'H5');
        // #endregion
        return { command: exeFromCmd, prefix: [], env };
      }
    }
  }

  // #region agent log
  dbgLog('resolvePythonLauncher:fail', 'all tries failed', {}, 'H3');
  // #endregion
  return { command: null, prefix: [], env };
}

function waitForHealth(timeoutMs = 45000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const tryOnce = () => {
      const req = http.request(
        {
          hostname: API_HOST,
          port: API_PORT,
          path: '/api/health',
          method: 'GET',
          timeout: 2000,
        },
        (res) => {
          if (res.statusCode === 200) {
            resolve(true);
          } else {
            scheduleRetry();
          }
        }
      );
      req.on('error', () => scheduleRetry());
      req.on('timeout', () => {
        req.destroy();
        scheduleRetry();
      });
      req.end();
    };

    const scheduleRetry = () => {
      if (Date.now() - start > timeoutMs) {
        reject(
          new Error(
            'Python 服务未在预期时间内启动。请在终端执行: cd server && python -m uvicorn app:app --host 127.0.0.1 --port 8765 查看报错；并确认已 pip install -r server/requirements.txt'
          )
        );
        return;
      }
      setTimeout(tryOnce, 400);
    };

    tryOnce();
  });
}

function startPythonServer() {
  const root = serverRoot();
  if (!fs.existsSync(path.join(root, 'app.py'))) {
    console.error('未找到 server 目录或 app.py:', root);
    return;
  }

  const { command, prefix, env } = resolvePythonLauncher();
  const args = [...prefix, '-m', 'uvicorn', 'app:app', '--host', API_HOST, '--port', String(API_PORT)];

  const childEnv = {
    ...env,
    SLIDE_ANNOTATE_PORT: String(API_PORT),
  };

  /** @param {import('child_process').ChildProcess} proc @param {string} label */
  function attachPythonProc(proc, label) {
    // #region agent log
    dbgLog('startPythonServer:spawn', 'spawn ok', { label, argsHead: args.slice(0, 4) }, 'H1');
    // #endregion
    pythonProcess = proc;
    const logLine = (buf, stream) => {
      const s = buf.toString().trim();
      if (s) {
        console.log(`[uvicorn ${stream}]`, s);
      }
    };
    proc.stdout?.on('data', (d) => logLine(d, 'out'));
    proc.stderr?.on('data', (d) => logLine(d, 'err'));

    proc.on('error', (err) => {
      console.error('无法启动 Python:', err);
      // #region agent log
      dbgLog('startPythonServer:spawnError', err.message || String(err), { code: err.code, label }, 'H1');
      // #endregion
      if (mainWindow && !mainWindow.isDestroyed()) {
        dialog.showErrorBox(
          '无法启动 Python',
          `${label}\n\n${err.message}\n\n可设置 SLIDE_ANNOTATE_PYTHON 为 python.exe 全路径。`
        );
      }
    });

    proc.on('exit', (code) => {
      if (code && code !== 0 && !app.isQuitting) {
        console.error('Python 进程退出，代码:', code);
      }
      pythonProcess = null;
    });
  }

  if (command) {
    attachPythonProc(
      spawn(command, args, {
        cwd: root,
        env: childEnv,
        stdio: ['ignore', 'pipe', 'pipe'],
        windowsHide: true,
      }),
      `${String(command).slice(-60)} ${args.slice(0, 3).join(' ')}`
    );
    return;
  }

  if (process.platform === 'win32') {
    const comspec = childEnv.ComSpec || path.join(childEnv.SystemRoot || 'C:\\Windows', 'System32', 'cmd.exe');
    const rootQ = root.replace(/"/g, '\\"');
    const script = `cd /d "${rootQ}" && py -3 -m uvicorn app:app --host ${API_HOST} --port ${API_PORT}`;
    // #region agent log
    dbgLog('startPythonServer:cmdFallback', 'py -3 via cmd', { scriptSlice: script.slice(0, 140) }, 'H2');
    // #endregion
    attachPythonProc(
      spawn(comspec, ['/d', '/s', '/c', script], {
        cwd: root,
        env: childEnv,
        stdio: ['ignore', 'pipe', 'pipe'],
        windowsHide: true,
      }),
      'cmd /c py -3 -m uvicorn'
    );
    return;
  }

  console.error('未检测到可用的 Python（已尝试本机常见路径与 py/python 命令）。');
  dialog.showErrorBox(
    '未找到 Python',
    'Electron 启动时找不到可用的 Python。\n\n' +
      '1) 安装 Python 3.10+ 并勾选「Add python.exe to PATH」\n' +
      '2) 或在用户环境变量中设置以下之一为 python.exe 的完整路径：\n' +
      '   • SLIDE_ANNOTATE_PYTHON（推荐，与 AI-writer 的 AIWRITER_PYTHON 类似）\n' +
      '   • PYTHON\n' +
      '3) 然后在终端执行：pip install -r server/requirements.txt\n\n' +
      '可用 PowerShell 检查：where.exe python ；或 py -3 -c "import sys;print(sys.executable)"'
  );
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1080,
    height: 820,
    minWidth: 880,
    minHeight: 640,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, '..', 'renderer', 'index.html'));

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

ipcMain.on('slide-annotate:get-base', (event) => {
  event.returnValue = `http://${API_HOST}:${API_PORT}`;
});

app.on('ready', async () => {
  // #region agent log
  dbgLog(
    'main:ready',
    'app ready',
    { platform: process.platform, execPath: process.execPath.slice(-80), cwd: process.cwd() },
    'H0'
  );
  // #endregion
  startPythonServer();
  try {
    await waitForHealth();
  } catch (e) {
    console.error(e.message);
    dialog.showMessageBox({
      type: 'warning',
      title: '本地 API 未就绪',
      message: '无法在超时时间内连接 Python 服务。',
      detail: String(e.message),
    });
  }
  createWindow();
});

app.on('before-quit', () => {
  app.isQuitting = true;
  if (pythonProcess && !pythonProcess.killed) {
    pythonProcess.kill();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
