import json
from copy import deepcopy
from typing import Any, Dict

from .paths import SETTINGS_PATH, ensure_user_config_dir
from .logger import log

# -----------------------------------------------------------
# Default settings schema (Option 3)
# -----------------------------------------------------------

DEFAULT_SETTINGS: Dict[str, Any] = {
    "version": 1,
    "defaults": {
        "chat_model": "local_chat",
        "edit_model": "local_edit",
        "plan_model": "local_apply",
        "workflow_model": "cloud_workflow",
        "temperature": 0.2,
        "max_tokens": 4096,
        "top_p": 0.95,
        "system_prompt_chat": "",
        "system_prompt_edit": "",
        "system_prompt_plan": ""
    },
    "workflow": {
        "rewrite": {
            "max_tokens": 4096,
            "use_cloud": True
        }
    },
    "mcp": {
        "enable": False,
        "endpoint": None
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
    Load settings.json, merging with DEFAULT_SETTINGS so all keys exist.
    """
    ensure_user_config_dir()
    if not SETTINGS_PATH.exists():
        log.info("[ComfyAI] settings.json not found, using defaults")
        return deepcopy(DEFAULT_SETTINGS)

    try:
        with SETTINGS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("settings.json root must be an object")
        merged = _deep_merge(DEFAULT_SETTINGS, data)
        return merged
    except Exception as e:
        log.error(f"[ComfyAI] Error loading settings.json, using defaults: {e}")
        return deepcopy(DEFAULT_SETTINGS)


def save_settings(settings: Dict[str, Any]) -> None:
    """
    Save settings dict to settings.json (no merge, full overwrite).
    Caller is expected to send a full structure compatible with DEFAULT_SETTINGS.
    """
    ensure_user_config_dir()
    try:
        with SETTINGS_PATH.open("w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        log.info("[ComfyAI] settings.json saved")
    except Exception as e:
        log.error(f"[ComfyAI] Error saving settings.json: {e}")
        raise
