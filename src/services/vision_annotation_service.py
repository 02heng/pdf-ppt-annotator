"""基于页面图片的视觉批注服务"""
from __future__ import annotations

import uuid
from typing import List, Optional

import fitz
from openai import OpenAI

from src.models.annotation import Annotation
from src.models.config import LLMConfig
from src.utils.image_ocr import ocr_image_b64
from src.utils.page_image import (
    PageImageData,
    extract_page_text_for_annotation,
    render_page_for_annotation,
)

DEEPSEEK_SYSTEM = (
    "你是专业的文档批注助手。用户消息中已包含从 PDF/PPT 页面识别出的文字内容，"
    "请直接基于这些内容完成任务。"
    "禁止要求用户上传图片、禁止说「无法看到图片」或「请提供图片文件」。"
)

# 原生视觉模型（OpenAI / Ollama）：消息中含 image_url 或 images 字段
VISION_ANNOTATION_PROMPT = """请根据消息中附带的页面图片，用中文生成本页批注。

要求：
1. 概括本页核心主题和关键信息
2. 解释专业术语（如有）
3. 指出重点和难点
4. 200-400 字，不要用 Markdown
5. 直接输出批注正文"""

VISION_DOCUMENT_PROMPT = """消息中按顺序附带了文档每一页的截图。请通读全部页面图片，输出「文档理解摘要」：
1. 主题、结构与目标读者（2-4 句）
2. 关键术语及解释
3. 逐页要点（格式：第 N 页：……）"""

# DeepSeek V4 Pro（文本 API）：页面内容以 OCR/识别文字形式提供
TEXT_ANNOTATION_PROMPT = """以下「当前页内容」来自系统对该页渲染图的文字识别，请直接基于此生成中文批注。

要求：
1. 概括本页核心主题和关键信息
2. 解释专业术语（如有）
3. 指出重点和难点
4. 200-400 字，不要用 Markdown
5. 直接输出批注正文，不要要求上传图片"""

TEXT_DOCUMENT_PROMPT = """以下「各页内容」来自系统对 PDF/PPT 每一页渲染图的文字识别。请通读并输出「文档理解摘要」：
1. 主题、结构与目标读者（2-4 句）
2. 关键术语及解释
3. 逐页要点（格式：第 N 页：……）

请直接基于下方文字处理，不要要求用户提供图片。"""

TEXT_PARTIAL_DOCUMENT_PROMPT = """以下是文档第 {start_page} 页到第 {end_page} 页（共 {total_pages} 页）的识别内容。请输出该片段理解摘要（含逐页要点）。"""

MERGE_SUMMARY_PROMPT = """以下是一份 {total_pages} 页文档分段理解后的片段摘要。请合并为完整「文档理解摘要」。"""

PAGE_CONTEXT_HEADER = """【整份文档理解摘要】
{document_context}

【当前批注页】第 {page_number} 页 / 共 {total_pages} 页

【当前页内容】"""

MAX_PAGES_PER_VISION_REQUEST = 12


class VisionAnnotationService:
    """将文档页面转为 base64 图片并调用模型阅读、批注"""

    def __init__(self, config: LLMConfig):
        self.config = config

    def supports_vision(self) -> bool:
        return self.config.provider in ("openai", "ollama", "deepseek")

    def ensure_vision_provider(self) -> None:
        if not self.supports_vision():
            raise RuntimeError(
                "请使用 OpenAI（gpt-4o）、Ollama 视觉模型，或 DeepSeek（deepseek-v4-pro）。"
            )

    def _deepseek_model(self) -> str:
        return (self.config.deepseek.model or "deepseek-v4-pro").lower()

    def _deepseek_native_vision(self) -> bool:
        name = self._deepseek_model()
        return any(k in name for k in ("vl", "vision", "janus"))

    def _uses_text_pipeline(self) -> bool:
        return self.config.provider == "deepseek" and not self._deepseek_native_vision()

    def _deepseek_v4(self) -> bool:
        name = self._deepseek_model()
        return name.startswith("deepseek-v4") or name in ("deepseek-chat", "deepseek-reasoner")

    def annotate_page_from_image(
        self,
        page_image: PageImageData,
        *,
        document_context: str = "",
        total_pages: int = 0,
    ) -> List[Annotation]:
        self.ensure_vision_provider()

        content = self._annotate_pages(
            [page_image],
            document_context=document_context,
            page_number=page_image.page_number + 1,
            total_pages=total_pages,
            thinking=False,
        )

        return [
            Annotation(
                id=str(uuid.uuid4()),
                page_number=page_image.page_number,
                content=content,
                original_text=None,
                position_x=max(page_image.width - 36, 12),
                position_y=24,
                width=160,
                height=100,
                agent_role="vision",
            )
        ]

    def annotate_page_from_pdf(
        self,
        pdf_path: str,
        page_number: int,
        pdf_doc: Optional[fitz.Document] = None,
        source_path: str = "",
        document_context: str = "",
        total_pages: int = 0,
    ) -> List[Annotation]:
        original = source_path or pdf_path
        _, image_b64, width, height = render_page_for_annotation(
            page_number,
            pdf_path=pdf_path,
            pdf_doc=pdf_doc,
            source_path=original,
        )
        supplement = extract_page_text_for_annotation(
            page_number,
            pdf_doc=pdf_doc,
            source_path=original,
        )
        page_image = PageImageData(
            page_number=page_number,
            png_bytes=b"",
            image_b64=image_b64,
            width=width,
            height=height,
            text_supplement=supplement.strip(),
        )
        return self.annotate_page_from_image(
            page_image,
            document_context=document_context,
            total_pages=total_pages or (len(pdf_doc) if pdf_doc else 0),
        )

    def analyze_document_from_images(
        self,
        page_images: List[PageImageData],
        *,
        total_pages: int,
        source_path: str = "",
    ) -> str:
        if not page_images:
            return "（未能生成页面图片，将逐页单独批注）"

        file_hint = ""
        if source_path:
            file_hint = f"\n\n文档：{source_path}，共 {total_pages} 页"

        if len(page_images) <= MAX_PAGES_PER_VISION_REQUEST:
            prompt = (
                (TEXT_DOCUMENT_PROMPT if self._uses_text_pipeline() else VISION_DOCUMENT_PROMPT)
                + file_hint
            )
            return self._understand_pages(page_images, prompt, thinking=True)

        partials: List[str] = []
        for batch_start in range(0, len(page_images), MAX_PAGES_PER_VISION_REQUEST):
            batch = page_images[batch_start : batch_start + MAX_PAGES_PER_VISION_REQUEST]
            start_page = batch[0].page_number + 1
            end_page = batch[-1].page_number + 1
            if self._uses_text_pipeline():
                prompt = TEXT_PARTIAL_DOCUMENT_PROMPT.format(
                    start_page=start_page,
                    end_page=end_page,
                    total_pages=total_pages,
                ) + file_hint
            else:
                prompt = (
                    f"以下是文档第 {start_page} 页到第 {end_page} 页（共 {total_pages} 页）的截图。"
                    "请输出该片段理解摘要。"
                ) + file_hint
            partials.append(self._understand_pages(batch, prompt, thinking=True))

        merge_prompt = (
            MERGE_SUMMARY_PROMPT.format(total_pages=total_pages)
            + file_hint
            + "\n\n"
            + "\n\n---\n\n".join(
                f"【片段 {i + 1}】\n{text}" for i, text in enumerate(partials)
            )
        )
        return self._call_text_only(merge_prompt, thinking=True)

    def _page_readable_text(self, page: PageImageData) -> str:
        ocr_text = ocr_image_b64(page.image_b64)
        if ocr_text:
            return ocr_text
        if page.text_supplement:
            return page.text_supplement
        return "（本页未识别到可读文字，请根据上下文做概括性说明）"

    def _build_text_pages_block(self, pages: List[PageImageData]) -> str:
        parts: list[str] = []
        for page in pages:
            page_no = page.page_number + 1
            body = self._page_readable_text(page)
            parts.append(f"--- 第 {page_no} 页 ---\n{body}")
        return "\n\n".join(parts)

    def _annotate_pages(
        self,
        pages: List[PageImageData],
        *,
        document_context: str,
        page_number: int,
        total_pages: int,
        thinking: bool,
    ) -> str:
        if self._uses_text_pipeline():
            header = TEXT_ANNOTATION_PROMPT
            if document_context.strip():
                header = PAGE_CONTEXT_HEADER.format(
                    document_context=document_context.strip(),
                    page_number=page_number,
                    total_pages=total_pages,
                )
            prompt = f"{header}\n\n{self._build_text_pages_block(pages)}"
            return self._call_deepseek_text(prompt, thinking=thinking)

        prompt = VISION_ANNOTATION_PROMPT
        if document_context.strip():
            prompt = (
                f"【文档理解摘要】\n{document_context.strip()}\n\n"
                f"请批注第 {page_number} 页（共 {total_pages} 页）。\n\n"
                + prompt
            )
        return self._call_openai_vision_multi(
            [p.image_b64 for p in pages],
            prompt,
        )

    def _understand_pages(
        self,
        pages: List[PageImageData],
        prompt: str,
        *,
        thinking: bool,
    ) -> str:
        if self._uses_text_pipeline():
            full = f"{prompt}\n\n{self._build_text_pages_block(pages)}"
            return self._call_deepseek_text(full, thinking=thinking)

        if self.config.provider == "ollama":
            return self._call_ollama_vision_multi(
                [p.image_b64 for p in pages],
                prompt,
            )
        return self._call_openai_vision_multi([p.image_b64 for p in pages], prompt)

    def _call_text_only(self, prompt: str, *, thinking: bool = False) -> str:
        provider = self.config.provider
        if provider == "openai":
            return self._call_openai_text(prompt)
        if provider == "deepseek":
            return self._call_deepseek_text(prompt, thinking=thinking)
        if provider == "ollama":
            return self._call_ollama_text(prompt)
        raise ValueError(f"不支持的 LLM 提供商: {provider}")

    def _deepseek_request_kwargs(self, *, thinking: bool) -> dict:
        if not self._deepseek_v4():
            return {}
        kwargs: dict = {
            "extra_body": {"thinking": {"type": "enabled" if thinking else "disabled"}},
        }
        if thinking:
            kwargs["reasoning_effort"] = "high"
        return kwargs

    def _call_openai_vision_multi(self, images_b64: List[str], prompt: str) -> str:
        cfg = self.config.openai
        client = OpenAI(api_key=cfg.api_key)

        content: list = []
        for image_b64 in images_b64:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_b64}",
                        "detail": "high",
                    },
                }
            )
        content.append({"type": "text", "text": prompt})

        response = client.chat.completions.create(
            model=cfg.model,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            messages=[{"role": "user", "content": content}],
        )
        return response.choices[0].message.content.strip()

    def _call_ollama_vision_multi(self, images_b64: List[str], prompt: str) -> str:
        import json
        import urllib.request

        cfg = self.config.ollama
        url = f"{cfg.base_url.rstrip('/')}/api/chat"
        payload = {
            "model": cfg.model,
            "messages": [{"role": "user", "content": prompt}],
            "images": images_b64,
            "stream": False,
            "options": {"temperature": cfg.temperature},
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=600) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result["message"]["content"].strip()

    def _call_openai_text(self, content: str) -> str:
        cfg = self.config.openai
        client = OpenAI(api_key=cfg.api_key)
        response = client.chat.completions.create(
            model=cfg.model,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            messages=[{"role": "user", "content": content}],
        )
        return response.choices[0].message.content.strip()

    def _call_deepseek_text(self, content: str, *, thinking: bool = False) -> str:
        cfg = self.config.deepseek
        client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
        response = client.chat.completions.create(
            model=cfg.model or "deepseek-v4-pro",
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            messages=[
                {"role": "system", "content": DEEPSEEK_SYSTEM},
                {"role": "user", "content": content},
            ],
            **self._deepseek_request_kwargs(thinking=thinking),
        )
        message = response.choices[0].message
        text = (message.content or "").strip()
        if not text and getattr(message, "reasoning_content", None):
            text = str(message.reasoning_content).strip()
        return text

    def _call_ollama_text(self, content: str) -> str:
        import json
        import urllib.request

        cfg = self.config.ollama
        url = f"{cfg.base_url.rstrip('/')}/api/chat"
        payload = {
            "model": cfg.model,
            "messages": [{"role": "user", "content": content}],
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
