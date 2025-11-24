"""
ComfyAI Provider Manager

Loads providers from config and exposes ChatClient instances.
"""

from __future__ import annotations
from typing import Dict, Optional, Any

from .utils.logger import log
from ..config.loader import load_config
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
        self.providers: Dict[str, ChatClient] = {}
        self.default_provider: Optional[str] = None

        self._load_providers()

    # ============================================================
    # Provider Loading
    # ============================================================
    def _load_providers(self):
        """Load all providers defined in config and build ChatClient instances."""
        providers_cfg: Dict[str, Any] = getattr(self.config, "providers", {})

        for name, raw_cfg in providers_cfg.items():
            # raw_cfg may be a plain dict or a ProviderConfig-like object
            if isinstance(raw_cfg, dict):
                p_type = raw_cfg.get("type", "local")
                base_url = raw_cfg.get("base_url", "")
                model = raw_cfg.get("model", "")
                api_key = raw_cfg.get("api_key", "")
                label = raw_cfg.get("label", name)
                is_default = bool(raw_cfg.get("default", False))
            else:
                # Dataclass-like ProviderConfig
                p_type = getattr(raw_cfg, "type", "local")
                base_url = getattr(raw_cfg, "base_url", "")
                model = getattr(raw_cfg, "model", "")
                api_key = getattr(raw_cfg, "api_key", "")
                label = getattr(raw_cfg, "label", name)
                is_default = bool(getattr(raw_cfg, "default", False))

            client = ChatClient(
                provider_name=name,
                provider_type=p_type,
                base_url=base_url,
                api_key=api_key,
                model=model,
            )

            self.providers[name] = client

            if is_default and self.default_provider is None:
                self.default_provider = name

        # Fallback default if none explicitly marked
        if self.default_provider is None and self.providers:
            self.default_provider = next(iter(self.providers.keys()))

        log.info(f"[ComfyAI] Loaded providers: {list(self.providers.keys())}")
        log.info(f"[ComfyAI] Default provider: {self.default_provider}")

    # ============================================================
    # Accessors
    # ============================================================
    def get_default_llm(self) -> Optional[ChatClient]:
        """Return ChatClient for the default provider."""
        if not self.default_provider:
            log.error("[ComfyAI] No default provider configured")
            return None
        return self.providers.get(self.default_provider)

    def get_provider(self, name: str) -> Optional[ChatClient]:
        """Return ChatClient for a named provider."""
        return self.providers.get(name)

    def pick_provider(self, task: str) -> Optional[ChatClient]:
        """
        Simple routing based on task name.

        For now:
          • "rewrite" prefers cloud_workflow, then local_apply, then default.
        """
        if task == "rewrite":
            for key in ("cloud_workflow", "local_apply", self.default_provider):
                if key and key in self.providers:
                    return self.providers[key]

        # Fallback to default
        return self.get_default_llm()

    # Alias for mcp_client compatibility
    def get_best_provider(self, task: str) -> Optional[ChatClient]:
        return self.pick_provider(task)


# Convenience function used by router/setup
def get_provider_manager() -> ProviderManager:
    return ProviderManager.instance()


__all__ = ["ProviderManager", "get_provider_manager"]
