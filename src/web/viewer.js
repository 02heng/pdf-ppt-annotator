/* PDF.js 批注预览 + 演示工具（聚焦 / 激光笔 / 墨迹，参考 PPT 放映与 pdf-annotate overlay 思路） */
const PDFJS_VERSION = "3.11.174";
pdfjsLib.GlobalWorkerOptions.workerSrc =
  `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${PDFJS_VERSION}/pdf.worker.min.js`;

const canvas = document.getElementById("pdf-canvas");
const ctx = canvas.getContext("2d");
const inkCanvas = document.getElementById("ink-canvas");
const inkCtx = inkCanvas.getContext("2d");
const laserCanvas = document.getElementById("laser-canvas");
const laserCtx = laserCanvas.getContext("2d");
const focusLayer = document.getElementById("focus-layer");
const layer = document.getElementById("annotation-layer");
const pageViewport = document.getElementById("page-viewport");
const pageContainer = document.getElementById("page-container");
const viewerWrap = document.getElementById("viewer-wrap");
const pageLabel = document.getElementById("page-label");
const statusEl = document.getElementById("status");
const toolsPanel = document.getElementById("tools-panel");

const INK_COLORS = [
  "#ffffff",
  "#000000",
  "#7f1d1d",
  "#ef4444",
  "#f97316",
  "#eab308",
  "#84cc16",
  "#16a34a",
  "#22d3ee",
  "#2563eb",
  "#1e3a8a",
  "#7c3aed",
];

let pdfDoc = null;
let currentPage = 0;
let totalPages = 0;
let renderTask = null;
const BASE_VIEWPORT_SCALE = 1.5;
let viewportScale = BASE_VIEWPORT_SCALE;
let basePageWidth = 0;
let basePageHeight = 0;
let pageWidth = 0;
let pageHeight = 0;
let annotationsByPage = {};
let activeMarker = null;
let activeMarkerIndex = null;
let lastPdfToken = "";
let lastStateFingerprint = "";

/* —— 演示工具 —— */
let currentTool = "pointer";
let currentColor = "#ef4444";
let inkByPage = {};
let isDrawing = false;
let currentStroke = null;
let lastInkPointer = null;
let inkDrawAnimId = null;
const INK_SAMPLE_PX = 2.5;
let laserTrail = [];
let laserAnimId = null;
let lastLaserPos = null;
const LASER_MAX_AGE = 680;
const LASER_SAMPLE_STEP = 2.5;
const LASER_TRAIL_MAX_POINTS = 200;
let magnifyActive = false;
let magnifyAnimating = false;
/** 按下时的聚焦锚点（页面归一化坐标 + 屏幕坐标，缩小全程不变） */
let magnifyOrigin = {
  nx: 0.5,
  ny: 0.5,
  px: 0,
  py: 0,
  clientX: 0,
  clientY: 0,
};
const MAGNIFY_FACTOR = 2;
const MAGNIFY_ZOOM_IN_MS = 560;
const MAGNIFY_ZOOM_OUT_MS = 560;
let magnifyHiResReady = false;
let magnifyTransitionHandler = null;
let magnifyEndInProgress = false;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function magnifyContentSize() {
  return {
    w: pageWidth || basePageWidth || 1,
    h: pageHeight || basePageHeight || 1,
  };
}

/** 以按下点像素为 transform-origin，避免百分比在容器尺寸变化时偏移 */
function setMagnifyOrigin(nx, ny, contentW = null, contentH = null) {
  const { w, h } = magnifyContentSize();
  const bw = contentW ?? w;
  const bh = contentH ?? h;
  const ox = (nx ?? magnifyOrigin.nx) * bw;
  const oy = (ny ?? magnifyOrigin.ny) * bh;
  pageContainer.style.transformOrigin = `${ox}px ${oy}px`;
}

/** 缩小还原后，让按下点在屏幕上的位置尽量与按下时一致 */
function preserveMagnifyAnchorOnScreen() {
  if (!viewerWrap || !pageViewport || !basePageWidth) return;
  const pr = pageViewport.getBoundingClientRect();
  if (!pr.width || !pr.height) return;
  const sx = magnifyOrigin.nx * pr.width;
  const sy = magnifyOrigin.ny * pr.height;
  const dx = magnifyOrigin.clientX - (pr.left + sx);
  const dy = magnifyOrigin.clientY - (pr.top + sy);
  if (Math.abs(dx) > 0.5) {
    viewerWrap.scrollLeft = Math.max(0, viewerWrap.scrollLeft + dx);
  }
  if (Math.abs(dy) > 0.5) {
    viewerWrap.scrollTop = Math.max(0, viewerWrap.scrollTop + dy);
  }
}

function applyMagnifyPan(nx, ny, currentW, currentH) {
  if (!basePageWidth || !basePageHeight) return;
  const tx = -(nx * currentW - nx * basePageWidth);
  const ty = -(ny * currentH - ny * basePageHeight);
  pageContainer.style.transform = `translate(${tx}px, ${ty}px)`;
}

function resetMagnifyLayout() {
  clearMagnifyTransitionListener();
  pageContainer.style.transform = "";
  pageContainer.style.transformOrigin = "";
  pageContainer.classList.remove("page-magnify-smooth", "page-magnify-sharp");
  magnifyHiResReady = false;
  if (basePageWidth && basePageHeight) {
    pageViewport.style.width = `${basePageWidth}px`;
    pageViewport.style.height = `${basePageHeight}px`;
  }
}

function clearMagnifyTransitionListener() {
  if (magnifyTransitionHandler) {
    pageContainer.removeEventListener("transitionend", magnifyTransitionHandler);
    magnifyTransitionHandler = null;
  }
}

function waitTransformTransition(ms) {
  return new Promise((resolve) => {
    clearMagnifyTransitionListener();
    const done = (e) => {
      if (e.target !== pageContainer || e.propertyName !== "transform") return;
      clearMagnifyTransitionListener();
      resolve();
    };
    magnifyTransitionHandler = done;
    pageContainer.addEventListener("transitionend", done);
    setTimeout(() => {
      clearMagnifyTransitionListener();
      resolve();
    }, ms + 60);
  });
}

function getHiResPanTranslate() {
  if (!basePageWidth || !basePageHeight) return { tx: 0, ty: 0 };
  const tx = -(magnifyOrigin.nx * pageWidth - magnifyOrigin.nx * basePageWidth);
  const ty = -(magnifyOrigin.ny * pageHeight - magnifyOrigin.ny * basePageHeight);
  return { tx, ty };
}

/** 基准分辨率上 CSS 缩放（放大前半段 / 仅 CSS 放大后的缩小） */
async function runCssMagnify(targetScale) {
  const zoomIn = targetScale > 1;
  const fromScale = zoomIn ? 1 : MAGNIFY_FACTOR;
  const { w, h } = magnifyContentSize();
  pageContainer.classList.remove("page-magnify-sharp");
  pageContainer.classList.add("page-magnify-smooth");
  setMagnifyOrigin(magnifyOrigin.nx, magnifyOrigin.ny, w, h);
  pageContainer.style.transform = `scale(${fromScale})`;
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  pageContainer.style.transform = `scale(${targetScale})`;
  await waitTransformTransition(zoomIn ? MAGNIFY_ZOOM_IN_MS : MAGNIFY_ZOOM_OUT_MS);
}

/** 高清态丝滑缩小：保持平移不变、仅缩放，避免 translate 归零导致页面左偏裁切 */
async function runCssMagnifyOutFromHiRes() {
  const { w, h } = magnifyContentSize();
  const ox = magnifyOrigin.nx * w;
  const oy = magnifyOrigin.ny * h;
  const { tx, ty } = getHiResPanTranslate();
  const inv = 1 / MAGNIFY_FACTOR;
  pageContainer.classList.remove("page-magnify-sharp");
  pageContainer.classList.add("page-magnify-smooth");
  setMagnifyOrigin(magnifyOrigin.nx, magnifyOrigin.ny, w, h);
  pageContainer.style.transform = `translate(${tx}px, ${ty}px) scale(1)`;
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  const txEnd = tx + ox * (1 - inv);
  const tyEnd = ty + oy * (1 - inv);
  pageContainer.style.transform = `translate(${txEnd}px, ${tyEnd}px) scale(${inv})`;
  await waitTransformTransition(MAGNIFY_ZOOM_OUT_MS);
}

/** 将屏幕坐标映射到与 canvas 像素一致的页面坐标（修复 CSS 缩放导致的笔触偏移） */
function getPageCoords(clientX, clientY) {
  const el = pageWidth > 0 ? inkCanvas : canvas;
  const rect = el.getBoundingClientRect();
  const w = el.width || pageWidth || 1;
  const h = el.height || pageHeight || 1;
  if (!rect.width || !rect.height) {
    return { px: 0, py: 0, nx: 0, ny: 0 };
  }
  const px = ((clientX - rect.left) * w) / rect.width;
  const py = ((clientY - rect.top) * h) / rect.height;
  return {
    px: Math.max(0, Math.min(px, w)),
    py: Math.max(0, Math.min(py, h)),
    nx: px / w,
    ny: py / h,
  };
}

function normPoint(clientX, clientY) {
  const { nx, ny } = getPageCoords(clientX, clientY);
  return { x: nx, y: ny };
}

function inkStorageKey() {
  return `topdf-preview-ink:${lastPdfToken || "default"}`;
}

function loadInkStore() {
  try {
    const raw = sessionStorage.getItem(inkStorageKey());
    inkByPage = raw ? JSON.parse(raw) : {};
  } catch (_) {
    inkByPage = {};
  }
}

function saveInkStore() {
  try {
    sessionStorage.setItem(inkStorageKey(), JSON.stringify(inkByPage));
  } catch (_) {}
}

function getPageStrokes(pageIndex) {
  const key = String(pageIndex);
  if (!inkByPage[key]) inkByPage[key] = [];
  return inkByPage[key];
}

function denormPoint(p) {
  const nx = p.nx ?? p.x ?? 0;
  const ny = p.ny ?? p.y ?? 0;
  return { x: nx * pageWidth, y: ny * pageHeight };
}

function setTool(tool) {
  currentTool = tool;
  document.querySelectorAll(".tool-item[data-tool]").forEach((btn) => {
    const t = btn.dataset.tool;
    btn.classList.toggle("active", t === tool && t !== "clear");
  });
  viewerWrap.className = "";
  inkCanvas.classList.remove("interactive");
  if (tool === "laser") viewerWrap.classList.add("mode-laser");
  if (tool === "pen") viewerWrap.classList.add("mode-pen");
  if (tool === "highlighter") viewerWrap.classList.add("mode-highlighter");
  if (tool === "eraser") viewerWrap.classList.add("mode-eraser");
  if (tool === "pen" || tool === "highlighter" || tool === "eraser") {
    inkCanvas.classList.add("interactive");
  }
  const hints = {
    pointer: "指针：按住丝滑放大，松开丝滑缩小还原",
    laser: "激光笔：柔和渐变拖尾，松开后较快淡出",
    pen: "笔：在页面上手绘，墨迹会保留",
    highlighter: "荧光笔：平滑宽笔触（自动补点）",
    eraser: "橡皮擦：拖动擦除墨迹",
  };
  statusEl.textContent = hints[tool] || statusEl.textContent;
}

async function startMagnify(clientX, clientY) {
  if (magnifyAnimating || !pdfDoc) return;
  magnifyAnimating = true;
  const coords = getPageCoords(clientX, clientY);
  magnifyOrigin = {
    nx: coords.nx,
    ny: coords.ny,
    px: coords.px,
    py: coords.py,
    clientX,
    clientY,
  };
  magnifyActive = true;
  magnifyHiResReady = false;

  if (viewportScale > BASE_VIEWPORT_SCALE * 1.02) {
    await renderPage(currentPage, { clearActive: false, scale: BASE_VIEWPORT_SCALE });
  }

  setMagnifyOrigin(magnifyOrigin.nx, magnifyOrigin.ny, basePageWidth, basePageHeight);
  await runCssMagnify(MAGNIFY_FACTOR);

  if (!magnifyActive) {
    magnifyAnimating = false;
    pageContainer.classList.remove("page-magnify-smooth");
    pageContainer.style.transform = "";
    return;
  }

  pageContainer.classList.remove("page-magnify-smooth");
  pageContainer.classList.add("page-magnify-sharp");
  pageContainer.style.transform = "scale(1)";
  await renderPage(currentPage, {
    clearActive: false,
    scale: BASE_VIEWPORT_SCALE * MAGNIFY_FACTOR,
    panOrigin: magnifyOrigin,
  });
  magnifyHiResReady = true;
  magnifyAnimating = false;
}

async function endMagnify() {
  if (!magnifyActive && !magnifyAnimating && !magnifyHiResReady) return;
  if (magnifyEndInProgress) return;
  magnifyEndInProgress = true;
  magnifyActive = false;

  try {
    if (magnifyAnimating) {
      clearMagnifyTransitionListener();
      pageContainer.classList.remove("page-magnify-smooth");
      try {
        if (magnifyHiResReady) {
          await runCssMagnifyOutFromHiRes();
        } else {
          await runCssMagnify(1);
        }
      } catch (_) {
        pageContainer.style.transform = "";
      }
      magnifyAnimating = false;
      magnifyHiResReady = false;
      await renderPage(currentPage, {
        clearActive: false,
        scale: BASE_VIEWPORT_SCALE,
        panOrigin: magnifyOrigin,
      });
      resetMagnifyLayout();
      preserveMagnifyAnchorOnScreen();
      return;
    }

    magnifyAnimating = true;
    try {
      if (magnifyHiResReady) {
        await runCssMagnifyOutFromHiRes();
        magnifyHiResReady = false;
        await renderPage(currentPage, {
          clearActive: false,
          scale: BASE_VIEWPORT_SCALE,
          panOrigin: magnifyOrigin,
        });
      } else if (viewportScale <= BASE_VIEWPORT_SCALE * 1.02) {
        await runCssMagnify(1);
      } else {
        setMagnifyOrigin(
          magnifyOrigin.nx,
          magnifyOrigin.ny,
          basePageWidth,
          basePageHeight,
        );
        pageContainer.classList.add("page-magnify-smooth");
        pageContainer.style.transform = `scale(${MAGNIFY_FACTOR})`;
        await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
        await runCssMagnify(1);
        await renderPage(currentPage, {
          clearActive: false,
          scale: BASE_VIEWPORT_SCALE,
          panOrigin: magnifyOrigin,
        });
      }
    } finally {
      resetMagnifyLayout();
      preserveMagnifyAnchorOnScreen();
      magnifyAnimating = false;
    }
  } finally {
    magnifyEndInProgress = false;
  }
}

function pushInkPoint(stroke, nx, ny) {
  const pts = stroke.points;
  const last = pts[pts.length - 1];
  if (!last) {
    pts.push({ x: nx, y: ny });
    return;
  }
  const dx = nx - last.x;
  const dy = ny - last.y;
  const distPx = Math.hypot(dx * pageWidth, dy * pageHeight);
  if (distPx < 0.4) return;
  if (distPx > INK_SAMPLE_PX) {
    const n = Math.ceil(distPx / INK_SAMPLE_PX);
    for (let i = 1; i <= n; i++) {
      const t = i / n;
      pts.push({ x: last.x + dx * t, y: last.y + dy * t });
    }
  } else {
    pts.push({ x: nx, y: ny });
  }
}

function drawSmoothStroke(stroke, context) {
  const pts = stroke.points;
  if (!pts || pts.length < 2) return;
  const c = context || inkCtx;
  const pixelPts = pts.map((p) => denormPoint(p));

  c.save();
  c.lineCap = "round";
  c.lineJoin = "round";
  c.strokeStyle = stroke.color;
  const isHi = stroke.tool === "highlighter";
  c.globalAlpha = isHi ? 0.42 : 1;
  c.lineWidth = stroke.width;
  if (isHi) {
    c.shadowColor = stroke.color;
    c.shadowBlur = Math.max(6, stroke.width * 0.25);
  }

  if (pixelPts.length === 2) {
    c.beginPath();
    c.moveTo(pixelPts[0].x, pixelPts[0].y);
    c.lineTo(pixelPts[1].x, pixelPts[1].y);
    c.stroke();
    c.restore();
    return;
  }

  c.beginPath();
  c.moveTo(pixelPts[0].x, pixelPts[0].y);
  for (let i = 1; i < pixelPts.length - 1; i++) {
    const xc = (pixelPts[i].x + pixelPts[i + 1].x) * 0.5;
    const yc = (pixelPts[i].y + pixelPts[i + 1].y) * 0.5;
    c.quadraticCurveTo(pixelPts[i].x, pixelPts[i].y, xc, yc);
  }
  const end = pixelPts[pixelPts.length - 1];
  const prev = pixelPts[pixelPts.length - 2];
  c.quadraticCurveTo(prev.x, prev.y, end.x, end.y);
  c.stroke();
  c.restore();
}

function redrawInk() {
  inkCtx.clearRect(0, 0, pageWidth, pageHeight);
  getPageStrokes(currentPage).forEach((s) => drawSmoothStroke(s, inkCtx));
}

function stopInkDrawLoop() {
  if (inkDrawAnimId) {
    cancelAnimationFrame(inkDrawAnimId);
    inkDrawAnimId = null;
  }
  lastInkPointer = null;
}

function startInkDrawLoop() {
  if (inkDrawAnimId) return;
  const tick = () => {
    if (!isDrawing || !currentStroke) {
      stopInkDrawLoop();
      return;
    }
    if (lastInkPointer) {
      pushInkPoint(currentStroke, lastInkPointer.nx, lastInkPointer.ny);
    }
    redrawInk();
    drawSmoothStroke(currentStroke, inkCtx);
    inkDrawAnimId = requestAnimationFrame(tick);
  };
  inkDrawAnimId = requestAnimationFrame(tick);
}

function strokeWidthForTool(tool) {
  if (tool === "highlighter") return Math.max(14, pageWidth * 0.018);
  if (tool === "eraser") return Math.max(18, pageWidth * 0.022);
  return Math.max(3, pageWidth * 0.004);
}

function eraseAt(nx, ny) {
  const radius = 0.025;
  const strokes = getPageStrokes(currentPage);
  for (let i = strokes.length - 1; i >= 0; i--) {
    const stroke = strokes[i];
    const hit = stroke.points.some(
      (p) => Math.hypot(p.x - nx, p.y - ny) < radius
    );
    if (hit) strokes.splice(i, 1);
  }
  saveInkStore();
  redrawInk();
}

function clearPageInk() {
  inkByPage[String(currentPage)] = [];
  saveInkStore();
  redrawInk();
}

function pushLaserPoint(x, y) {
  const now = Date.now();
  const last = laserTrail[laserTrail.length - 1];
  if (last) {
    const dx = x - last.x;
    const dy = y - last.y;
    const dist = Math.hypot(dx, dy);
    if (dist < 0.5) return;
    if (dist > LASER_SAMPLE_STEP) {
      const n = Math.ceil(dist / LASER_SAMPLE_STEP);
      for (let i = 1; i <= n; i++) {
        const t = i / n;
        laserTrail.push({
          x: last.x + dx * t,
          y: last.y + dy * t,
          t: now,
        });
      }
    } else {
      laserTrail.push({ x, y, t: now });
    }
  } else {
    laserTrail.push({ x, y, t: now });
  }
  laserTrail = laserTrail.filter((p) => now - p.t < LASER_MAX_AGE);
  if (laserTrail.length > LASER_TRAIL_MAX_POINTS) {
    laserTrail = laserTrail.slice(-LASER_TRAIL_MAX_POINTS);
  }
}

/** 0=最旧 … 1=最新，平滑缓动避免色带 */
function laserFadeT(t) {
  const x = Math.max(0, Math.min(1, t));
  return x * x * (3 - 2 * x);
}

/** 按点龄淡出：略陡于 laserFadeT，收尾尾迹更快消失 */
function laserAgeFade(remaining) {
  return Math.pow(laserFadeT(remaining), 1.45);
}

function drawLaserSmoothPath(ctx, points) {
  if (points.length < 2) return;
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length - 1; i++) {
    const xc = (points[i].x + points[i + 1].x) * 0.5;
    const yc = (points[i].y + points[i + 1].y) * 0.5;
    ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
  }
  const end = points[points.length - 1];
  const prev = points[points.length - 2];
  ctx.quadraticCurveTo(prev.x, prev.y, end.x, end.y);
  ctx.stroke();
}

/** 按时间与位置连续插值透明度、线宽（无分层色带） */
function drawLaserGradientTrail(ctx, points, now) {
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  const n = points.length;
  const tail = points[0];
  const head = points[n - 1];

  for (let i = 1; i < n; i++) {
    const a = points[i - 1];
    const b = points[i];
    const dist = Math.hypot(b.x - a.x, b.y - a.y);
    const sub = Math.max(1, Math.ceil(dist / 2));
    for (let j = 1; j <= sub; j++) {
      const u1 = j / sub;
      const u0 = (j - 1) / sub;
      const x0 = a.x + (b.x - a.x) * u0;
      const y0 = a.y + (b.y - a.y) * u0;
      const x1 = a.x + (b.x - a.x) * u1;
      const y1 = a.y + (b.y - a.y) * u1;
      const timeAt = a.t + (b.t - a.t) * u1;
      const ageFade = laserAgeFade(1 - (now - timeAt) / LASER_MAX_AGE);
      const posT = (i - 1 + u1) / Math.max(1, n - 1);
      const posFade = laserFadeT(posT);
      const fade = ageFade * 0.55 + posFade * 0.45;
      if (fade < 0.012) continue;
      const alpha = 0.04 + fade * 0.46;
      const w = 0.5 + fade * 4.5;
      ctx.beginPath();
      ctx.moveTo(x0, y0);
      ctx.lineTo(x1, y1);
      ctx.strokeStyle = `rgba(239, 68, 68, ${alpha})`;
      ctx.lineWidth = w;
      ctx.stroke();
    }
  }

  if (n >= 2) {
    const headFade = laserAgeFade(1 - (now - head.t) / LASER_MAX_AGE);
    const g = ctx.createRadialGradient(
      head.x,
      head.y,
      0,
      head.x,
      head.y,
      10,
    );
    g.addColorStop(0, `rgba(239, 68, 68, ${0.35 + headFade * 0.45})`);
    g.addColorStop(0.35, `rgba(239, 68, 68, ${0.12 + headFade * 0.2})`);
    g.addColorStop(1, "rgba(239, 68, 68, 0)");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(head.x, head.y, 10, 0, Math.PI * 2);
    ctx.fill();
  }

  void tail;
}

function drawLaserFrame() {
  if (currentTool !== "laser") {
    stopLaserAnim();
    return;
  }
  if (lastLaserPos) {
    pushLaserPoint(lastLaserPos.px, lastLaserPos.py);
  }

  laserCtx.clearRect(0, 0, pageWidth, pageHeight);
  const now = Date.now();
  laserTrail = laserTrail.filter((p) => now - p.t < LASER_MAX_AGE);
  if (laserTrail.length > LASER_TRAIL_MAX_POINTS) {
    laserTrail = laserTrail.slice(-LASER_TRAIL_MAX_POINTS);
  }

  if (laserTrail.length < 2) {
    if (laserTrail.length === 1) {
      const p = laserTrail[0];
      const g = laserCtx.createRadialGradient(p.x, p.y, 0, p.x, p.y, 8);
      g.addColorStop(0, "rgba(239, 68, 68, 0.85)");
      g.addColorStop(1, "rgba(239, 68, 68, 0)");
      laserCtx.fillStyle = g;
      laserCtx.beginPath();
      laserCtx.arc(p.x, p.y, 8, 0, Math.PI * 2);
      laserCtx.fill();
    }
    laserAnimId = requestAnimationFrame(drawLaserFrame);
    return;
  }

  laserCtx.save();
  laserCtx.globalCompositeOperation = "lighter";
  laserCtx.shadowColor = "rgba(239, 68, 68, 0.35)";
  laserCtx.shadowBlur = 10;
  laserCtx.strokeStyle = "rgba(239, 68, 68, 0.1)";
  laserCtx.lineWidth = 9;
  drawLaserSmoothPath(laserCtx, laserTrail);
  laserCtx.shadowBlur = 0;
  drawLaserGradientTrail(laserCtx, laserTrail, now);
  laserCtx.restore();

  laserAnimId = requestAnimationFrame(drawLaserFrame);
}

function stopLaserAnim() {
  if (laserAnimId) {
    cancelAnimationFrame(laserAnimId);
    laserAnimId = null;
  }
  laserCtx.clearRect(0, 0, pageWidth, pageHeight);
  laserTrail = [];
  lastLaserPos = null;
}

function resizeOverlayLayers(w, h) {
  pageWidth = w;
  pageHeight = h;
  canvas.style.width = `${w}px`;
  canvas.style.height = `${h}px`;
  [inkCanvas, laserCanvas].forEach((c) => {
    c.width = w;
    c.height = h;
    c.style.width = `${w}px`;
    c.style.height = `${h}px`;
  });
  focusLayer.style.width = `${w}px`;
  focusLayer.style.height = `${h}px`;
  layer.style.width = `${w}px`;
  layer.style.height = `${h}px`;
}

function initToolsUi() {
  const palette = document.getElementById("color-palette");
  INK_COLORS.forEach((color) => {
    const sw = document.createElement("button");
    sw.type = "button";
    sw.className = "color-swatch";
    sw.dataset.color = color;
    sw.style.background = color;
    sw.title = color;
    if (color === currentColor) sw.classList.add("selected");
    sw.addEventListener("click", () => {
      currentColor = color;
      palette.querySelectorAll(".color-swatch").forEach((el) => {
        el.classList.toggle("selected", el.dataset.color === color);
      });
    });
    palette.appendChild(sw);
  });

  document.getElementById("btn-tools").addEventListener("click", () => {
    toolsPanel.classList.toggle("hidden");
    document.getElementById("btn-tools").classList.toggle("active");
  });

  document.querySelectorAll(".tool-item[data-tool]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tool = btn.dataset.tool;
      if (tool === "clear") {
        if (confirm("清除当前页所有手绘墨迹？")) clearPageInk();
        return;
      }
      setTool(tool);
      if (tool === "laser") {
        if (!laserAnimId) drawLaserFrame();
      } else {
        stopLaserAnim();
      }
    });
  });

  pageContainer.addEventListener("pointerdown", (e) => {
    if (currentTool !== "pointer") return;
    if (e.target.closest(".annot-marker")) return;
    if (e.button !== 0) return;
    startMagnify(e.clientX, e.clientY);
    try {
      pageContainer.setPointerCapture(e.pointerId);
    } catch (_) {}
  });

  const onMagnifyEnd = (e) => {
    void endMagnify();
    try {
      if (e && e.pointerId != null) pageContainer.releasePointerCapture(e.pointerId);
    } catch (_) {}
  };

  pageContainer.addEventListener("pointerup", onMagnifyEnd);
  pageContainer.addEventListener("pointercancel", onMagnifyEnd);
  document.addEventListener("pointerup", () => {
    if (magnifyActive || magnifyAnimating || magnifyHiResReady) {
      void endMagnify();
    }
  });

  pageContainer.addEventListener("pointermove", (e) => {
    if (currentTool !== "laser") return;
    lastLaserPos = getPageCoords(e.clientX, e.clientY);
  });

  pageContainer.addEventListener("pointerleave", () => {
    if (currentTool === "laser") lastLaserPos = null;
  });

  inkCanvas.addEventListener("pointerdown", (e) => {
    if (currentTool !== "pen" && currentTool !== "highlighter" && currentTool !== "eraser") {
      return;
    }
    e.preventDefault();
    inkCanvas.setPointerCapture(e.pointerId);
    const coords = getPageCoords(e.clientX, e.clientY);
    if (currentTool === "eraser") {
      isDrawing = true;
      eraseAt(coords.nx, coords.ny);
      return;
    }
    isDrawing = true;
    currentStroke = {
      tool: currentTool,
      color: currentColor,
      width: strokeWidthForTool(currentTool),
      points: [{ x: coords.nx, y: coords.ny }],
    };
    lastInkPointer = coords;
    startInkDrawLoop();
  });

  inkCanvas.addEventListener("pointermove", (e) => {
    if (!isDrawing) return;
    const coords = getPageCoords(e.clientX, e.clientY);
    if (currentTool === "eraser") {
      eraseAt(coords.nx, coords.ny);
      return;
    }
    if (!currentStroke) return;
    lastInkPointer = coords;
  });

  const endStroke = (e) => {
    if (isDrawing && currentStroke && e) {
      const coords = getPageCoords(e.clientX, e.clientY);
      pushInkPoint(currentStroke, coords.nx, coords.ny);
    }
    stopInkDrawLoop();
    if (!isDrawing) return;
    isDrawing = false;
    if (currentStroke && currentStroke.points.length > 1) {
      getPageStrokes(currentPage).push(currentStroke);
      saveInkStore();
    }
    currentStroke = null;
    redrawInk();
  };

  inkCanvas.addEventListener("pointerup", endStroke);
  inkCanvas.addEventListener("pointercancel", endStroke);

  setTool("pointer");
}

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

const ANNOT_MARKER_SIZE = 24;
const ANNOT_POPUP_GAP = 30;
const ANNOT_POPUP_EDGE = 4;

/** 批注弹层在页面坐标内翻转/钳位，避免靠边时被 viewport 裁切 */
function layoutAnnotPopup(markerEl, popupEl, item) {
  const pageW = pageWidth || basePageWidth || 1;
  const pageH = pageHeight || basePageHeight || 1;
  const mx = Number(item.x) * viewportScale;
  const my = Number(item.y) * viewportScale;

  const prevDisplay = popupEl.style.display;
  popupEl.style.visibility = "hidden";
  popupEl.style.display = "block";
  const pw = popupEl.offsetWidth || 280;
  const ph = popupEl.offsetHeight || 120;
  popupEl.style.display = prevDisplay || "";
  popupEl.style.visibility = "";

  let px = mx + ANNOT_MARKER_SIZE + ANNOT_POPUP_GAP;
  if (px + pw > pageW - ANNOT_POPUP_EDGE) {
    px = mx - ANNOT_POPUP_GAP - pw;
  }
  px = Math.max(
    ANNOT_POPUP_EDGE,
    Math.min(px, pageW - pw - ANNOT_POPUP_EDGE),
  );

  let py = my;
  if (py + ph > pageH - ANNOT_POPUP_EDGE) {
    py = pageH - ph - ANNOT_POPUP_EDGE;
  }
  py = Math.max(
    ANNOT_POPUP_EDGE,
    Math.min(py, pageH - ph - ANNOT_POPUP_EDGE),
  );

  popupEl.style.left = `${px - mx}px`;
  popupEl.style.top = `${py - my}px`;
  popupEl.style.right = "auto";
  popupEl.style.bottom = "auto";
}

function scheduleAnnotPopupLayout(markerEl, popupEl, item) {
  requestAnimationFrame(() => {
    if (!markerEl.isConnected || !markerEl.classList.contains("active")) return;
    layoutAnnotPopup(markerEl, popupEl, item);
  });
}

function renderMarkers(pageIndex, restoreIndex = null) {
  const keepIndex = restoreIndex ?? activeMarkerIndex;
  clearLayer();

  const items = annotationsByPage[String(pageIndex)] || [];
  items.forEach((item) => {
    const marker = document.createElement("div");
    marker.className = "annot-marker";
    marker.dataset.index = String(item.index);
    marker.style.borderColor = item.color || "#7c3aed";
    marker.style.left = `${item.x * viewportScale}px`;
    marker.style.top = `${item.y * viewportScale}px`;
    marker.textContent = item.index;

    const popup = document.createElement("div");
    popup.className = "annot-popup";
    popup.style.borderColor = item.color || "#7c3aed";

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
      if (currentTool !== "pointer") return;
      if (activeMarker && activeMarker !== marker) {
        activeMarker.classList.remove("active");
      }
      marker.classList.toggle("active");
      if (marker.classList.contains("active")) {
        activeMarker = marker;
        activeMarkerIndex = item.index;
        scheduleAnnotPopupLayout(marker, popup, item);
      } else {
        activeMarker = null;
        activeMarkerIndex = null;
      }
    });

    if (keepIndex === item.index) {
      marker.classList.add("active");
      activeMarker = marker;
      activeMarkerIndex = item.index;
      scheduleAnnotPopupLayout(marker, popup, item);
    }

    layer.appendChild(marker);
  });

  if (keepIndex != null && !items.some((item) => item.index === keepIndex)) {
    activeMarkerIndex = null;
    activeMarker = null;
  }
}

async function renderPage(
  pageNum,
  { clearActive = true, scale = null, panOrigin = null } = {},
) {
  if (!pdfDoc) return;
  if (renderTask) {
    try {
      await renderTask.cancel();
    } catch (_) {}
  }

  if (clearActive && pageNum !== currentPage) {
    activeMarkerIndex = null;
    magnifyActive = false;
    resetMagnifyLayout();
  }

  currentPage = pageNum;
  const effectiveScale = scale != null ? scale : BASE_VIEWPORT_SCALE;
  viewportScale = effectiveScale;

  const page = await pdfDoc.getPage(pageNum + 1);
  const viewport = page.getViewport({ scale: effectiveScale });

  canvas.width = viewport.width;
  canvas.height = viewport.height;
  resizeOverlayLayers(viewport.width, viewport.height);

  ctx.imageSmoothingEnabled = true;
  if ("imageSmoothingQuality" in ctx) {
    ctx.imageSmoothingQuality = "high";
  }

  renderTask = page.render({ canvasContext: ctx, viewport });
  await renderTask.promise;

  if (effectiveScale === BASE_VIEWPORT_SCALE) {
    basePageWidth = viewport.width;
    basePageHeight = viewport.height;
    pageWidth = viewport.width;
    pageHeight = viewport.height;
    pageViewport.style.width = `${basePageWidth}px`;
    pageViewport.style.height = `${basePageHeight}px`;
    if (panOrigin) {
      applyMagnifyPan(panOrigin.nx, panOrigin.ny, viewport.width, viewport.height);
    } else {
      pageContainer.style.transform = "";
    }
  } else if (panOrigin) {
    pageViewport.style.width = `${basePageWidth}px`;
    pageViewport.style.height = `${basePageHeight}px`;
    applyMagnifyPan(panOrigin.nx, panOrigin.ny, viewport.width, viewport.height);
    setMagnifyOrigin(panOrigin.nx, panOrigin.ny, viewport.width, viewport.height);
  }

  renderMarkers(pageNum, clearActive ? null : activeMarkerIndex);
  redrawInk();
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

    const newToken = state.pdf_token || "";
    const pdfTokenChanged = newToken && newToken !== lastPdfToken;
    if (pdfTokenChanged) {
      pdfDoc = null;
      activeMarkerIndex = null;
      lastPdfToken = newToken;
      loadInkStore();
    } else if (newToken) {
      lastPdfToken = newToken;
    }

    if (!pdfDoc && state.pdf_available) {
      await loadPdf();
      totalPages = pdfDoc.numPages;
      if (newToken && !pdfTokenChanged) loadInkStore();
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

    if (currentTool === "pointer") {
      statusEl.textContent = "指针：按住丝滑放大，松开丝滑缩小；可切换激光笔/绘图";
    }
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

viewerWrap.addEventListener("click", (e) => {
  if (e.target.closest(".annot-marker")) return;
  if (e.target.closest("#tools-panel")) return;
  closeActiveMarker();
});

initToolsUi();
refresh(true);
setInterval(() => refresh(false), 2000);
