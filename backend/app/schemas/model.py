from typing import List, Optional

from pydantic import BaseModel, Field


class RemoteModelConfig(BaseModel):
    """远程模型配置"""

    provider: str = Field(..., description="模型服务提供商（如 OpenAI、Anthropic 等）")
    api_key: str = Field(..., description="API 密钥")


class ProviderList(BaseModel):
    """模型服务商列表响应"""

    provider: List[str]


class ProviderModels(BaseModel):
    """服务商模型列表响应"""

    model: List[str]
    api_key: Optional[str] = None


class LocalModel(BaseModel):
    name: str
    status: str  # ready/downloading/not_found
    size: str
    digest: str


class LocalModels(BaseModel):
    """本地模型列表响应"""

    model: List[LocalModel]


class ModelConfigureRequest(BaseModel):
    """配置模型请求"""

    type: str = Field(
        ..., pattern="^(remote|local)$", description="模型类型：remote 或 local"
    )
    name: str = Field(..., min_length=1, description="模型名称")
    provider: Optional[str] = Field(None, description="模型服务商")
    api_key: Optional[str] = Field(None, description="远程模型 API 密钥")


class ModelConfigureResponse(BaseModel):
    """配置模型响应"""

    success: bool
    message: str


class CurrentModel(BaseModel):
    """当前模型配置"""

    type: str = Field(
        ...,
        pattern="^(remote|local|null)$",
        description="模型类型：remote 或 local 或 null",
    )
    name: Optional[str] = Field(
        None, description="模型名称（如果 type 为 null，则为 null）"
    )
    provider: Optional[str] = Field(
        None, description="模型服务商（如果是本地模型，则为 null）"
    )


class SearchModel(BaseModel):
    name: str
    description: Optional[str] = None
    size: Optional[str] = None
    updated: Optional[str] = None


class SearchModelsResponse(BaseModel):
    models: List[SearchModel]


class ModelDownloadRequest(BaseModel):
    name: str


class ModelDownloadResponse(BaseModel):
    success: bool
    message: str


class ModelDownloadProgress(BaseModel):
    status: str  # downloading/completed/failed
    progress: float  # 0-100
    message: str
