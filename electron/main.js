const { app, BrowserWindow, ipcMain, dialog, Menu } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn, execSync } = require('child_process');
const http = require('http');

let mainWindow = null;
let previewWindow = null;
let pythonProcess = null;
const PYTHON_PORT = 8765;

function killProcessOnPort(port) {
  try {
    const out = execSync(`netstat -ano | findstr :${port} | findstr LISTENING`, { encoding: 'utf8' });
    const pids = new Set();
    for (const line of out.split('\n')) {
      const m = line.trim().match(/LISTENING\s+(\d+)/);
      if (m) pids.add(m[1]);
    }
    for (const pid of pids) {
      try { execSync(`taskkill /F /PID ${pid}`, { encoding: 'utf8' }); } catch (_) {}
    }
    if (pids.size > 0) console.log(`[startup] killed stale PIDs on port ${port}:`, [...pids]);
  } catch (_) {}
}

function waitForBackendReady(timeoutMs = 45000) {
  const start = Date.now();
  const maxWait = app.isPackaged ? timeoutMs : 15000;
  return new Promise((resolve) => {
    const check = () => {
      if (Date.now() - start > maxWait) { resolve(false); return; }
      const req = http.get(`http://127.0.0.1:${PYTHON_PORT}/api/health`, (res) => {
        let body = '';
        res.on('data', (c) => { body += c; });
        res.on('end', () => {
          try {
            const j = JSON.parse(body);
            if (j.ok && j.api_version >= 2) { resolve(true); return; }
          } catch (_) {}
          setTimeout(check, 300);
        });
      });
      req.on('error', () => setTimeout(check, 300));
      req.setTimeout(2000, () => { req.destroy(); setTimeout(check, 300); });
    };
    check();
  });
}

function getAppIconPath() {
  if (process.platform === 'win32') {
    return path.join(__dirname, 'assets', 'icon.ico');
  }
  return path.join(__dirname, 'assets', 'icon.png');
}

function resolveBundledBackendExe() {
  if (!app.isPackaged) return null;
  const base = path.join(process.resourcesPath, 'backend-bin');
  const name = process.platform === 'win32' ? 'topdf-backend.exe' : 'topdf-backend';
  const exePath = path.join(base, name);
  if (!fs.existsSync(exePath)) {
    console.warn('[backend] 已打包但未找到内置后端，将尝试本机 Python：', exePath);
    return null;
  }
  return exePath;
}

function getDevProjectRoot() {
  return path.join(__dirname, '..');
}

function isPreviewUrl(url) {
  try {
    const u = new URL(url);
    const port = u.port || (u.protocol === 'https:' ? '443' : '80');
    return (u.hostname === 'localhost' || u.hostname === '127.0.0.1')
      && port === String(PYTHON_PORT);
  } catch {
    return false;
  }
}

function openPreviewWindow() {
  if (previewWindow && !previewWindow.isDestroyed()) {
    previewWindow.webContents.executeJavaScript(
      'if(typeof refresh==="function") refresh(true); else location.reload();'
    ).catch(() => {
      previewWindow.loadURL(`http://127.0.0.1:${PYTHON_PORT}/?t=${Date.now()}`);
    });
    previewWindow.focus();
    return previewWindow;
  }

  previewWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 900,
    minHeight: 600,
    title: 'TO PDF · 批注预览',
    icon: getAppIconPath(),
    backgroundColor: '#F4F0FA',
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  previewWindow.loadURL(`http://127.0.0.1:${PYTHON_PORT}/`);

  previewWindow.on('closed', () => {
    previewWindow = null;
  });

  return previewWindow;
}

function notifyPreviewRefresh() {
  if (!previewWindow || previewWindow.isDestroyed()) return;
  previewWindow.webContents.executeJavaScript(
    'if(typeof refresh==="function") refresh(true);'
  ).catch(() => {});
}

function attachWindowOpenHandler(win) {
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (isPreviewUrl(url)) {
      openPreviewWindow();
      return { action: 'deny' };
    }
    return { action: 'deny' };
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1100,
    minHeight: 720,
    title: 'TO PDF · 中文批注',
    icon: getAppIconPath(),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    backgroundColor: '#F4F0FA',
    show: false,
  });

  mainWindow.loadFile(path.join(__dirname, 'src', 'index.html'));

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  attachWindowOpenHandler(mainWindow);
  Menu.setApplicationMenu(buildMenu());
}
function buildMenu() {
  const template = [
    {
      label: '文件',
      submenu: [
        { label: '导入', accelerator: 'CmdOrCtrl+O', click: () => mainWindow?.webContents.send('menu:import') },
        { label: '打开工程', accelerator: 'CmdOrCtrl+Shift+O', click: () => mainWindow?.webContents.send('menu:open-project') },
        { label: '保存工程', accelerator: 'CmdOrCtrl+S', click: () => mainWindow?.webContents.send('menu:save-project') },
        { type: 'separator' },
        { label: '导出 PDF', accelerator: 'CmdOrCtrl+E', click: () => mainWindow?.webContents.send('menu:export') },
        { type: 'separator' },
        { label: '系统 API 设置', click: () => mainWindow?.webContents.send('menu:settings') },
        { type: 'separator' },
        { role: 'quit', label: '退出' },
      ],
    },
    {
      label: '编辑',
      submenu: [
        { label: '撤销', accelerator: 'CmdOrCtrl+Z', click: () => mainWindow?.webContents.send('menu:undo') },
        { type: 'separator' },
        { role: 'cut', label: '剪切' },
        { role: 'copy', label: '复制' },
        { role: 'paste', label: '粘贴' },
        { role: 'selectAll', label: '全选' },
      ],
    },
    {
      label: '视图',
      submenu: [
        { label: '放大', accelerator: 'CmdOrCtrl+=', click: () => mainWindow?.webContents.send('menu:zoom-in') },
        { label: '缩小', accelerator: 'CmdOrCtrl+-', click: () => mainWindow?.webContents.send('menu:zoom-out') },
        { label: '重置缩放', accelerator: 'CmdOrCtrl+0', click: () => mainWindow?.webContents.send('menu:zoom-reset') },
        { type: 'separator' },
        { role: 'toggleDevTools', label: '开发者工具' },
        { role: 'reload', label: '重新加载' },
      ],
    },
  ];
  return Menu.buildFromTemplate(template);
}

function startPythonBackend() {
  const bundledExe = resolveBundledBackendExe();
  const env = {
    ...process.env,
    TOPDF_ELECTRON_MODE: '1',
    TOPDF_API_PORT: String(PYTHON_PORT),
    PYTHONUTF8: '1',
    PYTHONIOENCODING: 'utf-8',
  };

  if (bundledExe) {
    console.log('[backend] start frozen:', bundledExe);
    pythonProcess = spawn(bundledExe, ['--port', String(PYTHON_PORT)], {
      cwd: path.dirname(bundledExe),
      env,
      windowsHide: true,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
  } else {
    const pythonPath = process.env.PYTHON_PATH || 'python';
    const scriptPath = path.join(getDevProjectRoot(), 'src', 'main.py');
    console.log('[backend] start dev python:', pythonPath, scriptPath);
    pythonProcess = spawn(pythonPath, ['-u', scriptPath, '--electron', '--port', String(PYTHON_PORT)], {
      cwd: getDevProjectRoot(),
      env,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
  }

  pythonProcess.stdout?.on('data', (data) => {
    console.log(`[Python] ${data.toString().trim()}`);
  });

  pythonProcess.stderr?.on('data', (data) => {
    console.error(`[Python ERR] ${data.toString().trim()}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`[Python] exited with code ${code}`);
    pythonProcess = null;
  });
}

// ──── IPC Handlers ────

ipcMain.handle('dialog:open-files', async (_event, options) => {
  if (!mainWindow) return [];
  const result = await dialog.showOpenDialog(mainWindow, {
    title: options?.title || '选择文件',
    filters: options?.filters || [
      { name: 'PDF 文件', extensions: ['pdf'] },
      { name: 'PPT 文件', extensions: ['ppt', 'pptx'] },
      { name: '所有支持的文件', extensions: ['pdf', 'ppt', 'pptx'] },
    ],
    properties: ['openFile', 'multiSelections'],
  });
  return result.canceled ? [] : result.filePaths;
});

ipcMain.handle('dialog:open-project', async () => {
  if (!mainWindow) return null;
  const result = await dialog.showOpenDialog(mainWindow, {
    title: '打开工程',
    filters: [
      { name: 'TO PDF 工程', extensions: ['topdf'] },
      { name: '所有文件', extensions: ['*'] },
    ],
    properties: ['openFile'],
  });
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle('dialog:save-file', async (_event, options) => {
  if (!mainWindow) return null;
  const result = await dialog.showSaveDialog(mainWindow, {
    title: options?.title || '保存文件',
    defaultPath: options?.defaultPath,
    filters: options?.filters || [{ name: 'PDF 文件', extensions: ['pdf'] }],
  });
  return result.canceled ? null : result.filePath;
});

ipcMain.handle('dialog:save-project', async (_event, options) => {
  if (!mainWindow) return null;
  const result = await dialog.showSaveDialog(mainWindow, {
    title: '保存工程',
    defaultPath: options?.defaultPath,
    filters: [{ name: 'TO PDF 工程', extensions: ['topdf'] }],
  });
  return result.canceled ? null : result.filePath;
});

ipcMain.handle('get-python-port', () => PYTHON_PORT);

ipcMain.handle('app:is-packaged', () => app.isPackaged);

ipcMain.handle('app:pdf-base-path', () => {
  if (app.isPackaged) {
    return '../vendor/pdfjs';
  }
  return null;
});

ipcMain.handle('window:open-preview', () => {
  openPreviewWindow();
  return true;
});

ipcMain.handle('preview:refresh', () => {
  notifyPreviewRefresh();
  return true;
});

// ──── App Lifecycle ────

app.whenReady().then(async () => {
  if (process.platform === 'win32') {
    app.setAppUserModelId('com.topdf.annotator');
  }
  killProcessOnPort(PYTHON_PORT);
  startPythonBackend();
  const ready = await waitForBackendReady(45000);
  if (!ready) console.warn('[startup] backend did not become ready in time, proceeding anyway');
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }
  if (process.platform !== 'darwin') app.quit();
});
