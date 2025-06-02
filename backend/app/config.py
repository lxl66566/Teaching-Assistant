import os

from pydantic_settings import SettingsConfigDict


class Settings:
    # 应用配置
    APP_NAME: str = "RAG教学辅助系统"
    API_V1_STR: str = "/api"

    # 后端数据库配置
    DATABASE_URL: str = "sqlite:///./rag.db"

    # 向量数据库配置
    CHROMA_DIRECTORY = "./chroma_db"

    # ollama 配置
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: set[str] = {".pdf", ".docx", ".ppt", ".pptx", ".txt"}

    # 模型配置
    DEFAULT_MODEL: str = "gpt-3.5-turbo"

    # embedding
    EMBEDDING_MODEL_NAME = "milkey/gte:large-zh-f16"

    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
