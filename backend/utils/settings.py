import json
from copy import deepcopy
from typing import Any, Dict

from .paths import SETTINGS_PATH, DEFAULTS_PATH, ensure_user_config_dir
from .logger import log

# -----------------------------------------------------------
# Default settings schema (Only for version, actual defaults loaded from defaults.json)
# -----------------------------------------------------------

# This minimal default is used when defaults.json itself cannot be loaded.
DEFAULT_SETTINGS: Dict[str, Any] = {
    "version": 1,
    "mode": "chat",
    "defaults": {
        "temperature": 0.2
    }
}

def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep-merge two dicts. Values in override take precedence.
    """
    result = deepcopy(base)
    for k, v in override.items():
        if (
            isinstance(v, dict)
            and k in result
            and isinstance(result[k], dict)
        ):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result

# -----------------------------------------------------------
# Load / Save settings.json
# -----------------------------------------------------------

def load_settings() -> Dict[str, Any]:
    """
    Load settings, merging defaults.json and then settings.json.
    Persist repaired settings back to disk if needed.
    """
    ensure_user_config_dir()

    # 1. Load defaults from config/defaults.json
    defaults = deepcopy(DEFAULT_SETTINGS) # Start with minimal defaults
    if DEFAULTS_PATH.exists():
        try:
            with DEFAULTS_PATH.open("r", encoding="utf-8") as f:
                file_defaults = json.load(f)
            if isinstance(file_defaults, dict):
                defaults = _deep_merge(defaults, file_defaults)
            else:
                log.error(f"[ComfyAI] defaults.json root must be an object, using minimal defaults.")
        except Exception as e:
            log.error(f"[ComfyAI] Error loading defaults.json, using minimal defaults: {e}")
    else:
        log.warning(f"[ComfyAI] defaults.json not found, using minimal defaults.")

    # 2. Load user settings from settings.json
    user_settings = {}
    if SETTINGS_PATH.exists():
        try:
            with SETTINGS_PATH.open("r", encoding="utf-8") as f:
                user_settings = json.load(f)
            if not isinstance(user_settings, dict):
                raise ValueError("settings.json root must be an object")
        except Exception as e:
            log.error(f"[ComfyAI] Error loading settings.json, using defaults: {e}")
            user_settings = {}
    else:
        log.info("[ComfyAI] settings.json not found, creating from merged defaults")

    # 3. Deep-merge user settings over defaults
    merged_settings = _deep_merge(defaults, user_settings)

    # 🔥 SELF-HEAL: persist repaired settings if merged != user_settings
    # This handles cases where settings.json is missing keys or malformed.
    if merged_settings != user_settings or not SETTINGS_PATH.exists():
        log.warning("[ComfyAI][SETTINGS] Repaired or created settings.json — saving")
        save_settings(merged_settings)

    return merged_settings

def save_settings(settings: Dict[str, Any]) -> None:
    """
    Save settings dict to settings.json (no merge, full overwrite).
    Caller is expected to send a full structure compatible with loaded settings.
    """
    ensure_user_config_dir()
    try:
        with SETTINGS_PATH.open("w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        log.info("[ComfyAI] settings.json saved")
    except Exception as e:
        log.error(f"[ComfyAI] Error saving settings.json: {e}")
        raise
