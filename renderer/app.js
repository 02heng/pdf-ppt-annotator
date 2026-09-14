/** @type {{ baseUrl: string, health: () => Promise<any>, createJob: (f: File) => Promise<any>, generate: (id: string, b: object) => Promise<any>, updatePage: (id: string, i: number, b: object) => Promise<any>, exportUrl: (id: string) => string }} */
// eslint-disable-next-line no-undef
const bridge = window.api;

const $ = (id) => document.getElementById(id);

const fileInput = $('fileInput');
const apiKeyInput = $('apiKey');
const btnUpload = $('btnUpload');
const btnGenerateAll = $('btnGenerateAll');
const btnExport = $('btnExport');
const jobInfo = $('jobInfo');
const pageList = $('pageList');
const pageHint = $('pageHint');
const svcStatus = $('svcStatus');
const carouselBar = $('carouselBar');
const carouselIndicator = $('carouselIndicator');
const btnPrevPage = $('btnPrevPage');
const btnNextPage = $('btnNextPage');

const LS_KEY = 'slide_annotate_deepseek_key';
const LS_AUTO = 'slide_annotate_auto_gen';

/** @param {'info'|'ok'|'warn'|'err'} [tone] */
function setJobInfo(text, tone = 'info') {
  jobInfo.textContent = text;
  jobInfo.dataset.tone = tone;
}

const autoGenCheckbox = $('autoGenAfterUpload');
if (localStorage.getItem(LS_AUTO) === '0') {
  autoGenCheckbox.checked = false;
}
autoGenCheckbox.addEventListener('change', () => {
  localStorage.setItem(LS_AUTO, autoGenCheckbox.checked ? '1' : '0');
});

let currentJobId = null;
let pages = [];
/** 当前轮播页索引（0-based） */
let currentSlideIndex = 0;
/** @type {Map<string, string>} */
const previewBlobCache = new Map();
let previewLoadToken = 0;
/** 预览缩放（1 = 适应预览区宽度） */
let previewZoom = 1;

function previewCacheKey(jobId, idx) {
  return `${jobId}:${idx}:hd`;
}

function clearPreviewCache(jobId) {
  for (const [key, url] of previewBlobCache.entries()) {
    if (!jobId || key.startsWith(`${jobId}:`)) {
      URL.revokeObjectURL(url);
      previewBlobCache.delete(key);
    }
  }
}

function pagePreviewUrl(jobId, idx) {
  const base = typeof bridge.pagePreviewUrl === 'function'
    ? bridge.pagePreviewUrl(jobId, idx)
    : `${bridge.baseUrl}/api/jobs/${jobId}/pages/${idx}/preview`;
  return `${base}?max=${encodeURIComponent('2400')}`;
}

function applyPreviewZoom(img, label) {
  if (!img) return;
  const pct = Math.round(previewZoom * 100);
  img.style.width = `${pct}%`;
  img.style.maxWidth = 'none';
  if (label) label.textContent = `${pct}%`;
}

function setupPreviewZoomControls(card) {
  const img = card.querySelector('.page-preview');
  const label = card.querySelector('.preview-zoom-label');
  card.querySelector('[data-zoom-out]')?.addEventListener('click', () => {
    previewZoom = Math.max(0.5, Math.round((previewZoom - 0.25) * 100) / 100);
    applyPreviewZoom(img, label);
  });
  card.querySelector('[data-zoom-in]')?.addEventListener('click', () => {
    previewZoom = Math.min(2.5, Math.round((previewZoom + 0.25) * 100) / 100);
    applyPreviewZoom(img, label);
  });
  card.querySelector('[data-zoom-fit]')?.addEventListener('click', () => {
    previewZoom = 1;
    applyPreviewZoom(img, label);
  });
  img?.addEventListener('load', () => applyPreviewZoom(img, label));
}

async function mountPagePreview(jobId, idx, wrap) {
  const token = ++previewLoadToken;
  const img = wrap.querySelector('.page-preview');
  const loading = wrap.querySelector('.page-preview-loading');
  const fallback = wrap.querySelector('.page-preview-fallback');

  const setLoading = (on) => {
    if (loading) loading.hidden = !on;
  };
  const showErr = (msg) => {
    if (token !== previewLoadToken) return;
    if (img) {
      img.hidden = true;
      img.removeAttribute('src');
    }
    if (fallback) {
      fallback.hidden = false;
      fallback.textContent = msg;
    }
    setLoading(false);
  };
  const showImg = (url) => {
    if (token !== previewLoadToken) return;
    if (fallback) fallback.hidden = true;
    if (img) {
      img.hidden = false;
      img.onload = () => {
        const card = wrap.closest('.page-card');
        const label = card?.querySelector('.preview-zoom-label');
        applyPreviewZoom(img, label);
      };
      img.src = url;
    }
    setLoading(false);
  };

  if (!jobId) {
    showErr('暂无任务，请先上传文件');
    return;
  }

  const cacheKey = previewCacheKey(jobId, idx);
  if (previewBlobCache.has(cacheKey)) {
    showImg(previewBlobCache.get(cacheKey));
    return;
  }

  setLoading(true);
  if (img) img.hidden = true;
  if (fallback) fallback.hidden = true;

  try {
    const res = await fetch(pagePreviewUrl(jobId, idx), { cache: 'no-store' });
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const data = await res.json();
        if (data?.detail) detail = String(data.detail);
      } catch {
        /* ignore */
      }
      throw new Error(detail);
    }
    const blob = await res.blob();
    if (token !== previewLoadToken) return;
    if (!blob.size) throw new Error('预览图为空');
    const blobUrl = URL.createObjectURL(blob);
    previewBlobCache.set(cacheKey, blobUrl);
    showImg(blobUrl);
  } catch (e) {
    showErr(`页面预览加载失败：${e.message || e}`);
  }
}

function refreshCurrentPageAnnotation() {
  const idx = currentSlideIndex;
  const ta = pageList.querySelector(`textarea[data-idx="${idx}"]`);
  if (ta && pages[idx]) ta.value = pages[idx].annotation || '';
}

function setSvc(ok, msg) {
  svcStatus.textContent = msg;
  svcStatus.classList.remove('ok', 'err');
  svcStatus.classList.add(ok ? 'ok' : 'err');
}

async function ping() {
  try {
    await bridge.health();
    setSvc(true, '本地服务已连接');
  } catch {
    setSvc(false, '本地服务未就绪');
  }
}

function loadKey() {
  const k = localStorage.getItem(LS_KEY);
  if (k) apiKeyInput.value = k;
}

function saveKey() {
  localStorage.setItem(LS_KEY, apiKeyInput.value.trim());
}

apiKeyInput.addEventListener('change', saveKey);

fileInput.addEventListener('change', () => {
  btnUpload.disabled = !fileInput.files?.length;
});

/** 将当前屏上的批注写回内存并同步到后端 */
async function persistCurrentPageFromDom() {
  if (!currentJobId || !pages.length) return;
  const ta = pageList.querySelector('textarea[data-idx]');
  if (!ta) return;
  const idx = Number(ta.getAttribute('data-idx'));
  const val = ta.value;
  pages[idx].annotation = val;
  try {
    await bridge.updatePage(currentJobId, idx, { annotation: val });
  } catch {
    /* ignore */
  }
}

function updateCarouselChrome() {
  if (!pages.length) {
    carouselBar.hidden = true;
    return;
  }
  carouselBar.hidden = false;
  if (currentSlideIndex < 0) currentSlideIndex = 0;
  if (currentSlideIndex >= pages.length) currentSlideIndex = pages.length - 1;
  carouselIndicator.textContent = `第 ${currentSlideIndex + 1} / ${pages.length} 页`;
  btnPrevPage.disabled = currentSlideIndex <= 0;
  btnNextPage.disabled = currentSlideIndex >= pages.length - 1;
}

btnPrevPage.addEventListener('click', async () => {
  await persistCurrentPageFromDom();
  if (currentSlideIndex > 0) {
    currentSlideIndex -= 1;
    renderPages();
  }
});

btnNextPage.addEventListener('click', async () => {
  await persistCurrentPageFromDom();
  if (currentSlideIndex < pages.length - 1) {
    currentSlideIndex += 1;
    renderPages();
  }
});

document.addEventListener('keydown', (e) => {
  if (!pages.length || !currentJobId) return;
  const t = e.target;
  if (t && (t.tagName === 'TEXTAREA' || t.tagName === 'INPUT' || t.isContentEditable)) return;
  if (e.key === 'ArrowLeft' && !btnPrevPage.disabled) {
    e.preventDefault();
    btnPrevPage.click();
  }
  if (e.key === 'ArrowRight' && !btnNextPage.disabled) {
    e.preventDefault();
    btnNextPage.click();
  }
});

btnUpload.addEventListener('click', async () => {
  const f = fileInput.files?.[0];
  if (!f) return;
  saveKey();
  setJobInfo('正在上传…', 'info');
  pageList.innerHTML = '';
  carouselBar.hidden = true;
  clearPreviewCache(currentJobId);
  try {
    const data = await bridge.createJob(f);
    currentJobId = data.job_id;
    pages = data.pages || [];
    currentSlideIndex = 0;
    setJobInfo(
      `任务 ${currentJobId.slice(0, 8)}… · ${data.type.toUpperCase()} · ${data.page_count} 页`,
      'info',
    );
    btnGenerateAll.disabled = false;
    btnExport.disabled = false;
    renderPages();
    const key = apiKeyInput.value.trim();
    if (autoGenCheckbox.checked && key) {
      pageHint.textContent = '已解析。正在按页调用 DeepSeek 生成教学批注（可随进度翻页查看）…';
      await generateAllAnnotationsProgressive();
    } else if (autoGenCheckbox.checked && !key) {
      pageHint.textContent = '已解析。请填写 API Key 后点击「一键生成全部批注」（或保存 Key 后重新上传）。';
    } else {
      pageHint.textContent = '已解析。可用「上一页 / 下一页」逐页查看；一键生成将按页填写批注。';
    }
  } catch (e) {
    setJobInfo(String(e.message || e), 'err');
    currentJobId = null;
    pages = [];
    btnGenerateAll.disabled = true;
    btnExport.disabled = true;
    carouselBar.hidden = true;
  }
});

/** 逐页请求 API，并轮播到当前生成页以便查看 */
async function generateAllAnnotationsProgressive() {
  if (!currentJobId) return;
  saveKey();
  const key = apiKeyInput.value.trim();
  if (!key) {
    setJobInfo('请填写 DeepSeek API Key', 'warn');
    return;
  }
  const n = pages.length;
  setJobInfo(`DeepSeek 生成中：0 / ${n} 页…`, 'info');
  btnGenerateAll.disabled = true;
  btnPrevPage.disabled = true;
  btnNextPage.disabled = true;
  try {
    for (let i = 0; i < n; i++) {
      if (currentSlideIndex !== i) {
        currentSlideIndex = i;
        renderPages();
      } else {
        updateCarouselChrome();
      }
      setJobInfo(`DeepSeek 生成中：第 ${i + 1} / ${n} 页…`, 'info');
      const data = await bridge.generate(currentJobId, { api_key: key, indices: [i] });
      pages = data.pages || pages;
      refreshCurrentPageAnnotation();
    }
    setJobInfo(`已全部生成（${n} 页）。请逐页查看并修改批注，满意后点击「导出带批注文件」。`, 'ok');
    pageHint.textContent = '批注已写入各页，可在下方文本框编辑；确认无误后再手动导出。';
  } catch (e) {
    setJobInfo(String(e.message || e), 'err');
  } finally {
    btnGenerateAll.disabled = false;
    updateCarouselChrome();
  }
}

btnGenerateAll.addEventListener('click', () => {
  generateAllAnnotationsProgressive();
});

async function syncAllPagesFromDom() {
  await persistCurrentPageFromDom();
}

/**
 * 同步当前页批注并下载导出文件。
 * 先 GET；若遇 405（旧后端仅支持 POST）则自动改用 POST。
 */
async function exportAnnotatedFile(opts = {}) {
  if (!currentJobId) {
    throw new Error('无任务');
  }
  if (!opts.silentPrep) {
    setJobInfo('正在同步批注并生成文件…', 'info');
  }
  await syncAllPagesFromDom();
  const exportUrl = bridge.exportUrl(currentJobId);
  const init = { cache: 'no-store' };
  let res = await fetch(exportUrl, { ...init, method: 'GET' });
  if (res.status === 405) {
    res = await fetch(exportUrl, { ...init, method: 'POST' });
  }
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || `HTTP ${res.status}`);
  }
  const blob = await res.blob();
  const cd = res.headers.get('Content-Disposition');
  let filename = 'annotated';
  if (cd) {
    const m = /filename\*?=(?:UTF-8''|")?([^";\n]+)/i.exec(cd);
    if (m) {
      try {
        filename = decodeURIComponent(m[1].replace(/"/g, '').trim());
      } catch {
        filename = m[1].replace(/"/g, '').trim();
      }
    }
  }
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  setJobInfo(`已保存下载：${filename}`, 'ok');
  pageHint.textContent = '若未弹出保存位置，请查看浏览器或系统的下载列表。';
  return filename;
}

btnExport.addEventListener('click', async () => {
  if (!currentJobId) return;
  try {
    await exportAnnotatedFile({ silentPrep: false });
  } catch (e) {
    setJobInfo(String(e.message || e), 'err');
  }
});

function renderPages() {
  pageList.innerHTML = '';
  updateCarouselChrome();
  if (!pages.length) return;

  const idx = currentSlideIndex;
  previewZoom = 1;
  const card = document.createElement('div');
  card.className = 'page-card';
  card.innerHTML = `
      <div class="page-card-head">
        <h3>第 ${idx + 1} 页</h3>
        <div class="preview-toolbar row">
          <button type="button" data-zoom-out" title="缩小">−</button>
          <span class="preview-zoom-label">100%</span>
          <button type="button" data-zoom-in" title="放大">＋</button>
          <button type="button" data-zoom-fit title="适应宽度">适应宽度</button>
        </div>
      </div>
      <div class="page-preview-wrap">
        <div class="page-preview-loading">正在加载页面预览…</div>
        <img class="page-preview" alt="第 ${idx + 1} 页预览" hidden />
        <div class="page-preview-fallback muted" hidden>暂无页面预览</div>
      </div>
      <label class="muted">教学批注（中文）</label>
      <textarea data-idx="${idx}" placeholder="在此填写或编辑本页教学批注…">${escapeHtml(pages[idx].annotation || '')}</textarea>
      <div class="card-actions">
        <button type="button" data-regen="${idx}">本页重写</button>
        <button type="button" data-save="${idx}">保存本页</button>
      </div>
    `;
  pageList.appendChild(card);

  const previewWrap = card.querySelector('.page-preview-wrap');
  if (previewWrap && currentJobId) {
    mountPagePreview(currentJobId, idx, previewWrap);
  }
  setupPreviewZoomControls(card);

  const ta = card.querySelector('textarea');
  ta.addEventListener('blur', async () => {
    const text = ta.value;
    pages[idx].annotation = text;
    if (currentJobId) {
      try {
        await bridge.updatePage(currentJobId, idx, { annotation: text });
      } catch {
        /* ignore */
      }
    }
  });

  card.querySelector('button[data-save]')?.addEventListener('click', async () => {
    if (!currentJobId) return;
    pages[idx].annotation = ta.value;
    try {
      await bridge.updatePage(currentJobId, idx, { annotation: ta.value });
      setJobInfo(`第 ${idx + 1} 页已保存`, 'ok');
    } catch (e) {
      setJobInfo(String(e.message || e), 'err');
    }
  });

  card.querySelector('button[data-regen]')?.addEventListener('click', async (ev) => {
    if (!currentJobId) return;
    saveKey();
    const apiKey = apiKeyInput.value.trim();
    if (!apiKey) {
      setJobInfo('请填写 API Key', 'warn');
      return;
    }
    const btn = ev.currentTarget;
    btn.disabled = true;
    setJobInfo(`正在重写第 ${idx + 1} 页…`, 'info');
    try {
      const data = await bridge.generate(currentJobId, { api_key: apiKey, indices: [idx] });
      pages = data.pages || pages;
      ta.value = pages[idx].annotation || '';
      setJobInfo(`第 ${idx + 1} 页已重写`, 'ok');
    } catch (e) {
      setJobInfo(String(e.message || e), 'err');
    } finally {
      btn.disabled = false;
    }
  });
}

function escapeHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

loadKey();
ping().then(() => {
  setInterval(ping, 15000);
});
