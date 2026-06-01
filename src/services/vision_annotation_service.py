"""基于页面图片的视觉批注服务"""
import base64
import uuid
from typing import List, Optional

import fitz
from openai import OpenAI

from src.models.annotation import Annotation
from src.models.config import LLMConfig
from src.utils.page_image import render_page_from_doc, render_page_to_image

ANNOTATION_PROMPT = """你是专业的学术文档批注助手。请仔细分析这张 PDF 页面图片（可能是幻灯片或文档页），用中文生成简洁、专业的批注。

要求：
1. 概括本页核心主题和关键信息
2. 解释出现的专业术语（如有）
3. 指出重点和可能的难点
4. 批注总字数控制在 200-400 字
5. 不要使用 Markdown 格式（不要 #、**、--- 等符号）
6. 直接输出批注正文，不要加"批注："等前缀"""


class VisionAnnotationService:
    """将 PDF 页面转为图片并调用模型生成批注"""

    def __init__(self, config: LLMConfig):
        self.config = config

    def annotate_page_from_pdf(
        self,
        pdf_path: str,
        page_number: int,
        pdf_doc: Optional[fitz.Document] = None,
    ) -> List[Annotation]:
        """从 PDF 页面生成批注"""
        if pdf_doc is not None:
            _, image_b64, width, height = render_page_from_doc(pdf_doc, page_number)
            page_text = pdf_doc[page_number].get_text()
        else:
            _, image_b64, width, height = render_page_to_image(pdf_path, page_number)
            with fitz.open(pdf_path) as doc:
                page_text = doc[page_number].get_text()

        content = self._call_vision_model(image_b64, page_text)

        return [
            Annotation(
                id=str(uuid.uuid4()),
                page_number=page_number,
                content=content,
                original_text=page_text[:500] if page_text else None,
                position_x=max(width - 170, 10),
                position_y=30,
                width=160,
                height=100,
                agent_role="vision",
            )
        ]

    def _call_vision_model(self, image_b64: str, page_text: str) -> str:
        provider = self.config.provider

        if provider == "openai":
            return self._call_openai_vision(image_b64)
        elif provider == "ollama":
            return self._call_ollama_vision(image_b64)
        elif provider == "deepseek":
            return self._call_deepseek_with_image(image_b64, page_text)
        else:
            raise ValueError(f"不支持的 LLM 提供商: {provider}")

    def _call_openai_vision(self, image_b64: str) -> str:
        cfg = self.config.openai
        client = OpenAI(api_key=cfg.api_key)

        response = client.chat.completions.create(
            model=cfg.model,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ANNOTATION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_b64}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content.strip()

    def _call_ollama_vision(self, image_b64: str) -> str:
        import json
        import urllib.request

        cfg = self.config.ollama
        url = f"{cfg.base_url.rstrip('/')}/api/chat"

        payload = {
            "model": cfg.model,
            "messages": [{"role": "user", "content": ANNOTATION_PROMPT}],
            "images": [image_b64],
            "stream": False,
            "options": {"temperature": cfg.temperature},
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        return result["message"]["content"].strip()

    def _call_deepseek_with_image(self, image_b64: str, page_text: str) -> str:
        """
        DeepSeek 文本模型不支持图片，将页面图片 OCR 文本与提取文本合并后分析。
        若配置了 OpenAI 兼容视觉模型则优先尝试图片输入。
        """
        cfg = self.config.deepseek
        client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)

        ocr_text = self._ocr_image(image_b64)
        combined_context = self._build_text_context(page_text, ocr_text)

        response = client.chat.completions.create(
            model=cfg.model,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"{ANNOTATION_PROMPT}\n\n"
                        f"以下是从该 PDF 页面提取的完整文字内容（含 OCR）：\n\n{combined_context}"
                    ),
                }
            ],
        )
        return response.choices[0].message.content.strip()

    def _ocr_image(self, image_b64: str) -> str:
        """对页面图片做 OCR 提取文字"""
        try:
            import io

            from PIL import Image

            image_bytes = base64.b64decode(image_b64)
            image = Image.open(io.BytesIO(image_bytes))

            try:
                import pytesseract

                return pytesseract.image_to_string(image, lang="chi_sim+eng").strip()
            except ImportError:
                pass

            try:
                from liteparse import LiteParse

                import tempfile
                import os

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(image_bytes)
                    tmp_path = tmp.name

                try:
                    parser = LiteParse(ocr_enabled=True)
                    result = parser.parse(tmp_path)
                    texts = []
                    for page_data in result.pages:
                        if hasattr(page_data, "text_items") and page_data.text_items:
                            for item in page_data.text_items:
                                if hasattr(item, "text") and item.text.strip():
                                    texts.append(item.text.strip())
                    return "\n".join(texts)
                finally:
                    os.unlink(tmp_path)
            except Exception:
                pass

        except Exception:
            pass

        return ""

    def _build_text_context(self, page_text: str, ocr_text: str) -> str:
        parts = []
        if page_text.strip():
            parts.append(f"【PDF 文本层】\n{page_text.strip()}")
        if ocr_text.strip() and ocr_text.strip() != page_text.strip():
            parts.append(f"【OCR 识别】\n{ocr_text.strip()}")
        if not parts:
            return "（未能从页面提取文字，请根据常见学术幻灯片结构给出通用分析）"
        return "\n\n".join(parts)
