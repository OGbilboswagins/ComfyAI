"""
ComfyAI - Agent / Client Factory

Defines:
  • ChatMessage (TypedDict for LLM messages)
  • ChatClient  (simple async chat wrapper for a single provider)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict, List, Optional, cast, Union

from openai import AsyncOpenAI  # uses OpenAI-compatible APIs (OpenAI / Ollama / local proxy)
from openai.types.chat import ChatCompletionMessageParam
from ..config.provider_config import ProviderConfig
from .utils.logger import log


class ChatMessage(TypedDict, total=False):
    role: Literal["system", "user", "assistant", "developer"]
    content: Union[str, List[dict]]
    name: Optional[str]


@dataclass
class ChatClient:
    """
    Thin wrapper over an OpenAI-compatible chat endpoint.
    """
    provider_name: str
    base_url: str
    api_key: Optional[str]
    model: str

    async def chat(self, messages: List[ChatMessage]) -> str:
        """
        Send a chat completion request and return the assistant text.
        """
        log.info(f"[ComfyAI] ChatClient[{self.provider_name}] calling model={self.model}")

        client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

        resp = await client.chat.completions.create(
            model=self.model,
            messages=cast(List[ChatCompletionMessageParam], messages),
            temperature=0.7,
            top_p=1,
        )

        msg = resp.choices[0].message
        return msg.content or ""

    # --------------------------------------------------------
    # Factory
    # --------------------------------------------------------
    @classmethod
    def from_provider_config(cls, cfg: ProviderConfig) -> "ChatClient":
        """
        Build a ChatClient from a ProviderConfig.
        """
        return cls(
            provider_name=cfg.name,
            base_url=cfg.base_url,
            api_key=cfg.api_key,
            model=cfg.model,
        )
