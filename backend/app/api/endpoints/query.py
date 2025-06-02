import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Path

from ...database import get_db
from ...schemas.query import (
    CancelResponse,
    SendMessageRequest,
    SendMessageResponse,
    WorkflowType,
)
from ...services.query_service import QueryService

router = APIRouter()
from loguru import logger


@router.post("/send", response_model=SendMessageResponse)
async def send_chat(
    request: SendMessageRequest,
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    发送聊天请求，创建工作流

    前端需要发送完整的消息历史，后端不存储任何对话历史
    返回工作流ID和消息ID，前端使用工作流ID轮询结果
    """
    try:
        return await QueryService.send_chat_request(request, db)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/poll/{workflow_id}", response_model=WorkflowType)
async def poll_workflow(
    workflow_id: str = Path(..., description="工作流ID"),
):
    """
    轮询工作流状态

    Args:
        workflow_id: 工作流ID

    Returns:
        工作流状态响应
    """
    try:
        return QueryService.poll_workflow(workflow_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel/{workflow_id}", response_model=CancelResponse)
async def cancel_workflow(workflow_id: str = Path(..., description="工作流ID")):
    """
    取消正在进行中的工作流
    """
    try:
        return QueryService.cancel_workflow(workflow_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
