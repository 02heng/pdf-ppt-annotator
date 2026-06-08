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
| `assets/branding/toolbar-logo.png` | Electron 顶栏小图 |
| `electron/assets/*` | Electron 窗口图标与 NSIS 安装包（由脚本同步） |

打包前 `build_electron_windows.ps1` / CI 会自动执行上述脚本。

## Electron 版安装包（开箱即用，推荐）

与 [AI-writer-master](../AI-writer-master) 相同：PyInstaller 冻结 Python 后端 + electron-builder NSIS + `rcedit` 写入 exe 图标。

**用户无需安装 Python 或 pip**，安装后双击即可使用。

在项目根目录 PowerShell 中执行：

```powershell
.\packaging\build_electron_windows.ps1
```

或分步：

```powershell
python scripts/generate_app_icons.py
cd electron
npm install
npm run dist
```

产物：`packaging/output/TO PDF 批注工具 Setup *.exe`

- 安装向导 / 卸载 / 快捷方式 / 任务栏：均使用 `assets/branding/icon.ico`（TO PDF 紫渐变 logo）
- 内置后端：`resources/backend-bin/topdf-backend.exe`（PyInstaller onedir）

### macOS（Apple Silicon / Intel）

```bash
chmod +x packaging/build_electron_mac.sh
./packaging/build_electron_mac.sh arm64    # M 系列芯片
./packaging/build_electron_mac.sh x86_64   # Intel Mac
```

产物：`packaging/output/TOPDFAnnotator-*-mac-arm64.dmg` 或 `*-mac-x64.dmg`

## GitHub Actions 自动打包（推荐）

在 GitHub 云端同时构建 Windows 与 macOS（arm64 + Intel），无需本机双平台环境。

**手动触发：** 仓库 → Actions → **Build Installers** → Run workflow（可选 `mac-only` 仅构建 Mac）

**发布版本：** 版本号以仓库根目录 `VERSION` 文件为准。

```bash
git tag v0.2.0
git push origin v0.2.0
```

| 平台 | 产物 |
|------|------|
| Windows | `TOPDFAnnotator-Setup-*-win64.exe` |
| macOS arm64 | `TOPDFAnnotator-*-mac-arm64.dmg` |
| macOS Intel | `TOPDFAnnotator-*-mac-x64.dmg` |

打 tag 会自动创建 GitHub Release；手动触发时在 Actions 运行记录的 **Artifacts** 下载。

## 前置条件（仅本地打包时需要）

| 平台 | 要求 |
|------|------|
| Windows | Python 3.10+、Node.js 20+ |
| macOS | Python 3.10+、Node.js 20+、Xcode Command Line Tools |

## 用户数据与配置

安装版配置与数据保存在用户目录，不写入安装目录：

- Windows：`%APPDATA%\TO PDF\`
- macOS：`~/Library/Application Support/TO PDF/`

首次运行后在应用内「设置」中填写 API Key 即可。

## 常见问题

**Q: 安装包很大？**  
A: 内置 Python 运行时及 AI/PDF 相关库，体积通常在 200–500 MB，属正常现象。

**Q: macOS 提示「已损坏，无法打开」？**  
A: 未购买 Apple 开发者签名时常见，经微信/网盘传输后更容易出现。安装后打开「终端」执行（把路径改成你的 .app 位置）：

```bash
xattr -cr "/Applications/TO PDF 批注工具.app"
```

然后右键应用 → **打开**（不要双击）。若仍不行，在「系统设置 → 隐私与安全性」中点「仍要打开」。

**Q: macOS 提示「无法验证开发者」？**  
A: 未 Apple 签名时，用户需在「系统设置 → 隐私与安全性」中允许打开，或使用开发者账号 codesign + notarize。

**Q: Windows SmartScreen 拦截？**  
A: 未购买代码签名证书时常见，用户选「仍要运行」即可；正式发布建议购买 Authenticode 签名。
