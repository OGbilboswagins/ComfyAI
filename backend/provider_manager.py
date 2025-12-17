"""
ComfyAI Provider Manager

Loads providers from config and exposes ChatClient instances.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from .utils.logger import log
from ..config.loader import load_config
from .agent_factory import ChatClient
from ..config.provider_config import ProviderConfig
from .utils.paths import PROVIDERS_PATH


# ============================================================
# Default providers.json bootstrap
# ============================================================

DEFAULT_PROVIDERS_JSON = {
    "version": 1,
    "providers": {
        "ollama": {
            "type": "local",
            "base_url": "http://localhost:11434",
            "models": [],
            "default_model": None
        }
    }
}


def ensure_providers_file() -> None:
    """
    Ensure providers.json exists.
    If missing, create a minimal default config.
    """
    if PROVIDERS_PATH.exists():
        return

    PROVIDERS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with PROVIDERS_PATH.open("w", encoding="utf-8") as f:
        json.dump(DEFAULT_PROVIDERS_JSON, f, indent=2)

    log.info(f"[ComfyAI] Created default providers.json at {PROVIDERS_PATH}")


# ============================================================
# Provider Manager
# ============================================================

class ProviderManager:
    """Singleton manager for all LLM providers."""

    _instance: Optional["ProviderManager"] = None

    # ========================================================
    # Singleton
    # ========================================================
    @classmethod
    def instance(cls) -> "ProviderManager":
        if cls._instance is None:
            cls._instance = ProviderManager()
        return cls._instance

    # ========================================================
    # Constructor
    # ========================================================
    def __init__(self):
        # 🔑 MUST happen before load_config()
        ensure_providers_file()

        self.config = load_config()
        self.providers: Dict[str, ChatClient] = {}
        self.default_provider: Optional[str] = None

        self._load_providers()

    # ========================================================
    # Provider Loading
    # ========================================================
    def _load_providers(self):
        """Load ProviderConfig objects and build ChatClient instances."""
        providers_cfg = getattr(self.config, "providers", {})

        for name, cfg in providers_cfg.items():
            if not isinstance(cfg, ProviderConfig):
                log.error(f"[ComfyAI] Invalid provider config for {name}, skipping.")
                continue

            model_name = (
                cfg.default_model
                or (cfg.models[0].name if cfg.models else None)
                or ""
            )

            client = ChatClient(
                provider_name=name,
                provider_type=cfg.type,
                base_url=cfg.base_url or "",
                api_key=cfg.api_key or "",
                model=model_name or "",
            )

            self.providers[name] = client

            # Default provider: first valid provider
            if self.default_provider is None:
                self.default_provider = name

        if not self.default_provider and self.providers:
            self.default_provider = next(iter(self.providers.keys()))

        log.info(f"[ComfyAI] Loaded providers: {list(self.providers.keys())}")
        log.info(f"[ComfyAI] Default provider: {self.default_provider}")

    # ========================================================
    # Reload
    # ========================================================
    def reload(self):
        """Reload providers.json and rebuild clients."""
        log.info("[ComfyAI] Reloading provider config…")

        self.config = load_config()
        self.providers = {}
        self.default_provider = None

        self._load_providers()

        log.info(f"[ComfyAI] Reload complete → {list(self.providers.keys())}")

    # ========================================================
    # Accessors
    # ========================================================
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

        return self.get_default_llm()

    # Alias for MCP compatibility
    def get_best_provider(self, task: str) -> Optional[ChatClient]:
        return self.pick_provider(task)


# ============================================================
# Convenience
# ============================================================

def get_provider_manager() -> ProviderManager:
    return ProviderManager.instance()


__all__ = ["ProviderManager", "get_provider_manager"]
