from typing import Any, Dict, List

import aiohttp
from aiohttp import ClientTimeout
from .base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    name = "ollama"

    @property
    def api_base(self) -> str:
        return self.cfg.get("api_base", "http://localhost:11434")

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        Very simple probing of /api/tags.
        You can expand this later with richer metadata.
        """
        url = f"{self.api_base}/api/tags"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=ClientTimeout(total=5)) as resp:
                    data = await resp.json()
        except Exception as e:
            print(f"[ComfyAI] Ollama list_models error: {e}")
            return []

        models = []
        for item in data.get("models", []):
            models.append(
                {
                    "id": item.get("name"),
                    "tasks": ["chat", "plan", "edit"],
                    "provider": self.name,
                }
            )
        return models

    async def execute(
        self,
        task: str,
        model: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Minimal /api/chat wrapper. You can specialize by task later.
        """
        messages = payload.get("messages") or []
        url = f"{self.api_base}/v1/chat/completions"

        body: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=body, timeout=ClientTimeout(total=60)) as resp:
                    data = await resp.json()
        except Exception as e:
            print(f"[ComfyAI] Ollama execute error: {e}")
            return {
                "role": "assistant",
                "content": f"[Ollama error: {e}]",
                "raw": None,
                "error": True,
            }

        # Normalize like OpenAI's chat response
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message", {})
        return {
            "role": msg.get("role", "assistant"),
            "content": msg.get("content", ""),
            "raw": data,
            "error": False,
        }
