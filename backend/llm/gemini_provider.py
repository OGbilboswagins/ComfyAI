import os
from typing import Any, Dict, List

import aiohttp
from aiohttp import ClientTimeout
from .base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    name = "gemini"

    @property
    def api_base(self) -> str:
        # e.g. https://generativelanguage.googleapis.com/v1beta
        return self.cfg.get("api_base", "https://generativelanguage.googleapis.com/v1beta")

    @property
    def api_key(self) -> str | None:
        env_name = self.cfg.get("api_key_env", "GEMINI_API_KEY")
        return os.environ.get(env_name)

    async def list_models(self) -> List[Dict[str, Any]]:
        # Placeholder: you can later call /models properly
        return [
            {
                "id": "gemini-1.5-flash",
                "tasks": ["chat", "plan", "edit"],
                "provider": self.name,
            },
            {
                "id": "gemini-1.5-pro",
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
        Very minimal text-only chat wrapper.
        """
        api_key = self.api_key
        if not api_key:
            return {
                "role": "assistant",
                "content": "[Gemini API key not configured]",
                "raw": None,
                "error": True,
            }

        # e.g. POST /models/{model}:generateContent?key=API_KEY
        url = f"{self.api_base}/models/{model}:generateContent?key={api_key}"

        messages = payload.get("messages") or []
        # Flatten to simple text for now
        parts = []
        for m in messages:
            if m.get("role") == "user":
                parts.append({"text": m.get("content", "")})

        body: Dict[str, Any] = {
            "contents": [{"role": "user", "parts": parts}],
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=body, timeout=ClientTimeout(total=60)) as resp:
                    data = await resp.json()
        except Exception as e:
            print(f"[ComfyAI] Gemini execute error: {e}")
            return {
                "role": "assistant",
                "content": f"[Gemini error: {e}]",
                "raw": None,
                "error": True,
            }

        # Extremely simplified extraction
        candidates = data.get("candidates") or []
        content = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                content = parts[0].get("text", "")

        return {
            "role": "assistant",
            "content": content,
            "raw": data,
            "error": False,
        }
