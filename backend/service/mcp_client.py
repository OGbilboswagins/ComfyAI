"""
ComfyAI - MCP Client
Provides a thin interface used by the MCP subsystem.
"""

from __future__ import annotations

from typing import List
from ..utils.logger import log
from ..provider_manager import get_provider_manager
from ..agent_factory import ChatMessage, ChatClient


async def mcp_chat(messages: List[ChatMessage]) -> str:
    """
    Core wrapper for MCP chat operations.

    Uses the default provider defined in ProviderManager.
    """
    provider = get_provider_manager().get_default_llm()

    if provider is None:
        raise RuntimeError("No default provider configured for MCP")

    # provider is ChatClient, so adapt API
    log.info(f"[MCP-Client] Using provider: {provider.provider_name}")

    # ChatClient.chat() returns a string
    reply = await provider.chat(messages)

    return reply


__all__ = ["mcp_chat"]
