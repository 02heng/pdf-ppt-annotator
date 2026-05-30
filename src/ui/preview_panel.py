import customtkinter as ctk
from typing import Optional
from src.models.document import Document

class PreviewPanel(ctk.CTkFrame):
    """文档预览面板"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.document: Optional[Document] = None
        self.current_page = 0
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """创建预览组件"""
        # 页面导航
        self.nav_frame = ctk.CTkFrame(self)
        self.nav_frame.pack(fill="x", padx=5, pady=5)
        
        self.prev_btn = ctk.CTkButton(
            self.nav_frame,
            text="上一页",
            command=self._prev_page,
            width=80
        )
        self.prev_btn.pack(side="left", padx=5)
        
        self.page_label = ctk.CTkLabel(
            self.nav_frame,
            text="0 / 0"
        )
        self.page_label.pack(side="left", expand=True)
        
        self.next_btn = ctk.CTkButton(
            self.nav_frame,
            text="下一页",
            command=self._next_page,
            width=80
        )
        self.next_btn.pack(side="right", padx=5)
        
        # 内容显示区域
        self.content_text = ctk.CTkTextbox(self)
        self.content_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def load_document(self, document: Document) -> None:
        """加载文档"""
        self.document = document
        self.current_page = 0
        self._update_display()
    
    def _update_display(self) -> None:
        """更新显示"""
        if not self.document or self.document.total_pages == 0:
            return
        
        page = self.document.pages[self.current_page]
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", page.content)
        
        self.page_label.configure(
            text=f"{self.current_page + 1} / {self.document.total_pages}"
        )
    
    def _prev_page(self) -> None:
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_display()
    
    def _next_page(self) -> None:
        """下一页"""
        if self.document and self.current_page < self.document.total_pages - 1:
            self.current_page += 1
            self._update_display()