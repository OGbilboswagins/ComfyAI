import json
from pathlib import Path
from typing import Any, Dict

from ..utils.paths import SETTINGS_PATH, USER_CONFIG_DIR, ensure_user_config_dir

print("SETTINGS_PATH =", SETTINGS_PATH)


class SettingsManager:
    """
    Loads and saves ComfyAI's user settings from:
    COMFYUI_ROOT/user/default/ComfyUI-ComfyAI/settings.json
    """

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    # ------------------------------------------------------
    # Load settings.json if present
    # ------------------------------------------------------
    def load(self) -> None:
        ensure_user_config_dir()

        if SETTINGS_PATH.exists():
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                try:
                    self._data.update(json.load(f))
                except Exception:
                    # corrupt file fallback
                    self._data = {}

    # ------------------------------------------------------
    # Export to dict for JSON response
    # ------------------------------------------------------
    def to_json(self) -> Dict[str, Any]:
        return self._data

    # ------------------------------------------------------
    # Merge new settings (POST update)
    # ------------------------------------------------------
    def update_from_json(self, new_data: Dict[str, Any]) -> None:
        if not isinstance(new_data, dict):
            return
        self._data = new_data

    # ------------------------------------------------------
    # Save to disk
    # ------------------------------------------------------
    def save(self) -> None:
        ensure_user_config_dir()
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=4)
# ------------------------------------------------------
# Global Settings singleton
# ------------------------------------------------------
SETTINGS = SettingsManager()
SETTINGS.load() 
