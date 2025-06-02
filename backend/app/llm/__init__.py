import logging
import os
import sys
from contextlib import suppress
from typing import (
    Any,
    Awaitable,
    Callable,
    Concatenate,
    Dict,
    List,
    Optional,
    ParamSpec,
    cast,
    override,
)

import aiosqlite
import litellm
from AgenticWrapper import Agent
from litellm import models_by_provider, provider_list
from loguru import logger

from ..schemas.model import CurrentModel
from .ollama_client import OllamaClient

# region LLM


class LLM:
    """
    LLM 类，负责处理 LLM 的初始化、模型设置、API key 设置、查询生成等操作
    """

    def __init__(self):
        """初始化 LLM 类"""
        self.current_model: CurrentModel | None = None
        self.current_provider = None
        self.ollama_client = OllamaClient()
        self._api_keys: dict[str, str] = {}

    async def update_current_model_from_db(
        self, db: aiosqlite.Connection
    ) -> CurrentModel | None:
        """从数据库获取当前模型配置"""
        cursor = await db.execute("SELECT * FROM current_model_config LIMIT 1")
        row = await cursor.fetchone()
        if not row:
            return None
        self.current_model = CurrentModel(**dict(row))
        return self.current_model

    async def update_api_keys_from_db(self, db: aiosqlite.Connection) -> None:
        """从数据库获取所有 api key"""
        self._api_keys.clear()
        cursor = await db.execute("SELECT * FROM remote_model_configs")
        rows = await cursor.fetchall()
        for row in rows:
            self._api_keys[row[0]] = row[1]

    def get_providers(self) -> list[str]:
        """获取所有可用的服务商列表

        Returns:
            服务商名称列表，如 ['openai', 'anthropic', 'ollama', ...]
        """
        excepts = {
            "custom_openai",
            "openai_like",
            "galadriel",
            "lm_studio",
            "litellm_proxy",
            "clarifai",
            "anthropic_text",
        }
        return [
            provider
            for provider in provider_list
            if provider not in excepts and self.get_provider_models(provider)
        ]

    def get_provider_models(self, provider: str) -> list[str]:
        """获取指定服务商支持的所有模型名称

        Args:
            provider: 服务商名称，如 'openai', 'anthropic', 'ollama' 等

        Returns:
            该服务商支持的模型名称列表

        Raises:
            ValueError: 当服务商不正确时抛出
        """
        with suppress(KeyError):
            return models_by_provider[provider]
        return []

    def get_local_models(self) -> list[dict]:
        """获取本地所有模型"""
        return self.ollama_client.get_models()

    async def set_current_model(
        self, model: CurrentModel, db: aiosqlite.Connection
    ) -> None:
        """设置当前使用的模型，并更新数据库"""
        # 清空当前配置
        await db.execute("DELETE FROM current_model_config")

        # 插入新配置
        await db.execute(
            """
            INSERT INTO current_model_config (type, name, provider)
            VALUES (?, ?, ?)
            """,
            (model.type, model.name, model.provider),
        )
        await db.commit()
        self.current_model = model

    async def get_current_model_and_key(
        self, db: aiosqlite.Connection
    ) -> tuple[CurrentModel, str | None]:
        """
        从数据库获取当前使用的模型配置和 api key
        """
        await self.update_current_model_from_db(db)
        await self.update_api_keys_from_db(db)
        if not self.current_model:
            raise ValueError("未找到当前模型配置")
        if not self.current_model.provider:
            raise ValueError("未找到当前模型提供商，请检查当前模型是否为本地模型？")
        return self.current_model, self._api_keys.get(self.current_model.provider, None)

    async def set_api_key_before_query(self, provider: str, api_key: str) -> None:
        """设置指定服务商的 API key

        Args:
            provider: 服务商名称
            api_key: API 密钥
        """

        self._api_keys[provider] = api_key

        # litellm 支持通过环境变量设置各个服务商的 API key
        # 参考: https://docs.litellm.ai/docs/providers
        provider_env_vars = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "azure": "AZURE_API_KEY",
            "cohere": "COHERE_API_KEY",
            "replicate": "REPLICATE_API_KEY",
            "huggingface": "HUGGINGFACE_API_KEY",
            "ai21": "AI21_API_KEY",
            "together_ai": "TOGETHER_API_KEY",
            "vertex_ai": "VERTEX_API_KEY",
            "palm": "PALM_API_KEY",
            "claude": "CLAUDE_API_KEY",
            "bedrock": "AWS_ACCESS_KEY_ID",  # AWS 需要额外设置 AWS_SECRET_ACCESS_KEY
            "mistral": "MISTRAL_API_KEY",
            "groq": "GROQ_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }

        # 设置环境变量
        if provider in provider_env_vars:
            os.environ[provider_env_vars[provider]] = api_key

        # 某些服务商需要特殊处理
        if provider == "openai":
            litellm.openai_key = api_key
        elif provider == "anthropic":
            litellm.anthropic_key = api_key
        elif provider == "azure":
            litellm.azure_key = api_key
        elif provider == "cohere":
            litellm.cohere_key = api_key
        elif provider == "huggingface":
            litellm.huggingface_key = api_key

    async def get_api_key_from_db(
        self, provider: str, db: aiosqlite.Connection
    ) -> Optional[str]:
        """获取指定服务商的 API key

        Args:
            provider: 服务商名称

        Returns:
            API key，如果未设置则返回 None
        """
        cursor = await db.execute(
            "SELECT api_key FROM remote_model_configs WHERE provider = ? LIMIT 1",
            (provider,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return row[0]  # 返回查询到的 API key

    async def async_generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        """异步生成回复

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "hello"}, ...]
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数，None表示不限制

        Returns:
            str: 生成的回复内容

        Raises:
            ValueError: 当未设置当前模型时抛出
            Exception: 当生成失败时抛出
        """
        if not self.current_model or not self.current_model.name:
            raise ValueError("请先设置要使用的模型")

        try:
            if self.current_model.type == "local":
                # 使用 Ollama
                return await self.ollama_client.async_generate(
                    model=self.current_model.name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            else:
                # 使用 litellm 处理远程模型
                assert self.current_model.provider is not None
                await self.set_api_key_before_query(
                    self.current_model.provider,
                    self._api_keys[self.current_model.provider],
                )
                response = await litellm.acompletion(
                    model=self.current_model.name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                # 由于 litellm 的类型定义不完整，这里使用 Any 类型
                response_dict = cast(Any, response)
                content = response_dict.choices[0].message.content
                if not isinstance(content, str):
                    raise Exception("生成的内容格式不正确")
                return content
        except Exception as e:
            raise Exception(f"生成失败: {str(e)}")


llm = LLM()

# endregion LLM

# region Agent


P = ParamSpec("P")


class RAGAgent(Agent):
    """
    Agent 类，相当于拥有自身 prompt 和记忆的 LLM (用户提供)
    """

    @override
    def __init__(
        self,
        name: str,
        prompt: str,
        description: Optional[str] = None,
        tools: Optional[List[Callable[..., Awaitable[str]]]] = None,
        default_temperature: Optional[float] = None,
        default_max_tokens: Optional[int] = None,
        max_iterations: int = 8,
        max_log_length: int = 300,
    ):
        self.name = name
        self.description = description
        self.prompt = prompt  # 明确存储 prompt 属性
        super().__init__(
            llm.async_generate,
            [{"role": "user", "content": prompt}],
            tools,
            default_temperature,
            default_max_tokens,
            max_iterations,
            max_log_length,
        )

    def add_pre_query_func(self, func: Callable[[str], Awaitable[str]]) -> "RAGAgent":
        """
        添加一个在查询前执行的映射函数。
        """
        original_query = self.query

        async def new_query(
            user_input: str,
            *args: Any,
            **kwargs: Any,
        ):
            user_input = await func(user_input)
            return await original_query(user_input, *args, **kwargs)

        self.query = new_query
        return self

    def add_after_query_func(self, func: Callable[[str], Awaitable[str]]) -> "RAGAgent":
        """
        添加一个在查询后执行的映射函数。
        """

        original_query = self.query

        async def new_query(*args, **kwargs) -> str:
            super_result = await original_query(*args, **kwargs)
            assert isinstance(super_result, str)
            return await func(super_result)

        self.query = new_query  # type: ignore
        return self


# endregion Agent
