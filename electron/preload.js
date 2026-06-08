const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  openFiles: (options) => ipcRenderer.invoke('dialog:open-files', options),
  openProject: () => ipcRenderer.invoke('dialog:open-project'),
  saveFile: (options) => ipcRenderer.invoke('dialog:save-file', options),
  saveProject: (options) => ipcRenderer.invoke('dialog:save-project', options),
  getPythonPort: () => ipcRenderer.invoke('get-python-port'),
  isPackaged: () => ipcRenderer.invoke('app:is-packaged'),
  getPdfBasePath: () => ipcRenderer.invoke('app:pdf-base-path'),
  openPreview: () => ipcRenderer.invoke('window:open-preview'),
  refreshPreview: () => ipcRenderer.invoke('preview:refresh'),

  onMenuImport: (cb) => ipcRenderer.on('menu:import', cb),
  onMenuOpenProject: (cb) => ipcRenderer.on('menu:open-project', cb),
  onMenuSaveProject: (cb) => ipcRenderer.on('menu:save-project', cb),
  onMenuExport: (cb) => ipcRenderer.on('menu:export', cb),
  onMenuSettings: (cb) => ipcRenderer.on('menu:settings', cb),
  onMenuUndo: (cb) => ipcRenderer.on('menu:undo', cb),
  onMenuZoomIn: (cb) => ipcRenderer.on('menu:zoom-in', cb),
  onMenuZoomOut: (cb) => ipcRenderer.on('menu:zoom-out', cb),
  onMenuZoomReset: (cb) => ipcRenderer.on('menu:zoom-reset', cb),
});
