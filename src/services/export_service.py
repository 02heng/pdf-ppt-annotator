import os
from typing import Optional
from src.models.document import Document
from src.models.annotation import Annotation

class ExportService:
    """导出服务"""
    
    def export_annotated_pdf(
        self,
        document: Document,
        output_path: str,
        mode: str = "overlay"
    ) -> str:
        """
        导出带批注的 PDF
        
        Args:
            document: 文档对象
            output_path: 输出路径
            mode: 导出模式 ("overlay" 或 "sidebar")
            
        Returns:
            str: 导出文件路径
        """
        if document.file_type != "pdf":
            raise ValueError("只能导出 PDF 文件")
        
        import fitz
        
        try:
            pdf_document = fitz.open(document.file_path)
            
            for page in pdf_document:
                page_num = page.number + 1
                doc_page = document.get_page(page_num)
                
                if doc_page and doc_page.annotations:
                    if mode == "overlay":
                        self._add_overlay_annotations(page, doc_page.annotations)
            
            pdf_document.save(output_path)
            pdf_document.close()
            
            return output_path
            
        except Exception as e:
            raise ValueError(f"导出失败: {str(e)}")
    
    def _add_overlay_annotations(self, page, annotations: list) -> None:
        """添加覆盖式批注"""
        import fitz
        
        for ann in annotations:
            rect = fitz.Rect(
                ann.position_x,
                ann.position_y,
                ann.position_x + ann.width,
                ann.position_y + ann.height
            )
            
            annot = page.add_text_annot(
                fitz.Point(ann.position_x, ann.position_y),
                ann.content
            )
            annot.set_info(content=ann.content)
    
    def export_annotations_markdown(
        self,
        document: Document,
        output_path: str
    ) -> str:
        """
        导出批注为 Markdown
        
        Args:
            document: 文档对象
            output_path: 输出路径
            
        Returns:
            str: 导出文件路径
        """
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# {document.title or '文档批注'}\n\n")
            
            for page in document.pages:
                if page.annotations:
                    f.write(f"## 第 {page.page_number} 页\n\n")
                    
                    for ann in page.annotations:
                        f.write(f"### 批注\n\n{ann.content}\n\n")
                        f.write("---\n\n")
        
        return output_path
    
    def export_bilingual(
        self,
        document: Document,
        output_path: str
    ) -> str:
        """
        导出双语对照文档
        
        Args:
            document: 文档对象
            output_path: 输出路径
            
        Returns:
            str: 导出文件路径
        """
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# 双语对照批注\n\n")
            
            for page in document.pages:
                f.write(f"## 第 {page.page_number} 页\n\n")
                f.write("### 原文\n\n")
                f.write(f"{page.content}\n\n")
                
                if page.annotations:
                    f.write("### 批注\n\n")
                    for ann in page.annotations:
                        f.write(f"{ann.content}\n\n")
                
                f.write("---\n\n")
        
        return output_path
    
    def _get_output_path(
        self,
        original_path: str,
        suffix: str = "_annotated"
    ) -> str:
        """生成输出路径"""
        directory = os.path.dirname(original_path)
        filename = os.path.basename(original_path)
        name, ext = os.path.splitext(filename)
        
        return os.path.join(directory, f"{name}{suffix}{ext}")
