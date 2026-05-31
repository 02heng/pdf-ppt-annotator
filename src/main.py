import sys
import os
import yaml
from pathlib import Path
from src.models.config import Settings
from src.ui.app import App


def get_config_dir() -> str:
    """获取配置目录"""
    return os.path.join(os.path.dirname(__file__), "..", "config")


def load_config() -> Settings:
    """加载配置（合并 default.yaml 和 local.yaml）"""
    config_dir = get_config_dir()
    default_path = os.path.join(config_dir, "default.yaml")
    local_path = os.path.join(config_dir, "local.yaml")

    # 加载默认配置
    config_data = {}
    if os.path.exists(default_path):
        with open(default_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

    # 加载本地配置（覆盖默认配置）
    if os.path.exists(local_path):
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
    config_dir = get_config_dir()
    local_path = os.path.join(config_dir, "local.yaml")

    os.makedirs(config_dir, exist_ok=True)

    with open(local_path, "w", encoding="utf-8") as f:
        yaml.dump(settings.model_dump(), f, allow_unicode=True)


def main():
    """主函数"""
    settings = load_config()
    app = App(settings)
    app.mainloop()


if __name__ == "__main__":
    main()
