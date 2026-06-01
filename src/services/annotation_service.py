"""批注处理服务模块"""
from typing import List, Callable, Optional

from src.models.document import Document
from src.models.page import Page
from src.models.annotation import Annotation
from src.models.config import LLMConfig
from src.services.crew_service import CrewService


class AnnotationService:
    """批注处理服务"""

    def __init__(self, config: LLMConfig):
        self.crew_service = CrewService(config)
        self._progress_callback: Optional[Callable] = None
        self._is_paused = False
        self._is_cancelled = False

    def set_progress_callback(self, callback: Callable) -> None:
        """设置进度回调函数"""
        self._progress_callback = callback

    def pause(self) -> None:
        """暂停处理"""
        self._is_paused = True

    def resume(self) -> None:
        """继续处理"""
        self._is_paused = False

    def cancel(self) -> None:
        """取消处理"""
        self._is_cancelled = True

    def process_document(self, document: Document) -> Document:
        """处理整个文档，生成批注"""
        total_pages = document.total_pages

        for i, page in enumerate(document.pages):
            # 检查取消状态
            if self._is_cancelled:
                break

            # 检查暂停状态
            while self._is_paused:
                import time
                time.sleep(0.1)

            # 更新进度
            if self._progress_callback:
                self._progress_callback(
                    current=i + 1,
                    total=total_pages,
                    status=f"正在处理第 {i + 1} 页..."
                )

            # 处理单页
            annotations = self.crew_service.process_page(page)

            # 添加批注到页面
            for annotation in annotations:
                page.add_annotation(annotation)

        return document

    def process_page(
        self,
        page: Page,
        pdf_path: str = "",
        pdf_doc=None,
        source_path: str = "",
        document_context: str = "",
        total_pages: int = 0,
        page_image=None,
    ) -> List[Annotation]:
        """处理单个页面（将页图 base64 交给视觉模型阅读）"""
        if pdf_path or pdf_doc is not None or source_path or page_image is not None:
            from src.services.vision_annotation_service import VisionAnnotationService

            vision_service = VisionAnnotationService(self.crew_service.llm_service.config)
            if page_image is not None:
                return vision_service.annotate_page_from_image(
                    page_image,
                    document_context=document_context,
                    total_pages=total_pages,
                )
            return vision_service.annotate_page_from_pdf(
                pdf_path=pdf_path,
                page_number=page.page_number,
                pdf_doc=pdf_doc,
                source_path=source_path,
                document_context=document_context,
                total_pages=total_pages,
            )
        return self.crew_service.process_page(page)

    def analyze_document_context(
        self,
        page_images,
        *,
        total_pages: int,
        source_path: str = "",
    ) -> str:
        """将全部页面 base64 图片交给模型通读，生成理解摘要"""
        from src.services.vision_annotation_service import VisionAnnotationService

        vision_service = VisionAnnotationService(self.crew_service.llm_service.config)
        vision_service.ensure_vision_provider()
        return vision_service.analyze_document_from_images(
            page_images,
            total_pages=total_pages,
            source_path=source_path,
        )

    def render_document_page_images(
        self,
        *,
        total_pages: int,
        pdf_path: str = "",
        pdf_doc=None,
        source_path: str = "",
        on_progress=None,
    ):
        """将文档每页渲染为 base64 图片"""
        from src.utils.page_image import render_all_pages_for_annotation

        return render_all_pages_for_annotation(
            total_pages,
            pdf_path=pdf_path,
            pdf_doc=pdf_doc,
            source_path=source_path,
            on_progress=on_progress,
        )

    def switch_llm_provider(self, provider: str) -> None:
        """切换 LLM 提供商"""
        self.crew_service.switch_llm_provider(provider)
