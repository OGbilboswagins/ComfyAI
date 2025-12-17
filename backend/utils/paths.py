import os
from pathlib import Path

# Path to this file: .../custom_nodes/ComfyUI-ComfyAI/backend/utils/paths.py
_THIS_FILE = Path(__file__).resolve()

# Plugin root: .../custom_nodes/ComfyUI-ComfyAI
PLUGIN_ROOT = _THIS_FILE.parent.parent.parent

# ComfyUI root: .../comfyui
COMFYUI_ROOT = PLUGIN_ROOT.parent.parent

# -------------------------------
# Plugin Config (STATIC)
# -------------------------------
# These are *global plugin* configs, version-controlled.
PLUGIN_CONFIG_DIR = PLUGIN_ROOT / "config"
DEFAULTS_PATH = PLUGIN_CONFIG_DIR / "defaults.json"

# -------------------------------
# User Config (WRITABLE)
# -------------------------------
# These are user-writable configs (settings, cache, state)
USER_CONFIG_DIR = COMFYUI_ROOT / "user" / "default" / "ComfyUI-ComfyAI"
SETTINGS_PATH = USER_CONFIG_DIR / "settings.json"
PROVIDERS_PATH =USER_CONFIG_DIR / "providers.json"
CACHE_DIR = USER_CONFIG_DIR / "cache"

def ensure_user_config_dir() -> None:
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
