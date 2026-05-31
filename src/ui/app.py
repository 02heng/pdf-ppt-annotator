import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import List, Dict, Tuple
from PIL import Image, ImageTk
import io

from src.models.config import Settings
from src.ui.toolbar import Toolbar
from src.ui.status_bar import StatusBar


class AnnotationMarker:
    """批注标记"""

    def __init__(self, x: int, y: int, text: str, color: str = "#FF6B6B"):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        
        # 折叠状态（小方块）
        self.collapsed_width = 24
        self.collapsed_height = 24
        
        # 展开状态
        self.expanded_width = 200
        self.expanded_height = 150
        
        # 当前状态
        self.is_expanded = False
        self.width = self.collapsed_width
        self.height = self.collapsed_height
        
        self.canvas_id = None
        self.text_id = None
        self.expand_btn_id = None
        self.drag_data = {"x": 0, "y": 0}

    def toggle_expand(self):
        """切换展开/折叠状态"""
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.width = self.expanded_width
            self.height = self.expanded_height
        else:
            self.width = self.collapsed_width
            self.height = self.collapsed_height

    def collapse(self):
        """折叠"""
        self.is_expanded = False
        self.width = self.collapsed_width
        self.height = self.collapsed_height


class App(ctk.CTk):
    """主应用窗口"""

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

        # 批注相关
        self.annotations: Dict[int, List[AnnotationMarker]] = {}  # {page_num: [markers]}
        self.selected_marker: AnnotationMarker = None
        self.dragging = False

        # 配置窗口
        self.title("PDF/PPT 中文批注工具")
        self.geometry("1400x900")

        # 设置主题
        ctk.set_appearance_mode(settings.app.theme)
        ctk.set_default_color_theme("blue")

        # 创建 UI 组件
        self._create_widgets()

        # 配置布局
        self._configure_layout()

        # 绑定快捷键
        self.bind("<Control-plus>", lambda e: self._zoom_in())
        self.bind("<Control-minus>", lambda e: self._zoom_out())
        self.bind("<Control-0>", lambda e: self._zoom_reset())

    def _create_widgets(self) -> None:
        """创建 UI 组件"""
        # 工具栏
        self.toolbar = Toolbar(self)

        # 主内容区域
        self.content_frame = ctk.CTkFrame(self)

        # 左侧文件列表
        self.file_list_frame = ctk.CTkFrame(self.content_frame, width=200)
        self._create_file_list()

        # 中间预览区域
        self.preview_frame = ctk.CTkFrame(self.content_frame)

        # 右侧批注面板
        self.sidebar_frame = ctk.CTkFrame(self.content_frame, width=320)
        self._create_sidebar()

        # 状态栏
        self.status_bar = StatusBar(self)

    def _create_file_list(self) -> None:
        """创建文件列表"""
        # 标题
        title_label = ctk.CTkLabel(
            self.file_list_frame,
            text="文件列表",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=10)

        # 文件列表
        self.file_listbox = ctk.CTkScrollableFrame(self.file_list_frame)
        self.file_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # 提示标签
        self.file_hint = ctk.CTkLabel(
            self.file_list_frame,
            text="导入文件",
            text_color="gray"
        )
        self.file_hint.pack(pady=10)

    def _create_sidebar(self) -> None:
        """创建批注侧边栏"""
        # 标题
        title_frame = ctk.CTkFrame(self.sidebar_frame)
        title_frame.pack(fill="x", padx=5, pady=5)

        title_label = ctk.CTkLabel(
            title_frame,
            text="批注管理",
            font=("Arial", 14, "bold")
        )
        title_label.pack(side="left", padx=10)

        # 添加批注按钮
        add_btn = ctk.CTkButton(
            title_frame,
            text="+ 添加",
            width=70,
            command=self._add_annotation_mode
        )
        add_btn.pack(side="right", padx=5)

        # 当前页面批注列表
        self.annotation_list = ctk.CTkScrollableFrame(self.sidebar_frame)
        self.annotation_list.pack(fill="both", expand=True, padx=5, pady=5)

        # 批注编辑区域
        edit_frame = ctk.CTkFrame(self.sidebar_frame)
        edit_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(edit_frame, text="批注内容:").pack(anchor="w", padx=5, pady=2)

        self.annotation_input = ctk.CTkTextbox(edit_frame, height=80)
        self.annotation_input.pack(fill="x", padx=5, pady=2)

        # 按钮区域
        btn_frame = ctk.CTkFrame(edit_frame)
        btn_frame.pack(fill="x", padx=5, pady=5)

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
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self._delete_annotation
        )
        self.delete_btn.pack(side="left", padx=5)

        # 批注颜色选择
        color_frame = ctk.CTkFrame(edit_frame)
        color_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(color_frame, text="颜色:").pack(side="left", padx=5)

        self.color_var = ctk.StringVar(value="#FF6B6B")
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD"]
        for color in colors:
            btn = ctk.CTkButton(
                color_frame,
                text="",
                width=25,
                height=25,
                fg_color=color,
                hover_color=color,
                command=lambda c=color: self._set_color(c)
            )
            btn.pack(side="left", padx=2)

        # 批注模式提示
        self.mode_hint = ctk.CTkLabel(
            self.sidebar_frame,
            text="点击PDF页面添加批注",
            text_color="gray"
        )
        self.mode_hint.pack(pady=5)

    def _configure_layout(self) -> None:
        """配置布局"""
        self.toolbar.pack(fill="x", padx=5, pady=5)
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.file_list_frame.pack(side="left", fill="y")
        self.preview_frame.pack(side="left", fill="both", expand=True)
        self.sidebar_frame.pack(side="right", fill="y")
        self.status_bar.pack(fill="x", padx=5, pady=5)

    def update_status(self, message: str) -> None:
        """更新状态栏消息"""
        self.status_bar.set_message(message)

    def update_progress(self, current: int, total: int, status: str) -> None:
        """更新进度"""
        self.status_bar.set_progress(current, total, status)

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
            frame = ctk.CTkFrame(self.file_listbox)
            frame.pack(fill="x", pady=2)

            # 文件图标和名称
            file_name = file_path.split("/")[-1].split("\\")[-1]
            icon = "📄" if file_name.endswith(".pdf") else "📊"

            # 可点击的文件按钮
            file_btn = ctk.CTkButton(
                frame,
                text=f"{icon} {file_name}",
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda i=idx: self._on_file_select(i)
            )
            file_btn.pack(side="left", fill="x", expand=True, padx=5)

            # 移除按钮
            remove_btn = ctk.CTkButton(
                frame,
                text="×",
                width=25,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda i=idx: self._remove_file(i)
            )
            remove_btn.pack(side="right", padx=2)

        # 默认选中第一个文件
        if files and self.current_file_index < 0:
            self._on_file_select(0)

    def _on_file_select(self, index: int) -> None:
        """选择文件"""
        if 0 <= index < len(self.selected_files):
            self.current_file_index = index
            file_path = self.selected_files[index]
            file_name = file_path.split("/")[-1].split("\\")[-1]

            # 尝试读取文件内容
            self._load_file_content(file_path)

            # 更新状态栏
            self.update_status(f"已选择: {file_name}")

    def _load_file_content(self, file_path: str) -> None:
        """加载文件内容"""
        try:
            if file_path.lower().endswith('.pdf'):
                self._load_pdf(file_path)
            elif file_path.lower().endswith(('.ppt', '.pptx')):
                self._load_ppt(file_path)
            else:
                messagebox.showwarning("警告", "不支持的文件格式")
        except Exception as e:
            messagebox.showerror("错误", f"加载文件时出错: {str(e)}")

    def _load_pdf(self, file_path: str) -> None:
        """加载PDF文件并渲染为图片"""
        try:
            import fitz  # PyMuPDF

            # 关闭之前的文档
            if self.pdf_doc:
                self.pdf_doc.close()

            self.pdf_doc = fitz.open(file_path)
            self.total_pages = len(self.pdf_doc)
            self.current_page = 0

            # 渲染并显示
            self._render_page()

            self.update_status(f"已加载PDF: {self.total_pages}页")

        except ImportError:
            messagebox.showerror("错误", "请安装PyMuPDF: pip install pymupdf")
        except Exception as e:
            messagebox.showerror("错误", f"读取PDF出错: {str(e)}")

    def _load_ppt(self, file_path: str) -> None:
        """加载PPT文件"""
        messagebox.showinfo("提示", "PPT预览功能开发中，当前仅支持PDF文件")

    def _render_page(self) -> None:
        """渲染当前页面"""
        if not self.pdf_doc:
            return

        try:
            import fitz  # PyMuPDF
        except ImportError:
            messagebox.showerror("错误", "请安装PyMuPDF: pip install pymupdf")
            return

        # 清空预览区域
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        # 创建Canvas（放在顶部）
        self.canvas = tk.Canvas(self.preview_frame, bg="#f0f0f0")
        self.canvas.pack(fill="both", expand=True, padx=5, pady=(5, 0))

        # 渲染PDF页面为图片
        page = self.pdf_doc[self.current_page]

        # 根据缩放级别渲染
        mat = fitz.Matrix(self.zoom_level * 2, self.zoom_level * 2)  # 2x for better quality
        pix = page.get_pixmap(matrix=mat)

        # 转换为PIL Image
        img_data = pix.tobytes("png")
        self.page_image = Image.open(io.BytesIO(img_data))

        # 转换为Tkinter PhotoImage
        self.tk_image = ImageTk.PhotoImage(self.page_image)

        # 在Canvas上显示图片
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

        # 设置Canvas滚动区域
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)

        # 显示当前页面的批注
        self._show_annotations()

        # 页面导航（放在底部）
        self._create_page_navigation()

        # 更新页面信息
        self.page_label.configure(text=f"{self.current_page + 1} / {self.total_pages}")

        # 更新批注列表
        self._update_annotation_list()

    def _create_page_navigation(self) -> None:
        """创建页面导航（底部）"""
        nav_frame = ctk.CTkFrame(self.preview_frame)
        nav_frame.pack(fill="x", side="bottom", padx=5, pady=5)

        # 缩放控制（左侧）
        zoom_frame = ctk.CTkFrame(nav_frame)
        zoom_frame.pack(side="left", padx=10)

        zoom_out_btn = ctk.CTkButton(
            zoom_frame,
            text="-",
            width=30,
            command=self._zoom_out
        )
        zoom_out_btn.pack(side="left", padx=2)

        self.zoom_label = ctk.CTkLabel(
            zoom_frame,
            text=f"{int(self.zoom_level * 100)}%",
            width=50
        )
        self.zoom_label.pack(side="left", padx=5)

        zoom_in_btn = ctk.CTkButton(
            zoom_frame,
            text="+",
            width=30,
            command=self._zoom_in
        )
        zoom_in_btn.pack(side="left", padx=2)

        # 页面导航（中间）
        self.prev_btn = ctk.CTkButton(
            nav_frame,
            text="◀ 上一页",
            command=self._prev_page,
            width=100
        )
        self.prev_btn.pack(side="left", padx=20)

        self.page_label = ctk.CTkLabel(
            nav_frame,
            text=f"{self.current_page + 1} / {self.total_pages}",
            font=("Arial", 14, "bold")
        )
        self.page_label.pack(side="left", expand=True)

        self.next_btn = ctk.CTkButton(
            nav_frame,
            text="下一页 ▶",
            command=self._next_page,
            width=100
        )
        self.next_btn.pack(side="right", padx=20)

    def _show_annotations(self) -> None:
        """显示当前页面的批注"""
        if not self.canvas:
            return

        # 删除旧的批注标记
        self.canvas.delete("annotation")

        # 获取当前页面的批注
        markers = self.annotations.get(self.current_page, [])

        for marker in markers:
            x, y = marker.x, marker.y

            if marker.is_expanded:
                # 展开状态：显示完整批注框
                
                # 绘制阴影
                shadow_offset = 3
                self.canvas.create_rectangle(
                    x + shadow_offset, y + shadow_offset,
                    x + marker.width + shadow_offset, y + marker.height + shadow_offset,
                    fill="#999999",
                    outline="",
                    tags="annotation"
                )
                
                # 绘制背景矩形
                rect_id = self.canvas.create_rectangle(
                    x, y, x + marker.width, y + marker.height,
                    fill="white",
                    outline=marker.color,
                    width=2,
                    tags="annotation"
                )

                # 绘制标题栏（带颜色）
                self.canvas.create_rectangle(
                    x, y, x + marker.width, y + 28,
                    fill=marker.color,
                    outline=marker.color,
                    tags="annotation"
                )

                # 绘制标题栏文字
                self.canvas.create_text(
                    x + 10, y + 14,
                    text="批注",
                    anchor="w",
                    fill="white",
                    font=("Microsoft YaHei", 10, "bold"),
                    tags="annotation"
                )

                # 绘制关闭按钮
                self.canvas.create_text(
                    x + marker.width - 20, y + 14,
                    text="✕",
                    anchor="center",
                    fill="white",
                    font=("Arial", 10),
                    tags="annotation"
                )

                # 绘制批注内容
                self.canvas.create_text(
                    x + 10, y + 38,
                    text=marker.text,
                    anchor="nw",
                    fill="#333333",
                    font=("Microsoft YaHei", 10),
                    width=marker.width - 20,
                    tags="annotation"
                )

                # 保存canvas对象ID
                marker.canvas_id = rect_id
                marker.text_id = rect_id
                
            else:
                # 折叠状态：显示小方块和简短预览
                collapsed_width = 120  # 增加宽度以显示预览文本
                collapsed_height = 28
                
                rect_id = self.canvas.create_rectangle(
                    x, y, x + collapsed_width, y + collapsed_height,
                    fill=marker.color,
                    outline="#333333",
                    width=1,
                    tags="annotation"
                )

                # 绘制编号
                idx = markers.index(marker) + 1
                self.canvas.create_text(
                    x + 8, y + collapsed_height / 2,
                    text=f"{idx}",
                    anchor="w",
                    fill="white",
                    font=("Arial", 9, "bold"),
                    tags="annotation"
                )

                # 绘制简短预览文本（截取前15个字符）
                preview_text = marker.text[:15] + "..." if len(marker.text) > 15 else marker.text
                self.canvas.create_text(
                    x + 25, y + collapsed_height / 2,
                    text=preview_text,
                    anchor="w",
                    fill="white",
                    font=("Microsoft YaHei", 9),
                    width=collapsed_width - 30,
                    tags="annotation"
                )

                # 保存canvas对象ID
                marker.canvas_id = rect_id
                marker.text_id = rect_id

    def _on_canvas_click(self, event) -> None:
        """Canvas点击事件"""
        if not self.canvas:
            return

        # 获取点击位置（考虑滚动）
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # 检查是否点击了批注
        clicked_items = self.canvas.find_overlapping(x - 5, y - 5, x + 5, y + 5)
        
        clicked_marker = None

        for item in clicked_items:
            tags = self.canvas.gettags(item)
            if "annotation" in tags:
                # 找到被点击的批注
                markers = self.annotations.get(self.current_page, [])
                for marker in markers:
                    if marker.canvas_id == item or marker.text_id == item:
                        clicked_marker = marker
                        break
                break

        if clicked_marker:
            # 点击了某个批注
            if clicked_marker.is_expanded:
                # 已展开，检查是否点击了关闭按钮
                # 简化处理：点击就折叠
                clicked_marker.collapse()
                self.selected_marker = None
            else:
                # 未展开，先收回其他展开的批注
                markers = self.annotations.get(self.current_page, [])
                for m in markers:
                    if m != clicked_marker:
                        m.collapse()
                
                # 展开点击的批注
                clicked_marker.toggle_expand()
                self.selected_marker = clicked_marker
            
            # 重新显示
            self._show_annotations()
            
            # 更新右侧批注内容
            if self.selected_marker:
                self.annotation_input.delete("1.0", "end")
                self.annotation_input.insert("1.0", self.selected_marker.text)
                self.color_var.set(self.selected_marker.color)
            
            self._update_annotation_list()
        else:
            # 点击了空白区域，收回所有展开的批注
            markers = self.annotations.get(self.current_page, [])
            need_refresh = False
            for marker in markers:
                if marker.is_expanded:
                    marker.collapse()
                    need_refresh = True
            
            if need_refresh:
                self.selected_marker = None
                self._show_annotations()
                self._update_annotation_list()
            
            # 检查是否处于添加批注模式
            if hasattr(self, '_adding_annotation') and self._adding_annotation:
                self._create_annotation_at(x, y)
                self._adding_annotation = False
                self.mode_hint.configure(text="点击PDF页面添加批注")

    def _on_canvas_drag(self, event) -> None:
        """Canvas拖拽事件"""
        if not self.dragging or not self.selected_marker:
            return

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        marker = self.selected_marker

        # 移动批注
        marker.x = x - marker.drag_data["x"]
        marker.y = y - marker.drag_data["y"]

        # 重新显示批注（因为需要更新所有元素位置）
        self._show_annotations()

    def _on_canvas_release(self, event) -> None:
        """Canvas释放事件"""
        self.dragging = False

    def _on_mouse_wheel(self, event) -> None:
        """鼠标滚轮事件"""
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()

    def _add_annotation_mode(self) -> None:
        """进入添加批注模式"""
        self._adding_annotation = True
        self.mode_hint.configure(text="请点击PDF页面放置批注")

    def _create_annotation_at(self, x: int, y: int) -> None:
        """在指定位置创建批注"""
        text = self.annotation_input.get("1.0", "end-1c")
        if not text.strip():
            text = "新批注"
            self.annotation_input.delete("1.0", "end")
            self.annotation_input.insert("1.0", text)

        color = self.color_var.get()

        marker = AnnotationMarker(x, y, text, color)

        if self.current_page not in self.annotations:
            self.annotations[self.current_page] = []

        self.annotations[self.current_page].append(marker)
        self.selected_marker = marker

        # 重新显示批注
        self._show_annotations()
        self._update_annotation_list()

        self.update_status("批注已添加")

    def _save_annotation(self) -> None:
        """保存批注内容"""
        if not self.selected_marker:
            messagebox.showwarning("警告", "请先选择一个批注")
            return

        text = self.annotation_input.get("1.0", "end-1c")
        if not text.strip():
            messagebox.showwarning("警告", "批注内容不能为空")
            return

        self.selected_marker.text = text
        self.selected_marker.color = self.color_var.get()

        self._show_annotations()
        self._update_annotation_list()

        self.update_status("批注已保存")

    def _delete_annotation(self) -> None:
        """删除批注"""
        if not self.selected_marker:
            messagebox.showwarning("警告", "请先选择一个批注")
            return

        markers = self.annotations.get(self.current_page, [])
        if self.selected_marker in markers:
            markers.remove(self.selected_marker)
            self.selected_marker = None

            self.annotation_input.delete("1.0", "end")
            self._show_annotations()
            self._update_annotation_list()

            self.update_status("批注已删除")

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

        for idx, marker in enumerate(markers):
            frame = ctk.CTkFrame(self.annotation_list)
            frame.pack(fill="x", pady=2)

            # 颜色指示器
            color_indicator = ctk.CTkLabel(
                frame,
                text="●",
                text_color=marker.color,
                font=("Arial", 16)
            )
            color_indicator.pack(side="left", padx=5)

            # 批注内容预览
            preview_text = marker.text[:30] + "..." if len(marker.text) > 30 else marker.text
            text_label = ctk.CTkButton(
                frame,
                text=preview_text,
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda m=marker: self._select_marker(m)
            )
            text_label.pack(side="left", fill="x", expand=True, padx=5)

            # 高亮选中的批注
            if marker == self.selected_marker:
                frame.configure(fg_color=("gray80", "gray20"))

    def _select_marker(self, marker: AnnotationMarker) -> None:
        """选择批注"""
        self.selected_marker = marker
        self.annotation_input.delete("1.0", "end")
        self.annotation_input.insert("1.0", marker.text)
        self.color_var.set(marker.color)
        self._update_annotation_list()

    def _prev_page(self) -> None:
        """上一页"""
        if not self.pdf_doc:
            return

        if self.current_page > 0:
            self.current_page -= 1
            self._render_page()

    def _next_page(self) -> None:
        """下一页"""
        if not self.pdf_doc:
            return

        if self.current_page < self.total_pages - 1:
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

    def _remove_file(self, index: int) -> None:
        """移除文件"""
        if 0 <= index < len(self.selected_files):
            removed = self.selected_files.pop(index)

            # 如果移除的是当前选中的文件
            if index == self.current_file_index:
                if self.pdf_doc:
                    self.pdf_doc.close()
                    self.pdf_doc = None

                if self.selected_files:
                    self._on_file_select(0)
                else:
                    self.current_file_index = -1
                    self.total_pages = 0
                    self.current_page = 0

                    # 清空预览区域
                    for widget in self.preview_frame.winfo_children():
                        widget.destroy()

            elif index < self.current_file_index:
                self.current_file_index -= 1

            # 更新文件列表显示
            self.update_file_list(self.selected_files)

            file_name = removed.split("/")[-1].split("\\")[-1]
            self.update_status(f"已移除: {file_name}")
