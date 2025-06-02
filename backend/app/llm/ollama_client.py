import asyncio
import threading
from typing import Any, Dict

import ollama

from ..config import settings
from ..utils import format_size

# --- 全局状态管理 ---
# 使用字典存储每个模型拉取的进度和状态
# 结构: { model_name: {"status": str, "progress": float, "message": str, "thread": threading.Thread} }
_pull_states: Dict[str, Dict[str, Any]] = {}
# 使用锁来确保线程安全地访问 _pull_states
_pull_lock = threading.Lock()


class OllamaClient:
    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL):
        self.client = ollama.Client(base_url)

    def get_models(self) -> list[dict]:
        return list(
            map(
                lambda x: {
                    "name": x["model"],
                    "status": "ready",
                    "size": format_size(x["size"]),
                    "digest": x["digest"],
                },
                self.client.list().get("models", []),
            )
        )

    # --- 后台拉取任务 ---
    def _run_pull(self, name: str):
        """
        在后台线程中执行 ollama.pull 并更新共享状态。
        """
        global _pull_states
        current_progress = 0.0

        try:
            # stream=True 会返回一个生成器，实时产生进度更新
            stream = self.client.pull(model=name, stream=True)
            for progress in stream:
                # print(f"Debug progress for {name}: {progress}") # 用于调试进度字典的结构
                with _pull_lock:
                    # 更新状态为 downloading
                    if _pull_states[name]["status"] != "downloading":
                        _pull_states[name]["status"] = "downloading"
                        _pull_states[name]["message"] = progress.get(
                            "status", "Starting download..."
                        )  # Use first status message

                    # 查找进度信息
                    if (
                        "total" in progress
                        and "completed" in progress
                        and progress["total"] > 0
                    ):
                        current_progress = round(
                            (progress["completed"] / progress["total"]) * 100, 2
                        )
                        _pull_states[name]["progress"] = current_progress
                        _pull_states[name]["message"] = (
                            f"Downloading layer: {progress.get('status', '')}"  # More specific message
                        )
                    elif (
                        "status" in progress
                        and progress["status"] == "verifying sha256 digest"
                    ):
                        _pull_states[name]["message"] = "Verifying download..."
                    elif (
                        "status" in progress
                        and progress["status"] == "writing manifest"
                    ):
                        _pull_states[name]["message"] = "Writing manifest..."
                    elif (
                        "status" in progress
                        and progress["status"] == "removing any unused layers"
                    ):
                        _pull_states[name]["message"] = "Cleaning up..."

            # 拉取成功完成
            with _pull_lock:
                _pull_states[name]["status"] = "completed"
                _pull_states[name]["progress"] = 100.0
                _pull_states[name]["message"] = "Model pull completed successfully."

        except Exception as e:
            # 拉取过程中发生错误
            with _pull_lock:
                # 保留最后已知的进度
                _pull_states[name]["progress"] = current_progress
                _pull_states[name]["status"] = "failed"
                # 尝试获取更具体的 Ollama API 错误信息
                error_message = str(e)
                if hasattr(e, "response") and hasattr(e.response, "text"):  # type: ignore
                    try:
                        import json

                        error_data = json.loads(e.response.text)  # type: ignore
                        if "error" in error_data:
                            error_message = f"Ollama API Error: {error_data['error']}"
                    except Exception:
                        pass  # Keep original exception string if parsing fails
                _pull_states[name]["message"] = error_message

        finally:
            # 线程结束，可以选择是否移除线程对象引用
            with _pull_lock:
                if name in _pull_states:
                    # 标记线程已结束，但保留状态信息
                    _pull_states[name]["thread"] = None
                    # print(f"Debug: Thread for {name} finished.")

    # --- 公开的 API 函数 ---
    def pull_model(self, name: str) -> None:
        """
        启动一个后台线程来拉取指定的 Ollama 模型。

        Args:
            name (str): 要拉取的模型的名称 (例如 'llama3' 或 'mistral:7b')。
        """
        global _pull_states
        with _pull_lock:
            # 检查是否已有正在进行的拉取任务
            if (
                name in _pull_states
                and _pull_states[name].get("thread")
                and _pull_states[name]["thread"].is_alive()
            ):
                print(f"Pull request for model '{name}' is already in progress.")
                return

            # 检查模型是否已经存在（避免不必要的启动）
            # 注意：这只是一个初步检查，ollama.pull 本身会处理重复拉取
            try:
                local_models = [m["name"] for m in self.client.list().get("models", [])]
                # ollama list 返回 <model>:<tag> 格式
                if name in local_models or (
                    ":" not in name and f"{name}:latest" in local_models
                ):
                    print(
                        f"Model '{name}' already exists locally. Setting status to completed."
                    )
                    _pull_states[name] = {
                        "status": "completed",
                        "progress": 100.0,
                        "message": "Model already exists locally.",
                        "thread": None,
                    }
                    return
            except Exception as e:
                print(f"Warning: Could not check local models list: {e}")
                # 即使检查失败，也继续尝试pull

            # 初始化状态
            print(f"Initiating pull for model '{name}'...")
            _pull_states[name] = {
                "status": "starting",
                "progress": 0.0,
                "message": "Initializing pull request...",
                "thread": None,  # 稍后填充
            }

            # 创建并启动后台线程
            thread = threading.Thread(
                target=self._run_pull, args=(name,), daemon=True
            )  # daemon=True 允许主程序退出时线程也退出
            _pull_states[name]["thread"] = thread
            thread.start()

    def pull_status(self, name: str) -> Dict[str, Any]:
        """
        获取指定模型当前的拉取状态和进度。

        Args:
            name (str): 要查询状态的模型的名称。

        Returns:
            Dict[str, Any]: 包含状态信息的字典，格式为:
                {
                    "status": "string", // downloading/completed/failed/starting/unknown
                    "progress": "number", // 0-100
                    "message": "string" // 状态或错误信息
                }
        """
        global _pull_states
        with _pull_lock:
            if name in _pull_states:
                # 返回状态字典的副本，不包含线程对象
                state_copy = _pull_states[name].copy()
                state_copy.pop("thread", None)  # 移除内部使用的线程对象
                return state_copy
            else:
                # 如果从未调用 pull_model 或状态已被清理，检查模型是否已存在
                try:
                    local_models = [
                        m["name"] for m in self.client.list().get("models", [])
                    ]
                    if name in local_models or (
                        ":" not in name and f"{name}:latest" in local_models
                    ):
                        return {
                            "status": "completed",
                            "progress": 100.0,
                            "message": "Model found locally (pull not tracked by this session).",
                        }
                except Exception as e:
                    print(
                        f"Warning: Could not check local models list during status check: {e}"
                    )

                # 如果既不在跟踪状态中，也不在本地，则返回未知
                return {
                    "status": "unknown",
                    "progress": 0.0,
                    "message": "Pull status not tracked or model not found.",
                }

    async def async_generate(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        """异步生成回复

        Args:
            model: 模型名称
            messages: 消息列表，格式为 [{"role": "user", "content": "hello"}, ...]
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数，None表示不限制

        Returns:
            str: 生成的回复内容
        """
        try:
            # 将同步的 chat 调用包装在一个异步操作中
            response = await asyncio.to_thread(
                self.client.chat,
                model=model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens if max_tokens else -1,
                },
            )
            return response["message"]["content"]
        except Exception as e:
            raise Exception(f"Ollama generation failed: {str(e)}")


ollama_client = OllamaClient()
