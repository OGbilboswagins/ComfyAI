"""
Config Loader for ComfyAI

Loads:
  • user/default/ComfyUI-ComfyAI/providers.json  (main)
  • defaults.json                                 (fallback)
"""

from __future__ import annotations
import json
import os
from typing import Dict, Any

from .schema import ComfyAIConfig
from .provider_config import ProviderConfig


# Path to user's config:
USER_CONFIG_DIR = os.path.expanduser(
    "/mnt/ai/apps/comfyui/user/default/ComfyUI-ComfyAI"
)

USER_PROVIDERS_PATH = os.path.join(USER_CONFIG_DIR, "providers.json")

# Fallback defaults:
DEFAULTS_PATH = os.path.join(os.path.dirname(__file__), "defaults.json")


def _load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config() -> ComfyAIConfig:
    """
    Load providers from:
        1. providers.json in user directory
        2. defaults.json fallback

    providers.json uses FLAT STRUCTURE:
        {
            "local_chat": { ... },
            "local_edit": { ... }
        }
    """
    raw = _load_json(USER_PROVIDERS_PATH)

    if not raw:
        raw = _load_json(DEFAULTS_PATH)

    # Build ProviderConfig objects
    providers = {
        name: ProviderConfig(name=name, **cfg)
        for name, cfg in raw.items()
    }

    return ComfyAIConfig(providers=providers)
