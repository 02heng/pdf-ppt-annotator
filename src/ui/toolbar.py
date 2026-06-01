import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import datetime
import os
import threading
from typing import Optional


class Toolbar(ctk.CTkFrame):
    """工具栏"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.app = master  # 保存主应用引用
        self._annotating = False
        self._create_widgets()

    def _create_widgets(self) -> None:
        """创建工具栏按钮"""
        # 导入按钮
        self.import_btn = ctk.CTkButton(
            self,
            text="导入文件",
            command=self._on_import
        )
        self.import_btn.pack(side="left", padx=5)

        self.open_project_btn = ctk.CTkButton(
            self,
            text="打开工程",
            command=self._on_open_project,
        )
        self.open_project_btn.pack(side="left", padx=5)

        self.save_project_btn = ctk.CTkButton(
            self,
            text="保存工程",
            command=self._on_save_project,
            fg_color="#2980b9",
            hover_color="#2471a3",
        )
        self.save_project_btn.pack(side="left", padx=5)

        # 开始批注按钮
        self.annotate_btn = ctk.CTkButton(
            self,
            text="开始批注",
            command=self._on_annotate,
            fg_color="#2ecc71",
            hover_color="#27ae60"
        )
        self.annotate_btn.pack(side="left", padx=5)

        # 全部批注按钮
        self.annotate_all_btn = ctk.CTkButton(
            self,
            text="全部批注",
            command=self._on_annotate_all,
            fg_color="#16a085",
            hover_color="#138d75",
        )
        self.annotate_all_btn.pack(side="left", padx=5)

        # 导出按钮
        self.export_btn = ctk.CTkButton(
            self,
            text="导出",
            command=self._on_export
        )
        self.export_btn.pack(side="left", padx=5)

        # 预览（PDF.js）
        self.preview_btn = ctk.CTkButton(
            self,
            text="预览",
            command=self._on_web_preview,
            fg_color="#9b59b6",
            hover_color="#8e44ad",
        )
        self.preview_btn.pack(side="left", padx=5)

        # 批注模式切换
        self.mode_var = ctk.StringVar(value="sidebar")
        self.mode_switch = ctk.CTkSegmentedButton(
            self,
            values=["覆盖", "侧边栏"],
            variable=self.mode_var,
            command=self._on_mode_change
        )
        self.mode_switch.pack(side="left", padx=5)

        # LLM 切换
        self.llm_var = ctk.StringVar(value="openai")
        self.llm_switch = ctk.CTkSegmentedButton(
            self,
            values=["OpenAI", "Ollama", "DeepSeek"],
            variable=self.llm_var,
            command=self._on_llm_change
        )
        self.llm_switch.pack(side="left", padx=5)

        # 设置按钮
        self.settings_btn = ctk.CTkButton(
            self,
            text="设置",
            command=self._on_settings
        )
        self.settings_btn.pack(side="right", padx=5)

    def _on_import(self) -> None:
        """导入文件"""
        filetypes = [
            ("PDF 文件", "*.pdf"),
            ("PPT 文件", "*.ppt *.pptx"),
            ("所有支持的文件", "*.pdf *.ppt *.pptx")
        ]

        files = filedialog.askopenfilenames(
            title="选择文件",
            filetypes=filetypes
        )

        if files:
            # 存储选中的文件
            self.app.selected_files = list(files)

            # 更新文件列表显示
            self.app.update_file_list(list(files))

            # 更新状态栏
            file_names = [f.split("/")[-1].split("\\")[-1] for f in files]
            if len(file_names) == 1:
                self.app.update_status(f"导入成功: {file_names[0]}")
            else:
                self.app.update_status(f"导入成功: 共 {len(files)} 个文件")
            self.app.sync_web_preview()

    def _on_open_project(self) -> None:
        """打开可携带的工程文件"""
        from src.services.project_service import PROJECT_EXT, load_project

        file_path = filedialog.askopenfilename(
            title="打开工程",
            filetypes=[("TO PDF 工程", f"*{PROJECT_EXT}"), ("所有文件", "*.*")],
        )
        if not file_path:
            return
        try:
            load_project(self.app, file_path)
            name = os.path.basename(file_path)
            self.app.update_status(f"已打开工程: {name}")
        except Exception as e:
            self.app.update_status(f"打开工程失败: {str(e)}")
            messagebox.showerror("错误", f"打开工程失败: {str(e)}")

    def _on_save_project(self) -> None:
        """保存工程（含 PDF 与批注，可拷贝到其他电脑打开）"""
        from src.services.project_service import PROJECT_EXT, save_project

        if not self.app.selected_files:
            self.app.update_status("没有可保存的内容，请先导入 PDF")
            return

        self.app._persist_current_file_annotations()

        if self.app.project_file_path and os.path.isfile(self.app.project_file_path):
            target = self.app.project_file_path
        else:
            default_name = "我的批注工程" + PROJECT_EXT
            if self.app.selected_files:
                stem = os.path.splitext(os.path.basename(self.app.selected_files[0]))[0]
                default_name = f"{stem}{PROJECT_EXT}"
            target = filedialog.asksaveasfilename(
                title="保存工程",
                defaultextension=PROJECT_EXT,
                initialfile=default_name,
                filetypes=[("TO PDF 工程", f"*{PROJECT_EXT}")],
            )
            if not target:
                return

        try:
            save_project(self.app, target)
            name = os.path.basename(target)
            self.app.update_status(f"工程已保存: {name}（含 PDF 与批注，可直接拷贝使用）")
        except Exception as e:
            self.app.update_status(f"保存工程失败: {str(e)}")
            messagebox.showerror("错误", f"保存工程失败: {str(e)}")

    def _on_web_preview(self) -> None:
        """打开 PDF.js 批注预览"""
        if not self.app.pdf_doc:
            self.app.update_status("请先导入 PDF 文件")
            return
        self.app.open_web_preview()

    def _validate_annotate_ready(self) -> bool:
        """检查是否满足批注前置条件"""
        if not hasattr(self.app, "selected_files") or not self.app.selected_files:
            messagebox.showwarning("警告", "请先导入文件")
            return False

        provider = self.app.settings.llm.provider
        if provider == "openai" and not self.app.settings.llm.openai.api_key:
            messagebox.showwarning("警告", "请先在设置中配置 OpenAI API Key")
            return False
        if provider == "deepseek" and not self.app.settings.llm.deepseek.api_key:
            messagebox.showwarning("警告", "请先在设置中配置 DeepSeek API Key")
            return False

        if not self.app.pdf_doc:
            messagebox.showwarning("警告", "请先导入PDF文件")
            return False

        return True

    def _set_annotate_buttons_state(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.annotate_btn.configure(state=state)
        self.annotate_all_btn.configure(state=state)

    def _apply_annotations_to_page(self, page_num: int, annotations) -> int:
        """将 AI 批注写入指定页"""
        from src.ui.app import AnnotationMarker

        page = self.app.pdf_doc[page_num]
        existing_markers = self.app.annotations.get(page_num, [])
        scale = self.app.zoom_level * 2
        page_width = page.rect.width

        for i, ann in enumerate(annotations):
            x = (page_width - 170) * scale
            y = (20 + (len(existing_markers) + i) * 75) * scale
            marker = AnnotationMarker(
                x=x,
                y=y,
                text=ann.content,
                color="#FF6B6B",
            )
            existing_markers.append(marker)

        self.app.annotations[page_num] = existing_markers
        return len(annotations)

    def _on_annotate(self) -> None:
        """开始批注（当前页）"""
        if self._annotating:
            return
        if not self._validate_annotate_ready():
            return

        current_page = self.app.current_page
        if current_page < 0 or current_page >= self.app.total_pages:
            messagebox.showwarning("警告", "请选择一个页面")
            return

        self._annotating = True
        self._set_annotate_buttons_state(False)
        self.app.update_status(f"正在将第 {current_page + 1} 页转为图片并分析...")

        def worker():
            try:
                from src.services.annotation_service import AnnotationService
                from src.models.page import Page

                annotation_service = AnnotationService(self.app.settings.llm)
                page = self.app.pdf_doc[current_page]
                page_obj = Page(
                    page_number=current_page,
                    content=page.get_text(),
                    width=page.rect.width,
                    height=page.rect.height,
                )
                pdf_path = self.app.selected_files[self.app.current_file_index]
                annotations = annotation_service.process_page(
                    page_obj,
                    pdf_path=pdf_path,
                    pdf_doc=self.app.pdf_doc,
                )

                def finish():
                    self._annotating = False
                    self._set_annotate_buttons_state(True)
                    if annotations:
                        count = self._apply_annotations_to_page(current_page, annotations)
                        self.app._show_annotations()
                        self.app._update_annotation_list()
                        self.app.update_status(
                            f"第 {current_page + 1} 页批注生成完成，共 {count} 条批注"
                        )
                        self.app.sync_web_preview()
                    else:
                        self.app.update_status("未能生成批注")

                self.app.after(0, finish)
            except Exception as e:
                def fail():
                    self._annotating = False
                    self._set_annotate_buttons_state(True)
                    self.app.update_status(f"批注生成失败: {str(e)}")

                self.app.after(0, fail)

        threading.Thread(target=worker, daemon=True).start()

    def _on_annotate_all(self) -> None:
        """一键生成所有页批注"""
        if self._annotating:
            return
        if not self._validate_annotate_ready():
            return

        total = self.app.total_pages
        if total <= 0:
            messagebox.showwarning("警告", "没有可批注的页面")
            return

        self._annotating = True
        self._set_annotate_buttons_state(False)
        self.app.update_status(f"正在批量生成批注，共 {total} 页...")
        self.app.update_progress(0, total, "准备中...")

        def worker():
            try:
                from src.services.annotation_service import AnnotationService
                from src.models.page import Page

                annotation_service = AnnotationService(self.app.settings.llm)
                pdf_path = self.app.selected_files[self.app.current_file_index]
                page_results = []

                for page_num in range(total):
                    page = self.app.pdf_doc[page_num]
                    page_obj = Page(
                        page_number=page_num,
                        content=page.get_text(),
                        width=page.rect.width,
                        height=page.rect.height,
                    )

                    def update_progress(p=page_num):
                        self.app.update_progress(
                            p + 1,
                            total,
                            f"正在分析第 {p + 1}/{total} 页...",
                        )

                    self.app.after(0, update_progress)

                    annotations = annotation_service.process_page(
                        page_obj,
                        pdf_path=pdf_path,
                        pdf_doc=self.app.pdf_doc,
                    )
                    if annotations:
                        page_results.append((page_num, annotations))

                def finish():
                    self._annotating = False
                    self._set_annotate_buttons_state(True)
                    total_ann = 0
                    for page_num, annotations in page_results:
                        total_ann += self._apply_annotations_to_page(page_num, annotations)
                    pages_with_ann = len(page_results)
                    self.app.update_progress(total, total, "完成")
                    self.app._show_annotations()
                    self.app._update_annotation_list()
                    self.app.sync_web_preview()
                    self.app.update_status(
                        f"全部批注完成：{pages_with_ann}/{total} 页有批注，共 {total_ann} 条"
                    )

                self.app.after(0, finish)
            except Exception as e:
                def fail():
                    self._annotating = False
                    self._set_annotate_buttons_state(True)
                    self.app.update_status(f"批量批注失败: {str(e)}")

                self.app.after(0, fail)

        threading.Thread(target=worker, daemon=True).start()

    def _on_export(self) -> None:
        """导出文件"""
        if not hasattr(self.app, 'selected_files') or not self.app.selected_files:
            messagebox.showwarning("警告", "没有可导出的文件，请先导入并批注文件")
            return

        if not self.app.pdf_doc:
            messagebox.showwarning("警告", "请先导入PDF文件")
            return

        # 检查是否有批注
        self.app._persist_current_file_annotations()
        has_annotations = any(
            pages for pages in self.app.annotations_by_file.values()
        ) or bool(self.app.annotations)
        if not has_annotations:
            messagebox.showwarning("警告", "没有批注可导出，请先添加批注")
            return

        # 默认文件名：原文件名_时间戳
        source_file = self.app.selected_files[self.app.current_file_index]
        source_dir = os.path.dirname(source_file)
        source_stem = os.path.splitext(os.path.basename(source_file))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"{source_stem}_{timestamp}.pdf"

        file_path = filedialog.asksaveasfilename(
            title="导出PDF",
            defaultextension=".pdf",
            initialdir=source_dir,
            initialfile=default_name,
            filetypes=[("PDF 文件", "*.pdf")]
        )

        if file_path:
            try:
                self._export_pdf(file_path)
                file_name = os.path.basename(file_path)
                self.app.update_status(f"导出成功: {file_name}")
            except Exception as e:
                self.app.update_status(f"导出失败: {str(e)}")

    def _export_pdf(self, output_path: str) -> None:
        """导出带批注的 PDF"""
        try:
            import fitz
            from src.utils.pdf_annotation import draw_page_annotations

            self.app._persist_current_file_annotations()
            doc = fitz.open(self.app.selected_files[self.app.current_file_index])
            scale = self.app.zoom_level * 2
            file_path = self.app.selected_files[self.app.current_file_index]
            markers_by_page = self.app.annotations_by_file.get(file_path, self.app.annotations)

            for page_num in range(self.app.total_pages):
                page = doc[page_num]
                markers = markers_by_page.get(page_num, [])
                if markers:
                    draw_page_annotations(page, markers, scale=scale)

            doc.save(output_path)
            doc.close()

        except ImportError:
            raise Exception("请安装PyMuPDF: pip install pymupdf")
        except Exception as e:
            raise Exception(f"导出PDF出错: {str(e)}")

    def _on_mode_change(self, value: str) -> None:
        """切换批注模式"""
        mode = "overlay" if value == "覆盖" else "sidebar"
        self.app.settings.annotation.mode = mode
        self.app.update_status(f"批注模式已切换为: {value}")

    def _on_llm_change(self, value: str) -> None:
        """切换 LLM"""
        provider_map = {
            "OpenAI": "openai",
            "Ollama": "ollama",
            "DeepSeek": "deepseek"
        }
        provider = provider_map.get(value, "openai")
        self.app.settings.llm.provider = provider
        self.app.update_status(f"LLM 已切换为: {value}")

    def _on_settings(self) -> None:
        """打开设置"""
        from src.ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.app, self.app.settings)
        self.app.wait_window(dialog)

        if dialog.result:
            self.app.settings = dialog.result
            
            # 保存配置到文件
            try:
                from src.main import save_config
                save_config(self.app.settings)
                self.app.update_status("设置已保存并持久化到文件")
                messagebox.showinfo("成功", "设置已保存，API Key已持久化")
            except Exception as e:
                self.app.update_status(f"设置已保存，但持久化失败: {str(e)}")
                messagebox.showwarning("警告", f"设置已保存，但持久化到文件失败: {str(e)}")
