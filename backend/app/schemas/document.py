from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class DocumentBase(BaseModel):
    """文档基础模型"""

    filename: str
    type: str
    description: Optional[str] = None


class DocumentCreate(DocumentBase):
    pass


class Document(DocumentBase):
    """文档响应模型"""

    id: str
    status: str
    progress: int
    message: Optional[str] = None
    chunk_size: Optional[int] = None
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentList(BaseModel):
    """文档列表响应模型"""

    documents: List[Document]


class DocumentDelete(BaseModel):
    """文档删除请求模型"""

    success: bool
    message: str


class DocumentUpdate(BaseModel):
    """文档更新请求模型"""

    new_name: Optional[str] = None
    enabled: Optional[bool] = None
