# SlideAnnotate（Electron + 本地 Python）

源码：<https://github.com/02heng/pdf-ppt-annotator>

面向讲师：上传英文 **PDF** 或 **PPTX**，按页提取正文，调用 **DeepSeek** 生成中文**教学批注**（理解与课堂指导，非全文翻译），预览编辑后可导出：

- **PDF**：每页原文后**追加一页**「教学批注」专页（普通 PDF 页面，非注释弹窗），Edge/Chrome/Adobe 均可稳定阅读；原文页不改。
- **PPTX**：写入每页**演讲者备注**，幻灯片可视内容不变。

> 不支持旧版 `.ppt`，请在 PowerPoint / WPS 中**另存为 `.pptx`**。

## 分步操作（建议你按顺序做）

1. **安装 Node.js 18+**、**Python 3.10+**（Windows 从 [python.org](https://www.python.org/downloads/) 安装时勾选 *Add to PATH*）。
2. **安装 Python 依赖**（在项目根目录打开终端）：

   ```bash
   pip install -r server/requirements.txt
   ```

   （可选）若下载很慢或超时，可改用国内 PyPI 镜像，例如：

   ```bash
   pip install -r server/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. **安装前端依赖**：

   ```bash
   npm install
   ```

   若 Electron 二进制下载失败（如 `ECONNRESET`），可在**同一次**终端里先设镜像再安装，例如 PowerShell：

   ```powershell
   $env:ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
   npm install
   ```

4. **启动应用**：

   ```bash
   npm start
   ```

   启动脚本会通过 `node ./node_modules/electron/cli.js .` 打开窗口，无需全局安装 `electron`。

5. 在界面填写 **DeepSeek API Key** → 选 **.pdf / .pptx** → **上传并解析页面** → **一键生成全部批注** → 可编辑 → **导出带批注文件**。

---

## 环境要求（macOS）

1. **Node.js** 18+（建议用 [nvm](https://github.com/nvm-sh/nvm) 安装）
2. **Python 3.10+**（/Xcode CLT 不自带完整 pip 环境时，建议 `brew install python`）
3. **DeepSeek API Key**，在界面填写或设置环境变量 `DEEPSEEK_API_KEY`

可选环境变量（Python 侧）：

- `DEEPSEEK_BASE_URL`：默认 `https://api.deepseek.com`
- `DEEPSEEK_MODEL`：纯文本回退时使用的模型，默认 `deepseek-chat`（见[官方文档](https://api-docs.deepseek.com/)）
- `DEEPSEEK_VISION_MODEL`：**读图/多模态**时优先使用，未设置则与 `DEEPSEEK_MODEL` 相同；若接口报不支持图片会自动回退为纯文本批注（推荐试 `deepseek-v4-flash` 等当前文档列出的型号）
- `SLIDE_ANNOTATE_PORT`：本地 API 端口，默认 `8765`
- `SLIDE_ANNOTATE_PYTHON`：Windows 下若界面进程找不到 Python，请设为 `python.exe` 的**完整路径**（用法同 AI-writer 的 `AIWRITER_PYTHON`）
- `SLIDE_ANNOTATE_SOFFICE`：**PPTX 整页预览**用的 LibreOffice `soffice` 可执行文件路径；未安装时 PPTX 仅显示内嵌图片或占位提示，PDF 预览不受影响

界面「预览与编辑」区会显示 **PDF/PPTX 单页图像**；下方文本框用于手动编辑教学批注。

## 安装与开发运行

```bash
cd /path/to/slide-annotate
pip3 install -r server/requirements.txt
npm install
npm start
```

首次启动时，Electron 会自动在本机拉起 `uvicorn`（工作目录为 `server/`）。若状态栏显示「本地服务未就绪」，请在终端单独排查：

```bash
cd server && python3 -m uvicorn app:app --host 127.0.0.1 --port 8765
```

## 打包 macOS 应用（可选）

```bash
npm run dist:mac
```

产物在 `dist/`。注意：当前 `electron-builder` 会把 `server/` 复制进应用资源目录，但**仍依赖用户本机已安装的 Python 及 pip 依赖**。若需完全离线分发，可自行将 `server` 用 PyInstaller 等打成独立可执行文件，并修改 `electron/main.cjs` 的启动命令。

## 项目结构

- `server/app.py` — FastAPI：上传、提取、DeepSeek、导出
- `electron/main.cjs` — 主进程：启动/退出 Python 子进程
- `electron/preload.cjs` — 安全桥接 API
- `renderer/` — 界面

## 许可

MIT
