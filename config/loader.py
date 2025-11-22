"""
ComfyAI Configuration Loader
Loads config from:
1. Built-in defaults (defaults.json in this folder)
2. User overrides (providers.json + settings.json)
3. Environment variables
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

from .schema import ComfyAIConfig

ROOT = Path(__file__).parent
USER_ROOT = Path(os.getenv("COMFYUI_USER_DIR",
    "/mnt/ai/apps/comfyui/user/default/ComfyAI"
))


def load_json_or_empty(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def load_config() -> ComfyAIConfig:
    # 1. Load defaults
    defaults_path = ROOT / "defaults.json"
    defaults = json.loads(defaults_path.read_text())

    # 2. Load user overrides
    user_providers = load_json_or_empty(USER_ROOT / "providers.json")
    user_settings = load_json_or_empty(USER_ROOT / "settings.json")

    merged = defaults.copy()

    # Merge providers
    if "providers" in user_providers:
        for k, v in user_providers["providers"].items():
            merged["providers"][k] = {**merged["providers"].get(k, {}), **v}

    # Merge settings
    merged["settings"].update(user_settings)

    # 3. Environment variable overrides
    for key, value in os.environ.items():
        if key.startswith("COMFYAI_"):
            name = key.replace("COMFYAI_", "").lower()
            merged["settings"][name] = value

    return ComfyAIConfig(**merged)