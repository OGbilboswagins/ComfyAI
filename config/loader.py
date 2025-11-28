"""
Config Loader for ComfyAI
- Loads providers.json (multi-model format)
- Expands env vars
- Normalizes ProviderConfig objects safely
"""

from __future__ import annotations
import json, os, re
from typing import Dict, Any, List

from .schema import ComfyAIConfig
from .provider_config import ProviderConfig, ModelConfig
from ..backend.utils.paths import PROVIDERS_PATH, DEFAULTS_PATH



_var_pattern = re.compile(r"\$\{([^}]+)\}")

# ================================
# Helpers
# ================================
def expand_env(value):
    if isinstance(value, str):
        return _var_pattern.sub(lambda m: os.getenv(m.group(1), ""), value)
    return value


def _load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Root must be a dict for config files
    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain a JSON object: {path}")

    # Expand env vars inside dict only
    def walk_dict(obj: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            if isinstance(v, dict):
                out[k] = walk_dict(v)
            elif isinstance(v, list):
                out[k] = [
                    walk_dict(i) if isinstance(i, dict) else expand_env(i)
                    for i in v
                ]
            else:
                out[k] = expand_env(v)
        return out

    return walk_dict(data)

# ================================
# MAIN LOADER — NEW FORMAT
# ================================
def load_config() -> ComfyAIConfig:
    """
    Load multi-provider, multi-model config from providers.json.
    Falls back to defaults.json.
    """

    raw = _load_json(str(PROVIDERS_PATH))
    if not raw:
        raw = _load_json(str(DEFAULTS_PATH))

    providers = {}

    for provider_name, cfg in raw.get("providers", {}).items():
        # Extract fields with safe defaults
        p_type = cfg.get("type", "local")
        base_url = cfg.get("base_url")
        api_key = cfg.get("api_key")

        # Convert simple list of model names → List[ModelConfig]
        model_list: List[ModelConfig] = []
        raw_models = cfg.get("models", [])

        if isinstance(raw_models, list):
            for m in raw_models:
                # Allow both string or { name: "...", ... }
                if isinstance(m, str):
                    model_list.append(ModelConfig(name=m))
                elif isinstance(m, dict):
                    model_list.append(ModelConfig(**m))

        default_model = cfg.get("default_model")

        # Extra flags
        options = cfg.get("options", {})

        providers[provider_name] = ProviderConfig(
            name=provider_name,
            type=p_type,
            base_url=base_url,
            api_key=api_key,
            models=model_list,
            default_model=default_model,
            options=options,
        )

    return ComfyAIConfig(providers=providers)
