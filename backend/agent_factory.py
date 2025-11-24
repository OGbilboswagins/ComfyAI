"""
ComfyAI - Agent / Client Factory

Unified chat client supporting:
  • OpenAI-compatible APIs (OpenAI / Ollama / LM Studio / proxies)
  • Google Gemini v1beta API
"""

from __future__ import annotations

import aiohttp
import json
from dataclasses import dataclass
from typing import (
    Literal, TypedDict, Sequence, Dict, Any, List, Optional, Union, cast
)

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from ..config.provider_config import ProviderConfig
from .utils.logger import log


# ============================================================
# Typed message format used internally everywhere
# ============================================================

class ChatMessage(TypedDict, total=False):
    role: Literal["system", "user", "assistant"]
    content: str
    name: Optional[str]


# ============================================================
# Utility: detect if provider is Gemini
# ============================================================

def is_gemini_provider(cfg: ProviderConfig) -> bool:
    return "googleapis.com" in cfg.base_url or cfg.type == "cloud"


# ============================================================
# ChatClient implementation
# ============================================================

@dataclass
class ChatClient:
    provider_name: str
    base_url: str
    api_key: Optional[str]
    model: str
    provider_type: str  # "local" or "cloud"

    # --------------------------------------------------------
    # Public entrypoint
    # --------------------------------------------------------
    async def chat(self, messages: Sequence[ChatMessage]) -> str:
        """
        Send a chat request and return the assistant's text reply.
        """
        if self._is_gemini():
            return await self._chat_gemini(messages)
        else:
            return await self._chat_openai(messages)

    # --------------------------------------------------------
    # Provider type detection
    # --------------------------------------------------------
    def _is_gemini(self) -> bool:
        return "googleapis.com" in self.base_url or self.provider_type == "cloud"

    # --------------------------------------------------------
    # Google Gemini v1beta endpoint
    # --------------------------------------------------------
    async def _chat_gemini(self, messages: Sequence[ChatMessage]) -> str:
        """
        Handles Gemini "generateContent" format.
        """
        # Ensure correct model form "models/xxx"
        model_id = self.model
        if not model_id.startswith("models/"):
            model_id = f"models/{model_id}"

        url = f"{self.base_url}/{model_id}:generateContent?key={self.api_key}"

        # Convert messages into Gemini content blocks
        gemini_msgs: List[Dict[str, Any]] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

        # Skip degenerate messages with no content at all
            if not content:
                continue

            gemini_msgs.append({
                "role": role,
                "parts": [{"text": content}],
            })

        payload = {"contents": gemini_msgs}

        log.info(f"[ComfyAI] Gemini request → {url}")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                raw = await resp.text()

                if resp.status != 200:
                    return f"[Gemini ERROR] HTTP {resp.status}: {raw}"

                data = json.loads(raw)

        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return "[Gemini ERROR] malformed response"

        return text

    # --------------------------------------------------------
    # OpenAI-compatible endpoint (OpenAI / Ollama / LM Studio)
    # --------------------------------------------------------
    async def _chat_openai(self, messages: Sequence[ChatMessage]) -> str:
        """
        Handles all OpenAI-compatible APIs, including Ollama.
        """
        client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

        log.info(f"[ComfyAI] OpenAI-compatible request → model={self.model}")

        # Cast messages to OpenAI chat format
        msgs = cast(List[ChatCompletionMessageParam], messages)

        resp = await client.chat.completions.create(
            model=self.model,
            messages=msgs,
            temperature=0.7,
            top_p=1,
        )

        return resp.choices[0].message.content or ""

    # --------------------------------------------------------
    # Factory constructor
    # --------------------------------------------------------
    @classmethod
    def from_provider_config(cls, cfg: ProviderConfig) -> "ChatClient":
        return cls(
            provider_name=cfg.name,
            base_url=cfg.base_url,
            api_key=cfg.api_key,
            model=cfg.model,
            provider_type=cfg.type,
        )
