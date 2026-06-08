/**
 * 主渲染进程入口 — 初始化所有模块并处理全局事件
 * 对齐 src/main.py + App.__init__ 的启动流程
 */
(async function bootstrap() {
  'use strict';

  /* ─── 1. 等待 Python 后端就绪 ─── */
  StatusBar.setMessage('正在连接 Python 后端…');

  let port;
  try {
    port = await ApiClient.init();
    const health = await ApiClient.checkHealth();
    if (health?.api_version >= 2) {
      StatusBar.setMessage(`后端已就绪 (port ${port})`);
    } else {
      StatusBar.setMessage(`后端已连接但版本过旧 (port ${port})，删除等功能可能失败，请重启应用`);
    }
  } catch (err) {
    StatusBar.setMessage('后端连接失败: ' + err.message);
    console.error('[bootstrap] 后端连接失败', err);
  }

  /* ─── 2. 拉取后端设置 ─── */
  try {
    const settings = await ApiClient.getSettings();
    if (settings) AppState.set('settings', settings);
  } catch (e) {
    console.warn('[bootstrap] 无法加载远端设置, 使用默认值');
  }

  /* ─── 3. 初始化各组件 ─── */
  Toolbar.init();
  FilePanel.init();
  Preview.init();
  InkEngine.init();
  InkToolbar.init();
  Annotations.init();
  Sidebar.init();
  StatusBar.init();

  /* ─── 3.5 从后端恢复上次会话 ─── */
  try {
    const state = await ApiClient.getState();
    AppState.set('selectedFiles', state.files || []);
    AppState.set('currentFileIndex', state.current_file_index ?? -1);
    FilePanel.refresh();
    if (state.files && state.files.length > 0) {
      if (state.pdf_available) {
        await Preview.loadFromState(state);
        Annotations.refresh();
        Sidebar.refreshList();
        StatusBar.setMessage(`已恢复 ${state.files.length} 个文件`);
      } else {
        Preview.showPlaceholder();
        StatusBar.setMessage(`已恢复文件列表（${state.files.length} 个），PDF 不可用，请检查原文件是否存在`);
      }
    } else {
      Preview.showPlaceholder();
    }
  } catch (e) {
    console.warn('[bootstrap] 会话恢复失败', e);
    Preview.showPlaceholder();
  }

  /* ─── 4. 全局快捷键 ─── */
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'z') {
      e.preventDefault();
      handleUndo();
    }
    if (e.ctrlKey && e.key === 'y') {
      e.preventDefault();
      handleRedo();
    }
    if (e.key === 'Escape') {
      if (AppState.get('addingAnnotation')) {
        AppState.set('addingAnnotation', false);
        document.getElementById('mode-hint').textContent = '滚轮滚动 · ± 缩放 · 双击译文编辑 · 可拖动微调位置';
      }
      if (AppState.isInkToolActive()) {
        InkToolbar.closeTool();
      }
    }
    if ((e.key === 'Delete' || e.key === 'Backspace') && !e.ctrlKey && !e.metaKey && !e.altKey) {
      if (isTextInputFocused()) return;
      const page = AppState.get('selectedMarkerPage');
      const idx = AppState.get('selectedMarkerIndex');
      if (page != null && idx != null) {
        e.preventDefault();
        Sidebar.deleteSelectedMarker();
      }
    }
    if ((e.key === '+' || e.key === '=') && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      Preview.zoomIn();
    }
    if (e.key === '-' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      Preview.zoomOut();
    }
  });

  function isTextInputFocused() {
    const el = document.activeElement;
    if (!el) return false;
    const tag = el.tagName;
    if (tag === 'TEXTAREA' || tag === 'INPUT' || tag === 'SELECT') return true;
    return el.isContentEditable;
  }

  /* ─── 5. 页面切换 / 文件切换 → 刷新侧边栏 ─── */
  AppState.on('change:currentPage', () => {
    Sidebar.refreshList();
    Sidebar.deselectMarker();
  });

  AppState.on('change:currentFileIndex', () => {
    Sidebar.refreshList();
    Sidebar.deselectMarker();
  });

  /* ─── 6. 定时同步后端状态 ─── */
  setInterval(async () => {
    try {
      const state = await ApiClient.getState();
      if (state && state.annotations) {
        AppState.set('backendAnnotations', state.annotations);
      }
    } catch (_) {}
  }, 5000);

  /* ─── 7. 撤销 / 重做 ─── */
  const undoStack = [];
  const redoStack = [];

  function pushUndo(snapshot) {
    undoStack.push(snapshot);
    if (undoStack.length > 50) undoStack.shift();
    redoStack.length = 0;
  }

  function handleUndo() {
    if (undoStack.length === 0) return;
    const snapshot = undoStack.pop();
    redoStack.push(getCurrentSnapshot());
    restoreSnapshot(snapshot);
    StatusBar.setMessage('撤销');
  }

  function handleRedo() {
    if (redoStack.length === 0) return;
    const snapshot = redoStack.pop();
    undoStack.push(getCurrentSnapshot());
    restoreSnapshot(snapshot);
    StatusBar.setMessage('重做');
  }

  function getCurrentSnapshot() {
    const page = AppState.get('currentPage');
    return {
      page,
      annotations: JSON.parse(JSON.stringify(AppState.getPageAnnotations(page))),
    };
  }

  function restoreSnapshot(snap) {
    AppState.setPageAnnotations(snap.page, snap.annotations);
    Annotations.refresh();
    Sidebar.refreshList();
  }

  window._pushUndo = pushUndo;

  /* ─── 完成 ─── */
  StatusBar.setMessage('就绪');
  console.log('[bootstrap] Electron 前端初始化完成');
})();
