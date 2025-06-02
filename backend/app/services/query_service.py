import aiosqlite
from loguru import logger

from ..llm.workflow import workflow_service
from ..schemas.query import (
    AppMode,  # 导入 AppMode
    CancelResponse,
    SendMessageRequest,
    SendMessageResponse,
    WorkflowType,
)


class QueryService:
    """
    查询服务，处理聊天请求和轮询
    """

    @staticmethod
    async def send_chat_request(
        request: SendMessageRequest, db: aiosqlite.Connection
    ) -> SendMessageResponse:
        """
        发送聊天请求，创建工作流

        Args:
            request: 包含消息内容和完整消息历史的请求

        Returns:
            带有工作流ID和消息ID的响应
        """
        # 设置默认温度值
        temperature = 0.2
        if request.options and request.options.temperature is not None:
            temperature = request.options.temperature

        # 设置最大token（可选）
        max_tokens = None
        if request.options and request.options.max_tokens is not None:
            max_tokens = request.options.max_tokens

        # 获取模式，如果为 None 则使用默认值 AppMode.TEACHING_PLAN
        mode = request.mode if request.mode is not None else AppMode.TEACHING_PLAN

        # 创建工作流
        workflow_id = await workflow_service.create_workflow(
            messages=request.messages,
            temperature=temperature,
            max_tokens=max_tokens,
            mode=mode,  # 传递 mode 参数
            db=db,
        )

        # 返回工作流ID和消息ID
        return SendMessageResponse(
            workflow_id=workflow_id,
            message_id=f"assistant-{workflow_id}",
        )

    @staticmethod
    def poll_workflow(workflow_id: str) -> WorkflowType:
        """
        轮询工作流状态

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流状态响应
        """
        try:
            # 获取工作流状态
            return workflow_service.get_workflow_status(workflow_id)

        except Exception as e:
            # 如果出现错误，构建错误响应
            logger.error(f"轮询工作流失败: {str(e)}")
            raise ValueError(f"轮询工作流失败: {str(e)}")

    @staticmethod
    def cancel_workflow(workflow_id: str) -> CancelResponse:
        """
        取消工作流
        """
        try:
            res = workflow_service.cancel_workflow(workflow_id)
            if not res:
                raise Exception("llm: 工作流取消失败")
            return CancelResponse(success=True, message="成功取消工作流")
        except Exception as e:
            logger.error(f"工作流取消失败: {str(e)}")
            return CancelResponse(success=False, message=str(e))
