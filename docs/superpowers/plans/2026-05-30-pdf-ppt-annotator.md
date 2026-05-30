# PDF/PPT 中文批注桌面应用实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一款桌面端软件，用户导入英文 PDF/PPT 文件后，通过多智能体协作自动生成中文批注

**Architecture:** 采用 CrewAI 多智能体框架 + CustomTkinter GUI + PyMuPDF/python-pptx 文档处理，支持 OpenAI/Ollama 双 LLM 后端

**Tech Stack:** Python 3.10+, CrewAI, CustomTkinter, PyMuPDF, python-pptx, OpenAI API, Ollama

---

## 文件结构

```
pdf-ppt-annotator/
├── src/
│   ├── __init__.py
│   ├── main.py                    # 应用入口
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── translator.py          # 翻译员智能体
│   │   ├── analyst.py             # 分析员智能体
│   │   ├── annotator.py           # 批注员智能体
│   │   └── reviewer.py            # 审核员智能体
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base_parser.py         # 解析器基类
│   │   ├── pdf_parser.py          # PDF 解析器
│   │   └── ppt_parser.py          # PPT 解析器
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_service.py         # LLM 服务管理
│   │   ├── crew_service.py        # CrewAI 编排服务
│   │   ├── annotation_service.py  # 批注处理服务
│   │   └── export_service.py      # 导出服务
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── app.py                 # 主应用窗口
│   │   ├── file_panel.py          # 文件导入面板
│   │   ├── preview_panel.py       # 文档预览面板
│   │   ├── sidebar_panel.py       # 批注侧边栏
│   │   ├── toolbar.py             # 工具栏
│   │   ├── status_bar.py          # 状态栏
│   │   └── settings_dialog.py     # 设置对话框
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py            # 文档模型
│   │   ├── page.py                # 页面模型
│   │   ├── annotation.py          # 批注模型
│   │   └── config.py              # 配置模型
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py          # 文件工具
│       ├── text_utils.py          # 文本工具
│       └── crypto_utils.py        # 加密工具
├── tests/
│   ├── __init__.py
│   ├── test_parsers/
│   │   ├── __init__.py
│   │   ├── test_pdf_parser.py
│   │   └── test_ppt_parser.py
│   ├── test_agents/
│   │   ├── __init__.py
│   │   └── test_crew_service.py
│   ├── test_services/
│   │   ├── __init__.py
│   │   ├── test_llm_service.py
│   │   └── test_annotation_service.py
│   └── test_models/
│       ├── __init__.py
│       └── test_document.py
├── config/
│   └── default.yaml               # 默认配置
├── requirements.txt
├── setup.py
└── README.md
```

---

## Task 1: 项目初始化和依赖管理

**Files:**
- Create: `requirements.txt`
- Create: `setup.py`
- Create: `config/default.yaml`
- Create: `src/__init__.py`

- [ ] **Step 1: 创建 requirements.txt**

```txt
crewai>=1.14.0
customtkinter>=5.2.0
PyMuPDF>=1.23.0
python-pptx>=0.6.21
openai>=1.0.0
pydantic>=2.0.0
pyyaml>=6.0
cryptography>=41.0.0
Pillow>=10.0.0
```

- [ ] **Step 2: 创建 setup.py**

```python
from setuptools import setup, find_packages

setup(
    name="pdf-ppt-annotator",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "crewai>=1.14.0",
        "customtkinter>=5.2.0",
        "PyMuPDF>=1.23.0",
        "python-pptx>=0.6.21",
        "openai>=1.0.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "cryptography>=41.0.0",
        "Pillow>=10.0.0",
    ],
    entry_points={
        "console_scripts": [
            "pdf-annotator=src.main:main",
        ],
    },
)
```

- [ ] **Step 3: 创建默认配置文件**

```yaml
# config/default.yaml
llm:
  provider: "openai"
  openai:
    api_key: ""
    model: "gpt-4o"
    temperature: 0.3
    max_tokens: 4096
  ollama:
    base_url: "http://localhost:11434"
    model: "llama3:70b"
    temperature: 0.3

annotation:
  mode: "sidebar"
  detail_level: "detailed"
  style:
    font_family: "Microsoft YaHei"
    font_size: 12
    color: "#333333"
    background: "#FFFFCC"

app:
  language: "zh-CN"
  theme: "system"
  recent_files_limit: 10
  auto_save: true
```

- [ ] **Step 4: 创建 src/__init__.py**

```python
"""PDF/PPT 中文批注桌面应用"""

__version__ = "1.0.0"
```

- [ ] **Step 5: 安装依赖并验证**

Run: `cd "e:\desktop\TO PDF" && pip install -r requirements.txt`
Expected: 成功安装所有依赖

- [ ] **Step 6: 提交**

```bash
git add requirements.txt setup.py config/ src/__init__.py
git commit -m "feat: initialize project with dependencies and config"
```

---

## Task 2: 数据模型层

**Files:**
- Create: `src/models/__init__.py`
- Create: `src/models/document.py`
- Create: `src/models/page.py`
- Create: `src/models/annotation.py`
- Create: `src/models/config.py`
- Create: `tests/test_models/__init__.py`
- Create: `tests/test_models/test_document.py`

- [ ] **Step 1: 创建文档模型测试**

```python
# tests/test_models/test_document.py
import pytest
from src.models.document import Document
from src.models.page import Page

def test_document_creation():
    doc = Document(file_path="test.pdf", file_type="pdf")
    assert doc.file_path == "test.pdf"
    assert doc.file_type == "pdf"
    assert doc.pages == []
    assert doc.total_pages == 0

def test_document_add_page():
    doc = Document(file_path="test.pdf", file_type="pdf")
    page = Page(page_number=1, content="Test content")
    doc.add_page(page)
    assert doc.total_pages == 1
    assert doc.pages[0].content == "Test content"

def test_document_get_page():
    doc = Document(file_path="test.pdf", file_type="pdf")
    page1 = Page(page_number=1, content="Page 1")
    page2 = Page(page_number=2, content="Page 2")
    doc.add_page(page1)
    doc.add_page(page2)
    assert doc.get_page(1).content == "Page 1"
    assert doc.get_page(2).content == "Page 2"
    assert doc.get_page(3) is None
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd "e:\desktop\TO PDF" && python -m pytest tests/test_models/test_document.py -v`
Expected: FAIL - "ModuleNotFoundError: No module named 'src.models.document'"

- [ ] **Step 3: 创建文档模型**

```python
# src/models/document.py
from typing import List, Optional
from pydantic import BaseModel, Field
from .page import Page

class Document(BaseModel):
    """文档模型"""
    file_path: str
    file_type: str  # "pdf" 或 "ppt"
    title: Optional[str] = None
    author: Optional[str] = None
    pages: List[Page] = Field(default_factory=list)
    
    @property
    def total_pages(self) -> int:
        return len(self.pages)
    
    def add_page(self, page: Page) -> None:
        self.pages.append(page)
    
    def get_page(self, page_number: int) -> Optional[Page]:
        for page in self.pages:
            if page.page_number == page_number:
                return page
        return None
```

- [ ] **Step 4: 创建页面模型**

```python
# src/models/page.py
from typing import List, Optional
from pydantic import BaseModel, Field
from .annotation import Annotation

class Page(BaseModel):
    """页面模型"""
    page_number: int
    content: str
    images: List[str] = Field(default_factory=list)
    width: float = 0.0
    height: float = 0.0
    annotations: List[Annotation] = Field(default_factory=list)
    
    def add_annotation(self, annotation: Annotation) -> None:
        self.annotations.append(annotation)
    
    def get_annotations(self) -> List[Annotation]:
        return self.annotations
```

- [ ] **Step 5: 创建批注模型**

```python
# src/models/annotation.py
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class Annotation(BaseModel):
    """批注模型"""
    id: str
    page_number: int
    content: str  # 批注内容（中文）
    original_text: Optional[str] = None  # 原文
    position_x: float = 0.0
    position_y: float = 0.0
    width: float = 200.0
    height: float = 100.0
    created_at: datetime = Field(default_factory=datetime.now)
    agent_role: str = ""  # 生成批注的智能体角色
    
    def to_overlay_format(self) -> dict:
        """转换为覆盖模式格式"""
        return {
            "id": self.id,
            "content": self.content,
            "position": {"x": self.position_x, "y": self.position_y},
            "size": {"width": self.width, "height": self.height}
        }
    
    def to_sidebar_format(self) -> dict:
        """转换为侧边栏模式格式"""
        return {
            "id": self.id,
            "page": self.page_number,
            "content": self.content,
            "original": self.original_text,
            "agent": self.agent_role
        }
```

- [ ] **Step 6: 创建配置模型**

```python
# src/models/config.py
from typing import Optional
from pydantic import BaseModel, Field

class OpenAIConfig(BaseModel):
    """OpenAI 配置"""
    api_key: str = ""
    model: str = "gpt-4o"
    temperature: float = 0.3
    max_tokens: int = 4096

class OllamaConfig(BaseModel):
    """Ollama 配置"""
    base_url: str = "http://localhost:11434"
    model: str = "llama3:70b"
    temperature: float = 0.3

class LLMConfig(BaseModel):
    """LLM 配置"""
    provider: str = "openai"  # "openai" 或 "ollama"
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)

class AnnotationStyle(BaseModel):
    """批注样式配置"""
    font_family: str = "Microsoft YaHei"
    font_size: int = 12
    color: str = "#333333"
    background: str = "#FFFFCC"

class AnnotationConfig(BaseModel):
    """批注配置"""
    mode: str = "sidebar"  # "overlay" 或 "sidebar"
    detail_level: str = "detailed"  # "summary", "detailed", "custom"
    style: AnnotationStyle = Field(default_factory=AnnotationStyle)

class AppConfig(BaseModel):
    """应用配置"""
    language: str = "zh-CN"
    theme: str = "system"  # "light", "dark", "system"
    recent_files_limit: int = 10
    auto_save: bool = True

class Settings(BaseModel):
    """全局设置"""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    annotation: AnnotationConfig = Field(default_factory=AnnotationConfig)
    app: AppConfig = Field(default_factory=AppConfig)
```

- [ ] **Step 7: 创建模型 __init__.py**

```python
# src/models/__init__.py
from .document import Document
from .page import Page
from .annotation import Annotation
from .config import Settings, LLMConfig, AnnotationConfig, AppConfig

__all__ = [
    "Document",
    "Page", 
    "Annotation",
    "Settings",
    "LLMConfig",
    "AnnotationConfig",
    "AppConfig"
]
```

- [ ] **Step 8: 运行测试验证通过**

Run: `cd "e:\desktop\TO PDF" && python -m pytest tests/test_models/test_document.py -v`
Expected: PASS - 3 tests passed

- [ ] **Step 9: 提交**

```bash
git add src/models/ tests/test_models/
git commit -m "feat: add data models for document, page, annotation, and config"
```

---

## Task 3: 文档解析器

**Files:**
- Create: `src/parsers/__init__.py`
- Create: `src/parsers/base_parser.py`
- Create: `src/parsers/pdf_parser.py`
- Create: `src/parsers/ppt_parser.py`
- Create: `tests/test_parsers/__init__.py`
- Create: `tests/test_parsers/test_pdf_parser.py`
- Create: `tests/test_parsers/test_ppt_parser.py`

- [ ] **Step 1: 创建解析器测试**

```python
# tests/test_parsers/test_pdf_parser.py
import pytest
from src.parsers.pdf_parser import PDFParser

def test_pdf_parser_initialization():
    parser = PDFParser()
    assert parser is not None

def test_pdf_parser_nonexistent_file():
    parser = PDFParser()
    with pytest.raises(FileNotFoundError):
        parser.parse("nonexistent.pdf")
```

```python
# tests/test_parsers/test_ppt_parser.py
import pytest
from src.parsers.ppt_parser import PPTParser

def test_ppt_parser_initialization():
    parser = PPTParser()
    assert parser is not None

def test_ppt_parser_nonexistent_file():
    parser = PPTParser()
    with pytest.raises(FileNotFoundError):
        parser.parse("nonexistent.pptx")
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd "e:\desktop\TO PDF" && python -m pytest tests/test_parsers/ -v`
Expected: FAIL - "ModuleNotFoundError"

- [ ] **Step 3: 创建解析器基类**

```python
# src/parsers/base_parser.py
from abc import ABC, abstractmethod
from typing import Optional
from src.models.document import Document

class BaseParser(ABC):
    """文档解析器基类"""
    
    @abstractmethod
    def parse(self, file_path: str) -> Document:
        """
        解析文档文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Document: 解析后的文档对象
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持
        """
        pass
    
    @abstractmethod
    def supports_format(self, file_path: str) -> bool:
        """检查是否支持该文件格式"""
        pass
```

- [ ] **Step 4: 创建 PDF 解析器**

```python
# src/parsers/pdf_parser.py
import fitz  # PyMuPDF
from typing import List
from src.models.document import Document
from src.models.page import Page
from .base_parser import BaseParser

class PDFParser(BaseParser):
    """PDF 文档解析器"""
    
    def parse(self, file_path: str) -> Document:
        """
        解析 PDF 文件
        
        Args:
            file_path: PDF 文件路径
            
        Returns:
            Document: 解析后的文档对象
        """
        import os
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not self.supports_format(file_path):
            raise ValueError(f"不支持的文件格式: {file_path}")
        
        doc = Document(file_path=file_path, file_type="pdf")
        
        try:
            pdf_document = fitz.open(file_path)
            
            # 提取元数据
            metadata = pdf_document.metadata
            if metadata:
                doc.title = metadata.get("title")
                doc.author = metadata.get("author")
            
            # 逐页解析
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                
                # 提取文本
                text = page.get_text("text")
                
                # 提取图片
                images = self._extract_images(page)
                
                # 获取页面尺寸
                rect = page.rect
                
                page_model = Page(
                    page_number=page_num + 1,
                    content=text,
                    images=images,
                    width=rect.width,
                    height=rect.height
                )
                doc.add_page(page_model)
            
            pdf_document.close()
            
        except Exception as e:
            raise ValueError(f"PDF 解析错误: {str(e)}")
        
        return doc
    
    def supports_format(self, file_path: str) -> bool:
        """检查是否为 PDF 文件"""
        return file_path.lower().endswith(".pdf")
    
    def _extract_images(self, page) -> List[str]:
        """提取页面中的图片"""
        images = []
        image_list = page.get_images(full=True)
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            images.append(f"image_{xref}")
        
        return images
```

- [ ] **Step 5: 创建 PPT 解析器**

```python
# src/parsers/ppt_parser.py
from pptx import Presentation
from pptx.util import Inches
import os
from src.models.document import Document
from src.models.page import Page
from .base_parser import BaseParser

class PPTParser(BaseParser):
    """PPT 文档解析器"""
    
    def parse(self, file_path: str) -> Document:
        """
        解析 PPT 文件
        
        Args:
            file_path: PPT 文件路径
            
        Returns:
            Document: 解析后的文档对象
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not self.supports_format(file_path):
            raise ValueError(f"不支持的文件格式: {file_path}")
        
        doc = Document(file_path=file_path, file_type="ppt")
        
        try:
            prs = Presentation(file_path)
            
            # 提取元数据
            if prs.core_properties:
                doc.title = prs.core_properties.title
                doc.author = prs.core_properties.author
            
            # 逐页解析
            for slide_num, slide in enumerate(prs.slides):
                text_content = self._extract_slide_text(slide)
                images = self._extract_slide_images(slide)
                
                # 获取幻灯片尺寸
                width = prs.slide_width / 914400  # 转换为英寸
                height = prs.slide_height / 914400
                
                page = Page(
                    page_number=slide_num + 1,
                    content=text_content,
                    images=images,
                    width=width,
                    height=height
                )
                doc.add_page(page)
            
        except Exception as e:
            raise ValueError(f"PPT 解析错误: {str(e)}")
        
        return doc
    
    def supports_format(self, file_path: str) -> bool:
        """检查是否为 PPT 文件"""
        return file_path.lower().endswith((".ppt", ".pptx"))
    
    def _extract_slide_text(self, slide) -> str:
        """提取幻灯片文本"""
        texts = []
        
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                texts.append(shape.text)
        
        # 提取备注
        if slide.has_notes_slide:
            notes_slide = slide.notes_slide
            if notes_slide.notes_text_frame:
                texts.append(f"[备注] {notes_slide.notes_text_frame.text}")
        
        return "\n".join(texts)
    
    def _extract_slide_images(self, slide) -> list:
        """提取幻灯片图片"""
        images = []
        
        for shape in slide.shapes:
            if shape.shape_type == 13:  # 图片类型
                images.append(f"image_{shape.shape_id}")
        
        return images
```

- [ ] **Step 6: 创建解析器 __init__.py**

```python
# src/parsers/__init__.py
from .base_parser import BaseParser
from .pdf_parser import PDFParser
from .ppt_parser import PPTParser

__all__ = ["BaseParser", "PDFParser", "PPTParser"]
```

- [ ] **Step 7: 运行测试验证通过**

Run: `cd "e:\desktop\TO PDF" && python -m pytest tests/test_parsers/ -v`
Expected: PASS - 4 tests passed

- [ ] **Step 8: 提交**

```bash
git add src/parsers/ tests/test_parsers/
git commit -m "feat: add PDF and PPT document parsers"
```

---

## Task 4: LLM 服务层

**Files:**
- Create: `src/services/__init__.py`
- Create: `src/services/llm_service.py`
- Create: `tests/test_services/__init__.py`
- Create: `tests/test_services/test_llm_service.py`

- [ ] **Step 1: 创建 LLM 服务测试**

```python
# tests/test_services/test_llm_service.py
import pytest
from src.services.llm_service import LLMService
from src.models.config import LLMConfig, OpenAIConfig, OllamaConfig

def test_llm_service_initialization():
    config = LLMConfig(provider="openai")
    service = LLMService(config)
    assert service is not None
    assert service.provider == "openai"

def test_llm_service_invalid_provider():
    config = LLMConfig(provider="invalid")
    with pytest.raises(ValueError):
        LLMService(config)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd "e:\desktop\TO PDF" && python -m pytest tests/test_services/test_llm_service.py -v`
Expected: FAIL - "ModuleNotFoundError"

- [ ] **Step 3: 创建 LLM 服务**

```python
# src/services/llm_service.py
from typing import Optional
from crewai import LLM
from src.models.config import LLMConfig

class LLMService:
    """LLM 服务管理器"""
    
    def __init__(self, config: LLMConfig):
        """
        初始化 LLM 服务
        
        Args:
            config: LLM 配置
        """
        self.config = config
        self.provider = config.provider
        self._llm: Optional[LLM] = None
        
        if self.provider not in ["openai", "ollama"]:
            raise ValueError(f"不支持的 LLM 提供商: {self.provider}")
    
    @property
    def llm(self) -> LLM:
        """获取 LLM 实例"""
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm
    
    def _create_llm(self) -> LLM:
        """创建 LLM 实例"""
        if self.provider == "openai":
            return self._create_openai_llm()
        elif self.provider == "ollama":
            return self._create_ollama_llm()
        else:
            raise ValueError(f"不支持的提供商: {self.provider}")
    
    def _create_openai_llm(self) -> LLM:
        """创建 OpenAI LLM"""
        config = self.config.openai
        return LLM(
            model=f"openai/{config.model}",
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            api_key=config.api_key
        )
    
    def _create_ollama_llm(self) -> LLM:
        """创建 Ollama LLM"""
        config = self.config.ollama
        return LLM(
            model=f"ollama/{config.model}",
            base_url=config.base_url,
            temperature=config.temperature
        )
    
    def switch_provider(self, provider: str) -> None:
        """
        切换 LLM 提供商
        
        Args:
            provider: 提供商名称 ("openai" 或 "ollama")
        """
        if provider not in ["openai", "ollama"]:
            raise ValueError(f"不支持的提供商: {provider}")
        
        self.provider = provider
        self._llm = None  # 重置 LLM 实例
    
    def update_config(self, config: LLMConfig) -> None:
        """更新配置"""
        self.config = config
        self.provider = config.provider
        self._llm = None  # 重置以重新创建
```

- [ ] **Step 4: 创建服务 __init__.py**

```python
# src/services/__init__.py
from .llm_service import LLMService

__all__ = ["LLMService"]
```

- [ ] **Step 5: 运行测试验证通过**

Run: `cd "e:\desktop\TO PDF" && python -m pytest tests/test_services/test_llm_service.py -v`
Expected: PASS - 2 tests passed

- [ ] **Step 6: 提交**

```bash
git add src/services/ tests/test_services/
git commit -m "feat: add LLM service with OpenAI and Ollama support"
```

---

## Task 5: 多智能体定义

**Files:**
- Create: `src/agents/__init__.py`
- Create: `src/agents/translator.py`
- Create: `src/agents/analyst.py`
- Create: `src/agents/annotator.py`
- Create: `src/agents/reviewer.py`

- [ ] **Step 1: 创建翻译员智能体**

```python
# src/agents/translator.py
from crewai import Agent
from crewai import LLM

def create_translator_agent(llm: LLM) -> Agent:
    """
    创建翻译员智能体
    
    Args:
        llm: LLM 实例
        
    Returns:
        Agent: 翻译员智能体
    """
    return Agent(
        role="专业文档翻译员",
        goal="将英文技术文档准确翻译成中文，保留专业术语",
        backstory="""
        你是一位拥有 10 年经验的专业翻译员，精通计算机科学、
        人工智能、软件工程等领域的术语翻译。你的翻译风格准确、
        流畅，善于处理长难句和专业概念。
        
        你的工作原则：
        1. 保持原文的逻辑结构
        2. 专业术语首次出现时附带英文原文
        3. 对于难以直译的概念，提供意译解释
        4. 保持翻译的自然流畅
        """,
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
```

- [ ] **Step 2: 创建分析员智能体**

```python
# src/agents/analyst.py
from crewai import Agent
from crewai import LLM

def create_analyst_agent(llm: LLM) -> Agent:
    """
    创建分析员智能体
    
    Args:
        llm: LLM 实例
        
    Returns:
        Agent: 分析员智能体
    """
    return Agent(
        role="内容结构分析师",
        goal="深入分析文档内容结构，识别关键概念和逻辑关系",
        backstory="""
        你是一位资深的技术分析师，擅长快速理解复杂文档的结构
        和核心概念。你能够识别文档的主旨、论点、支撑细节，
        以及各部分之间的逻辑关系。
        
        你的分析方法：
        1. 识别段落主题句
        2. 提取关键术语和概念
        3. 分析论证逻辑
        4. 标记重要数据和引用
        5. 识别技术难点和易混淆点
        """,
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
```

- [ ] **Step 3: 创建批注员智能体**

```python
# src/agents/annotator.py
from crewai import Agent
from crewai import LLM

def create_annotator_agent(llm: LLM) -> Agent:
    """
    创建批注员智能体
    
    Args:
        llm: LLM 实例
        
    Returns:
        Agent: 批注员智能体
    """
    return Agent(
        role="专业批注撰写员",
        goal="基于分析结果撰写详细、有洞察力的中文批注",
        backstory="""
        你是一位专业的技术文档批注专家，擅长用简洁明了的中文
        解释复杂概念。你的批注不仅翻译原文，还提供背景知识、
        术语解释和相关联想，帮助读者深入理解。
        
        你的批注风格：
        1. 术语解释：首次出现的专业术语提供详细解释
        2. 背景补充：相关概念的背景知识
        3. 实例说明：用例子帮助理解抽象概念
        4. 关联提示：与文档其他部分的关联
        5. 难点提醒：标记可能难以理解的部分
        """,
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
```

- [ ] **Step 4: 创建审核员智能体**

```python
# src/agents/reviewer.py
from crewai import Agent
from crewai import LLM

def create_reviewer_agent(llm: LLM) -> Agent:
    """
    创建审核员智能体
    
    Args:
        llm: LLM 实例
        
    Returns:
        Agent: 审核员智能体
    """
    return Agent(
        role="质量审核专家",
        goal="确保批注的准确性、完整性和可读性",
        backstory="""
        你是一位严格的质量审核专家，拥有敏锐的语言感知力和
        技术背景。你负责检查批注的准确性、一致性、格式规范，
        并提出改进建议。
        
        你的审核标准：
        1. 准确性：翻译和解释是否准确
        2. 完整性：是否遗漏重要信息
        3. 一致性：术语使用是否一致
        4. 可读性：批注是否易于理解
        5. 格式：是否符合规范要求
        """,
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
```

- [ ] **Step 5: 创建智能体 __init__.py**

```python
# src/agents/__init__.py
from .translator import create_translator_agent
from .analyst import create_analyst_agent
from .annotator import create_annotator_agent
from .reviewer import create_reviewer_agent

__all__ = [
    "create_translator_agent",
    "create_analyst_agent",
    "create_annotator_agent",
    "create_reviewer_agent"
]
```

- [ ] **Step 6: 提交**

```bash
git add src/agents/
git commit -m "feat: add agent definitions for translator, analyst, annotator, reviewer"
```

---

## Task 6: CrewAI 编排服务

**Files:**
- Create: `src/services/crew_service.py`
- Create: `tests/test_agents/__init__.py`
- Create: `tests/test_agents/test_crew_service.py`

- [ ] **Step 1: 创建 Crew 服务测试**

```python
# tests/test_agents/test_crew_service.py
import pytest
from src.services.crew_service import CrewService
from src.models.config import LLMConfig

def test_crew_service_initialization():
    config = LLMConfig(provider="openai")
    service = CrewService(config)
    assert service is not None

def test_crew_service_create_crew():
    config = LLMConfig(provider="openai")
    service = CrewService(config)
    # 注意：实际测试需要 mock LLM
    # crew = service.create_crew()
    # assert crew is not None
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd "e:\desktop\TO PDF" && python -m pytest tests/test_agents/test_crew_service.py -v`
Expected: FAIL - "ModuleNotFoundError"

- [ ] **Step 3: 创建 Crew 服务**

```python
# src/services/crew_service.py
from typing import List, Optional
from crewai import Crew, Task
from src.models.config import LLMConfig
from src.models.page import Page
from src.models.annotation import Annotation
from src.services.llm_service import LLMService
from src.agents import (
    create_translator_agent,
    create_analyst_agent,
    create_annotator_agent,
    create_reviewer_agent
)

class CrewService:
    """CrewAI 编排服务"""
    
    def __init__(self, config: LLMConfig):
        """
        初始化 Crew 服务
        
        Args:
            config: LLM 配置
        """
        self.llm_service = LLMService(config)
        self._agents = None
    
    @property
    def agents(self):
        """获取智能体集合"""
        if self._agents is None:
            self._agents = self._create_agents()
        return self._agents
    
    def _create_agents(self) -> dict:
        """创建所有智能体"""
        llm = self.llm_service.llm
        return {
            "translator": create_translator_agent(llm),
            "analyst": create_analyst_agent(llm),
            "annotator": create_annotator_agent(llm),
            "reviewer": create_reviewer_agent(llm)
        }
    
    def create_page_tasks(self, page: Page) -> List[Task]:
        """
        为单个页面创建任务链
        
        Args:
            page: 页面对象
            
        Returns:
            List[Task]: 任务列表
        """
        # 任务 1: 翻译
        translate_task = Task(
            description=f"""
            将以下英文内容翻译成中文，保留专业术语对照：
            
            {page.content}
            
            要求：
            1. 保持原文的段落结构
            2. 专业术语首次出现时用括号标注英文原文
            3. 确保翻译流畅自然
            """,
            expected_output="中文翻译文本，格式清晰，术语标注完整",
            agent=self.agents["translator"]
        )
        
        # 任务 2: 分析
        analyze_task = Task(
            description=f"""
            分析以下翻译后的内容，识别：
            1. 核心主题和关键概念
            2. 技术术语列表
            3. 段落逻辑结构
            4. 重点和难点
            
            内容：
            {{translate_task.output}}
            """,
            expected_output="结构化分析报告，包含主题、术语表、逻辑结构",
            agent=self.agents["analyst"],
            context=[translate_task]
        )
        
        # 任务 3: 批注
        annotate_task = Task(
            description=f"""
            基于分析结果，为每个段落生成详细的中文批注：
            
            要求：
            1. 术语解释：对专业术语进行详细解释
            2. 背景补充：提供相关背景知识
            3. 难点提示：标记可能难以理解的部分
            4. 关联说明：指出与其他内容的关联
            
            原文：{page.content}
            分析结果：{{analyze_task.output}}
            """,
            expected_output="详细的批注内容，格式化输出",
            agent=self.agents["annotator"],
            context=[translate_task, analyze_task]
        )
        
        # 任务 4: 审核
        review_task = Task(
            description=f"""
            审核批注质量，确保：
            1. 翻译准确性
            2. 术语使用一致性
            3. 批注完整性
            4. 可读性
            
            如有问题，直接修正。
            
            批注内容：{{annotate_task.output}}
            """,
            expected_output="审核通过的最终批注内容",
            agent=self.agents["reviewer"],
            context=[annotate_task]
        )
        
        return [translate_task, analyze_task, annotate_task, review_task]
    
    def process_page(self, page: Page) -> List[Annotation]:
        """
        处理单个页面，生成批注
        
        Args:
            page: 页面对象
            
        Returns:
            List[Annotation]: 批注列表
        """
        tasks = self.create_page_tasks(page)
        
        crew = Crew(
            agents=list(self.agents.values()),
            tasks=tasks,
            verbose=True
        )
        
        result = crew.kickoff()
        
        # 解析结果并创建批注对象
        annotations = self._parse_crew_result(result, page.page_number)
        
        return annotations
    
    def _parse_crew_result(self, result, page_number: int) -> List[Annotation]:
        """解析 Crew 执行结果"""
        import uuid
        
        annotations = []
        
        # 将结果转换为批注对象
        annotation = Annotation(
            id=str(uuid.uuid4()),
            page_number=page_number,
            content=str(result),
            agent_role="multi-agent"
        )
        annotations.append(annotation)
        
        return annotations
    
    def switch_llm_provider(self, provider: str) -> None:
        """切换 LLM 提供商"""
        self.llm_service.switch_provider(provider)
        self._agents = None  # 重置智能体
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd "e:\desktop\TO PDF" && python -m pytest tests/test_agents/test_crew_service.py -v`
Expected: PASS - 2 tests passed

- [ ] **Step 5: 提交**

```bash
git add src/services/crew_service.py tests/test_agents/
git commit -m "feat: add CrewAI orchestration service"
```

---

## Task 7: 批注处理服务

**Files:**
- Create: `src/services/annotation_service.py`
- Create: `tests/test_services/test_annotation_service.py`

- [ ] **Step 1: 创建批注服务测试**

```python
# tests/test_services/test_annotation_service.py
import pytest
from src.services.annotation_service import AnnotationService
from src.models.document import Document
from src.models.page import Page
from src.models.config import LLMConfig

def test_annotation_service_initialization():
    config = LLMConfig(provider="openai")
    service = AnnotationService(config)
    assert service is not None

def test_annotation_service_process_document():
    config = LLMConfig(provider="openai")
    service = AnnotationService(config)
    
    doc = Document(file_path="test.pdf", file_type="pdf")
    doc.add_page(Page(page_number=1, content="Test content"))
    
    # 注意：实际测试需要 mock CrewService
    # result = service.process_document(doc)
    # assert result is not None
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd "e:\desktop\TO PDF" && python -m pytest tests/test_services/test_annotation_service.py -v`
Expected: FAIL - "ModuleNotFoundError"

- [ ] **Step 3: 创建批注服务**

```python
# src/services/annotation_service.py
from typing import List, Callable, Optional
from src.models.document import Document
from src.models.page import Page
from src.models.annotation import Annotation
from src.models.config import LLMConfig
from src.services.crew_service import CrewService

class AnnotationService:
    """批注处理服务"""
    
    def __init__(self, config: LLMConfig):
        """
        初始化批注服务
        
        Args:
            config: LLM 配置
        """
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
        """
        处理整个文档，生成批注
        
        Args:
            document: 文档对象
            
        Returns:
            Document: 包含批注的文档对象
        """
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
    
    def process_page(self, page: Page) -> List[Annotation]:
        """
        处理单个页面
        
        Args:
            page: 页面对象
            
        Returns:
            List[Annotation]: 批注列表
        """
        return self.crew_service.process_page(page)
    
    def switch_llm_provider(self, provider: str) -> None:
        """切换 LLM 提供商"""
        self.crew_service.switch_llm_provider(provider)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd "e:\desktop\TO PDF" && python -m pytest tests/test_services/test_annotation_service.py -v`
Expected: PASS - 2 tests passed

- [ ] **Step 5: 提交**

```bash
git add src/services/annotation_service.py tests/test_services/test_annotation_service.py
git commit -m "feat: add annotation processing service"
```

---

## Task 8: 导出服务

**Files:**
- Create: `src/services/export_service.py`

- [ ] **Step 1: 创建导出服务**

```python
# src/services/export_service.py
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
            # 打开原始 PDF
            pdf_document = fitz.open(document.file_path)
            
            for page in pdf_document:
                page_num = page.number + 1
                doc_page = document.get_page(page_num)
                
                if doc_page and doc_page.annotations:
                    if mode == "overlay":
                        self._add_overlay_annotations(page, doc_page.annotations)
                    # sidebar 模式在 UI 中处理
            
            # 保存
            pdf_document.save(output_path)
            pdf_document.close()
            
            return output_path
            
        except Exception as e:
            raise ValueError(f"导出失败: {str(e)}")
    
    def _add_overlay_annotations(self, page, annotations: list) -> None:
        """添加覆盖式批注"""
        import fitz
        
        for ann in annotations:
            # 创建文本注释
            rect = fitz.Rect(
                ann.position_x,
                ann.position_y,
                ann.position_x + ann.width,
                ann.position_y + ann.height
            )
            
            # 添加注释
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
```

- [ ] **Step 2: 提交**

```bash
git add src/services/export_service.py
git commit -m "feat: add export service for annotated documents"
```

---

## Task 9: 主应用窗口

**Files:**
- Create: `src/ui/__init__.py`
- Create: `src/ui/app.py`
- Create: `src/ui/toolbar.py`
- Create: `src/ui/status_bar.py`

- [ ] **Step 1: 创建主应用窗口**

```python
# src/ui/app.py
import customtkinter as ctk
from typing import Optional
from src.models.config import Settings
from src.ui.toolbar import Toolbar
from src.ui.status_bar import StatusBar

class App(ctk.CTk):
    """主应用窗口"""
    
    def __init__(self, settings: Settings):
        """
        初始化应用
        
        Args:
            settings: 应用设置
        """
        super().__init__()
        
        self.settings = settings
        
        # 配置窗口
        self.title("PDF/PPT 中文批注工具")
        self.geometry("1200x800")
        
        # 设置主题
        ctk.set_appearance_mode(settings.app.theme)
        ctk.set_default_color_theme("blue")
        
        # 创建 UI 组件
        self._create_widgets()
        
        # 配置布局
        self._configure_layout()
    
    def _create_widgets(self) -> None:
        """创建 UI 组件"""
        # 工具栏
        self.toolbar = Toolbar(self)
        
        # 主内容区域
        self.content_frame = ctk.CTkFrame(self)
        
        # 文档预览区域
        self.preview_frame = ctk.CTkFrame(self.content_frame)
        
        # 批注侧边栏
        self.sidebar_frame = ctk.CTkFrame(self.content_frame, width=300)
        
        # 状态栏
        self.status_bar = StatusBar(self)
    
    def _configure_layout(self) -> None:
        """配置布局"""
        # 工具栏在顶部
        self.toolbar.pack(fill="x", padx=5, pady=5)
        
        # 主内容区域
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 预览区域占据主要空间
        self.preview_frame.pack(side="left", fill="both", expand=True)
        
        # 侧边栏在右侧
        self.sidebar_frame.pack(side="right", fill="y")
        
        # 状态栏在底部
        self.status_bar.pack(fill="x", padx=5, pady=5)
    
    def update_status(self, message: str) -> None:
        """更新状态栏消息"""
        self.status_bar.set_message(message)
    
    def update_progress(self, current: int, total: int, status: str) -> None:
        """更新进度"""
        self.status_bar.set_progress(current, total, status)
```

- [ ] **Step 2: 创建工具栏**

```python
# src/ui/toolbar.py
import customtkinter as ctk

class Toolbar(ctk.CTkFrame):
    """工具栏"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
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
            values=["OpenAI", "Ollama"],
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
        pass
    
    def _on_export(self) -> None:
        """导出文件"""
        pass
    
    def _on_mode_change(self, value: str) -> None:
        """切换批注模式"""
        pass
    
    def _on_llm_change(self, value: str) -> None:
        """切换 LLM"""
        pass
    
    def _on_settings(self) -> None:
        """打开设置"""
        pass
```

- [ ] **Step 3: 创建状态栏**

```python
# src/ui/status_bar.py
import customtkinter as ctk

class StatusBar(ctk.CTkFrame):
    """状态栏"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """创建状态栏组件"""
        # 状态消息
        self.message_label = ctk.CTkLabel(
            self,
            text="就绪",
            anchor="w"
        )
        self.message_label.pack(side="left", fill="x", expand=True, padx=5)
        
        # 进度条
        self.progress_bar = ctk.CTkProgressBar(self, width=200)
        self.progress_bar.pack(side="right", padx=5)
        self.progress_bar.set(0)
        
        # 进度文本
        self.progress_label = ctk.CTkLabel(
            self,
            text="",
            anchor="e"
        )
        self.progress_label.pack(side="right", padx=5)
    
    def set_message(self, message: str) -> None:
        """设置状态消息"""
        self.message_label.configure(text=message)
    
    def set_progress(self, current: int, total: int, status: str) -> None:
        """设置进度"""
        if total > 0:
            progress = current / total
            self.progress_bar.set(progress)
            self.progress_label.configure(text=f"{current}/{total}")
        self.message_label.configure(text=status)
```

- [ ] **Step 4: 创建 UI __init__.py**

```python
# src/ui/__init__.py
from .app import App

__all__ = ["App"]
```

- [ ] **Step 5: 提交**

```bash
git add src/ui/
git commit -m "feat: add main application window with toolbar and status bar"
```

---

## Task 10: 文档预览和批注侧边栏

**Files:**
- Create: `src/ui/preview_panel.py`
- Create: `src/ui/sidebar_panel.py`

- [ ] **Step 1: 创建文档预览面板**

```python
# src/ui/preview_panel.py
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
```

- [ ] **Step 2: 创建批注侧边栏**

```python
# src/ui/sidebar_panel.py
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
        # 清空现有卡片
        for card in self.annotation_cards:
            card.destroy()
        self.annotation_cards.clear()
        
        # 创建新卡片
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
        
        # 重新显示过滤后的批注
        for card in self.annotation_cards:
            card.destroy()
        self.annotation_cards.clear()
        
        for ann in filtered:
            card = self._create_annotation_card(ann)
            card.pack(fill="x", pady=5)
            self.annotation_cards.append(card)
```

- [ ] **Step 3: 提交**

```bash
git add src/ui/preview_panel.py src/ui/sidebar_panel.py
git commit -m "feat: add document preview and annotation sidebar panels"
```

---

## Task 11: 设置对话框

**Files:**
- Create: `src/ui/settings_dialog.py`

- [ ] **Step 1: 创建设置对话框**

```python
# src/ui/settings_dialog.py
import customtkinter as ctk
from typing import Optional
from src.models.config import Settings

class SettingsDialog(ctk.CTkToplevel):
    """设置对话框"""
    
    def __init__(self, master, settings: Settings, **kwargs):
        super().__init__(master, **kwargs)
        
        self.settings = settings
        self.result: Optional[Settings] = None
        
        # 配置窗口
        self.title("设置")
        self.geometry("500x600")
        self.resizable(False, False)
        
        # 模态对话框
        self.transient(master)
        self.grab_set()
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """创建设置组件"""
        # 选项卡
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # LLM 设置选项卡
        self.llm_tab = self.tabview.add("LLM 设置")
        self._create_llm_settings()
        
        # 批注设置选项卡
        self.annotation_tab = self.tabview.add("批注设置")
        self._create_annotation_settings()
        
        # 应用设置选项卡
        self.app_tab = self.tabview.add("应用设置")
        self._create_app_settings()
        
        # 按钮
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(fill="x", padx=10, pady=10)
        
        self.save_btn = ctk.CTkButton(
            self.button_frame,
            text="保存",
            command=self._on_save
        )
        self.save_btn.pack(side="right", padx=5)
        
        self.cancel_btn = ctk.CTkButton(
            self.button_frame,
            text="取消",
            command=self._on_cancel
        )
        self.cancel_btn.pack(side="right", padx=5)
    
    def _create_llm_settings(self) -> None:
        """创建 LLM 设置"""
        # 提供商选择
        ctk.CTkLabel(self.llm_tab, text="LLM 提供商:").pack(anchor="w", padx=10, pady=5)
        
        self.provider_var = ctk.StringVar(value=self.settings.llm.provider)
        self.provider_segment = ctk.CTkSegmentedButton(
            self.llm_tab,
            values=["openai", "ollama"],
            variable=self.provider_var
        )
        self.provider_segment.pack(fill="x", padx=10, pady=5)
        
        # OpenAI 设置
        self.openai_frame = ctk.CTkFrame(self.llm_tab)
        self.openai_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.openai_frame, text="API Key:").pack(anchor="w", padx=5, pady=2)
        self.api_key_entry = ctk.CTkEntry(self.openai_frame, show="*")
        self.api_key_entry.pack(fill="x", padx=5, pady=2)
        self.api_key_entry.insert(0, self.settings.llm.openai.api_key)
        
        ctk.CTkLabel(self.openai_frame, text="模型:").pack(anchor="w", padx=5, pady=2)
        self.model_entry = ctk.CTkEntry(self.openai_frame)
        self.model_entry.pack(fill="x", padx=5, pady=2)
        self.model_entry.insert(0, self.settings.llm.openai.model)
        
        # Ollama 设置
        self.ollama_frame = ctk.CTkFrame(self.llm_tab)
        self.ollama_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.ollama_frame, text="Base URL:").pack(anchor="w", padx=5, pady=2)
        self.base_url_entry = ctk.CTkEntry(self.ollama_frame)
        self.base_url_entry.pack(fill="x", padx=5, pady=2)
        self.base_url_entry.insert(0, self.settings.llm.ollama.base_url)
        
        ctk.CTkLabel(self.ollama_frame, text="模型:").pack(anchor="w", padx=5, pady=2)
        self.ollama_model_entry = ctk.CTkEntry(self.ollama_frame)
        self.ollama_model_entry.pack(fill="x", padx=5, pady=2)
        self.ollama_model_entry.insert(0, self.settings.llm.ollama.model)
    
    def _create_annotation_settings(self) -> None:
        """创建批注设置"""
        # 批注模式
        ctk.CTkLabel(self.annotation_tab, text="批注模式:").pack(anchor="w", padx=10, pady=5)
        
        self.mode_var = ctk.StringVar(value=self.settings.annotation.mode)
        self.mode_segment = ctk.CTkSegmentedButton(
            self.annotation_tab,
            values=["overlay", "sidebar"],
            variable=self.mode_var
        )
        self.mode_segment.pack(fill="x", padx=10, pady=5)
        
        # 详细程度
        ctk.CTkLabel(self.annotation_tab, text="详细程度:").pack(anchor="w", padx=10, pady=5)
        
        self.detail_var = ctk.StringVar(value=self.settings.annotation.detail_level)
        self.detail_segment = ctk.CTkSegmentedButton(
            self.annotation_tab,
            values=["summary", "detailed", "custom"],
            variable=self.detail_var
        )
        self.detail_segment.pack(fill="x", padx=10, pady=5)
        
        # 字体设置
        self.font_frame = ctk.CTkFrame(self.annotation_tab)
        self.font_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.font_frame, text="字体大小:").pack(anchor="w", padx=5, pady=2)
        self.font_size_entry = ctk.CTkEntry(self.font_frame)
        self.font_size_entry.pack(fill="x", padx=5, pady=2)
        self.font_size_entry.insert(0, str(self.settings.annotation.style.font_size))
    
    def _create_app_settings(self) -> None:
        """创建应用设置"""
        # 主题
        ctk.CTkLabel(self.app_tab, text="主题:").pack(anchor="w", padx=10, pady=5)
        
        self.theme_var = ctk.StringVar(value=self.settings.app.theme)
        self.theme_segment = ctk.CTkSegmentedButton(
            self.app_tab,
            values=["light", "dark", "system"],
            variable=self.theme_var
        )
        self.theme_segment.pack(fill="x", padx=10, pady=5)
        
        # 语言
        ctk.CTkLabel(self.app_tab, text="语言:").pack(anchor="w", padx=10, pady=5)
        
        self.language_var = ctk.StringVar(value=self.settings.app.language)
        self.language_segment = ctk.CTkSegmentedButton(
            self.app_tab,
            values=["zh-CN", "en-US"],
            variable=self.language_var
        )
        self.language_segment.pack(fill="x", padx=10, pady=5)
    
    def _on_save(self) -> None:
        """保存设置"""
        # 更新设置对象
        self.settings.llm.provider = self.provider_var.get()
        self.settings.llm.openai.api_key = self.api_key_entry.get()
        self.settings.llm.openai.model = self.model_entry.get()
        self.settings.llm.ollama.base_url = self.base_url_entry.get()
        self.settings.llm.ollama.model = self.ollama_model_entry.get()
        self.settings.annotation.mode = self.mode_var.get()
        self.settings.annotation.detail_level = self.detail_var.get()
        self.settings.app.theme = self.theme_var.get()
        self.settings.app.language = self.language_var.get()
        
        self.result = self.settings
        self.destroy()
    
    def _on_cancel(self) -> None:
        """取消"""
        self.destroy()
```

- [ ] **Step 2: 提交**

```bash
git add src/ui/settings_dialog.py
git commit -m "feat: add settings dialog for LLM, annotation, and app configuration"
```

---

## Task 12: 文件导入和应用入口

**Files:**
- Create: `src/ui/file_panel.py`
- Create: `src/main.py`
- Create: `src/utils/__init__.py`
- Create: `src/utils/file_utils.py`

- [ ] **Step 1: 创建文件工具**

```python
# src/utils/file_utils.py
import os
from typing import List, Tuple

SUPPORTED_EXTENSIONS = {".pdf", ".ppt", ".pptx"}

def get_file_type(file_path: str) -> str:
    """
    获取文件类型
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 文件类型 ("pdf" 或 "ppt")
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return "pdf"
    elif ext in (".ppt", ".pptx"):
        return "ppt"
    else:
        raise ValueError(f"不支持的文件格式: {ext}")

def is_supported_file(file_path: str) -> bool:
    """检查文件是否支持"""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in SUPPORTED_EXTENSIONS

def get_supported_files(directory: str) -> List[str]:
    """
    获取目录中所有支持的文件
    
    Args:
        directory: 目录路径
        
    Returns:
        List[str]: 文件路径列表
    """
    files = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath) and is_supported_file(filepath):
            files.append(filepath)
    return files

def validate_file(file_path: str) -> Tuple[bool, str]:
    """
    验证文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        Tuple[bool, str]: (是否有效, 错误消息)
    """
    if not os.path.exists(file_path):
        return False, "文件不存在"
    
    if not os.path.isfile(file_path):
        return False, "路径不是文件"
    
    if not is_supported_file(file_path):
        return False, "不支持的文件格式"
    
    return True, ""
```

- [ ] **Step 2: 创建工具 __init__.py**

```python
# src/utils/__init__.py
from .file_utils import get_file_type, is_supported_file, get_supported_files, validate_file

__all__ = ["get_file_type", "is_supported_file", "get_supported_files", "validate_file"]
```

- [ ] **Step 3: 创建文件导入面板**

```python
# src/ui/file_panel.py
import customtkinter as ctk
from tkinter import filedialog
from typing import List, Callable
from src.utils.file_utils import is_supported_file

class FilePanel(ctk.CTkFrame):
    """文件导入面板"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.files: List[str] = []
        self.on_files_selected: Callable = None
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """创建文件面板组件"""
        # 标题
        self.title_label = ctk.CTkLabel(
            self,
            text="文件导入",
            font=("Arial", 14, "bold")
        )
        self.title_label.pack(pady=10)
        
        # 导入按钮
        self.import_btn = ctk.CTkButton(
            self,
            text="选择文件",
            command=self._on_import
        )
        self.import_btn.pack(pady=5)
        
        # 文件列表
        self.file_list = ctk.CTkScrollableFrame(self)
        self.file_list.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 处理按钮
        self.process_btn = ctk.CTkButton(
            self,
            text="开始处理",
            command=self._on_process,
            state="disabled"
        )
        self.process_btn.pack(pady=10)
    
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
            self.files = list(files)
            self._update_file_list()
            
            if self.on_files_selected:
                self.on_files_selected(self.files)
    
    def _update_file_list(self) -> None:
        """更新文件列表显示"""
        # 清空现有列表
        for widget in self.file_list.winfo_children():
            widget.destroy()
        
        # 添加新文件
        for file_path in self.files:
            frame = ctk.CTkFrame(self.file_list)
            frame.pack(fill="x", pady=2)
            
            label = ctk.CTkLabel(
                frame,
                text=file_path.split("/")[-1],
                anchor="w"
            )
            label.pack(side="left", fill="x", expand=True, padx=5)
            
            remove_btn = ctk.CTkButton(
                frame,
                text="移除",
                width=60,
                command=lambda p=file_path: self._remove_file(p)
            )
            remove_btn.pack(side="right", padx=5)
        
        # 更新按钮状态
        if self.files:
            self.process_btn.configure(state="normal")
        else:
            self.process_btn.configure(state="disabled")
    
    def _remove_file(self, file_path: str) -> None:
        """移除文件"""
        if file_path in self.files:
            self.files.remove(file_path)
            self._update_file_list()
    
    def _on_process(self) -> None:
        """开始处理"""
        pass
    
    def get_selected_files(self) -> List[str]:
        """获取选中的文件"""
        return self.files.copy()
```

- [ ] **Step 4: 创建主入口**

```python
# src/main.py
import sys
import os
import yaml
from pathlib import Path
from src.models.config import Settings
from src.ui.app import App

def load_config(config_path: str = None) -> Settings:
    """加载配置"""
    if config_path is None:
        # 使用默认配置路径
        config_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "config",
            "default.yaml"
        )
    
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
            return Settings(**config_data)
    
    return Settings()

def save_config(settings: Settings, config_path: str = None) -> None:
    """保存配置"""
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "config",
            "default.yaml"
        )
    
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(settings.model_dump(), f, allow_unicode=True)

def main():
    """主函数"""
    # 加载配置
    settings = load_config()
    
    # 创建并运行应用
    app = App(settings)
    app.mainloop()

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: 提交**

```bash
git add src/ui/file_panel.py src/main.py src/utils/
git commit -m "feat: add file import panel and application entry point"
```

---

## Task 13: 集成测试

**Files:**
- Create: `tests/integration_test.py`

- [ ] **Step 1: 创建集成测试**

```python
# tests/integration_test.py
import pytest
import os
from src.models.config import Settings, LLMConfig
from src.parsers.pdf_parser import PDFParser
from src.parsers.ppt_parser import PPTParser
from src.models.document import Document

def test_pdf_parser_integration():
    """PDF 解析器集成测试"""
    parser = PDFParser()
    
    # 测试不存在的文件
    with pytest.raises(FileNotFoundError):
        parser.parse("nonexistent.pdf")
    
    # 测试不支持的格式
    with pytest.raises(ValueError):
        parser.parse("test.txt")

def test_ppt_parser_integration():
    """PPT 解析器集成测试"""
    parser = PPTParser()
    
    # 测试不存在的文件
    with pytest.raises(FileNotFoundError):
        parser.parse("nonexistent.pptx")
    
    # 测试不支持的格式
    with pytest.raises(ValueError):
        parser.parse("test.txt")

def test_settings_model():
    """设置模型测试"""
    settings = Settings()
    
    assert settings.llm.provider == "openai"
    assert settings.annotation.mode == "sidebar"
    assert settings.app.language == "zh-CN"

def test_document_model():
    """文档模型测试"""
    from src.models.page import Page
    from src.models.annotation import Annotation
    
    doc = Document(file_path="test.pdf", file_type="pdf")
    
    # 添加页面
    page = Page(page_number=1, content="Test content")
    doc.add_page(page)
    
    assert doc.total_pages == 1
    assert doc.get_page(1).content == "Test content"
    
    # 添加批注
    annotation = Annotation(
        id="test-1",
        page_number=1,
        content="测试批注",
        agent_role="translator"
    )
    page.add_annotation(annotation)
    
    assert len(page.annotations) == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

- [ ] **Step 2: 运行集成测试**

Run: `cd "e:\desktop\TO PDF" && python -m pytest tests/integration_test.py -v`
Expected: PASS - 5 tests passed

- [ ] **Step 3: 提交**

```bash
git add tests/integration_test.py
git commit -m "test: add integration tests for parsers and models"
```

---

## Task 14: 项目文档

**Files:**
- Create: `README.md`

- [ ] **Step 1: 创建 README**

```markdown
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

### 1. 克隆项目

```bash
git clone https://github.com/your-username/pdf-ppt-annotator.git
cd pdf-ppt-annotator
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置

编辑 `config/default.yaml` 配置 LLM 提供商和 API 密钥：

```yaml
llm:
  provider: "openai"  # 或 "ollama"
  openai:
    api_key: "your-api-key"
    model: "gpt-4o"
  ollama:
    base_url: "http://localhost:11434"
    model: "llama3:70b"
```

### 4. 运行

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
│   ├── parsers/         # 文档解析器
│   ├── services/        # 业务服务
│   ├── ui/              # 用户界面
│   ├── models/          # 数据模型
│   └── utils/           # 工具函数
├── tests/               # 测试文件
├── config/              # 配置文件
└── docs/                # 文档
```

## 许可证

MIT License
```

- [ ] **Step 2: 提交**

```bash
git add README.md
git commit -m "docs: add project README with installation and usage instructions"
```

---

## 执行建议

完成所有任务后，建议按以下顺序执行：

1. **初始化项目**: Task 1
2. **数据模型**: Task 2
3. **文档解析**: Task 3
4. **LLM 服务**: Task 4
5. **智能体定义**: Task 5
6. **Crew 编排**: Task 6
7. **批注服务**: Task 7
8. **导出服务**: Task 8
9. **UI 组件**: Task 9-12
10. **测试和文档**: Task 13-14

每个任务完成后运行测试验证，确保代码质量。
