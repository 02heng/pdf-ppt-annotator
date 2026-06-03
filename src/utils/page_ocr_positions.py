"""从 PDF 页面图片中 OCR 提取带坐标的文字块（图表、扫描页）。"""
from __future__ import annotations

import base64
import io
import json
import os
import re
import tempfile
from collections import defaultdict
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import fitz

from src.utils.block_font_size import font_size_from_line_height

if TYPE_CHECKING:
    from src.models.config import LLMConfig

OCR_DPI = 280
MIN_BLOCK_CHARS = 2
MIN_OCR_BLOCKS_TARGET = 12
VISION_OCR_MIN_BLOCKS = 15
TEXT_PARAGRAPHS_SKIP_IMAGE_OCR = 5

VISION_OCR_BLOCKS_PROMPT = """你是 OCR 引擎。识别图中每一处可见英文/中文文字（含图表标题、坐标轴标签、图例、流程框内文字、箭头旁说明）。
务必识别图表主体区域内的所有词组，不要只识别页眉标题。

【分行规则 — 必须遵守】
1. 画面上独立的一行文字 = JSON 数组中的一个块，不要合并。
2. 编号列表、项目符号列表：每一项单独一块（如「1. Welcome」「2. Introduction」各一项）。
3. 仅当多行在视觉上属于同一段落（自动换行、句子被折行）时，才可合并为一个块；合并时 text 内用换行符 \\n 保留行结构。
4. 不要把目录、列表、多行要点压成一段长文。

返回 JSON 数组，每项：
{"text":"原文","x":0.12,"y":0.34,"width":0.08,"height":0.02}
x,y,width,height 为相对整图宽高的比例（0~1，左上为原点）。不要 Markdown，只输出 JSON 数组。"""


def _scale_blocks_to_pdf(
    blocks: List[Dict[str, Any]],
    img_w: float,
    img_h: float,
    page_w: float,
    page_h: float,
) -> List[Dict[str, Any]]:
    if img_w <= 0 or img_h <= 0:
        return []
    sx = page_w / img_w
    sy = page_h / img_h
    out: List[Dict[str, Any]] = []
    for b in blocks:
        text = (b.get("text") or "").strip()
        if len(text) < MIN_BLOCK_CHARS:
            continue
        x = float(b.get("x", 0)) * sx
        y = float(b.get("y", 0)) * sy
        w = max(float(b.get("width", 0)) * sx, 8)
        h = max(float(b.get("height", 0)) * sy, 8)
        out.append(
            {
                "text": text,
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "font_size": font_size_from_line_height(h),
            }
        )
    return out


def _blocks_from_liteparse_image(png_bytes: bytes, page_w: float, page_h: float) -> List[Dict[str, Any]]:
    try:
        from liteparse import LiteParse
    except ImportError:
        return []

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(png_bytes)
        tmp_path = tmp.name

    try:
        parser = LiteParse(ocr_enabled=True)
        result = parser.parse(tmp_path)
        if not result.pages:
            return []
        page_data = result.pages[0]
        img_w = float(getattr(page_data, "width", 0) or page_w)
        img_h = float(getattr(page_data, "height", 0) or page_h)
        raw: List[Dict[str, Any]] = []
        for item in getattr(page_data, "text_items", None) or []:
            text = (getattr(item, "text", "") or "").strip()
            if not text:
                continue
            raw.append(
                {
                    "text": text,
                    "x": float(getattr(item, "x", 0)),
                    "y": float(getattr(item, "y", 0)),
                    "width": float(getattr(item, "width", 0) or 8),
                    "height": float(getattr(item, "height", 0) or 8),
                }
            )
        return _scale_blocks_to_pdf(raw, img_w, img_h, page_w, page_h)
    except Exception:
        return []
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _group_tesseract_lines(data: dict, img_w: float, img_h: float) -> List[Dict[str, Any]]:
    """将 Tesseract 词级结果按行合并为文本块。"""
    lines: Dict[tuple, List[dict]] = defaultdict(list)
    n = len(data.get("text", []))
    for i in range(n):
        text = (data["text"][i] or "").strip()
        if not text:
            continue
        try:
            conf = int(float(data["conf"][i]))
        except (ValueError, TypeError):
            conf = -1
        if conf < 15:
            continue
        key = (
            int(data.get("block_num", [0])[i]),
            int(data.get("par_num", [0])[i]),
            int(data.get("line_num", [0])[i]),
        )
        lines[key].append(
            {
                "text": text,
                "left": float(data["left"][i]),
                "top": float(data["top"][i]),
                "width": float(data["width"][i]),
                "height": float(data["height"][i]),
            }
        )

    raw: List[Dict[str, Any]] = []
    for parts in lines.values():
        if not parts:
            continue
        parts.sort(key=lambda p: p["left"])
        text = " ".join(p["text"] for p in parts).strip()
        if len(text) < MIN_BLOCK_CHARS:
            continue
        x0 = min(p["left"] for p in parts)
        y0 = min(p["top"] for p in parts)
        x1 = max(p["left"] + p["width"] for p in parts)
        y1 = max(p["top"] + p["height"] for p in parts)
        raw.append(
            {
                "text": text,
                "x": x0,
                "y": y0,
                "width": max(x1 - x0, 8),
                "height": max(y1 - y0, 8),
            }
        )
    return raw


def _configure_tesseract_cmd() -> bool:
    """Windows 上尝试常见安装路径。"""
    try:
        import pytesseract
    except ImportError:
        return False
    cmd = getattr(pytesseract.pytesseract, "tesseract_cmd", None)
    if cmd and os.path.isfile(cmd):
        return True
    if os.name != "nt":
        return True
    for candidate in (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ):
        if os.path.isfile(candidate):
            pytesseract.pytesseract.tesseract_cmd = candidate
            return True
    return False


def _tesseract_usable() -> bool:
    try:
        import pytesseract

        _configure_tesseract_cmd()
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _vision_ocr_usable(llm_config: Optional["LLMConfig"]) -> bool:
    if not llm_config:
        return False
    provider = llm_config.provider
    if provider == "openai":
        return bool(llm_config.openai.api_key)
    if provider == "ollama":
        return bool(llm_config.ollama.base_url)
    if provider == "deepseek":
        return bool(llm_config.deepseek.api_key)
    if provider == "xiaomi":
        return bool(llm_config.xiaomi.api_key)
    return False


def _ocr_empty_status_hint(
    llm_config: Optional["LLMConfig"],
    *,
    text_layer_paragraphs: int = 0,
) -> str:
    if text_layer_paragraphs > 0:
        return (
            f"图内 OCR 未补充到文字，已使用页面文字层（{text_layer_paragraphs} 段）"
        )
    parts = ["本页图内 OCR 未识别到文字。"]
    if not _tesseract_usable():
        parts.append("可安装 Tesseract（含 eng/chi_sim 语言包）")
    if _vision_ocr_usable(llm_config):
        prov = getattr(llm_config, "provider", "")
        if prov == "xiaomi":
            parts.append("或确认小米 MiMo API Key 有效（识图请用 mimo-v2.5）")
        else:
            parts.append("或确认已配置 OpenAI/Ollama/小米 视觉模型")
    elif llm_config and llm_config.provider == "deepseek":
        parts.append("DeepSeek 文本接口不支持识图，请改用 OpenAI 或 Ollama 视觉")
    else:
        parts.append("或在「系统 API 设置」中配置带视觉的模型")
    return "；".join(parts)


def _blocks_from_tesseract(png_bytes: bytes, page_w: float, page_h: float) -> List[Dict[str, Any]]:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return []

    if not _configure_tesseract_cmd():
        return []

    try:
        image = Image.open(io.BytesIO(png_bytes))
        img_w, img_h = image.size
        for psm in (11, 6, 3):
            try:
                config = f"--psm {psm} --oem 3"
                data = pytesseract.image_to_data(
                    image,
                    lang="eng+chi_sim",
                    config=config,
                    output_type=pytesseract.Output.DICT,
                )
                raw = _group_tesseract_lines(data, img_w, img_h)
                blocks = _scale_blocks_to_pdf(raw, img_w, img_h, page_w, page_h)
                if len(blocks) >= MIN_OCR_BLOCKS_TARGET:
                    return blocks
            except Exception:
                continue
        data = pytesseract.image_to_data(
            image, lang="eng+chi_sim", output_type=pytesseract.Output.DICT
        )
        raw = _group_tesseract_lines(data, img_w, img_h)
        return _scale_blocks_to_pdf(raw, img_w, img_h, page_w, page_h)
    except Exception:
        return []


def _parse_vision_ocr_json(text: str, page_w: float, page_h: float) -> List[Dict[str, Any]]:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end <= start:
        return []
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        t = (item.get("text") or "").strip()
        if len(t) < MIN_BLOCK_CHARS:
            continue
        x = float(item.get("x", 0))
        y = float(item.get("y", 0))
        w = float(item.get("width", 0.05))
        h = float(item.get("height", 0.02))
        if w <= 1.5 and h <= 1.5:
            x, y, w, h = x * page_w, y * page_h, w * page_w, h * page_h
        out.append(
            {
                "text": t,
                "x": max(0, x),
                "y": max(0, y),
                "width": max(w, 8),
                "height": max(h, 8),
            }
        )
    return out


def _blocks_from_vision_llm(
    image_b64: str,
    page_w: float,
    page_h: float,
    llm_config: "LLMConfig",
) -> List[Dict[str, Any]]:
    try:
        from src.services.vision_annotation_service import VisionAnnotationService
    except ImportError:
        return []

    svc = VisionAnnotationService(llm_config)
    provider = llm_config.provider
    raw = ""
    try:
        if provider == "openai":
            raw = svc._call_openai_vision_multi([image_b64], VISION_OCR_BLOCKS_PROMPT)
        elif provider == "xiaomi":
            raw = svc._call_xiaomi_vision_multi([image_b64], VISION_OCR_BLOCKS_PROMPT)
        elif provider == "ollama":
            raw = svc._call_ollama_vision_multi([image_b64], VISION_OCR_BLOCKS_PROMPT)
        elif provider == "deepseek":
            try:
                raw = svc._call_openai_vision_multi([image_b64], VISION_OCR_BLOCKS_PROMPT)
            except Exception:
                raw = ""
    except Exception:
        return []

    return _parse_vision_ocr_json(raw, page_w, page_h)


def _ocr_region(
    page: fitz.Page,
    clip: fitz.Rect,
    page_w: float,
    page_h: float,
    zoom: float,
) -> List[Dict[str, Any]]:
    """对页面局部区域 OCR，坐标换算回整页 PDF 点。"""
    matrix = fitz.Matrix(zoom, zoom)
    try:
        pix = page.get_pixmap(matrix=matrix, clip=clip, alpha=False)
    except Exception:
        return []
    png_bytes = pix.tobytes("png")
    blocks = _blocks_from_liteparse_image(png_bytes, clip.width, clip.height)
    blocks = _merge_blocks(blocks, _blocks_from_tesseract(png_bytes, clip.width, clip.height))
    offset_x = clip.x0
    offset_y = clip.y0
    shifted: List[Dict[str, Any]] = []
    for b in blocks:
        shifted.append(
            {
                "text": b["text"],
                "x": float(b["x"]) + offset_x,
                "y": float(b["y"]) + offset_y,
                "width": b["width"],
                "height": b["height"],
            }
        )
    return shifted


def extract_page_ocr_blocks(
    page: fitz.Page,
    *,
    pdf_doc: Optional[fitz.Document] = None,
    page_num: int = 0,
    llm_config: Optional["LLMConfig"] = None,
    use_vision_fallback: bool = True,
) -> List[Dict[str, Any]]:
    """渲染当前页并 OCR（整页 + 下半区加强），返回 PDF 点坐标下的文字块。"""
    page_w = page.rect.width
    page_h = page.rect.height
    zoom = OCR_DPI / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    png_bytes = pix.tobytes("png")
    image_b64 = base64.b64encode(png_bytes).decode("utf-8")

    blocks = _blocks_from_liteparse_image(png_bytes, page_w, page_h)
    blocks = _merge_blocks(blocks, _blocks_from_tesseract(png_bytes, page_w, page_h))

    # 幻灯片常把正文放在页中下部（照片下方），对下半区再 OCR 一次
    bands = (
        (0.0, 0.0, 1.0, 0.38),
        (0.0, 0.32, 1.0, 0.72),
        (0.0, 0.52, 1.0, 1.0),
    )
    for x0r, y0r, x1r, y1r in bands:
        clip = fitz.Rect(
            page_w * x0r,
            page_h * y0r,
            page_w * x1r,
            page_h * y1r,
        )
        blocks = _merge_blocks(blocks, _ocr_region(page, clip, page_w, page_h, zoom))

    if use_vision_fallback and llm_config and len(blocks) < VISION_OCR_MIN_BLOCKS:
        vision_blocks = _blocks_from_vision_llm(image_b64, page_w, page_h, llm_config)
        blocks = _merge_blocks(blocks, vision_blocks)

    return blocks


def _merge_blocks(
    primary: List[Dict[str, Any]],
    extra: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if not extra:
        return list(primary)
    if not primary:
        return list(extra)
    return _dedupe_blocks(primary + extra)


def _dedupe_blocks(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    kept: List[Dict[str, Any]] = []
    seen: List[tuple] = []
    for b in blocks:
        text = (b.get("text") or "").strip()
        if len(text) < MIN_BLOCK_CHARS:
            continue
        cy = float(b["y"]) + float(b["height"]) / 2
        cx = float(b["x"]) + float(b["width"]) / 2
        key = (round(cx, 0), round(cy, 0), text[:48].lower())
        if key in seen:
            continue
        seen.append(key)
        kept.append(b)
    kept.sort(key=lambda b: (round(float(b["y"]), 1), float(b["x"])))
    return kept


def ensure_page_ocr_positions(
    app,
    page_num: int,
    llm_config: Optional["LLMConfig"] = None,
    *,
    force: bool = False,
    text_layer_paragraphs: int = 0,
) -> List[Dict[str, Any]]:
    """OCR 并缓存到 app.ocr_text_positions；force=True 时忽略旧缓存。"""
    if not getattr(app, "ocr_text_positions", None):
        app.ocr_text_positions = {}

    if not force and page_num in app.ocr_text_positions:
        cached = app.ocr_text_positions.get(page_num)
        if cached is not None:
            return cached

    if not app.pdf_doc or page_num < 0 or page_num >= app.total_pages:
        app.ocr_text_positions[page_num] = []
        return []

    if hasattr(app, "update_status"):
        app.update_status(f"第 {page_num + 1} 页：正在 OCR 识别图表/图片中的文字...")

    page = app.pdf_doc[page_num]
    blocks = extract_page_ocr_blocks(
        page,
        pdf_doc=app.pdf_doc,
        page_num=page_num,
        llm_config=llm_config,
        use_vision_fallback=bool(llm_config),
    )
    app.ocr_text_positions[page_num] = blocks
    if hasattr(app, "update_status"):
        if blocks:
            app.update_status(
                f"第 {page_num + 1} 页图内 OCR 完成，识别 {len(blocks)} 处文字"
            )
        elif text_layer_paragraphs >= TEXT_PARAGRAPHS_SKIP_IMAGE_OCR:
            pass
        else:
            app.update_status(
                f"第 {page_num + 1} 页："
                + _ocr_empty_status_hint(
                    llm_config, text_layer_paragraphs=text_layer_paragraphs
                )
            )
    return blocks


def clear_page_ocr_cache(app, page_num: Optional[int] = None) -> None:
    if not getattr(app, "ocr_text_positions", None):
        app.ocr_text_positions = {}
    if page_num is None:
        app.ocr_text_positions.clear()
    else:
        app.ocr_text_positions.pop(page_num, None)
