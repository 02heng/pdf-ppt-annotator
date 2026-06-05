; Inno Setup — Windows 安装包
; 需先运行 build_windows.ps1，再在本机安装 Inno Setup 6 后编译此脚本

#ifndef MyAppVersion
  #define MyAppVersion "0.1.4"
#endif
#define MyAppName "TO PDF 批注工具"
#define MyAppPublisher "TO PDF"
#define MyAppExeName "TOPDFAnnotator.exe"
#define BuildDir "..\..\dist\TOPDFAnnotator"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\output
OutputBaseFilename=TOPDFAnnotator-Setup-{#MyAppVersion}-win64
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
SetupIconFile=..\..\assets\branding\icon.ico
UninstallDisplayIcon={app}\TOPDFAnnotator.exe

[Languages]
; CI/精简版 Inno Setup 可能未带中文语言包，使用内置默认语言
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加选项:"; Flags: unchecked

[Files]
Source: "{#BuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\TO PDF\ppt_cache"
