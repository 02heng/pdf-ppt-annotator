import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional


class Toolbar(ctk.CTkFrame):
    """工具栏"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.app = master  # 保存主应用引用
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

        # 开始批注按钮
        self.annotate_btn = ctk.CTkButton(
            self,
            text="开始批注",
            command=self._on_annotate,
            fg_color="#2ecc71",
            hover_color="#27ae60"
        )
        self.annotate_btn.pack(side="left", padx=5)

        # 导出按钮
        self.export_btn = ctk.CTkButton(
            self,
            text="导出",
            command=self._on_export
        )
        self.export_btn.pack(side="left", padx=5)

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
            self.app.update_status(f"已导入 {len(files)} 个文件: {', '.join(file_names)}")

    def _on_annotate(self) -> None:
        """开始批注"""
        if not hasattr(self.app, 'selected_files') or not self.app.selected_files:
            messagebox.showwarning("警告", "请先导入文件")
            return

        # 检查LLM配置
        provider = self.app.settings.llm.provider
        if provider == "openai" and not self.app.settings.llm.openai.api_key:
            messagebox.showwarning("警告", "请先在设置中配置 OpenAI API Key")
            return
        elif provider == "deepseek" and not self.app.settings.llm.deepseek.api_key:
            messagebox.showwarning("警告", "请先在设置中配置 DeepSeek API Key")
            return

        # 检查是否有PDF文档
        if not self.app.pdf_doc:
            messagebox.showwarning("警告", "请先导入PDF文件")
            return

        # 获取当前页面
        current_page = self.app.current_page
        if current_page < 0 or current_page >= self.app.total_pages:
            messagebox.showwarning("警告", "请选择一个页面")
            return

        # 开始批注处理
        self.app.update_status("正在生成批注，请稍候...")
        messagebox.showinfo("开始批注", "正在调用AI生成批注，这可能需要一些时间...")

        try:
            # 导入批注服务
            from src.services.annotation_service import AnnotationService
            
            # 创建批注服务实例
            annotation_service = AnnotationService(self.app.settings.llm)
            
            # 获取当前页面内容
            page = self.app.pdf_doc[current_page]
            page_text = page.get_text()
            
            # 创建页面对象
            from src.models.page import Page
            page_obj = Page(
                page_number=current_page,
                content=page_text,
                width=page.rect.width,
                height=page.rect.height
            )
            
            # 调用批注服务生成批注
            annotations = annotation_service.process_page(page_obj)
            
            # 将批注添加到UI（追加而不是替换）
            if annotations:
                from src.ui.app import AnnotationMarker
                
                # 获取现有批注，如果没有则创建空列表
                existing_markers = self.app.annotations.get(current_page, [])
                
                # 计算新批注的起始位置（避免重叠）
                base_x = 50
                base_y = 50
                if existing_markers:
                    # 如果已有批注，放在右侧
                    max_x = max(m.x for m in existing_markers)
                    base_x = max_x + 150
                
                for i, ann in enumerate(annotations):
                    # 计算位置，垂直排列
                    x = base_x
                    y = base_y + i * 60
                    
                    marker = AnnotationMarker(
                        x=x,
                        y=y,
                        text=ann.content,
                        color="#FF6B6B"
                    )
                    existing_markers.append(marker)
                
                # 保存批注（追加到现有批注）
                self.app.annotations[current_page] = existing_markers
                
                # 刷新显示
                self.app._show_annotations()
                self.app._update_annotation_list()
                
                self.app.update_status(f"第 {current_page + 1} 页批注生成完成，共 {len(annotations)} 条批注")
                messagebox.showinfo("成功", f"已生成 {len(annotations)} 条批注")
            else:
                self.app.update_status("未能生成批注")
                messagebox.showwarning("警告", "未能生成批注，请检查页面内容")
                
        except Exception as e:
            self.app.update_status(f"批注生成失败: {str(e)}")
            messagebox.showerror("错误", f"批注生成失败: {str(e)}")

    def _on_export(self) -> None:
        """导出文件"""
        if not hasattr(self.app, 'selected_files') or not self.app.selected_files:
            messagebox.showwarning("警告", "没有可导出的文件，请先导入并批注文件")
            return

        if not self.app.pdf_doc:
            messagebox.showwarning("警告", "请先导入PDF文件")
            return

        # 检查是否有批注
        if not self.app.annotations:
            messagebox.showwarning("警告", "没有批注可导出，请先添加批注")
            return

        # 选择导出文件路径
        file_path = filedialog.asksaveasfilename(
            title="导出PDF",
            defaultextension=".pdf",
            filetypes=[("PDF 文件", "*.pdf")]
        )

        if file_path:
            try:
                self._export_pdf(file_path)
                messagebox.showinfo("成功", f"已导出到: {file_path}")
                self.app.update_status(f"导出成功: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")

    def _export_pdf(self, output_path: str) -> None:
        """导出带批注的PDF"""
        try:
            import fitz  # PyMuPDF

            # 打开原始文档进行复制
            doc = fitz.open(self.app.selected_files[self.app.current_file_index])

            # 遍历每一页
            for page_num in range(self.app.total_pages):
                # 获取页面
                page = doc[page_num]

                # 添加批注
                markers = self.app.annotations.get(page_num, [])

                for i, marker in enumerate(markers):
                    # 计算标记位置（考虑缩放）
                    marker_x = marker.x / (self.app.zoom_level * 2)
                    marker_y = marker.y / (self.app.zoom_level * 2)

                    # 解析颜色
                    color_hex = marker.color.lstrip('#')
                    r, g, b = int(color_hex[0:2], 16)/255, int(color_hex[2:4], 16)/255, int(color_hex[4:6], 16)/255

                    # 绘制小方块标记（带编号）
                    square_size = 20
                    square_rect = fitz.Rect(
                        marker_x, marker_y,
                        marker_x + square_size, marker_y + square_size
                    )
                    
                    # 绘制彩色方块
                    shape = page.new_shape()
                    shape.draw_rect(square_rect)
                    shape.finish(fill=(r, g, b), fill_opacity=0.9, color=(r, g, b), width=1)
                    shape.commit()

                    # 在方块中添加编号
                    page.insert_text(
                        fitz.Point(marker_x + 5, marker_y + 15),
                        f"{i+1}",
                        fontsize=10,
                        fontname="helv",
                        color=(1, 1, 1)
                    )

                    # 添加PDF注释（鼠标悬停/点击时显示内容）
                    # 使用Text Annotation，这样鼠标悬停会显示内容
                    annot = page.add_text_annot(
                        fitz.Point(marker_x + square_size, marker_y),
                        marker.text,  # 批注内容
                        icon="Comment"  # 注释图标类型
                    )
                    
                    # 设置注释标题
                    annot.set_info(title=f"批注 #{i+1}")
                    
                    # 设置注释颜色
                    annot.set_colors(stroke=(r, g, b))
                    
                    # 更新注释
                    annot.update()

            # 保存文档
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
