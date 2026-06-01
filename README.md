# PDF/PPT 中文批注桌面应用

一款基于多智能体协作的桌面端软件，自动为英文 PDF/PPT 文档生成详细的中文批注。

## 功能特性

- **多格式支持**: 支持 PDF 和 PPT 文件
- **智能批注**: 4 个 AI 智能体协作生成高质量批注
- **双模式显示**: 覆盖模式和侧边栏模式可切换
- **双 LLM 支持**: 支持 OpenAI 和 Ollama（本地模型）
- **批量处理**: 支持同时处理多个文件
- **导出选项**: 多种导出格式（PDF、Markdown、双语对照）

## 安装

### 方式一：安装包（推荐给最终用户）

无需安装 Python 或任何库。详见 [packaging/README.md](packaging/README.md)。

| 平台 | 开发者构建命令 | 分发给用户 |
|------|----------------|------------|
| Windows | `.\packaging\build_windows.ps1` | `packaging\output\TOPDFAnnotator-Setup-*.exe` |
| macOS | `./packaging/build_mac.sh`（需在 Mac 上运行） | `packaging/output/TOPDFAnnotator-*.dmg` |

### 方式二：源码运行（开发者）

#### 1. 克隆项目

```bash
git clone https://github.com/02heng/pdf-ppt-annotator.git
cd pdf-ppt-annotator
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置

编辑 `config/default.yaml` 或在应用「设置」中填写 API Key。

#### 4. 运行

```bash
python -m src.main
```

## 使用说明

1. **导入文件**: 点击"导入文件"按钮或拖拽文件到窗口
2. **选择模式**: 在工具栏选择批注模式（覆盖/侧边栏）
3. **开始处理**: 点击"开始处理"按钮
4. **查看批注**: 在预览区域查看文档和批注
5. **导出结果**: 点击"导出"按钮保存批注

## 技术栈

- **多智能体框架**: CrewAI
- **桌面 UI**: CustomTkinter
- **PDF 处理**: PyMuPDF
- **PPT 处理**: python-pptx
- **LLM**: OpenAI API / Ollama

## 项目结构

```
pdf-ppt-annotator/
├── src/
│   ├── agents/          # AI 智能体定义
│   │   ├── analyst.py   # 文档分析智能体
│   │   ├── annotator.py # 批注生成智能体
│   │   ├── translator.py# 翻译智能体
│   │   └── reviewer.py  # 审校智能体
│   ├── parsers/         # 文档解析器
│   │   ├── base_parser.py
│   │   ├── pdf_parser.py
│   │   └── ppt_parser.py
│   ├── services/        # 业务服务
│   │   ├── annotation_service.py
│   │   ├── crew_service.py
│   │   ├── export_service.py
│   │   └── llm_service.py
│   ├── ui/              # 用户界面
│   │   ├── app.py
│   │   ├── file_panel.py
│   │   ├── preview_panel.py
│   │   ├── settings_dialog.py
│   │   ├── sidebar_panel.py
│   │   ├── status_bar.py
│   │   └── toolbar.py
│   ├── models/          # 数据模型
│   │   ├── annotation.py
│   │   ├── config.py
│   │   ├── document.py
│   │   └── page.py
│   ├── utils/           # 工具函数
│   └── main.py          # 应用入口
├── tests/               # 测试文件
├── config/              # 配置文件
├── docs/                # 文档
├── requirements.txt     # Python 依赖
└── setup.py             # 安装配置
```

## 许可证

MIT License
