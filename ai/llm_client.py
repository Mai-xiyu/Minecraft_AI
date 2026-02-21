"""
通用 LLM 客户端 —— 兼容所有 OpenAI 格式 API
支持 DeepSeek、Ollama (http://localhost:11434/v1)、OpenAI 等
"""

import json
import time
import logging
import requests

logger = logging.getLogger(__name__)


class LLMClient:
    """
    通用聊天补全客户端。
    只需提供 base_url 和 model 即可接入任何 OpenAI 兼容服务。
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 60,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        # 使用连接池
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            max_retries=2, pool_connections=2, pool_maxsize=5
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 统计
        self.total_calls = 0
        self.total_tokens = 0

    # ── 核心方法 ──────────────────────────────────────────

    def chat(self, messages: list[dict]) -> str:
        """
        发送聊天补全请求。

        参数:
            messages: [{"role": "system"|"user"|"assistant", "content": "..."}]

        返回:
            助手回复文本 (str)
        """
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        for attempt in range(3):
            try:
                logger.debug(
                    "LLM 请求 [%s] attempt=%d messages=%d",
                    self.model, attempt + 1, len(messages),
                )
                resp = self.session.post(
                    url, headers=headers, json=payload, timeout=self.timeout
                )

                if resp.status_code == 429:
                    wait = min(2 ** attempt * 2, 10)
                    logger.warning("速率限制, 等待 %ds", wait)
                    time.sleep(wait)
                    continue

                if resp.status_code >= 500:
                    wait = 2 ** attempt
                    logger.warning("服务器错误 %d, 等待 %ds", resp.status_code, wait)
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                data = resp.json()

                # 统计 token
                usage = data.get("usage", {})
                self.total_tokens += usage.get("total_tokens", 0)
                self.total_calls += 1

                content = data["choices"][0]["message"]["content"]
                logger.debug("LLM 回复 (%d chars)", len(content))
                return content.strip()

            except requests.exceptions.Timeout:
                logger.warning("请求超时 (attempt %d)", attempt + 1)
                if attempt == 2:
                    raise TimeoutError("LLM 请求超时 (已重试 3 次)")
            except requests.exceptions.ConnectionError as e:
                logger.error("连接失败: %s", e)
                if attempt == 2:
                    raise
            except (KeyError, IndexError) as e:
                resp_text = resp.text[:200] if resp is not None else "(no response)"
                logger.error("解析响应失败: %s | body=%s", e, resp_text)
                raise ValueError(f"LLM 响应格式错误: {e}")
            except Exception as e:
                logger.error("LLM 调用异常: %s", e)
                if attempt == 2:
                    raise

        raise RuntimeError("LLM 调用失败 (已重试 3 次)")

    # ── 便捷方法 ──────────────────────────────────────────

    def quick_chat(self, system_prompt: str, user_message: str) -> str:
        """快捷调用: 单轮对话"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        return self.chat(messages)

    def get_stats(self) -> dict:
        """返回使用统计"""
        return {
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens,
            "model": self.model,
            "base_url": self.base_url,
        }

    def test_connection(self) -> bool:
        """测试 API 连通性"""
        try:
            result = self.chat([
                {"role": "user", "content": "Say OK"},
            ])
            return bool(result)
        except Exception as e:
            logger.error("连接测试失败: %s", e)
            return False
