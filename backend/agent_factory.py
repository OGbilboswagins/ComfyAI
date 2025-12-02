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
    base = cfg.base_url or ""
    return "googleapis.com" in base or cfg.type == "cloud"


# ============================================================
# ChatClient implementation
# ============================================================

@dataclass
class ChatClient:
    provider_name: str
    base_url: str
    api_key: Optional[str]
    model: str
    provider_type: str  # "local", "cloud", "ollama", etc.

    # --------------------------------------------------------
    # Helper detection
    # --------------------------------------------------------
    def _is_gemini(self) -> bool:
        base = self.base_url or ""
        return ("googleapis.com" in base) or (self.provider_name.lower() == "google")

    def _is_ollama(self) -> bool:
        # Name-based OR URL-based detection
        return (
            self.provider_name.lower() == "ollama"
            or "11434" in self.base_url
        )

    # --------------------------------------------------------
    # Public entrypoint
    # --------------------------------------------------------
    async def chat(self, messages: Sequence[ChatMessage]) -> str:
        """
        Send a chat request and return text.
        """
        if self._is_gemini():
            return await self._chat_gemini(messages)

        if self._is_ollama():
            return await self._chat_ollama(messages)

        # Default OpenAI-compatible path
        return await self._chat_openai(messages)

    # --------------------------------------------------------
    # Streaming entrypoint
    # --------------------------------------------------------
    async def stream_chat(self, messages: Sequence[ChatMessage]):
        """
        Async generator yielding chunks of text as they arrive.
        """
        if self._is_gemini():
            # For now, Gemini doesn't stream → yield once
            text = await self._chat_gemini(messages)
            yield text
            return

        if self._is_ollama():
            async for chunk in self._stream_ollama(messages):
                yield chunk
            return

        # Default: OpenAI-compatible streaming
        async for chunk in self._stream_openai(messages):
            yield chunk

    # --------------------------------------------------------
    # OLLAMA CHAT API (correct)
    # --------------------------------------------------------
    async def _chat_ollama(self, messages: Sequence[ChatMessage]) -> str:
        """
        Use Ollama's native /api/chat endpoint.
        """
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": [
                {"role": m.get("role", "user"), "content": m.get("content", "")}
                for m in messages
            ],
            "stream": False
        }

        log.info(f"[ComfyAI] Ollama request → {url}")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                raw = await resp.text()
                if resp.status != 200:
                    return f"[Ollama ERROR] HTTP {resp.status}: {raw}"

                data = json.loads(raw)

        try:
            return data["message"]["content"]
        except Exception:
            return "[Ollama ERROR] malformed response"

    async def _stream_ollama(self, messages: Sequence[ChatMessage]):
        """
        Native Ollama streaming via /api/chat with stream=true.
        Yields text chunks.
        """
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": [
                {"role": m.get("role", "user"), "content": m.get("content", "")}
                for m in messages
            ],
            "stream": True,
        }

        log.info(f"[ComfyAI] Ollama STREAM request → {url}")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                async for line_bytes in resp.content:
                    line = line_bytes.decode("utf-8").strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except Exception:
                        continue

                    msg = data.get("message", {})
                    content = msg.get("content")
                    if content:
                        yield content

                    if data.get("done"):
                        break

    # --------------------------------------------------------
    # GOOGLE GEMINI 2.x CHAT (supports text + streaming)
    # --------------------------------------------------------
    async def _chat_gemini(self, messages: Sequence[ChatMessage]) -> str:
        """
        Gemini requires a special payload structure.
        For now, return full response as text (non-streaming).
        Streaming is handled separately in stream endpoint.
        """

        # Convert model name (must be `models/...`)
        model_id = self.model
        if not model_id.startswith("models/"):
            model_id = f"models/{model_id}"

        url = f"{self.base_url}/{model_id}:generateContent?key={self.api_key}"

        # Convert messages → Gemini format
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            text = msg.get("content", "")

            if not text:
                continue

            contents.append({
                "role": role,
                "parts": [{"text": text}]
            })

        payload = {"contents": contents}

        log.info(f"[ComfyAI] Gemini request → {url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    raw = await resp.text()

                    if resp.status != 200:
                        return f"[Gemini ERROR] HTTP {resp.status}: {raw}"

                    data = json.loads(raw)

        except Exception as e:
            log.error(f"[ComfyAI] Gemini exception: {e}")
            return f"[Gemini ERROR] {e}"

        # Extract text
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return "[Gemini ERROR] malformed response"

    # --------------------------------------------------------
    # OPENAI/OPENROUTER/LMSTUDIO CHAT
    # --------------------------------------------------------
    async def _chat_openai(self, messages: Sequence[ChatMessage]) -> str:
        client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

        log.info(f"[ComfyAI] OpenAI-compatible request → model={self.model}")

        msgs = cast(List[ChatCompletionMessageParam], messages)

        resp = await client.chat.completions.create(
            model=self.model,
            messages=msgs,
            temperature=0.7,
            top_p=1,
        )

        return resp.choices[0].message.content or ""

    async def _stream_openai(self, messages: Sequence[ChatMessage]):
        """
        OpenAI / OpenRouter / LM Studio streaming using async-openai.
        """
        client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

        log.info(f"[ComfyAI] OpenAI-compatible STREAM request → model={self.model}")

        msgs = cast(List[ChatCompletionMessageParam], messages)

        stream = await client.chat.completions.create(
            model=self.model,
            messages=msgs,
            temperature=0.7,
            top_p=1,
            stream=True,
        )

        async for event in stream:
            try:
                delta = event.choices[0].delta
                content = delta.content
                if content:
                    yield content
            except Exception:
                continue
            
    # --------------------------------------------------------
    # Factory constructor
    # --------------------------------------------------------
    @classmethod
    def from_provider_config(cls, cfg: ProviderConfig) -> "ChatClient":
        return cls(
            provider_name=cfg.name,
            base_url=cfg.base_url or "",
            api_key=cfg.api_key,
            model=cfg.model or "",
            provider_type=cfg.type or "",
        )
