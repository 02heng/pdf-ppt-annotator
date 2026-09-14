const { contextBridge, ipcRenderer } = require('electron');

function base() {
  try {
    const url = ipcRenderer.sendSync('slide-annotate:get-base');
    return typeof url === 'string' && url ? url : 'http://127.0.0.1:8765';
  } catch {
    return 'http://127.0.0.1:8765';
  }
}

async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) {
    const msg = data && data.detail ? data.detail : text || res.statusText;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return data;
}

contextBridge.exposeInMainWorld('api', {
  get baseUrl() {
    return base();
  },

  health() {
    return fetchJson(`${base()}/api/health`);
  },

  /** @param {File} file */
  async createJob(file) {
    const fd = new FormData();
    fd.append('file', file);
    return fetchJson(`${base()}/api/jobs`, { method: 'POST', body: fd });
  },

  /** @param {string} jobId @param {{ api_key?: string, indices?: number[] }} body */
  generate(jobId, body) {
    return fetchJson(`${base()}/api/jobs/${jobId}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    });
  },

  /** @param {string} jobId @param {number} pageIndex @param {{ annotation: string }} body */
  updatePage(jobId, pageIndex, body) {
    return fetchJson(`${base()}/api/jobs/${jobId}/pages/${pageIndex}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  },

  /** @param {string} jobId */
  exportUrl(jobId) {
    return `${base()}/api/jobs/${jobId}/export`;
  },

  /** @param {string} jobId @param {number} pageIndex */
  pagePreviewUrl(jobId, pageIndex) {
    return `${base()}/api/jobs/${jobId}/pages/${pageIndex}/preview`;
  },
});
