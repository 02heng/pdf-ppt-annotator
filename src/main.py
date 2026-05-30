import sys
import os
import yaml
from pathlib import Path
from src.models.config import Settings
from src.ui.app import App


def load_config(config_path: str = None) -> Settings:
    """加载配置"""
    if config_path is None:
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
    settings = load_config()
    app = App(settings)
    app.mainloop()


if __name__ == "__main__":
    main()
