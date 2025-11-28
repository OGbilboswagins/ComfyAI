from __future__ import annotations

import json
from functools import lru_cache
from typing import Dict, Any, List

from ..backend.utils.paths import PROVIDERS_PATH
from .provider_config import ProviderConfig, ModelConfig


def _normalize_model_entry(entry: Any) -> ModelConfig:
    """
    Accept either:
      - "model-name"
      - { "name": "...", ...metadata }
    and always return a ModelConfig instance.
    """
    if isinstance(entry, str):
        return ModelConfig(name=entry)

    if isinstance(entry, dict):
        name = entry.get("name")
        if not name:
            raise ValueError("Model entry is missing required 'name' field")

        return ModelConfig(
            name=name,
            context=entry.get("context"),
            size=entry.get("size"),
            capabilities=list(entry.get("capabilities", [])),
            metadata={k: v for k, v in entry.items()
                      if k not in {"name", "context", "size", "capabilities"}},
        )

    raise TypeError(f"Invalid model entry type: {type(entry)!r}")


def _normalize_provider(name: str, data: Dict[str, Any]) -> ProviderConfig:
    """
    Validate + normalize a single provider entry from providers.json.

    Supports both the NEW format:
      {
        "type": "local",
        "base_url": "http://localhost:11434",
        "models": ["qwen2.5:7b-instruct-fp16", ...],
        "default_model": "qwen2.5:7b-instruct-fp16"
      }

    and a legacy/simplified format:
      {
        "type": "local",
        "base_url": "http://localhost:11434",
        "model": "qwen2.5:7b-instruct-fp16"
      }
    """
    if not isinstance(data, dict):
        raise TypeError(f"Provider '{name}' must be a JSON object")

    p_type = data.get("type", "local")
    base_url = data.get("base_url")
    api_key = data.get("api_key")

    # Legacy: single "model" string
    legacy_model = data.get("model")

    # New: list of "models"
    models_raw = data.get("models", [])
    models: List[ModelConfig] = []

    if models_raw:
        if not isinstance(models_raw, list):
            raise TypeError(f"Provider '{name}': 'models' must be a list")
        for m in models_raw:
            models.append(_normalize_model_entry(m))
    elif legacy_model:
        # Upgrade legacy single-model provider into models[]
        models.append(ModelConfig(name=legacy_model))

    # Default model
    default_model: str | None = data.get("default_model")

    if default_model is None and models:
        # If not explicitly set, use the first model
        default_model = models[0].name

    return ProviderConfig(
        name=name,
        type=p_type,
        base_url=base_url,
        api_key=api_key,
        models=models,
        default_model=default_model,
        options=data.get("options", {}),
    )


@lru_cache()
def load_providers() -> Dict[str, ProviderConfig]:
    """
    Main entry point: load and normalize providers.json.

    Location:
        comfyui/user/default/ComfyUI-ComfyAI/providers.json

    If the file does not exist, we return an empty dict for now.
    (Later phases can auto-create this from defaults.json if needed.)
    """
    if not PROVIDERS_PATH.exists():
        # No providers.json yet → empty config, no crash.
        return {}

    with PROVIDERS_PATH.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, dict):
        raise TypeError("providers.json must contain a top-level JSON object")

    providers_raw = raw.get("providers")
    if providers_raw is None:
        # Also accept the simpler shape { "ollama": {...}, "openai": {...} }
        providers_raw = raw

    if not isinstance(providers_raw, dict):
        raise TypeError("'providers' must be an object in providers.json")

    result: Dict[str, ProviderConfig] = {}

    for name, pdata in providers_raw.items():
        cfg = _normalize_provider(name, pdata)
        result[name] = cfg

    return result


def reload_providers_cache() -> Dict[str, ProviderConfig]:
    """
    Helper to clear the lru_cache and reload from disk.
    Useful for future settings UI or hot-reload endpoints.
    """
    load_providers.cache_clear()
    return load_providers()
