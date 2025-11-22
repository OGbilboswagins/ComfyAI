"""
ComfyAI Provider Manager

Loads and manages model providers (OpenAI, LM Studio, Ollama, etc.).
"""

from __future__ import annotations

from typing import Dict, Optional, Any

from .utils.logger import log
from ..config.loader import load_config
from ..config.provider_config import ProviderConfig
from .agent_factory import ChatClient


class ProviderManager:
    """Singleton manager for all LLM providers."""

    _instance: Optional["ProviderManager"] = None

    # ============================================================
    # Singleton
    # ============================================================
    @classmethod
    def instance(cls) -> "ProviderManager":
        if cls._instance is None:
            cls._instance = ProviderManager()
        return cls._instance

    # ============================================================
    # Constructor
    # ============================================================
    def __init__(self):
        self.config = load_config()
        self.providers: Dict[str, ProviderConfig] = {}
        self.default_provider: Optional[str] = None

        self._load_providers()

    # ============================================================
    # Provider Loading
    # ============================================================
    def _load_providers(self) -> None:
        """Load all providers defined in config."""
        for name, cfg in self.config.providers.items():
            self.providers[name] = cfg
            if getattr(cfg, "default", False):
                self.default_provider = name

        log.info(f"[ComfyAI] Loaded providers: {list(self.providers.keys())}")
        log.info(f"[ComfyAI] Default provider: {self.default_provider}")

    # ============================================================
    # Accessors
    # ============================================================
    def get_default_llm(self) -> Optional[ChatClient]:
        """Return a ChatClient for the configured default provider."""
        if self.default_provider is None:
            log.error("[ComfyAI] No default provider configured")
            return None

        provider_cfg = self.providers.get(self.default_provider)
        if provider_cfg is None:
            log.error(f"[ComfyAI] Provider {self.default_provider} not found")
            return None

        return ChatClient.from_provider_config(provider_cfg)

    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        return self.providers.get(name)


# Convenience function used elsewhere
def get_provider_manager() -> ProviderManager:
    return ProviderManager.instance()
