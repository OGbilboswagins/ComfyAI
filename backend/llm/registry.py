from typing import Any, Dict, List

from ..utils.settings import load_settings
from .base import BaseLLMProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider


class LLMRegistry:
    """
    Central registry for all LLM providers configured in settings.json.
    """

    def __init__(self) -> None:
        self.settings: Dict[str, Any] = load_settings()
        self.providers: Dict[str, BaseLLMProvider] = {}
        self._init_providers()

    def _init_providers(self) -> None:
        cfg_providers: Dict[str, Any] = self.settings.get("providers", {})

        # Ollama
        ollama_cfg = cfg_providers.get("ollama", {})
        if ollama_cfg.get("enabled", True):
            self.providers["ollama"] = OllamaProvider(ollama_cfg)

        # OpenAI
        openai_cfg = cfg_providers.get("openai", {})
        if openai_cfg.get("enabled", False):
            self.providers["openai"] = OpenAIProvider(openai_cfg)

        # Gemini
        gem_cfg = cfg_providers.get("gemini", {})
        if gem_cfg.get("enabled", False):
            self.providers["gemini"] = GeminiProvider(gem_cfg)

        print(f"[ComfyAI] LLMRegistry loaded providers: {list(self.providers.keys())}")

    def reload_settings(self) -> None:
        self.settings = load_settings()
        self.providers.clear()
        self._init_providers()

    async def list_providers(self) -> Dict[str, Any]:
        """
        Returns a dict keyed by provider name with models + capabilities.
        """
        result: Dict[str, Any] = {}
        for name, provider in self.providers.items():
            try:
                models = await provider.list_models()
            except Exception as e:
                print(f"[ComfyAI] list_models error for {name}: {e}")
                models = []

            result[name] = {
                "name": name,
                "models": models,
            }
        return result

    async def execute(
        self,
        provider_name: str,
        task: str,
        model: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        provider = self.providers.get(provider_name)
        if not provider:
            return {
                "role": "assistant",
                "content": f"[ComfyAI] Unknown provider: {provider_name}",
                "raw": None,
                "error": True,
            }
        return await provider.execute(task=task, model=model, payload=payload)
