import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog

from src.ui.message_dialog import ask_yes_no, show_warning
from typing import List, Dict, Tuple
from PIL import Image, ImageTk
import io
import os

from src.models.config import Settings
from src.ui.toolbar import Toolbar
from src.ui.status_bar import StatusBar
from src.ui.theme import UITheme
from src.ui.chrome import SectionHeader
from src.utils.annotation_text import format_annotation_list_preview


class AnnotationMarker:
    """批注标记（小方块 + 双击弹出内容）"""

    MARKER_SIZE = 22
    POPUP_OFFSET_X = 28
    POPUP_WIDTH = 300
    POPUP_MAX_HEIGHT = 420
    TITLE_AREA = 42
    POPUP_PADDING = 10

    def __init__(self, x: int, y: int, text: str, color: str = "#7C3AED"):
        self.x = x
        self.y = y
        self.text = text
        self.color = color

        self.collapsed_width = self.MARKER_SIZE
        self.collapsed_height = self.MARKER_SIZE
        self.expanded_width = self.POPUP_WIDTH

        self.is_expanded = False
        self.width = self.collapsed_width
        self.height = self.collapsed_height
        self.popup_x = 0
        self.popup_y = 0

        self.canvas_id = None
        self.text_id = None
        self.drag_data = {"x": 0, "y": 0}
        self.icon_rect = (0, 0, 0, 0)
        self.popup_rect = None
        self.close_rect = None
        self.popup_window_id = None

    @staticmethod
    def _wrap_font():
        import tkinter.font as tkfont

        return tkfont.Font(family="Microsoft YaHei UI", size=11)

    def _measure_body_height(self) -> int:
        """按与弹层 Textbox 相同的字体/宽度测算正文高度"""
        font = self._wrap_font()
        wrap_width = self.POPUP_WIDTH - 28
        line_height = font.metrics("linespace") + 6
        lines = 0

        for paragraph in self.text.split("\n"):
            if not paragraph.strip():
                lines += 1
                continue
            line = ""
            for ch in paragraph:
                trial = line + ch
                if font.measure(trial) <= wrap_width:
                    line = trial
                else:
                    if line:
                        lines += 1
                    line = ch
            if line:
                lines += 1

        # 留一点余量，避免测算偏矮导致画出白框
        return max(lines, 1) * line_height + 16

    def _calc_popup_height(self) -> int:
        """弹层总高度 = 标题区 + 正文区（超出最大高度时正文区可滚动）"""
        max_body = self.POPUP_MAX_HEIGHT - self.TITLE_AREA - self.POPUP_PADDING
        body_h = min(self._measure_body_height(), max_body)
        total = self.TITLE_AREA + body_h + self.POPUP_PADDING
        return int(max(min(total, self.POPUP_MAX_HEIGHT), 100))

    def toggle_expand(self):
        """切换展开/折叠状态"""
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.height = self._calc_popup_height()
        else:
            self.width = self.collapsed_width
            self.height = self.collapsed_height
            self.popup_rect = None
            self.close_rect = None

    def collapse(self):
        """折叠"""
        self.is_expanded = False
        self.width = self.collapsed_width
        self.height = self.collapsed_height
        self.popup_rect = None
        self.close_rect = None

    def refresh_expanded_size(self):
        """文本更新后刷新展开尺寸"""
        if self.is_expanded:
            self.height = self._calc_popup_height()


class App(ctk.CTk):
    """主应用窗口"""

    PPT_IMPORT_ZOOM = 0.6

    def __init__(self, settings: Settings):
        super().__init__()

        self.settings = settings
        self.selected_files: List[str] = []
        self.current_file_index: int = -1

        # PDF渲染相关
        self.pdf_doc = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_level = 1.0
        self.page_image = None
        self.tk_image = None
        self.text_positions = {}  # LiteParse 文本位置信息
        self._preview_shell_ready = False
        self._page_image_id = None
        self._page_offset_x = 0
        self._page_offset_y = 0
        self._canvas_configure_after = None

        # 批注相关
        self.annotations: Dict[int, List[AnnotationMarker]] = {}  # 当前文件的批注
        self.annotations_by_file: Dict[str, Dict[int, List[AnnotationMarker]]] = {}
        self.project_file_path: str = None
        self.converted_pdf_paths: Dict[str, str] = {}
        self._autosave_job = None
        self.selected_marker: AnnotationMarker = None
        self.dragging = False
        self._press_pos: Tuple[float, float] = None
        self._did_drag = False

        # 配置窗口
        self.title("TO PDF · 中文批注")
        self.geometry("1440x920")
        self.minsize(1100, 720)

        UITheme.install()
        UITheme.apply_root(self)

        from src.utils.branding import apply_window_icon

        apply_window_icon(self)

        # 创建 UI 组件
        self._create_widgets()
        self._apply_theme()

        # 配置布局
        self._configure_layout()

        # 绑定快捷键
        self.bind("<Control-plus>", lambda e: self._zoom_in())
        self.bind("<Control-minus>", lambda e: self._zoom_out())
        self.bind("<Control-0>", lambda e: self._zoom_reset())

        from src.services.web_preview_server import WebPreviewServer

        self.web_preview = WebPreviewServer()
        self.web_preview.start()
        self._web_preview_opened = False

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(200, self._restore_last_session)

    def _create_widgets(self) -> None:
        """创建 UI 组件"""
        # 工具栏
        self.toolbar = Toolbar(self)

        # 主内容区域
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")

        # 左侧文件列表
        self.file_list_frame = ctk.CTkFrame(self.content_frame, width=248)
        self._create_file_list()

        # 中间预览区域
        self.preview_frame = ctk.CTkFrame(self.content_frame)

        # 右侧批注面板
        self.sidebar_frame = ctk.CTkFrame(self.content_frame, width=380)
        self._create_sidebar()

        # 状态栏
        self.status_bar = StatusBar(self)

    def _create_file_list(self) -> None:
        """创建文件列表"""
        header = SectionHeader(self.file_list_frame, text="文件列表")
        header.pack(fill="x", padx=UITheme.PAD, pady=(UITheme.PAD, UITheme.PAD_SM))

        # 文件列表
        self.file_listbox = ctk.CTkScrollableFrame(
            self.file_list_frame,
            fg_color=UITheme.FILE_LIST_BG,
            label_fg_color=UITheme.FILE_LIST_BG,
            **UITheme.scrollable_frame_kwargs(),
        )
        self.file_listbox.pack(fill="both", expand=True, padx=UITheme.PAD, pady=UITheme.PAD_SM)
        UITheme.style_scrollable_frame(self.file_listbox)

        self.file_hint = ctk.CTkLabel(self.file_list_frame, text="点击顶部「导入」添加 PDF / PPT")
        self.file_hint.pack(pady=UITheme.PAD)

    def _create_sidebar(self) -> None:
        """创建批注侧边栏（单卡片统一宽度，避免列表与编辑区不齐）"""
        pad = UITheme.PAD_SM
        self._editor_card = ctk.CTkFrame(self.sidebar_frame)
        self._editor_card.pack(fill="both", expand=True, padx=UITheme.PAD, pady=UITheme.PAD)
        UITheme.style_card(self._editor_card, elevated=True)

        title_row = ctk.CTkFrame(self._editor_card, fg_color="transparent")
        title_row.pack(fill="x", padx=pad, pady=(pad, 4))

        SectionHeader(title_row, text="批注管理").pack(side="left")

        add_btn = ctk.CTkButton(
            title_row,
            text="+ 添加",
            width=88,
            command=self._add_annotation_mode,
        )
        add_btn.pack(side="right")
        UITheme.style_primary(add_btn)

        self.annotation_list = ctk.CTkScrollableFrame(
            self._editor_card,
            height=150,
            fg_color="transparent",
            **UITheme.scrollable_frame_kwargs(),
        )
        self.annotation_list.pack(fill="x", padx=pad, pady=(0, pad))
        UITheme.style_scrollable_frame(self.annotation_list)

        SectionHeader(self._editor_card, text="批注内容").pack(
            fill="x", padx=pad, pady=(pad, 4)
        )

        self.annotation_input = ctk.CTkTextbox(
            self._editor_card,
            height=240,
            wrap="word",
            activate_scrollbars=True,
        )
        self.annotation_input.pack(fill="both", expand=True, padx=pad, pady=4)
        UITheme.style_textbox(self.annotation_input)

        btn_frame = ctk.CTkFrame(self._editor_card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=pad, pady=pad)

        self.save_btn = ctk.CTkButton(
            btn_frame,
            text="保存",
            width=80,
            command=self._save_annotation
        )
        self.save_btn.pack(side="left", padx=5)

        self.delete_btn = ctk.CTkButton(
            btn_frame,
            text="删除",
            width=80,
            command=self._delete_annotation
        )
        self.delete_btn.pack(side="left", padx=5)

        color_frame = ctk.CTkFrame(self._editor_card, fg_color="transparent")
        color_frame.pack(fill="x", padx=pad, pady=(0, pad))

        ctk.CTkLabel(color_frame, text="标记颜色", font=UITheme.font_caption(), text_color=UITheme.TEXT_MUTED).pack(
            side="left", padx=(0, 8)
        )

        self.color_var = ctk.StringVar(value=UITheme.ANNOTATION_COLORS[0])
        colors = UITheme.ANNOTATION_COLORS
        for color in colors:
            btn = ctk.CTkButton(
                color_frame,
                text="",
                width=28,
                height=28,
                corner_radius=14,
                fg_color=color,
                hover_color=color,
                command=lambda c=color: self._set_color(c),
            )
            btn.pack(side="left", padx=3)

        self.mode_hint = ctk.CTkLabel(
            self.sidebar_frame,
            text="滚轮滚动页面 · ± 缩放 · 拖动标记移动",
        )
        self.mode_hint.pack(pady=(0, UITheme.PAD))

    def _apply_theme(self) -> None:
        """应用设计系统"""
        UITheme.style_card(self.file_list_frame)
        UITheme.style_card(self.preview_frame)
        UITheme.style_card(self.sidebar_frame)
        if hasattr(self, "_editor_card"):
            UITheme.style_card(self._editor_card, elevated=True)
        UITheme.style_primary(self.save_btn)
        UITheme.style_soft_danger(self.delete_btn)
        UITheme.muted_label(self.file_hint)
        UITheme.muted_label(self.mode_hint)
        if hasattr(self, "_nav_inner"):
            UITheme.style_nav_bar(self._nav_inner)
            for btn in getattr(self, "_nav_buttons", []):
                UITheme.style_nav_button(btn)
            UITheme.title_label(self.page_label)

    def _configure_layout(self) -> None:
        """配置布局（状态栏先贴底，避免被 expand 的中间区域挤出屏幕）"""
        p = UITheme.PAD
        self.status_bar.pack(side="bottom", fill="x", padx=p, pady=(0, p))
        self.toolbar.pack(side="top", fill="x", padx=p, pady=(p, UITheme.PAD_SM))
        self.content_frame.pack(
            side="top", fill="both", expand=True, padx=p, pady=(UITheme.PAD_SM, UITheme.PAD_SM)
        )
        self.file_list_frame.pack(side="left", fill="y", padx=(0, UITheme.PAD_SM))
        self.preview_frame.pack(side="left", fill="both", expand=True, padx=UITheme.PAD_SM)
        self.sidebar_frame.pack(side="right", fill="y", padx=(UITheme.PAD_SM, 0))

    def _current_file_path(self) -> str:
        if 0 <= self.current_file_index < len(self.selected_files):
            return self.selected_files[self.current_file_index]
        return ""

    def get_render_pdf_path(self, file_path: str = "") -> str:
        """当前文件对应的 PDF 路径（PPT 为转换后的 PDF）"""
        from src.utils.ppt_converter import get_render_pdf_path

        path = file_path or self._current_file_path()
        return get_render_pdf_path(path, self.converted_pdf_paths)

    def _canvas_scale(self) -> float:
        """PDF 点坐标 → 画布像素的缩放比"""
        return self.zoom_level * 2

    def _marker_to_canvas(self, marker: AnnotationMarker) -> Tuple[float, float]:
        scale = self._canvas_scale()
        return (
            marker.x * scale + self._page_offset_x,
            marker.y * scale + self._page_offset_y,
        )

    def _canvas_to_pdf(self, cx: float, cy: float) -> Tuple[float, float]:
        scale = self._canvas_scale()
        if scale <= 0:
            return cx, cy
        return (
            (cx - self._page_offset_x) / scale,
            (cy - self._page_offset_y) / scale,
        )

    def _normalize_markers(self, page_num: int) -> None:
        """将旧版画布坐标转为 PDF 页坐标，并限制在页面内"""
        if not self.pdf_doc:
            return
        markers = self.annotations.get(page_num, [])
        if not markers:
            return

        page = self.pdf_doc[page_num]
        pw, ph = page.rect.width, page.rect.height
        scale = self._canvas_scale()
        size = AnnotationMarker.MARKER_SIZE

        for marker in markers:
            if marker.x > pw + 10 or marker.y > ph + 10:
                marker.x /= scale
                marker.y /= scale
            marker.x = max(0, min(marker.x, pw - size))
            marker.y = max(0, min(marker.y, ph - size))

    def _file_key(self, path: str) -> str:
        from src.utils.file_utils import file_key

        return file_key(path)

    def _rekey_annotations_by_file(self) -> None:
        """统一批注存储键，合并同一路径的重复项"""
        merged: Dict[str, Dict[int, List[AnnotationMarker]]] = {}
        for path, pages in self.annotations_by_file.items():
            key = self._file_key(path)
            bucket = merged.setdefault(key, {})
            for page, markers in pages.items():
                bucket[int(page)] = list(markers)
        self.annotations_by_file = merged

    def _get_stored_annotations(self, file_path: str) -> Dict[int, List[AnnotationMarker]]:
        key = self._file_key(file_path)
        if key in self.annotations_by_file:
            return self.annotations_by_file[key]
        base = os.path.basename(file_path)
        for path, pages in self.annotations_by_file.items():
            if os.path.basename(path) == base:
                return pages
        return {}

    def _persist_current_file_annotations(self) -> None:
        path = self._current_file_path()
        if path:
            key = self._file_key(path)
            self.annotations_by_file[key] = {
                page: list(markers) for page, markers in self.annotations.items()
            }

    def _restore_file_annotations(self, file_path: str) -> None:
        stored = self._get_stored_annotations(file_path)
        self.annotations = {
            int(page): list(markers) for page, markers in stored.items()
        }
        self.selected_marker = None
        if self.pdf_doc:
            for page_num in list(self.annotations.keys()):
                if 0 <= page_num < self.total_pages:
                    self._normalize_markers(page_num)

    def schedule_persist(self) -> None:
        if not self.settings.app.auto_save:
            return
        if self._autosave_job:
            self.after_cancel(self._autosave_job)
        self._autosave_job = self.after(800, self._do_persist)

    def _flush_persist(self) -> None:
        """立即保存会话（不等待防抖）"""
        if self._autosave_job:
            self.after_cancel(self._autosave_job)
            self._autosave_job = None
        from src.services.project_service import save_session

        save_session(self)

    def _do_persist(self) -> None:
        self._autosave_job = None
        self._flush_persist()

    def _restore_last_session(self) -> None:
        from src.services.project_service import restore_session

        if restore_session(self):
            self._rekey_annotations_by_file()

    def _on_close(self) -> None:
        self._persist_current_file_annotations()
        self._flush_persist()
        if self.pdf_doc:
            self.pdf_doc.close()
        self.destroy()

    def update_status(self, message: str) -> None:
        """更新状态栏消息"""
        self.status_bar.set_message(message)

    def update_progress(self, current: int, total: int, status: str) -> None:
        """更新进度"""
        self.status_bar.set_progress(current, total, status)

    def sync_web_preview(self) -> None:
        """同步批注数据到 PDF.js 预览服务"""
        if hasattr(self, "web_preview"):
            self.web_preview.update_from_app(self)
        self.schedule_persist()

    def open_web_preview(self) -> None:
        """在浏览器中打开 PDF.js 批注预览"""
        import webbrowser

        self.sync_web_preview()
        webbrowser.open(self.web_preview.url)
        self._web_preview_opened = True
        self.update_status("预览已打开，点击黄色标记查看批注，点击空白处关闭")

    def update_file_list(self, files: List[str]) -> None:
        """更新文件列表显示"""
        # 清空现有列表
        for widget in self.file_listbox.winfo_children():
            widget.destroy()

        if not files:
            self.file_hint.configure(text="导入文件")
            return

        self.file_hint.configure(text="")

        for idx, file_path in enumerate(files):
            file_name = os.path.basename(file_path)
            lower = file_name.lower()
            if lower.endswith(".pdf"):
                icon = "📄"
            elif lower.endswith((".ppt", ".pptx")):
                icon = "📊"
            else:
                icon = "📁"

            is_current = idx == self.current_file_index
            display_name = UITheme.truncate_filename(file_name)

            row = ctk.CTkFrame(
                self.file_listbox,
                fg_color=UITheme.PURPLE_100 if is_current else UITheme.SURFACE,
                border_color=UITheme.PURPLE_400 if is_current else UITheme.BORDER,
                border_width=1 if is_current else 0,
                corner_radius=UITheme.RADIUS,
            )
            row.pack(fill="x", pady=3, padx=2)
            row.grid_columnconfigure(0, weight=1)

            name_label = ctk.CTkLabel(
                row,
                text=f"{icon} {display_name}",
                anchor="w",
                justify="left",
                font=UITheme.font_body(),
                text_color=UITheme.PURPLE_800 if is_current else UITheme.TEXT,
                cursor="hand2",
            )
            name_label.grid(row=0, column=0, sticky="ew", padx=(10, 4), pady=8)

            def select_file(_event=None, i=idx):
                self._on_file_select(i)

            name_label.bind("<Button-1>", select_file)
            row.bind("<Button-1>", select_file)
            UITheme.bind_tooltip(name_label, file_name)
            UITheme.bind_tooltip(row, file_name)

            remove_btn = ctk.CTkButton(
                row,
                text="删",
                width=32,
                height=28,
                command=lambda i=idx: self._remove_file(i),
            )
            remove_btn.grid(row=0, column=1, padx=(0, 6), pady=6)
            UITheme.style_danger(remove_btn)

        # 默认选中第一个文件
        if files and self.current_file_index < 0:
            self._on_file_select(0)

    def _on_file_select(self, index: int, page: int = None) -> None:
        """选择文件（各文件批注独立存储）"""
        if 0 <= index < len(self.selected_files):
            self._persist_current_file_annotations()
            self.current_file_index = index
            file_path = self.selected_files[index]
            file_name = os.path.basename(file_path)

            self._load_file_content(file_path, page=page)
            self._restore_file_annotations(file_path)
            self._show_annotations()
            self._update_annotation_list()

            self.update_status(f"已选择: {file_name}")
            self.update_file_list(self.selected_files)
            self.sync_web_preview()

    def _load_file_content(self, file_path: str, page: int = None) -> None:
        """加载文件内容"""
        try:
            if file_path.lower().endswith('.pdf'):
                self._load_pdf(file_path, page=page)
            elif file_path.lower().endswith(('.ppt', '.pptx')):
                self._load_ppt(file_path, page=page)
            else:
                show_warning(self, "警告", "不支持的文件格式")
        except Exception as e:
            show_warning(self, "错误", f"加载文件时出错: {str(e)}")

    def _get_page_text(self, page_num: int) -> str:
        """获取当前文件指定页的文字"""
        from src.utils.page_image import extract_page_text_for_annotation

        return extract_page_text_for_annotation(
            page_num,
            pdf_doc=self.pdf_doc,
            source_path=self._current_file_path(),
        )

    def _load_pdf(self, file_path: str, page: int = None, load_text_positions: bool = True) -> None:
        """加载PDF文件并渲染为图片"""
        try:
            import fitz  # PyMuPDF

            if self.pdf_doc:
                self.pdf_doc.close()

            self.pdf_doc = fitz.open(file_path)
            self.total_pages = len(self.pdf_doc)
            if page is None:
                self.current_page = 0
            else:
                self.current_page = max(0, min(page, self.total_pages - 1))

            if load_text_positions:
                self._load_text_positions(file_path)
            self._render_page()

            self.update_status(f"已加载PDF: {self.total_pages}页")

        except ImportError:
            show_warning(self, "错误", "请安装PyMuPDF: pip install pymupdf")
        except Exception as e:
            show_warning(self, "错误", f"读取PDF出错: {str(e)}")

    def _load_text_positions(self, file_path: str) -> None:
        """使用 LiteParse 加载文本位置信息"""
        try:
            from liteparse import LiteParse
            parser = LiteParse(ocr_enabled=False)  # 不需要 OCR，速度更快
            result = parser.parse(file_path)

            # 存储每页的文本位置信息
            self.text_positions = {}
            for page_data in result.pages:
                page_num = page_data.page_num - 1  # LiteParse 是 1-indexed
                positions = []

                if hasattr(page_data, 'text_items') and page_data.text_items:
                    for item in page_data.text_items:
                        if hasattr(item, 'text') and item.text.strip():
                            positions.append({
                                "text": item.text,
                                "x": getattr(item, 'x', 0),
                                "y": getattr(item, 'y', 0),
                                "width": getattr(item, 'width', 0),
                                "height": getattr(item, 'height', 0),
                            })

                self.text_positions[page_num] = positions

            print(f"LiteParse: 已加载 {len(self.text_positions)} 页的文本位置信息")

        except ImportError:
            print("提示: 未安装 liteparse，将使用基本模式")
            self.text_positions = {}
        except Exception as e:
            print(f"LiteParse 加载失败: {e}")
            self.text_positions = {}

    def _load_pptx_text_positions(self, file_path: str) -> None:
        """从 PPTX 提取各页文字位置信息"""
        try:
            from pptx import Presentation

            prs = Presentation(file_path)
            self.text_positions = {}
            for slide_index, slide in enumerate(prs.slides):
                positions = []
                for shape in slide.shapes:
                    if getattr(shape, "has_text_frame", False) and shape.has_text_frame:
                        text = shape.text_frame.text.strip()
                        if text:
                            positions.append(
                                {
                                    "text": text,
                                    "x": getattr(shape, "left", 0),
                                    "y": getattr(shape, "top", 0),
                                    "width": getattr(shape, "width", 0),
                                    "height": getattr(shape, "height", 0),
                                }
                            )
                self.text_positions[slide_index] = positions
        except Exception as e:
            print(f"PPTX 文字提取失败: {e}")
            self.text_positions = {}

    def _load_ppt(self, file_path: str, page: int = None) -> None:
        """加载 PPT/PPTX（转换为 PDF 后预览，批注时用幻灯片图片）"""
        try:
            from src.utils.ppt_converter import convert_ppt_to_pdf

            if file_path.lower().endswith(".pptx"):
                self._load_pptx_text_positions(file_path)

            pdf_path = convert_ppt_to_pdf(file_path)
            self.converted_pdf_paths[self._file_key(file_path)] = pdf_path
            self.zoom_level = self.PPT_IMPORT_ZOOM
            self._load_pdf(pdf_path, page=page, load_text_positions=False)
            self.update_status(f"已加载 PPT: {self.total_pages} 页")
        except Exception as e:
            show_warning(self, "错误", f"无法打开 PPT：{e}")
            raise

    def _ensure_preview_shell(self) -> None:
        """固定预览区：底部缩放/翻页栏 + 带滚动条的画布（PDF/PPT 共用）"""
        if self._preview_shell_ready:
            return

        nav_outer = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        nav_outer.pack(side="bottom", fill="x", padx=UITheme.PAD, pady=UITheme.PAD)

        self._nav_inner = ctk.CTkFrame(nav_outer)
        self._nav_inner.pack(fill="x")
        UITheme.style_nav_bar(self._nav_inner)

        nav = self._nav_inner
        self._nav_buttons = []

        zoom_frame = ctk.CTkFrame(nav, fg_color="transparent")
        zoom_frame.pack(side="left", padx=UITheme.PAD, pady=UITheme.PAD_SM)

        zoom_out_btn = ctk.CTkButton(zoom_frame, text="−", width=36, command=self._zoom_out)
        zoom_out_btn.pack(side="left", padx=2)
        UITheme.style_nav_button(zoom_out_btn)
        self._nav_buttons.append(zoom_out_btn)

        self.zoom_label = ctk.CTkLabel(
            zoom_frame,
            text=f"{int(self.zoom_level * 100)}%",
            width=56,
            font=UITheme.font_section(),
            text_color=UITheme.PURPLE_800,
        )
        self.zoom_label.pack(side="left", padx=6)

        zoom_in_btn = ctk.CTkButton(zoom_frame, text="+", width=36, command=self._zoom_in)
        zoom_in_btn.pack(side="left", padx=2)
        UITheme.style_nav_button(zoom_in_btn)
        self._nav_buttons.append(zoom_in_btn)

        self.prev_btn = ctk.CTkButton(nav, text="上一页", command=self._prev_page, width=96)
        self.prev_btn.pack(side="left", padx=UITheme.PAD)
        UITheme.style_nav_button(self.prev_btn)
        self._nav_buttons.append(self.prev_btn)

        self.page_label = ctk.CTkLabel(
            nav,
            text="0 / 0",
            font=UITheme.font_section(),
            text_color=UITheme.TEXT,
        )
        self.page_label.pack(side="left", expand=True)

        self.next_btn = ctk.CTkButton(nav, text="下一页", command=self._next_page, width=96)
        self.next_btn.pack(side="right", padx=UITheme.PAD)
        UITheme.style_nav_button(self.next_btn)
        self._nav_buttons.append(self.next_btn)

        self._viewer_host = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        self._viewer_host.pack(side="top", fill="both", expand=True, padx=5, pady=(5, 0))

        self._canvas_panel = tk.Frame(self._viewer_host, bg=UITheme.BG, highlightthickness=0)
        self._canvas_panel.pack(fill="both", expand=True)
        self._canvas_panel.grid_rowconfigure(0, weight=1)
        self._canvas_panel.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            self._canvas_panel,
            bg=UITheme.SURFACE,
            highlightthickness=0,
        )
        self._v_scroll = ctk.CTkScrollbar(
            self._canvas_panel,
            orientation="vertical",
            command=self.canvas.yview,
        )
        self._h_scroll = ctk.CTkScrollbar(
            self._canvas_panel,
            orientation="horizontal",
            command=self.canvas.xview,
        )
        self.canvas.configure(
            yscrollcommand=self._v_scroll.set,
            xscrollcommand=self._h_scroll.set,
        )
        UITheme.style_scrollbar(self._v_scroll)
        UITheme.style_scrollbar(self._h_scroll)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self._v_scroll.grid(row=0, column=1, sticky="ns")
        self._h_scroll.grid(row=1, column=0, sticky="ew")

        self._bind_canvas_events()
        self._preview_shell_ready = True

    def _bind_canvas_events(self) -> None:
        """画布交互：滚轮滚动（非缩放），批注拖拽等"""
        self.canvas.bind("<Button-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Double-Button-1>", self._on_canvas_double_click)

        for widget in (self.canvas, self._canvas_panel, self._viewer_host):
            widget.bind("<MouseWheel>", self._on_canvas_scroll)
            widget.bind("<Button-4>", self._on_canvas_scroll_linux_up)
            widget.bind("<Button-5>", self._on_canvas_scroll_linux_down)

        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event) -> None:
        """窗口尺寸变化时保持页面在可视区域居中"""
        if event.width < 2 or not self.page_image:
            return
        if self._canvas_configure_after:
            self.after_cancel(self._canvas_configure_after)
        self._canvas_configure_after = self.after(80, self._relayout_page_view)

    def _relayout_page_view(self) -> None:
        self._canvas_configure_after = None
        if not self.page_image or not self.canvas:
            return
        self._layout_page_in_canvas()
        self._show_annotations()

    def _layout_page_in_canvas(self) -> None:
        """将 PDF 页面置于滚动区域中央，并调整初始滚动位置"""
        if not self.page_image or not self.canvas:
            return

        pad = 24
        pw, ph = self.page_image.size
        self.canvas.update_idletasks()
        cw = max(self.canvas.winfo_width(), 1)
        ch = max(self.canvas.winfo_height(), 1)

        region_w = max(pw + pad * 2, cw)
        region_h = max(ph + pad * 2, ch)
        self._page_offset_x = (region_w - pw) // 2
        self._page_offset_y = (region_h - ph) // 2

        if self._page_image_id:
            self.canvas.coords(
                self._page_image_id,
                self._page_offset_x,
                self._page_offset_y,
            )
        else:
            self._page_image_id = self.canvas.create_image(
                self._page_offset_x,
                self._page_offset_y,
                anchor="nw",
                image=self.tk_image,
            )

        self.canvas.configure(scrollregion=(0, 0, region_w, region_h))

        if region_w > cw:
            self.canvas.xview_moveto(
                max(0, (self._page_offset_x + pw / 2 - cw / 2) / (region_w - cw))
            )
        else:
            self.canvas.xview_moveto(0)

        if region_h > ch:
            self.canvas.yview_moveto(
                max(0, (self._page_offset_y + ph / 2 - ch / 2) / (region_h - ch))
            )
        else:
            self.canvas.yview_moveto(0)

    def _on_canvas_scroll(self, event) -> str:
        """滚轮上下滚动页面（与 Web 预览一致，不用滚轮缩放）"""
        if not hasattr(self, "canvas"):
            return "break"
        delta = int(-1 * (event.delta / 120)) if event.delta else 0
        if delta:
            self.canvas.yview_scroll(delta, "units")
        return "break"

    def _on_canvas_scroll_linux_up(self, event) -> str:
        self.canvas.yview_scroll(-3, "units")
        return "break"

    def _on_canvas_scroll_linux_down(self, event) -> str:
        self.canvas.yview_scroll(3, "units")
        return "break"

    def _destroy_preview_shell(self) -> None:
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        self._preview_shell_ready = False

    def _render_page(self) -> None:
        """渲染当前页面"""
        if not self.pdf_doc:
            return

        try:
            import fitz  # PyMuPDF
        except ImportError:
            show_warning(self, "错误", "请安装PyMuPDF: pip install pymupdf")
            return

        self._ensure_preview_shell()

        page = self.pdf_doc[self.current_page]
        mat = fitz.Matrix(self.zoom_level * 2, self.zoom_level * 2)
        pix = page.get_pixmap(matrix=mat)

        img_data = pix.tobytes("png")
        self.page_image = Image.open(io.BytesIO(img_data))
        self.tk_image = ImageTk.PhotoImage(self.page_image)

        self.canvas.delete("all")
        self._page_image_id = None
        self._page_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

        self._normalize_markers(self.current_page)
        self._layout_page_in_canvas()
        self._show_annotations()

        bbox = self.canvas.bbox("all")
        if bbox:
            x1, y1, x2, y2 = bbox
            region = self.canvas.cget("scrollregion").split()
            if len(region) == 4:
                rw, rh = float(region[2]), float(region[3])
                self.canvas.configure(
                    scrollregion=(
                        min(0, x1),
                        min(0, y1),
                        max(rw, x2),
                        max(rh, y2),
                    )
                )

        self.page_label.configure(text=f"{self.current_page + 1} / {self.total_pages}")
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
        self._update_annotation_list()
        self.sync_web_preview()

    def _show_annotations(self) -> None:
        """显示当前页面的批注（小标记 + 双击弹层）"""
        if not self.canvas:
            return

        self.canvas.delete("annotation")
        markers = self.annotations.get(self.current_page, [])
        canvas_w = (
            self._page_offset_x + self.page_image.width
            if self.page_image
            else 2000
        )

        for idx, marker in enumerate(markers, start=1):
            x, y = self._marker_to_canvas(marker)
            size = AnnotationMarker.MARKER_SIZE

            marker.icon_rect = (x, y, x + size, y + size)
            rect_id = self.canvas.create_rectangle(
                x, y, x + size, y + size,
                fill=UITheme.MARKER_FILL,
                outline=marker.color or UITheme.MARKER_OUTLINE_DEFAULT,
                width=2,
                tags="annotation",
            )
            self.canvas.create_text(
                x + size / 2, y + size / 2,
                text=str(idx),
                anchor="center",
                fill=UITheme.POPUP_TEXT,
                font=("Arial", 10, "bold"),
                tags="annotation",
            )
            marker.canvas_id = rect_id
            marker.text_id = rect_id

            if not marker.is_expanded:
                marker.popup_rect = None
                marker.close_rect = None
                continue

            pw = AnnotationMarker.POPUP_WIDTH
            ph = marker._calc_popup_height()
            px = x + AnnotationMarker.POPUP_OFFSET_X
            if px + pw > canvas_w:
                px = max(4, x - pw - 8)

            marker.popup_x = px
            marker.popup_y = y
            marker.popup_rect = (px, y, px + pw, y + ph)
            marker.close_rect = None

            self.canvas.create_rectangle(
                px + 3, y + 3, px + pw + 3, y + ph + 3,
                fill=UITheme.POPUP_SHADOW,
                outline="",
                tags="annotation",
            )

            popup_host = self._build_annotation_popup(marker, idx, pw, ph)
            marker.popup_window_id = self.canvas.create_window(
                px,
                y,
                window=popup_host,
                anchor="nw",
                width=pw,
                height=ph,
                tags="annotation",
            )

    def _build_annotation_popup(
        self, marker: AnnotationMarker, idx: int, pw: int, ph: int
    ) -> ctk.CTkFrame:
        """固定尺寸弹层容器，正文在框内滚动，避免超出白框"""
        outline = marker.color or UITheme.MARKER_OUTLINE_DEFAULT

        def on_close() -> None:
            marker.collapse()
            self.selected_marker = None
            self._show_annotations()
            self._update_annotation_list()

        host = ctk.CTkFrame(
            self.canvas,
            width=pw,
            height=ph,
            fg_color=UITheme.POPUP_BG,
            border_color=outline,
            border_width=2,
            corner_radius=UITheme.RADIUS,
        )
        host.pack_propagate(False)
        host.grid_propagate(False)

        header = ctk.CTkFrame(host, fg_color="transparent", height=AnnotationMarker.TITLE_AREA)
        header.pack(fill="x", padx=8, pady=(6, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text=f"批注 {idx}",
            font=UITheme.font_section(),
            text_color=outline,
        ).pack(side="left", padx=4)

        close_btn = ctk.CTkButton(
            header,
            text="✕",
            width=28,
            height=28,
            corner_radius=UITheme.RADIUS_SM,
            fg_color=UITheme.PURPLE_100,
            hover_color=UITheme.PURPLE_200,
            text_color=outline,
            command=on_close,
        )
        close_btn.pack(side="right", padx=2)
        marker.close_rect = None

        body_h = max(
            ph - AnnotationMarker.TITLE_AREA - AnnotationMarker.POPUP_PADDING,
            48,
        )
        text_box = ctk.CTkTextbox(
            host,
            height=body_h,
            wrap="word",
            font=UITheme.font_body(),
            fg_color=UITheme.POPUP_BG,
            text_color=UITheme.POPUP_TEXT,
            border_width=0,
            activate_scrollbars=True,
        )
        text_box.pack(fill="both", expand=True, padx=10, pady=(2, 10))
        UITheme.style_textbox(text_box)
        text_box.configure(fg_color=UITheme.POPUP_BG, border_width=0)
        text_box.insert("1.0", marker.text)
        text_box.configure(state="disabled")

        return host

    def _point_in_rect(self, x: float, y: float, rect) -> bool:
        if not rect:
            return False
        x1, y1, x2, y2 = rect
        return x1 <= x <= x2 and y1 <= y <= y2

    def _find_marker_at(self, x: float, y: float, *, icon_only: bool = False) -> AnnotationMarker:
        """根据坐标查找批注"""
        markers = self.annotations.get(self.current_page, [])
        for marker in reversed(markers):
            if self._point_in_rect(x, y, marker.icon_rect):
                return marker
            if not icon_only and marker.is_expanded and self._point_in_rect(x, y, marker.popup_rect):
                return marker
        return None

    def _collapse_all_markers(self) -> bool:
        need_refresh = False
        for marker in self.annotations.get(self.current_page, []):
            if marker.is_expanded:
                marker.collapse()
                need_refresh = True
        return need_refresh

    def _select_marker(self, marker: AnnotationMarker) -> None:
        """选择批注（侧边栏同步）"""
        self.selected_marker = marker
        self.annotation_input.delete("1.0", "end")
        self.annotation_input.insert("1.0", marker.text)
        self.color_var.set(marker.color)
        self._update_annotation_list()

    def _expand_marker(self, marker: AnnotationMarker) -> None:
        for m in self.annotations.get(self.current_page, []):
            if m != marker:
                m.collapse()
        marker.toggle_expand()
        self._select_marker(marker)
        self._show_annotations()

    def _on_canvas_press(self, event) -> None:
        """鼠标按下：选中批注并准备拖动"""
        if not self.canvas:
            return

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self._press_pos = (x, y)
        self._did_drag = False

        clicked_marker = self._find_marker_at(x, y, icon_only=True)
        if clicked_marker:
            self.selected_marker = clicked_marker
            self.dragging = True
            pdf_x, pdf_y = self._canvas_to_pdf(x, y)
            clicked_marker.drag_data = {
                "x": pdf_x - clicked_marker.x,
                "y": pdf_y - clicked_marker.y,
            }
            self._select_marker(clicked_marker)
        else:
            self.selected_marker = None
            self.dragging = False

    def _on_canvas_drag(self, event) -> None:
        """鼠标拖动：移动批注"""
        if not self.dragging or not self.selected_marker:
            return

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        if self._press_pos:
            dx = abs(x - self._press_pos[0])
            dy = abs(y - self._press_pos[1])
            if dx > 3 or dy > 3:
                self._did_drag = True

        pdf_x, pdf_y = self._canvas_to_pdf(x, y)
        marker = self.selected_marker
        page = self.pdf_doc[self.current_page]
        size = AnnotationMarker.MARKER_SIZE
        marker.x = max(0, min(pdf_x - marker.drag_data["x"], page.rect.width - size))
        marker.y = max(0, min(pdf_y - marker.drag_data["y"], page.rect.height - size))

        self._show_annotations()

    def _on_canvas_release(self, event) -> None:
        """鼠标释放：区分点击与拖动"""
        if not self.canvas:
            return

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        if self._did_drag:
            self.dragging = False
            self.update_status("批注位置已更新")
            self.sync_web_preview()
            return

        clicked_marker = self._find_marker_at(x, y)

        if clicked_marker:
            if clicked_marker.is_expanded and clicked_marker.close_rect and self._point_in_rect(
                x, y, clicked_marker.close_rect
            ):
                clicked_marker.collapse()
                self.selected_marker = None
                self._show_annotations()
                self._update_annotation_list()
            else:
                self._select_marker(clicked_marker)
        else:
            if self._collapse_all_markers():
                self.selected_marker = None
                self._show_annotations()
                self._update_annotation_list()

            if hasattr(self, "_adding_annotation") and self._adding_annotation:
                self._create_annotation_at(x, y)
                self._adding_annotation = False
                self.mode_hint.configure(text="拖动标记可移动，双击查看批注，点击空白处关闭")

        self.dragging = False
        self._press_pos = None
        self._did_drag = False

    def _on_canvas_double_click(self, event) -> None:
        """双击标记展开/收起批注弹层"""
        if not self.canvas:
            return

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        marker = self._find_marker_at(x, y, icon_only=True)
        if not marker:
            return

        if marker.is_expanded:
            marker.collapse()
            self.selected_marker = None
            self._show_annotations()
            self._update_annotation_list()
        else:
            self._expand_marker(marker)

    def _add_annotation_mode(self) -> None:
        """进入添加批注模式"""
        self._adding_annotation = True
        self.mode_hint.configure(text="请点击PDF页面放置批注，之后可拖动移动")

    def _create_annotation_at(self, x: int, y: int) -> None:
        """在指定位置创建批注"""
        text = self.annotation_input.get("1.0", "end-1c")
        if not text.strip():
            text = "新批注"
            self.annotation_input.delete("1.0", "end")
            self.annotation_input.insert("1.0", text)

        pdf_x, pdf_y = self._canvas_to_pdf(x, y)
        color = self.color_var.get()

        marker = AnnotationMarker(int(pdf_x), int(pdf_y), text, color)

        if self.current_page not in self.annotations:
            self.annotations[self.current_page] = []

        self.annotations[self.current_page].append(marker)
        self.selected_marker = marker

        # 重新显示批注
        self._show_annotations()
        self._update_annotation_list()

        self.update_status("批注已添加")
        self.sync_web_preview()

    def _save_annotation(self) -> None:
        """保存批注内容"""
        if not self.selected_marker:
            show_warning(self, "警告", "请先选择一个批注")
            return

        text = self.annotation_input.get("1.0", "end-1c")
        if not text.strip():
            show_warning(self, "警告", "批注内容不能为空")
            return

        self.selected_marker.text = text
        self.selected_marker.color = self.color_var.get()
        self.selected_marker.refresh_expanded_size()

        self._show_annotations()
        self._update_annotation_list()

        self.update_status("批注已保存")
        self.sync_web_preview()

    def _delete_annotation(self) -> None:
        """删除批注"""
        if not self.selected_marker:
            show_warning(self, "警告", "请先选择一个批注")
            return

        markers = self.annotations.get(self.current_page, [])
        if self.selected_marker in markers:
            markers.remove(self.selected_marker)
            self.selected_marker = None

            self.annotation_input.delete("1.0", "end")
            self._show_annotations()
            self._update_annotation_list()

            self.update_status("批注已删除")
            self.sync_web_preview()

    def _set_color(self, color: str) -> None:
        """设置批注颜色"""
        self.color_var.set(color)
        if self.selected_marker:
            self.selected_marker.color = color
            self._show_annotations()

    def _update_annotation_list(self) -> None:
        """更新批注列表"""
        # 清空列表
        for widget in self.annotation_list.winfo_children():
            widget.destroy()

        markers = self.annotations.get(self.current_page, [])

        list_pad = UITheme.PAD_SM
        for idx, marker in enumerate(markers):
            frame = ctk.CTkFrame(self.annotation_list, fg_color="transparent", cursor="hand2")
            frame.pack(fill="x", pady=3, padx=0)
            frame.bind("<Button-1>", lambda _e, m=marker: self._select_marker(m))
            UITheme.style_annotation_row(frame, selected=(marker == self.selected_marker))

            inner = ctk.CTkFrame(frame, fg_color="transparent", cursor="hand2")
            inner.pack(fill="x", padx=list_pad, pady=6)
            inner.bind("<Button-1>", lambda _e, m=marker: self._select_marker(m))
            inner.grid_columnconfigure(1, weight=1)

            color_indicator = ctk.CTkLabel(
                inner,
                text="●",
                text_color=marker.color,
                font=("Arial", 16),
                width=20,
            )
            color_indicator.grid(row=0, column=0, padx=(0, 6), sticky="w")
            color_indicator.bind("<Button-1>", lambda _e, m=marker: self._select_marker(m))

            preview_text = format_annotation_list_preview(marker.text)
            text_label = ctk.CTkLabel(
                inner,
                text=preview_text,
                anchor="w",
                justify="left",
                font=UITheme.font_body(),
                text_color=UITheme.TEXT,
                cursor="hand2",
            )
            text_label.grid(row=0, column=1, sticky="ew")
            text_label.bind("<Button-1>", lambda _e, m=marker: self._select_marker(m))

    def _prev_page(self) -> None:
        """上一页"""
        if not self.pdf_doc:
            return

        if self.current_page > 0:
            self._collapse_all_markers()
            self.current_page -= 1
            self._render_page()

    def _next_page(self) -> None:
        """下一页"""
        if not self.pdf_doc:
            return

        if self.current_page < self.total_pages - 1:
            self._collapse_all_markers()
            self.current_page += 1
            self._render_page()

    def _zoom_in(self) -> None:
        """放大"""
        if self.zoom_level < 3.0:
            self.zoom_level += 0.1
            self._render_page()
            self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")

    def _zoom_out(self) -> None:
        """缩小"""
        if self.zoom_level > 0.5:
            self.zoom_level -= 0.1
            self._render_page()
            self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")

    def _zoom_reset(self) -> None:
        """重置缩放"""
        self.zoom_level = 1.0
        self._render_page()
        self.zoom_label.configure(text="100%")

    def _remove_current_file(self) -> None:
        """移除当前选中的文件"""
        if self.current_file_index < 0 or not self.selected_files:
            self.update_status("没有可移除的文件")
            return
        self._remove_file(self.current_file_index)

    def _remove_file(self, index: int) -> None:
        """从列表中移除已导入的文件（不删除磁盘原文件）"""
        if not (0 <= index < len(self.selected_files)):
            return

        removed = self.selected_files[index]
        file_name = os.path.basename(removed)
        key = self._file_key(removed)
        has_annotations = bool(self.annotations_by_file.get(key))

        if has_annotations:
            if not ask_yes_no(
                self,
                "确认移除",
                f"确定从列表中移除「{file_name}」吗？\n该文件的批注也会一并删除（不会删除磁盘上的原文件）。",
            ):
                return

        self._persist_current_file_annotations()
        self.selected_files.pop(index)
        self.annotations_by_file.pop(key, None)
        self.converted_pdf_paths.pop(key, None)

        if index == self.current_file_index:
            if self.pdf_doc:
                self.pdf_doc.close()
                self.pdf_doc = None

            if self.selected_files:
                new_index = min(index, len(self.selected_files) - 1)
                self._on_file_select(new_index)
            else:
                self.current_file_index = -1
                self.total_pages = 0
                self.current_page = 0
                self.annotations = {}
                self.selected_marker = None

                self._destroy_preview_shell()
                self.file_hint.configure(text="导入文件")

        elif index < self.current_file_index:
            self.current_file_index -= 1

        self.update_file_list(self.selected_files)
        self.update_status(f"已移除: {file_name}")
        self.sync_web_preview()
        self._flush_persist()
