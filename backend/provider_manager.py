import json
import os
from typing import Dict, Any, Optional

from ..config.loader import load_config
from ..utils.logger import log


class ProviderError(Exception):
    """Raised when provider resolution fails."""
    pass


class ProviderManager:
    """
    Responsible for:
    - Loading provider configs
    - Resolving provider for a given task (chat, rewrite, debug, edit, apply)
    - Constructing OpenAI-compatible clients
    """

    def __init__(self):
        self.config = load_config()
        self.providers = self._load_providers()
        self.task_map = self._load_task_map()

    # ------------------------------------------------------------
    # CONFIG LOADING
    # ------------------------------------------------------------

    def _load_providers(self) -> Dict[str, Any]:
        """
        Load providers from config:
        - defaults.json (bundled)
        - providers.local.json (optional)
        """
        providers = self.config.get("providers", {})

        log.info(f"[ProviderManager] Loaded {len(providers)} providers.")
        return providers

    def _load_task_map(self) -> Dict[str, str]:
        """
        Map task → provider key as defined in defaults.json
        Example:
            "chat": "local-chat"
            "rewrite": "cloud-heavy"
            "debug": "cloud-heavy"
        """
        tasks = self.config.get("tasks", {})
        log.info(f"[ProviderManager] Task map loaded: {tasks}")
        return tasks

    # ------------------------------------------------------------
    # PROVIDER RESOLUTION
    # ------------------------------------------------------------

    def get_provider_key(self, task: str) -> str:
        """
        Returns provider key for a given task.
        """
        if task not in self.task_map:
            raise ProviderError(f"No provider defined for task: {task}")

        return self.task_map[task]

    def get_provider(self, task: str) -> Dict[str, Any]:
        """
        Returns provider config (url, api_key, model, etc.)
        """
        key = self.get_provider_key(task)

        if key not in self.providers:
            raise ProviderError(f"Provider '{key}' not found in providers.json")

        provider = self.providers[key]

        # Validate basic structure
        if "type" not in provider:
            raise ProviderError(f"Provider '{key}' missing required field: 'type'")

        if "model" not in provider:
            raise ProviderError(f"Provider '{key}' missing required field: 'model'")

        return provider

    # ------------------------------------------------------------
    # OPENAI-COMPATIBLE CLIENT GENERATOR
    # ------------------------------------------------------------

    def create_client(self, task: str):
        """
        Creates an OpenAI-compatible client for the provider.
        Supports:
        - local providers (ollama)
        - cloud providers (openai, gemini, anthropic)
        """
        provider = self.get_provider(task)
        provider_type = provider["type"]

        base_url = provider.get("base_url")
        api_key = provider.get("api_key", "EMPTY")

        # Lazy import to avoid unnecessary dependencies
        from openai import OpenAI

        if provider_type == "local":
            # Ollama-style OpenAI-compatible server
            if not base_url:
                raise ProviderError("Local provider missing 'base_url'")

            return OpenAI(api_key=api_key, base_url=base_url)

        elif provider_type == "cloud":
            if not api_key:
                raise ProviderError("Cloud provider missing API key")

            if not base_url:
                raise ProviderError("Cloud provider missing base_url")

            return OpenAI(api_key=api_key, base_url=base_url)

        else:
            raise ProviderError(f"Unknown provider type: {provider_type}")


# ------------------------------------------------------------
# GLOBAL INSTANCE
# ------------------------------------------------------------

provider_manager = ProviderManager()