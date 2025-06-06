from pathlib import Path
from typing import Optional

import toml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "Teaching Assistant"
    API_V1_STR: str = "/api"

    DATA_DIR: Path = Path("./data")

    # 后端数据库配置
    DATABASE_URL: str = Field(
        default_factory=lambda: f"sqlite:///{Settings().DATA_DIR}/rag.db"
    )

    # 向量数据库配置
    CHROMA_DIRECTORY: Path = Field(
        default_factory=lambda: Settings().DATA_DIR / "chroma"
    )

    LOG_DIR: Path = Field(default_factory=lambda: Settings().DATA_DIR / "logs")

    # 文件上传配置
    UPLOAD_DIR: Path = Field(default_factory=lambda: Settings().DATA_DIR / "upload")

    # ollama 配置
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"

    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: set[str] = {
        ".pdf",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".txt",
        ".md",
    }

    # embedding
    EMBEDDING_MODEL_NAME: str = "milkey/gte:large-zh-f16"

    # 每次向量数据库添加的文档数量
    EMBEDDING_BATCH_SIZE: int = 100

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore",
    )


def load_settings(config_file: Optional[Path] = None) -> Settings:
    """
    加载配置，并可选择从TOML文件合并配置
    """
    # 加载默认配置
    default_config_path = Path(__file__).parent / "config.toml"
    default_settings_dict = {}
    if default_config_path.exists():
        with open(default_config_path, "r", encoding="utf-8") as f:
            default_settings_dict = toml.load(f)

    # 将路径字符串转换为Path对象
    for key in ["DATA_DIR", "CHROMA_DIRECTORY", "LOG_DIR", "UPLOAD_DIR"]:
        if key in default_settings_dict and isinstance(default_settings_dict[key], str):
            default_settings_dict[key] = Path(default_settings_dict[key])

    # 创建默认Settings实例
    settings_instance = Settings(**default_settings_dict)

    # 如果提供了可选的TOML文件，则加载并合并
    if config_file:
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        with open(config_file, "r", encoding="utf-8") as f:
            user_config = toml.load(f)

        # 将路径字符串转换为Path对象
        for key in ["DATA_DIR", "CHROMA_DIRECTORY", "LOG_DIR", "UPLOAD_DIR"]:
            if key in user_config and isinstance(user_config[key], str):
                user_config[key] = Path(user_config[key])

        # 合并配置，用户配置覆盖默认配置
        updated_settings_dict = settings_instance.model_dump()
        updated_settings_dict.update(user_config)
        settings_instance = Settings(**updated_settings_dict)

    # 确保所有目录存在
    settings_instance.DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings_instance.CHROMA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    settings_instance.LOG_DIR.mkdir(parents=True, exist_ok=True)
    settings_instance.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    return settings_instance


settings = load_settings()
