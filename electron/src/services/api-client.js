/**
 * Python 后端 API 通信层
 * 与 src/services/web_preview_server.py Flask 端对接
 */
const ApiClient = (() => {
  let baseUrl = 'http://localhost:8765';

  async function init() {
    if (window.electronAPI) {
      const port = await window.electronAPI.getPythonPort();
      baseUrl = `http://localhost:${port}`;
      return port;
    }
    return 8765;
  }

  async function fetchJSON(path, options = {}) {
    const res = await fetch(`${baseUrl}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!res.ok) {
      let detail = '';
      try {
        const body = await res.json();
        detail = body.error ? `: ${body.error}` : '';
      } catch (_) {}
      const hint = res.status === 405
        ? '（后端版本过旧，请完全退出应用后重新 npm start）'
        : '';
      throw new Error(`API ${path}: ${res.status}${detail}${hint}`);
    }
    return res.json();
  }

  async function checkHealth() {
    try {
      return await fetchJSON('/api/health');
    } catch (_) {
      return null;
    }
  }

  async function getState() { return fetchJSON('/api/state'); }
  async function getAnnotations() { return fetchJSON('/api/annotations'); }

  async function getPdfArrayBuffer(pdfToken) {
    const q = pdfToken
      ? `?v=${encodeURIComponent(pdfToken)}`
      : `?t=${Date.now()}`;
    const res = await fetch(`${baseUrl}/api/pdf${q}`, { cache: 'no-store' });
    if (!res.ok) throw new Error('PDF not available');
    return res.arrayBuffer();
  }

  async function getInk() { return fetchJSON('/api/ink'); }

  async function putInk(pages) {
    return fetchJSON('/api/ink', {
      method: 'PUT',
      body: JSON.stringify({ pages }),
    });
  }

  async function saveInkToDocument(pages, overwrite = false) {
    return fetchJSON('/api/ink/save', {
      method: 'POST',
      body: JSON.stringify({ pages, overwrite }),
    });
  }

  async function importFiles(filePaths) {
    return fetchJSON('/api/import', {
      method: 'POST',
      body: JSON.stringify({ files: filePaths }),
    });
  }

  async function annotatePages(startPage, endPage) {
    return fetchJSON('/api/annotate', {
      method: 'POST',
      body: JSON.stringify({ start_page: startPage, end_page: endPage }),
    });
  }

  async function getAnnotateProgress() {
    return fetchJSON('/api/annotate/progress');
  }

  async function annotateSingle(pageNum) {
    return fetchJSON('/api/annotate/page', {
      method: 'POST',
      body: JSON.stringify({ page: pageNum }),
    });
  }

  async function exportPdf(outputPath) {
    return fetchJSON('/api/export', {
      method: 'POST',
      body: JSON.stringify({ output_path: outputPath }),
    });
  }

  async function saveProject(path) {
    return fetchJSON('/api/project/save', {
      method: 'POST',
      body: JSON.stringify({ path }),
    });
  }

  async function openProject(path) {
    return fetchJSON('/api/project/open', {
      method: 'POST',
      body: JSON.stringify({ path }),
    });
  }

  async function getSettings() { return fetchJSON('/api/settings'); }

  async function saveSettings(settings) {
    return fetchJSON('/api/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  async function selectFile(index, page = null) {
    return fetchJSON('/api/select-file', {
      method: 'POST',
      body: JSON.stringify({ index, page }),
    });
  }

  async function navigatePage(page) {
    return fetchJSON('/api/navigate', {
      method: 'POST',
      body: JSON.stringify({ page }),
    });
  }

  async function updateAnnotation(pageNum, markerIndex, data) {
    return fetchJSON('/api/annotation/update', {
      method: 'PUT',
      body: JSON.stringify({ page: pageNum, index: markerIndex, ...data }),
    });
  }

  async function addAnnotation(pageNum, data) {
    return fetchJSON('/api/annotation/add', {
      method: 'POST',
      body: JSON.stringify({ page: pageNum, ...data }),
    });
  }

  async function deleteAnnotation(pageNum, markerIndex) {
    return fetchJSON('/api/annotation/remove', {
      method: 'POST',
      body: JSON.stringify({ page: pageNum, index: markerIndex }),
    });
  }

  async function deleteAllAnnotations(pageNum) {
    return fetchJSON('/api/annotation/remove-all', {
      method: 'POST',
      body: JSON.stringify({ page: pageNum }),
    });
  }

  async function undo() { return fetchJSON('/api/undo', { method: 'POST' }); }

  async function removeFile(index) {
    return fetchJSON('/api/file/remove', {
      method: 'DELETE',
      body: JSON.stringify({ index }),
    });
  }

  return {
    init, checkHealth, getState, getAnnotations, getPdfArrayBuffer, getInk, putInk,
    saveInkToDocument, importFiles, annotatePages, getAnnotateProgress, annotateSingle,
    exportPdf, saveProject, openProject, getSettings, saveSettings,
    selectFile, navigatePage, updateAnnotation, addAnnotation,
    deleteAnnotation, deleteAllAnnotations, undo, removeFile,
  };
})();
