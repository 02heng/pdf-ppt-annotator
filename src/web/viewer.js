/* PDF.js 点击批注预览 */
const PDFJS_VERSION = "3.11.174";
pdfjsLib.GlobalWorkerOptions.workerSrc =
  `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${PDFJS_VERSION}/pdf.worker.min.js`;

const canvas = document.getElementById("pdf-canvas");
const ctx = canvas.getContext("2d");
const layer = document.getElementById("annotation-layer");
const pageLabel = document.getElementById("page-label");
const statusEl = document.getElementById("status");

let pdfDoc = null;
let currentPage = 0;
let totalPages = 0;
let renderTask = null;
let viewportScale = 1.5;
let annotationsByPage = {};
let activeMarker = null;
let activeMarkerIndex = null;
let lastPdfToken = "";
let lastStateFingerprint = "";

async function fetchState() {
  const res = await fetch("/api/state");
  return res.json();
}

async function loadPdf() {
  const res = await fetch("/api/pdf");
  if (!res.ok) throw new Error("PDF 不可用");
  const data = await res.arrayBuffer();
  pdfDoc = await pdfjsLib.getDocument({ data }).promise;
  totalPages = pdfDoc.numPages;
}

function stateFingerprint(state) {
  return JSON.stringify({
    pdf_token: state.pdf_token || "",
    current_page: state.current_page || 0,
    total_pages: state.total_pages || 0,
    annotations: state.annotations || {},
  });
}

function clearLayer() {
  layer.innerHTML = "";
  activeMarker = null;
}

function renderMarkers(pageIndex, restoreIndex = null) {
  const keepIndex = restoreIndex ?? activeMarkerIndex;
  clearLayer();

  const items = annotationsByPage[String(pageIndex)] || [];
  items.forEach((item) => {
    const marker = document.createElement("div");
    marker.className = "annot-marker";
    marker.dataset.index = String(item.index);
    marker.style.borderColor = item.color || "#e74c3c";
    marker.style.left = `${item.x * viewportScale}px`;
    marker.style.top = `${item.y * viewportScale}px`;
    marker.textContent = item.index;

    const popup = document.createElement("div");
    popup.className = "annot-popup";
    popup.style.borderColor = item.color || "#e74c3c";

    const title = document.createElement("div");
    title.className = "annot-popup-title";
    title.textContent = `批注 ${item.index}`;

    const body = document.createElement("div");
    body.textContent = item.text || "";

    popup.appendChild(title);
    popup.appendChild(body);
    marker.appendChild(popup);

    marker.addEventListener("click", (e) => {
      e.stopPropagation();
      if (activeMarker && activeMarker !== marker) {
        activeMarker.classList.remove("active");
      }
      marker.classList.toggle("active");
      if (marker.classList.contains("active")) {
        activeMarker = marker;
        activeMarkerIndex = item.index;
      } else {
        activeMarker = null;
        activeMarkerIndex = null;
      }
    });

    if (keepIndex === item.index) {
      marker.classList.add("active");
      activeMarker = marker;
      activeMarkerIndex = item.index;
    }

    layer.appendChild(marker);
  });

  if (keepIndex != null && !items.some((item) => item.index === keepIndex)) {
    activeMarkerIndex = null;
    activeMarker = null;
  }
}

async function renderPage(pageNum, { clearActive = true } = {}) {
  if (!pdfDoc) return;
  if (renderTask) {
    try {
      await renderTask.cancel();
    } catch (_) {}
  }

  if (clearActive && pageNum !== currentPage) {
    activeMarkerIndex = null;
  }

  currentPage = pageNum;
  const page = await pdfDoc.getPage(pageNum + 1);
  const viewport = page.getViewport({ scale: viewportScale });

  canvas.width = viewport.width;
  canvas.height = viewport.height;
  layer.style.width = `${viewport.width}px`;
  layer.style.height = `${viewport.height}px`;

  renderTask = page.render({ canvasContext: ctx, viewport });
  await renderTask.promise;

  renderMarkers(pageNum, clearActive ? null : activeMarkerIndex);
  pageLabel.textContent = `${pageNum + 1} / ${totalPages}`;
}

async function updateMarkersOnly() {
  if (!pdfDoc) return;
  renderMarkers(currentPage, activeMarkerIndex);
}

async function refresh(force = false) {
  try {
    const state = await fetchState();
    const fingerprint = stateFingerprint(state);

    if (!force && fingerprint === lastStateFingerprint) {
      return;
    }

    const prevFingerprint = lastStateFingerprint;
    lastStateFingerprint = fingerprint;

    const newAnnotations = state.annotations || {};
    const serverPage = state.current_page || 0;
    totalPages = state.total_pages || 0;

    const pdfTokenChanged =
      state.pdf_token && state.pdf_token !== lastPdfToken;
    if (pdfTokenChanged) {
      pdfDoc = null;
      lastPdfToken = state.pdf_token;
      activeMarkerIndex = null;
    }

    if (!pdfDoc && state.pdf_available) {
      await loadPdf();
      totalPages = pdfDoc.numPages;
    }

    if (!pdfDoc) {
      statusEl.textContent = "请先在桌面应用中导入 PDF";
      return;
    }

    annotationsByPage = newAnnotations;
    const targetPage = Math.max(0, Math.min(serverPage, pdfDoc.numPages - 1));
    const pageChanged = targetPage !== currentPage;

    if (pdfTokenChanged || !prevFingerprint || pageChanged) {
      if (pageChanged) {
        activeMarkerIndex = null;
      }
      await renderPage(targetPage, { clearActive: pageChanged });
    } else {
      await updateMarkersOnly();
    }

    statusEl.textContent = "点击黄色标记查看批注，点击空白处关闭";
  } catch (err) {
    statusEl.textContent = `加载失败: ${err.message}`;
  }
}

document.getElementById("btn-prev").addEventListener("click", async () => {
  if (!pdfDoc || currentPage <= 0) return;
  activeMarkerIndex = null;
  await renderPage(currentPage - 1);
});

document.getElementById("btn-next").addEventListener("click", async () => {
  if (!pdfDoc || currentPage >= totalPages - 1) return;
  activeMarkerIndex = null;
  await renderPage(currentPage + 1);
});

document.getElementById("btn-refresh").addEventListener("click", () => refresh(true));

function closeActiveMarker() {
  if (activeMarker) {
    activeMarker.classList.remove("active");
    activeMarker = null;
  }
  activeMarkerIndex = null;
}

document.getElementById("viewer-wrap").addEventListener("click", (e) => {
  if (e.target.closest(".annot-marker")) return;
  closeActiveMarker();
});

refresh(true);
setInterval(() => refresh(false), 2000);
