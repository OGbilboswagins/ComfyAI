from __future__ import annotations
from aiohttp import web

from ..utils.logger import log
from ..utils.settings import load_settings, save_settings as save_settings_to_disk

# ------------------------------
# GET /api/comfyai/settings
# ------------------------------
async def get_settings(request: web.Request) -> web.Response:
    settings = load_settings()
    return web.json_response(settings)

def deep_merge(base: dict, incoming: dict) -> dict:
    for k, v in incoming.items():
        # 🔒 Never overwrite a dict with None
        if v is None and isinstance(base.get(k), dict):
            continue

        if isinstance(v, dict) and isinstance(base.get(k), dict):
            deep_merge(base[k], v)
        else:
            base[k] = v
    return base

# ------------------------------
# POST /api/comfyai/settings
# ------------------------------
async def save_settings(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    # 🔥 HARD GUARD: defaults must NEVER be None
    if body.get("defaults") is None:
        log.warning("[ComfyAI][SETTINGS] Incoming defaults is None — DROPPING KEY")
        body.pop("defaults", None)

    try:
        settings = load_settings()
        merged = deep_merge(settings, body)
        save_settings_to_disk(merged)
        return web.json_response(merged)
    except Exception as e:
        log.exception("[ComfyAI] Failed to save settings")
        return web.json_response({"error": str(e)}, status=500)

# ------------------------------
# ROUTE REGISTRATION
# ------------------------------
def setup(app: web.Application) -> None:
    """
    Registers /api/comfyai/settings endpoints.
    """
    app.router.add_get("/api/comfyai/settings", get_settings)
    app.router.add_post("/api/comfyai/settings", save_settings)

    log.info("[ROUTER] Registered /api/comfyai/settings routes")
