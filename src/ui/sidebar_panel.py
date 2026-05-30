import customtkinter as ctk
from typing import List
from src.models.annotation import Annotation

class SidebarPanel(ctk.CTkFrame):
    """批注侧边栏"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, width=300, **kwargs)
        self.annotations: List[Annotation] = []
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """创建侧边栏组件"""
        # 标题
        self.title_label = ctk.CTkLabel(
            self,
            text="批注",
            font=("Arial", 16, "bold")
        )
        self.title_label.pack(pady=10)
        
        # 搜索框
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="搜索批注..."
        )
        self.search_entry.pack(fill="x", padx=10, pady=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search())
        
        # 批注列表
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 批注卡片容器
        self.annotation_cards = []
    
    def update_annotations(self, annotations: List[Annotation]) -> None:
        """更新批注列表"""
        self.annotations = annotations
        self._refresh_display()
    
    def _refresh_display(self) -> None:
        """刷新显示"""
        for card in self.annotation_cards:
            card.destroy()
        self.annotation_cards.clear()
        
        for ann in self.annotations:
            card = self._create_annotation_card(ann)
            card.pack(fill="x", pady=5)
            self.annotation_cards.append(card)
    
    def _create_annotation_card(self, annotation: Annotation) -> ctk.CTkFrame:
        """创建批注卡片"""
        card = ctk.CTkFrame(self.scroll_frame)
        
        # 页面号
        page_label = ctk.CTkLabel(
            card,
            text=f"第 {annotation.page_number} 页",
            font=("Arial", 10, "bold")
        )
        page_label.pack(anchor="w", padx=5, pady=2)
        
        # 批注内容
        content_text = ctk.CTkTextbox(card, height=100)
        content_text.pack(fill="x", padx=5, pady=2)
        content_text.insert("1.0", annotation.content)
        content_text.configure(state="disabled")
        
        # 智能体角色
        if annotation.agent_role:
            role_label = ctk.CTkLabel(
                card,
                text=f"来源: {annotation.agent_role}",
                font=("Arial", 9),
                text_color="gray"
            )
            role_label.pack(anchor="w", padx=5, pady=2)
        
        return card
    
    def _on_search(self) -> None:
        """搜索批注"""
        query = self.search_entry.get().lower()
        if not query:
            self._refresh_display()
            return
        
        filtered = [
            ann for ann in self.annotations
            if query in ann.content.lower()
        ]
        
        for card in self.annotation_cards:
            card.destroy()
        self.annotation_cards.clear()
        
        for ann in filtered:
            card = self._create_annotation_card(ann)
            card.pack(fill="x", pady=5)
            self.annotation_cards.append(card)