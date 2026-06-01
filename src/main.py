import yaml
from src.models.config import Settings
from src.ui.ctk_patch import apply_ctk_patches
from src.ui.app import App
from src.utils.runtime import get_default_config_path, get_local_config_path

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
    apply_ctk_patches()
    settings = load_config()
    app = App(settings)
    app.mainloop()


if __name__ == "__main__":
    main()
