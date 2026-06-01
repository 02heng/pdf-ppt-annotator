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
    ) -> List[Annotation]:
        """处理单个页面（优先使用页面图片视觉分析）"""
        if pdf_path or pdf_doc is not None or source_path:
            from src.services.vision_annotation_service import VisionAnnotationService

            vision_service = VisionAnnotationService(self.crew_service.llm_service.config)
            return vision_service.annotate_page_from_pdf(
                pdf_path=pdf_path,
                page_number=page.page_number,
                pdf_doc=pdf_doc,
                source_path=source_path,
            )
        return self.crew_service.process_page(page)

    def switch_llm_provider(self, provider: str) -> None:
        """切换 LLM 提供商"""
        self.crew_service.switch_llm_provider(provider)
