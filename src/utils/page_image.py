"""PDF 页面转图片工具"""
import base64
import io
from typing import Tuple

import fitz
from PIL import Image


def render_page_to_image(
    pdf_path: str,
    page_number: int,
    dpi: int = 150,
) -> Tuple[bytes, str, float, float]:
    """
    将 PDF 单页渲染为 PNG 图片

    Returns:
        (png_bytes, base64_str, page_width, page_height)
    """
    doc = fitz.open(pdf_path)
    try:
        page = doc[page_number]
        page_width = page.rect.width
        page_height = page.rect.height

        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        png_bytes = pix.tobytes("png")
        b64_str = base64.b64encode(png_bytes).decode("utf-8")
        return png_bytes, b64_str, page_width, page_height
    finally:
        doc.close()


def render_page_from_doc(
    pdf_doc: fitz.Document,
    page_number: int,
    dpi: int = 150,
) -> Tuple[bytes, str, float, float]:
    """从已打开的 PDF 文档渲染单页"""
    page = pdf_doc[page_number]
    page_width = page.rect.width
    page_height = page.rect.height

    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)

    png_bytes = pix.tobytes("png")
    b64_str = base64.b64encode(png_bytes).decode("utf-8")
    return png_bytes, b64_str, page_width, page_height


def save_page_image_temp(
    pdf_path: str,
    page_number: int,
    output_dir: str,
    dpi: int = 150,
) -> str:
    """保存页面图片到临时目录，返回文件路径"""
    import os

    os.makedirs(output_dir, exist_ok=True)
    png_bytes, _, _, _ = render_page_to_image(pdf_path, page_number, dpi)
    output_path = os.path.join(output_dir, f"page_{page_number + 1}.png")
    with open(output_path, "wb") as f:
        f.write(png_bytes)
    return output_path
