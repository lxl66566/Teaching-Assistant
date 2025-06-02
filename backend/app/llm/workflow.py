import asyncio
import uuid
from pathlib import Path
from typing import Dict, List

import aiosqlite
from loguru import logger

from ..schemas.query import (
    STATUS_ORDER,
    AppMode,  # 导入 AppMode
    StepStatus,
    WorkflowStatus,
    WorkflowStep,
    WorkflowType,
)
from ..utils.llm_utils import flatten_svg_in_markdown, remove_think
from . import RAGAgent, llm
from .svg_gen import process_text_with_svg_generation
from .tool_use import get_wikipedia_content, query_vector_db

MAX_DESCRIPTION_LENGTH = 60


class Workflow:
    """
    Workflow 类，用于编排 RAGAgent 实例的线性执行流程，并提供基于 WorkflowStep 列表的状态视图。
    数据流从首个 RAGAgent 流向后续的 RAGAgent。
    """

    def __init__(self, workflow_self: WorkflowType, agents: List[RAGAgent]):
        """
        Args:
            workflow_self: 一个外部列表，用于同步 workflow 的步骤状态。
                           调用方负责创建和传入此空列表。workflow 将管理此列表的内容和排序。
            agents: 构成线性工作流的 RAGAgent 实例列表。
        """
        self.agents: List[RAGAgent] = []
        self._agent_name_map: Dict[str, RAGAgent] = {}  # 用于通过名称快速查找 Agent

        # 验证并添加 Agent
        for agent in agents:
            if not isinstance(agent, RAGAgent):
                raise TypeError("工作流中只能添加 RAGAgent 实例。")
            if not hasattr(agent, "name") or not isinstance(agent.name, str):
                raise ValueError("RAGAgent 实例必须具有类型为 str 的 'name' 属性。")
            if agent.name in self._agent_name_map:
                raise ValueError(
                    f"名称为 '{agent.name}' 的 RAGAgent 已存在于工作流中。"
                )

            self.agents.append(agent)
            self._agent_name_map[agent.name] = agent

        # --- WorkflowStep 相关 ---
        self.workflow_self = workflow_self  # 外部列表的引用
        self._agent_steps: Dict[
            str, WorkflowStep
        ] = {}  # 将 Agent 名称映射到其 WorkflowStep 实例

        # 在初始化时构建初始的 workflow_steps 列表
        self._build_initial_step_list()

    def _build_initial_step_list(self):
        """
        根据线性 Agent 列表构建初始的 workflow_steps 列表和内部 agent->step 映射。
        清空传入的列表，并重新填充和排序。
        """
        logger.info("正在构建/排序 workflow_steps 列表...")

        # 清空外部列表和内部映射，以便重新构建
        self.workflow_self.steps.clear()
        self._agent_steps.clear()

        for index, agent in enumerate(self.agents):
            # 使用 agent.prompt 作为描述，因为它是 RAGAgent 明确拥有的属性
            description = agent.description or agent.prompt
            if len(description) > MAX_DESCRIPTION_LENGTH:
                description = description[:MAX_DESCRIPTION_LENGTH] + "..."

            step = WorkflowStep(
                index=index,  # 根据线性顺序分配索引
                name=agent.name,
                description=description,
                status=StepStatus.WAITING,  # 初始状态
                result=None,
                error=None,
            )
            self.workflow_self.steps.append(step)
            self._agent_steps[agent.name] = step

        # 列表已填充，现在进行初始排序（所有都是 WAITING，因此按索引排序）
        self._sort_workflow_steps()

    def _sort_workflow_steps(self):
        """
        根据状态 (Completed, Processing, Waiting, Error) 和索引对 workflow_steps 列表进行排序。
        """
        # 确保列表中所有步骤都具有状态和索引，然后进行排序
        if not all(
            hasattr(step, "status") and hasattr(step, "index")
            for step in self.workflow_self.steps
        ):
            logger.warning("警告：并非所有步骤都具有状态或索引，跳过排序。")
            return

        self.workflow_self.steps.sort(
            key=lambda step: (STATUS_ORDER.get(step.status, 99), step.index)
        )  # 使用 get 并设置默认值以确保安全

    def _insert_tool_step(self, agent_name: str, tool_call: Dict, current_index: int):
        """
        在当前 Agent 步骤之后插入一个工具调用步骤，并更新后续步骤的索引。
        """
        # 查找当前 Agent 步骤在 workflow_self.steps 中的实际位置
        insert_at_index = -1
        for i, step in enumerate(self.workflow_self.steps):
            if step.name == agent_name and step.index == current_index:
                insert_at_index = i + 1  # 插入到当前 Agent 步骤之后
                break

        if insert_at_index == -1:
            logger.error(
                f"未找到 Agent '{agent_name}' 的 WorkflowStep，无法插入工具步骤。"
            )
            return

        content = tool_call.get("content", "")
        if len(content) > MAX_DESCRIPTION_LENGTH:
            content = content[:MAX_DESCRIPTION_LENGTH] + "..."

        tool_step = WorkflowStep(
            index=current_index + 1,  # 临时索引，后续会重新计算
            name="工具调用",
            description=f"{tool_call.get('name', '未知工具')}",
            status=StepStatus.COMPLETED,  # 工具调用通常是同步完成的
            result=tool_call.get("content", ""),
            error=None,
        )

        # 插入工具步骤
        self.workflow_self.steps.insert(insert_at_index, tool_step)

        # 更新所有后续步骤的索引
        for i in range(insert_at_index + 1, len(self.workflow_self.steps)):
            self.workflow_self.steps[i].index += 1

        # 更新工具步骤的实际索引
        tool_step.index = insert_at_index
        self._sort_workflow_steps()  # 重新排序以确保索引和状态正确

    async def run(self, initial_messages: str | List[str]) -> Dict[str, str]:
        """
        异步执行线性 workflow。

        Args:
            initial_messages: 提供给第一个 RAGAgent 的初始输入消息。

        Returns:
            一个字典，包含 workflow 中所有已成功执行 RAGAgent 的最终输出，键为 RAGAgent 名称，值为输出字符串。
            未执行或失败的 RAGAgent 不会包含在结果中。
        """
        if not self.agents:
            self.workflow_self.steps.clear()
            self._agent_steps.clear()
            logger.info("工作流中没有 Agent。返回空结果。")
            return {}

        logger.info("\n初始 workflow_steps 列表（全部 WAITING，按索引排序）：")
        for step in self.workflow_self.steps:
            logger.info(f"- {step}")

        outputs: Dict[str, str] = {}
        # 将初始消息转换为单个字符串作为第一个 Agent 的输入
        current_input_str: str = (
            initial_messages
            if isinstance(initial_messages, str)
            else "\n".join(initial_messages)
        )

        for i, agent in enumerate(self.agents):
            agent_name = agent.name
            step = self._agent_steps.get(agent_name)

            if step is None:
                logger.error(f"未找到 Agent '{agent_name}' 的 WorkflowStep。")
                continue

            # 更新当前 Agent 步骤状态为 PROCESSING
            step.status = StepStatus.PROCESSING
            self._sort_workflow_steps()
            logger.info(f"工作流状态：Agent '{agent_name}' 正在处理中。")
            for s in self.workflow_self.steps:
                logger.info(f"- {s}")

            try:
                # 执行 Agent 查询，传入单个字符串，并明确返回类型为 str
                result = await agent.query(current_input_str)
                assert isinstance(result, str)
                result = flatten_svg_in_markdown(remove_think(result))
                outputs[agent_name] = result

                # 更新 Agent 步骤状态为 COMPLETED
                step.status = StepStatus.COMPLETED
                step.result = result
                logger.info(f"Agent '{agent_name}' 成功完成。")

                # 检查 Agent 的 memory 中是否有工具调用
                for mem_entry in agent.memory:
                    if isinstance(mem_entry, dict) and mem_entry.get("role") == "tool":
                        logger.info(
                            f"Agent '{agent_name}' 检测到工具调用：{mem_entry.get('name')}"
                        )
                        # 插入工具调用步骤
                        self._insert_tool_step(agent_name, mem_entry, step.index)

                # 将当前 Agent 的输出作为下一个 Agent 的输入
                current_input_str = result

            except Exception as e:
                logger.error(f"Agent '{agent_name}' 执行失败，错误：{e}")
                step.status = StepStatus.ERROR
                step.error = str(e)
                # 如果一个 Agent 失败，后续 Agent 将无法获得输入，因此也应标记为 ERROR
                for j in range(i + 1, len(self.agents)):
                    next_agent_name = self.agents[j].name
                    next_step = self._agent_steps.get(next_agent_name)
                    if next_step and next_step.status == StepStatus.WAITING:
                        next_step.status = StepStatus.ERROR
                        next_step.error = f"上游 Agent '{agent_name}' 失败。"
                break  # 终止工作流执行

            finally:
                # 每次状态变化后重新排序列表
                self._sort_workflow_steps()

        logger.info("\n工作流执行完成。")
        logger.info(f"总 Agent 数量: {len(self.agents)}")
        logger.info(self.workflow_self.steps)

        return outputs


# region WorkflowService


class WorkflowService:
    """
    Workflows 类，负责处理工作流的创建、处理、取消等操作
    """

    def __init__(self):
        self.llm = llm
        # 工作流缓存，存储每个工作流的状态和结果
        self.workflows: dict[str, WorkflowType] = {}
        # 存储每个工作流的任务
        self.tasks: Dict[str, asyncio.Task] = {}

    async def create_workflow(
        self,
        messages: List[dict[str, str]],
        db: aiosqlite.Connection,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        mode: AppMode = AppMode.TEACHING_PLAN,  # 新增 mode 参数
    ) -> str:
        """创建一个新的工作流"""

        try:
            if not self.llm.current_model:
                await self.llm.update_current_model_from_db(db)
            if not self.llm.current_model:
                raise ValueError("请先使用 set_model() 设置要使用的模型")

            if self.llm.current_model.type == "remote":
                await self.llm.update_api_keys_from_db(db)
        except Exception as e:
            logger.error(f"获取当前模型失败: {e}")
            raise

        try:
            if self.llm.current_model.type == "remote":
                await self.llm.update_api_keys_from_db(db)
        except Exception as e:
            logger.error(f"从数据库获取 api key 失败: {e}")
            raise

        workflow_id = str(uuid.uuid4())

        # 存储工作流状态
        self.workflows[workflow_id] = WorkflowType(
            status=WorkflowStatus.PROCESSING,
            current_step=0,
            total_steps=3,
            steps=[],
        )

        # 根据模式定义工作流步骤
        agents = None
        if mode == AppMode.TEACHING_PLAN:
            agents = [
                RAGAgent(
                    name="预处理",
                    prompt="""准确地规范化用户指令。你需要补充提问中可能有关的名词，对于教学指令，则目标受众默认为大学生。
**输出：只输出一句陈述句**，代表规范化后的用户指令。需要包含足够的信息量。""",
                    description="用户指令规范化与信息补充",
                ),
                RAGAgent(
                    name="生成",
                    tools=[query_vector_db, get_wikipedia_content],
                    prompt=r"""你是一名教学领域设计专家，我要求你为我指定的学科领域设计一个系统化、创新性的教案。

首先，你需要进行工具调用。在通过工具获取到足够信息后，再进行教案的生成。

内容生成需满足以下要求：

- 按"基础模块→进阶模块→创新模块"三级递进；
- 包含教学案例和开放性讨论。对于你生成的任何题目，你都需要给出标准解答。
- 对于理科专业的教案，可以生成 markdown 行内公式（需要用 `$` 包裹）；电路图等图片请生成 ```img\n...\n``` markdown 代码块包裹的尽可能准确的**自然语言描述**，最好附带上 ASCII art，有效信息越多越准确越好。

请你先仔细思考你完成该任务的所需步骤，再进行回答。

输出：工具调用格式，或者你所要执行的步骤 + markdown 格式的教案内容；不要带有其他额外内容。""",
                    description="教案生成",
                ),
                RAGAgent(
                    name="后处理",
                    prompt="""请对大模型的输出结果做检查，若有不合适的地方，请修复。例如：
- 不要有步骤提示，只返回教案内容；
- 该输出结果需要是有效的 markdown 语法，行内公式需要用 `$` 包裹，<svg> 标签处在正文内。
  - svg 本身正确（标签层次正确并闭合）
- 公式中使用符号需要是中国教学标准符号，主要输出语言需要是简体中文。
- 逻辑连贯，没有乱码。
输出：修复后的大模型输出结果。不要输出任何额外内容。""",
                    description="大模型输出结果检查修复",
                ).add_pre_query_func(process_text_with_svg_generation),
            ]
        elif mode == AppMode.AGENT:
            agents = [
                RAGAgent(
                    name="Agent",
                    prompt="""你是一个智能助手，请根据用户的问题提供简洁准确的回答。
你可以使用工具来获取信息，获取信息后，结合你的思考进行回答。""",
                    tools=[query_vector_db, get_wikipedia_content],
                    description="Agent 模式问答",
                )
            ]

        try:
            # 创建异步任务
            if mode != AppMode.FREE:
                assert agents is not None
                self.agents_workflow = Workflow(self.workflows[workflow_id], agents)
                task = asyncio.create_task(
                    self._process_workflow(workflow_id, messages)
                )
            else:
                task = asyncio.create_task(
                    self._process_workflow_simple(workflow_id, messages)
                )
            self.tasks[workflow_id] = task
            # 添加完成回调
            task.add_done_callback(
                lambda t: asyncio.create_task(
                    self._workflow_completed_callback(workflow_id, t)
                )
            )
        except Exception as e:
            logger.error(f"创建工作流任务失败: {e}")
            raise

        return workflow_id

    async def _process_workflow_simple(
        self,
        workflow_id: str,
        messages: List[dict[str, str]],
    ):
        """异步处理工作流，用于简单模式"""
        workflow = self.workflows[workflow_id]

        try:
            if asyncio.current_task().cancelled():  # type: ignore
                workflow.status = WorkflowStatus.CANCELLED
                return

            workflow.status = WorkflowStatus.PROCESSING
            logger.info(f"WorkflowService got user message: {messages}")
            res = await self.llm.async_generate(
                messages=messages, temperature=0.2, max_tokens=None
            )

            workflow.status = WorkflowStatus.COMPLETED
            workflow.final_content = res or "无内容，请检查 workflow 内是否有错误"

            # 保存到日志
            md_path = Path("logs") / workflow_id
            md_path.mkdir(parents=True, exist_ok=True)
            with open(md_path / "最终生成结果_自由模式.md", "w", encoding="utf-8") as f:
                f.write(workflow.final_content)

        except Exception as e:
            logger.error(f"工作流 {workflow_id} 处理失败: {e}")
            workflow.status = WorkflowStatus.ERROR
            workflow.error = str(e)
            raise

    async def _process_workflow(
        self,
        workflow_id: str,
        messages: List[dict[str, str]],
    ) -> None:
        """异步处理工作流"""
        workflow = self.workflows[workflow_id]

        try:
            if asyncio.current_task().cancelled():  # type: ignore
                workflow.status = WorkflowStatus.CANCELLED
                return

            # 更新当前步骤状态
            workflow.current_step = 0
            messages_extract = [x["content"] for x in messages]
            logger.info(f"WorkflowService got user message: {messages_extract}")
            workflow_outputs = await self.agents_workflow.run(messages_extract)

            workflow.status = WorkflowStatus.COMPLETED
            workflow.final_content = (
                workflow_outputs[self.agents_workflow.agents[-1].name]
                or workflow.steps[-1].result
                or "无内容，请检查 workflow 内是否有错误"
            )

            # 保存到日志
            md_path = Path("logs") / workflow_id
            md_path.mkdir(parents=True, exist_ok=True)
            with open(md_path / "最终生成结果.md", "w", encoding="utf-8") as f:
                f.write(workflow.final_content)

        except Exception as e:
            logger.error(f"工作流 {workflow_id} 处理失败: {e}")
            workflow.status = WorkflowStatus.ERROR
            workflow.error = str(e)
            raise

    async def _workflow_completed_callback(
        self, workflow_id: str, task: asyncio.Task
    ) -> None:
        """工作流完成后的回调函数"""
        try:
            await task

        except asyncio.CancelledError:
            if workflow_id in self.workflows:
                self.workflows[workflow_id].status = WorkflowStatus.CANCELLED
        except Exception as e:
            if workflow_id in self.workflows:
                self.workflows[workflow_id].status = WorkflowStatus.ERROR
                self.workflows[workflow_id].error = str(e)

        finally:
            # 清理任务对象
            if workflow_id in self.tasks:
                del self.tasks[workflow_id]

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """取消指定的工作流

        Args:
            workflow_id: 要取消的工作流ID

        Returns:
            bool: 是否成功取消

        Raises:
            ValueError: 如果工作流不存在
        """
        logger.info(f"取消工作流：{workflow_id}")
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流 {workflow_id} 不存在")

        if workflow_id not in self.tasks:
            return False

        # 尝试取消任务
        task = self.tasks[workflow_id]
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        return True

    def get_workflow_status(self, workflow_id: str) -> WorkflowType:
        """获取工作流状态

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流状态信息
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流 {workflow_id} 不存在")
        return self.workflows[workflow_id]


workflow_service = WorkflowService()
