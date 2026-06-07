import os
import sys
import traceback
from pathlib import Path

import yaml
from src.models.config import Settings
from src.ui.ctk_patch import apply_ctk_patches
from src.ui.theme import UITheme
from src.utils.runtime import get_default_config_path, get_local_config_path


def _get_log_dir() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home())) / "TOPDFAnnotator" / "logs"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Logs" / "TOPDFAnnotator"
    return Path.home() / ".local" / "share" / "TOPDFAnnotator" / "logs"


def _log_startup_error(exc: Exception) -> None:
    """将启动错误写入日志文件，方便排查"""
    log_dir = _get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "startup_error.log"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Platform: {sys.platform}\n")
        f.write(f"Python: {sys.version}\n")
        f.write(f"Frozen: {getattr(sys, 'frozen', False)}\n")
        f.write(f"Executable: {sys.executable}\n\n")
        f.write(traceback.format_exc())

    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "启动错误",
            f"应用启动时发生错误：\n\n{exc}\n\n详细日志：\n{log_path}"
        )
        root.destroy()
    except Exception:
        pass

def load_config() -> Settings:
    """加载配置（合并 default.yaml 和 local.yaml）"""
    default_path = get_default_config_path()
    local_path = get_local_config_path()

    config_data = {}
    if default_path.is_file():
        with open(default_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

    if local_path.is_file():
        with open(local_path, "r", encoding="utf-8") as f:
            local_data = yaml.safe_load(f) or {}
            _deep_merge(config_data, local_data)

    return Settings(**config_data)


def _deep_merge(base: dict, override: dict) -> None:
    """深度合并字典"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def save_config(settings: Settings) -> None:
    """保存配置到 local.yaml（不修改 default.yaml）"""
    local_path = get_local_config_path()
    local_path.parent.mkdir(parents=True, exist_ok=True)

    with open(local_path, "w", encoding="utf-8") as f:
        yaml.dump(settings.model_dump(), f, allow_unicode=True)


def main():
    """主函数"""
    try:
        apply_ctk_patches()
        UITheme.install()
        settings = load_config()
        from src.ui.app import App
        app = App(settings)
        app.mainloop()
    except Exception as e:
        _log_startup_error(e)
        raise


if __name__ == "__main__":
    main()
