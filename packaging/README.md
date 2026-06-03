# 打包说明

用户安装后**无需**安装 Python 或任何 pip 库。发布包内只有编译后的可执行文件与依赖，**不包含** `.py` 源码。

## 品牌图标

与 [AI-writer-master](https://github.com) 类似，图标由脚本从品牌图生成（本项目用 Pillow 绘制紫渐变 PDF+批注图标）：

```bash
python scripts/generate_app_icons.py
```

| 文件 | 用途 |
|------|------|
| `assets/branding/icon.ico` | Windows  exe / 任务栏 / Inno Setup 安装包 |
| `assets/branding/icon.png` | macOS `.app`、通用 512×512 |
| `assets/branding/logo.svg` | 矢量源稿（可改后重新运行脚本） |
| `src/web/favicon.png` | 浏览器预览页标签图标 |
| `src/web/brand-logo.png` | Web 顶栏、桌面顶栏小图 |

打包前 `build_windows.ps1` / CI 会自动执行上述脚本。

## GitHub Actions 自动打包（推荐）

在 GitHub 云端同时构建 Windows 与 macOS，无需本机双平台环境。

**手动触发：** 仓库 → Actions → **Build Installers** → Run workflow

**发布版本：**
```bash
git tag v1.0.0
git push origin v1.0.0
```

| 平台 | 产物 |
|------|------|
| Windows | `TOPDFAnnotator-Setup-1.0.0-win64.exe`、便携 zip |
| macOS | `TOPDFAnnotator-1.0.0-mac.dmg` |

打 tag 会自动创建 GitHub Release；手动触发时在 Actions 运行记录的 **Artifacts** 下载。

## 前置条件（仅本地打包时需要）

| 平台 | 要求 |
|------|------|
| Windows | Python 3.10+、本仓库源码 |
| macOS | Python 3.10+、Xcode Command Line Tools |

可选：

- **Windows 安装包**： [Inno Setup 6](https://jrsoftware.org/isdl.php)
- **macOS**：系统自带 `hdiutil`（用于生成 `.dmg`）

## Windows

在项目根目录 PowerShell 中执行：

```powershell
.\packaging\build_windows.ps1
```

产物：

| 类型 | 路径 |
|------|------|
| 便携版（文件夹） | `dist\TOPDFAnnotator\` |
| 安装程序（需 Inno Setup） | `packaging\output\TOPDFAnnotator-Setup-1.0.0-win64.exe` |

分发给用户：

- **推荐**：`TOPDFAnnotator-Setup-*.exe` 双击安装
- **免安装**：将整个 `dist\TOPDFAnnotator` 文件夹打成 zip 分发，运行其中的 `TOPDFAnnotator.exe`

## macOS

在 Mac 上克隆仓库后执行：

```bash
chmod +x packaging/build_mac.sh
./packaging/build_mac.sh
```

产物：

| 类型 | 路径 |
|------|------|
| 应用包 | `dist/TOPDFAnnotator.app` |
| 安装镜像 | `packaging/output/TOPDFAnnotator-1.0.0-mac.dmg` |

用户将 `.app` 或 DMG 中的程序拖入「应用程序」即可。

> **注意**：PyInstaller 无法在当前 Windows 机器上交叉编译 macOS 应用，必须在 Mac 上构建。

## 用户数据与配置

安装版配置与数据保存在用户目录，不写入安装目录：

- Windows：`%APPDATA%\TO PDF\`
- macOS：`~/Library/Application Support/TO PDF/`

首次运行后在应用内「设置」中填写 API Key 即可。

## 常见问题

**Q: 安装包很大？**  
A: 内置 Python 运行时及 AI/PDF 相关库，体积通常在 200–500 MB，属正常现象。

**Q: macOS 提示「无法验证开发者」？**  
A: 未 Apple 签名时，用户需在「系统设置 → 隐私与安全性」中允许打开，或使用开发者账号 codesign + notarize。

**Q: Windows SmartScreen 拦截？**  
A: 未购买代码签名证书时常见，用户选「仍要运行」即可；正式发布建议购买 Authenticode 签名。
