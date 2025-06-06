from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime


class ChatSession(BaseModel):
    id: str
    created_at: datetime


class ChatSessionWithLastMessage(ChatSession):
    last_message: Optional[str] = None


class ChatOptions(BaseModel):
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = None


class AppMode(str, Enum):
    TEACHING_PLAN = "teaching plan"
    AGENT = "agent"
    FREE = "free"
    GRAPH = "graph"


class SendMessageRequest(BaseModel):
    content: str
    messages: List[Dict[str, str]]
    mode: Optional[AppMode] = (
        AppMode.TEACHING_PLAN
    )  # 新增 mode 字段，默认为 "teaching plan"
    options: Optional[ChatOptions] = None


class SendMessageResponse(BaseModel):
    workflow_id: str
    message_id: str


class StepStatus(str, Enum):
    WAITING = "waiting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


# 定义状态的排序顺序：Completed < Processing < Waiting < Error
STATUS_ORDER = {
    StepStatus.COMPLETED: 0,
    StepStatus.PROCESSING: 1,
    StepStatus.WAITING: 2,
    StepStatus.ERROR: 3,
}


class WorkflowStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class WorkflowStep(BaseModel):
    index: int
    name: str
    description: str
    status: StepStatus
    result: Optional[str] = None
    error: Optional[str] = None


class WorkflowType(BaseModel):
    status: WorkflowStatus
    current_step: int
    total_steps: int
    steps: List[WorkflowStep]
    final_content: Optional[str] = None
    error: Optional[str] = None


class CancelResponse(BaseModel):
    success: bool
    message: str
