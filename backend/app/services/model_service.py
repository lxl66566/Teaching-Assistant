import asyncio
import re
from typing import Optional

import httpx
from loguru import logger

from ..config import settings
from ..llm import llm
from ..llm.ollama_client import ollama_client
from ..schemas.model import CurrentModel


class ModelService:
    def __init__(self, db):
        self.db = db
        self.ollama_base_url = settings.OLLAMA_BASE_URL

    async def get_providers(self) -> list[str]:
        """获取所有支持的模型服务商"""
        return llm.get_providers()

    async def get_provider_models(self, provider: str) -> list[str]:
        """获取某个服务商支持的所有模型"""
        return llm.get_provider_models(provider)

    async def get_provider_api_key(self, provider: str) -> str | None:
        """获取某个服务商的 API 密钥"""
        return await llm.get_api_key_from_db(provider, self.db)

    async def get_local_models(self) -> list[dict]:
        """获取所有本地 Ollama 模型"""
        return llm.get_local_models()

    async def configure_remote_model_api_key(
        self,
        provider: str,
        api_key: str,
    ) -> None:
        """配置远程模型（只更新 API 密钥）"""
        # 更新或插入模型配置
        await self.db.execute(
            """
            INSERT OR REPLACE INTO remote_model_configs (provider, api_key)
            VALUES (?, ?)
            """,
            (provider, api_key),
        )
        await self.db.commit()

    async def get_current_model(self) -> CurrentModel | None:
        """获取当前使用的模型配置"""
        return await llm.update_current_model_from_db(self.db)

    async def set_current_model(
        self,
        model_type: str,
        model_name: str,
        provider: Optional[str] = None,
    ) -> None:
        """设置当前使用的模型"""
        await llm.set_current_model(
            CurrentModel(type=model_type, name=model_name, provider=provider),
            self.db,
        )

    async def _fetch_model_tags(
        self, client: httpx.AsyncClient, name: str
    ) -> Optional[dict]:
        """获取单个模型的标签信息"""
        try:
            tags_response = await client.get(f"https://ollama.com/library/{name}/tags")
            if tags_response.status_code != 200:
                return None

            content = tags_response.text
            tags_info = re.findall(r'href="/library/([^"]+)"', content)
            tags_info = tags_info[1:]

            description = re.findall(
                r"""<span id="summary-content"[^>]*>([^<>/]*)</span>""", content
            )
            description = description[0].strip() if description else ""

            # 解析标签信息，每个标签包含：大小和更新时间
            other_info_pattern = r"•\s+([\d.]+[KMGT]B)\s+•\s+([^<]+)"
            other_info: list[tuple[str, str]] = re.findall(other_info_pattern, content)
            other_info = [(x[0].strip(), x[1].strip()) for x in other_info]

            if len(tags_info) == len(other_info) * 2:
                tags_info = [tags_info[i] for i in range(len(tags_info)) if i % 2 == 0]

            assert len(other_info) == len(tags_info), (
                f"other_info_len: {len(other_info)}, tags_info_len: {len(tags_info)}"
            )

            if not other_info or not tags_info:
                return None

            # 构建标签列表
            tags_list = []
            for i in range(len(other_info)):
                tags_list.append(
                    {
                        "tag": tags_info[i].strip(),
                        "size": other_info[i][0].strip(),
                        "updated": other_info[i][1].strip(),
                    }
                )
            return {
                "name": name,
                "description": description or "No description available",
                "tags": tags_list,
            }
        except Exception as e:
            logger.error(f"获取模型 {name} 的标签失败: {e}")
            return None

    async def search_models(self, query: str) -> list[dict]:
        """搜索可下载的在线模型"""
        async with httpx.AsyncClient() as client:
            try:
                # 获取所有可用模型列表
                response = await client.get("https://ollama.com/library")
                if response.status_code != 200:
                    logger.error(f"获取模型列表失败: {response.status_code}")
                    return []

                # 解析 HTML 内容获取模型名称
                content = response.text
                model_names = re.findall(r'href="/library/([^"]+)"', content)
                model_names = list(set(model_names))  # 去重

                # 如果提供了搜索查询，进行过滤
                if query:
                    model_names = [
                        name for name in model_names if query.lower() in name.lower()
                    ]

                # 并行获取所有模型的标签信息
                model_names = model_names[:5]  # 限制返回数量
                tasks = [self._fetch_model_tags(client, name) for name in model_names]
                results = await asyncio.gather(*tasks)
                logger.debug(results)

                # 过滤掉失败的结果
                results = [model for model in results if model is not None]
                output = []
                for model in results:
                    for tag in model["tags"]:
                        output.append(
                            {
                                "name": tag["tag"],
                                "description": model["description"],
                                "size": tag["size"],
                                "updated": tag["updated"],
                            }
                        )
                return output

            except Exception as e:
                logger.error(f"搜索模型失败: {e}")
                return []

    async def start_model_download(self, name: str) -> None:
        """开始下载模型"""
        return ollama_client.pull_model(name)

    async def get_download_progress(self, model_name: str) -> dict:
        """获取模型下载进度"""
        return ollama_client.pull_status(model_name)
