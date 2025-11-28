import os
from typing import Any, Dict, List

import aiohttp
from aiohttp import ClientTimeout
from .base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    name = "openai"

    @property
    def api_base(self) -> str:
        return self.cfg.get("api_base", "https://api.openai.com/v1")

    @property
    def api_key(self) -> str | None:
        env_name = self.cfg.get("api_key_env", "OPENAI_API_KEY")
        return os.environ.get(env_name)

    async def list_models(self) -> List[Dict[str, Any]]:
        # Minimal; you can cache or hardcode for now
        # To keep it simple and avoid rate limits, we just return a static set.
        return [
            {
                "id": "gpt-4o-mini",
                "tasks": ["chat", "plan", "edit"],
                "provider": self.name,
            },
            {
                "id": "gpt-4o",
                "tasks": ["chat", "plan", "edit"],
                "provider": self.name,
            },
        ]

    async def execute(
        self,
        task: str,
        model: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Basic chat.completions wrapper. Task is mostly semantic here
        (you control behavior in system prompts later).
        """
        api_key = self.api_key
        if not api_key:
            return {
                "role": "assistant",
                "content": "[OpenAI API key not configured]",
                "raw": None,
                "error": True,
            }

        url = f"{self.api_base}/chat/completions"
        messages = payload.get("messages") or []

        body: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=body,
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=ClientTimeout(total=60),
                ) as resp:
                    data = await resp.json()
        except Exception as e:
            print(f"[ComfyAI] OpenAI execute error: {e}")
            return {
                "role": "assistant",
                "content": f"[OpenAI error: {e}]",
                "raw": None,
                "error": True,
            }

        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message", {})
        return {
            "role": msg.get("role", "assistant"),
            "content": msg.get("content", ""),
            "raw": data,
            "error": False,
        }
