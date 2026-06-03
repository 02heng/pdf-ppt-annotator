import customtkinter as ctk
from tkinter import filedialog

from src.ui.message_dialog import ask_page_range, ask_yes_no, show_info, show_warning
from datetime import datetime
import os
import threading
from typing import Optional

from src.ui.theme import UITheme
from src.ui.chrome import GradientToolbar
from src.utils.branding import load_toolbar_logo_ctk


class Toolbar(GradientToolbar):
    """渐变顶栏 + 分组操作"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.app = master
        self._annotating = False
        self._create_widgets()

    def _divider(self, parent) -> ctk.CTkFrame:
        d = ctk.CTkFrame(parent, width=1, height=28)
        d.pack(side="left", padx=10, pady=6)
        UITheme.style_toolbar_divider(d)
        d.pack_propagate(False)
        return d

    def _create_widgets(self) -> None:
        row = self.inner
        pad = UITheme.PAD_SM

        brand_row = ctk.CTkFrame(row, fg_color="transparent")
        brand_row.pack(side="left", padx=(UITheme.PAD, pad))
        logo = load_toolbar_logo_ctk(32)
        if logo:
            ctk.CTkLabel(brand_row, text="", image=logo, width=32).pack(
                side="left", padx=(0, 6)
            )
        self.brand = ctk.CTkLabel(brand_row, text="TO PDF · 中文批注")
        self.brand.pack(side="left")
        UITheme.style_toolbar_brand(self.brand)
        self._divider(row)

        self.import_btn = ctk.CTkButton(row, text="导入", command=self._on_import)
        self.import_btn.pack(side="left", padx=pad)
        UITheme.style_toolbar_button(self.import_btn, primary=True)

        self.open_project_btn = ctk.CTkButton(row, text="打开工程", command=self._on_open_project)
        self.open_project_btn.pack(side="left", padx=pad)
        UITheme.style_toolbar_button(self.open_project_btn)

        self.save_project_btn = ctk.CTkButton(row, text="保存工程", command=self._on_save_project)
        self.save_project_btn.pack(side="left", padx=pad)
        UITheme.style_toolbar_button(self.save_project_btn)
        self._divider(row)

        self.annotate_btn = ctk.CTkButton(row, text="开始批注", command=self._on_annotate)
        self.annotate_btn.pack(side="left", padx=pad)
        UITheme.style_toolbar_button(self.annotate_btn, primary=True)

        self.annotate_all_btn = ctk.CTkButton(row, text="全部批注", command=self._on_annotate_all)
        self.annotate_all_btn.pack(side="left", padx=pad)
        UITheme.style_toolbar_button(self.annotate_all_btn)
        self._divider(row)

        self.export_btn = ctk.CTkButton(row, text="导出", command=self._on_export)
        self.export_btn.pack(side="left", padx=pad)
        UITheme.style_toolbar_button(self.export_btn)

        self.preview_btn = ctk.CTkButton(row, text="预览", command=self._on_web_preview)
        self.preview_btn.pack(side="left", padx=pad)
        UITheme.style_toolbar_button(self.preview_btn)

        # 顶栏不展示「覆盖/侧边栏」「OpenAI/Ollama/DeepSeek」分段控件，改在系统 API 设置中配置
        self._init_toolbar_state_vars()

        self.settings_btn = ctk.CTkButton(
            row,
            text="系统 API 设置",
            width=140,
            command=self._on_settings,
        )
        self.settings_btn.pack(side="right", padx=(pad, UITheme.PAD))
        UITheme.style_toolbar_button(self.settings_btn, primary=True)

    def _init_toolbar_state_vars(self) -> None:
        """与配置文件同步（无顶栏分段控件时使用）"""
        mode_map = {"overlay": "覆盖", "sidebar": "侧边栏"}
        llm_map = {"openai": "OpenAI", "ollama": "Ollama", "deepseek": "DeepSeek"}
        mode = getattr(self.app.settings.annotation, "mode", "sidebar")
        provider = getattr(self.app.settings.llm, "provider", "openai")
        self.mode_var = ctk.StringVar(value=mode_map.get(mode, "侧边栏"))
        self.llm_var = ctk.StringVar(value=llm_map.get(provider, "OpenAI"))

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
            self.app._persist_current_file_annotations()
            existing = list(self.app.selected_files)
            existing_norm = {os.path.normpath(p) for p in existing}
            added: list[str] = []

            for f in files:
                norm = os.path.normpath(f)
                if norm not in existing_norm:
                    added.append(f)
                    existing.append(f)
                    existing_norm.add(norm)

            if not existing:
                existing = list(files)
                added = list(files)

            self.app.selected_files = existing
            self.app.update_file_list(existing)

            select_path = added[-1] if added else files[0]
            select_norm = os.path.normpath(select_path)
            for idx, path in enumerate(existing):
                if os.path.normpath(path) == select_norm:
                    self.app._on_file_select(idx)
                    break

            file_names = [os.path.basename(f) for f in (added if added else files)]
            if len(file_names) == 1:
                self.app.update_status(f"导入成功: {file_names[0]}")
            elif added:
                self.app.update_status(f"新增 {len(added)} 个文件，共 {len(existing)} 个")
            else:
                self.app.update_status(f"文件已在列表中，共 {len(existing)} 个")
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
            show_warning(self.app, "错误", f"打开工程失败: {str(e)}")

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
            show_warning(self.app, "错误", f"保存工程失败: {str(e)}")

    def _on_web_preview(self) -> None:
        """打开 PDF.js 批注预览"""
        if not self.app.pdf_doc:
            self.app.update_status("请先导入 PDF 文件")
            return
        self.app.open_web_preview()

    def _validate_annotate_ready(self) -> bool:
        """检查是否满足批注前置条件"""
        if not hasattr(self.app, "selected_files") or not self.app.selected_files:
            show_warning(self.app, "警告", "请先导入文件")
            return False

        provider = self.app.settings.llm.provider
        if provider == "openai" and not self.app.settings.llm.openai.api_key:
            show_warning(self.app, "警告", "请先在设置中配置 OpenAI API Key")
            return False
        if provider == "deepseek" and not self.app.settings.llm.deepseek.api_key:
            show_warning(self.app, "警告", "请先在设置中配置 DeepSeek API Key")
            return False

        if not self.app.pdf_doc:
            show_warning(self.app, "警告", "请先导入 PDF 或 PPT 文件")
            return False

        return True

    def _set_annotate_buttons_state(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.annotate_btn.configure(state=state)
        self.annotate_all_btn.configure(state=state)

    def _apply_annotations_to_page(
        self,
        page_num: int,
        annotations,
        *,
        replace: bool = False,
    ) -> int:
        """将 AI 批注写入指定页（坐标为 PDF 页坐标）"""
        from src.ui.app import AnnotationMarker

        page = self.app.pdf_doc[page_num]
        page_w = page.rect.width
        page_h = page.rect.height
        marker_size = AnnotationMarker.MARKER_SIZE

        if replace:
            existing_markers = []
        else:
            existing_markers = list(self.app.annotations.get(page_num, []))

        for i, ann in enumerate(annotations):
            x = float(getattr(ann, "position_x", 0) or 0)
            y = float(getattr(ann, "position_y", 0) or 0)
            if x <= 0:
                x = max(page_w - marker_size - 12, 12)
            if y <= 0:
                y = 24 + (len(existing_markers) + i) * (marker_size + 10)
            x = max(0, min(x, page_w - marker_size))
            y = max(0, min(y, page_h - marker_size))

            marker = AnnotationMarker(
                x=int(x),
                y=int(y),
                text=ann.content,
                color="#FF6B6B",
            )
            existing_markers.append(marker)

        self.app.annotations[page_num] = existing_markers
        self.app._persist_current_file_annotations()
        return len(annotations)

    def _annotate_one_page(
        self,
        annotation_service,
        page_num: int,
        source_path: str,
        pdf_path: str,
        *,
        document_context: str = "",
        total_pages: int = 0,
        page_image=None,
        use_multi_agent: bool = False,
        cache_friendly: bool = False,
    ):
        """单页批注；use_multi_agent 时走四智能体；cache_friendly 时走前缀稳定单模型"""
        from src.models.page import Page

        page = self.app.pdf_doc[page_num]
        page_obj = Page(
            page_number=page_num,
            content="",
            width=page.rect.width,
            height=page.rect.height,
        )
        return annotation_service.process_page(
            page_obj,
            pdf_path=pdf_path,
            pdf_doc=self.app.pdf_doc,
            source_path=source_path,
            document_context=document_context,
            total_pages=total_pages or self.app.total_pages,
            page_image=page_image,
            multi_agent=use_multi_agent,
            cache_friendly=cache_friendly,
        )

    def _on_annotate(self) -> None:
        """开始批注（当前页）"""
        if self._annotating:
            return
        if not self._validate_annotate_ready():
            return

        current_page = self.app.current_page
        if current_page < 0 or current_page >= self.app.total_pages:
            show_warning(self.app, "警告", "请选择一个页面")
            return

        self._annotating = True
        self._set_annotate_buttons_state(False)
        self.app.update_status(f"正在将第 {current_page + 1} 页转为图片并分析...")

        def worker():
            try:
                from src.services.annotation_service import AnnotationService

                annotation_service = AnnotationService(self.app.settings.llm)
                source_path = self.app.selected_files[self.app.current_file_index]
                pdf_path = self.app.get_render_pdf_path(source_path)

                annotations = self._annotate_one_page(
                    annotation_service,
                    current_page,
                    source_path,
                    pdf_path,
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

    def _apply_annotations_to_page_ui(
        self,
        page_num: int,
        annotations,
        *,
        done: int,
        job_total: int,
    ) -> int:
        """主线程：写入批注并刷新界面（当前页立即显示标记）"""
        count = self._apply_annotations_to_page(
            page_num, annotations, replace=True
        )
        self.app._normalize_markers(page_num)
        if page_num == self.app.current_page:
            self.app._show_annotations()
        self.app._update_annotation_list()
        self.app.sync_web_preview()
        self.app.update_status(
            f"第 {page_num + 1} 页批注已生成（{done}/{job_total}）"
        )
        return count

    def _on_annotate_all(self) -> None:
        """批量生成批注：先选页码范围，生成一页即显示一页"""
        if self._annotating:
            return
        if not self._validate_annotate_ready():
            return

        total = self.app.total_pages
        if total <= 0:
            show_warning(self.app, "警告", "没有可批注的页面")
            return

        page_range = ask_page_range(self.app, total)
        if page_range is None:
            return

        start_page_1, end_page_1 = page_range
        start_idx = start_page_1 - 1
        end_idx = end_page_1 - 1
        job_total = end_idx - start_idx + 1

        if not ask_yes_no(
            self.app,
            "确认全部批注",
            f"将对第 {start_page_1} 页到第 {end_page_1} 页（共 {job_total} 页）生成 AI 批注。\n\n"
            "流程：渲染所选页 → 理解文档上下文 → 逐页批注；"
            "每完成一页会立即显示在界面上。\n\n"
            "确定要开始吗？",
            width=480,
        ):
            return

        self._annotating = True
        self._set_annotate_buttons_state(False)
        self.app.update_status(
            f"正在批量生成批注：第 {start_page_1}–{end_page_1} 页（共 {job_total} 页）..."
        )
        self.app.update_progress(0, job_total, "准备中...")

        def worker():
            try:
                from src.services.annotation_service import AnnotationService

                annotation_service = AnnotationService(self.app.settings.llm)
                source_path = self.app.selected_files[self.app.current_file_index]
                pdf_path = self.app.get_render_pdf_path(source_path)
                pages_with_ann = 0
                total_ann = 0

                def update_progress(current: int, message: str) -> None:
                    self.app.after(
                        0,
                        lambda c=current, m=message: self.app.update_progress(
                            c, job_total, m
                        ),
                    )

                update_progress(0, "正在将所选页转为图片...")
                self.app.after(
                    0,
                    lambda: self.app.update_status("正在渲染所选页面为图片..."),
                )

                def on_render(current: int, render_total: int) -> None:
                    update_progress(
                        0,
                        f"正在渲染 {current}/{render_total} 页图片...",
                    )

                page_images = annotation_service.render_document_page_images(
                    total_pages=total,
                    pdf_path=pdf_path,
                    pdf_doc=self.app.pdf_doc,
                    source_path=source_path,
                    on_progress=on_render,
                    start_page=start_idx,
                    end_page=end_idx,
                )

                images_by_page = {img.page_number: img for img in page_images}

                update_progress(0, "正在理解文档上下文...")
                self.app.after(
                    0,
                    lambda: self.app.update_status(
                        "正在通读所选页面并生成全局理解..."
                    ),
                )

                document_context = annotation_service.analyze_document_context(
                    page_images,
                    total_pages=total,
                    source_path=source_path,
                    multi_agent=False,
                    cache_friendly=True,
                )

                update_progress(0, "全局理解完成，逐页批注...")
                self.app.after(
                    0,
                    lambda: self.app.update_status(
                        f"逐页批注中（第 {start_page_1}–{end_page_1} 页）..."
                    ),
                )

                for offset, page_num in enumerate(range(start_idx, end_idx + 1)):
                    done = offset + 1
                    update_progress(
                        done,
                        f"批注第 {page_num + 1} 页（{done}/{job_total}）...",
                    )

                    page_img = images_by_page.get(page_num)
                    annotations = self._annotate_one_page(
                        annotation_service,
                        page_num,
                        source_path,
                        pdf_path,
                        document_context=document_context,
                        total_pages=total,
                        page_image=page_img,
                        use_multi_agent=False,
                        cache_friendly=True,
                    )
                    if annotations:
                        pages_with_ann += 1
                        total_ann += len(annotations)

                        def apply_now(
                            p=page_num,
                            ann=annotations,
                            d=done,
                        ):
                            self._apply_annotations_to_page_ui(
                                p, ann, done=d, job_total=job_total
                            )

                        self.app.after(0, apply_now)

                def finish():
                    self._annotating = False
                    self._set_annotate_buttons_state(True)
                    self.app.update_progress(job_total, job_total, "完成")
                    if self.app.current_page >= start_idx and self.app.current_page <= end_idx:
                        self.app._show_annotations()
                    self.app._update_annotation_list()
                    self.app.sync_web_preview()
                    self.app.update_status(
                        f"批注完成：第 {start_page_1}–{end_page_1} 页，"
                        f"{pages_with_ann}/{job_total} 页有批注，共 {total_ann} 条"
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
            show_warning(self.app, "警告", "没有可导出的文件，请先导入并批注文件")
            return

        if not self.app.pdf_doc:
            show_warning(self.app, "警告", "请先导入PDF文件")
            return

        # 检查是否有批注
        self.app._persist_current_file_annotations()
        has_annotations = any(
            pages for pages in self.app.annotations_by_file.values()
        ) or bool(self.app.annotations)
        if not has_annotations:
            show_warning(self.app, "警告", "没有批注可导出，请先添加批注")
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
            source_file = self.app.selected_files[self.app.current_file_index]
            render_pdf = self.app.get_render_pdf_path(source_file)
            doc = fitz.open(render_pdf)
            file_path = self.app.selected_files[self.app.current_file_index]
            markers_by_page = self.app._get_stored_annotations(file_path)
            if not markers_by_page:
                markers_by_page = self.app.annotations

            for page_num in range(self.app.total_pages):
                page = doc[page_num]
                markers = markers_by_page.get(page_num, [])
                if markers:
                    draw_page_annotations(page, markers)

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
            self._init_toolbar_state_vars()

            # 保存配置到文件
            try:
                from src.main import save_config
                save_config(self.app.settings)
                self.app.update_status("设置已保存并持久化到文件")
                show_info(self.app, "成功", "设置已保存，API Key已持久化")
            except Exception as e:
                self.app.update_status(f"设置已保存，但持久化失败: {str(e)}")
                show_warning(self.app, "警告", f"设置已保存，但持久化到文件失败: {str(e)}")
