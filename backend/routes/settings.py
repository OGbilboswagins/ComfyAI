from __future__ import annotations
from aiohttp import web

from ..utils.logger import log
from ..utils.settings_manager import (
    SETTINGS,
    SETTINGS_PATH,
)

# ------------------------------
# GET /api/comfyai/settings
# ------------------------------
async def get_settings(request: web.Request) -> web.Response:
    """
    Returns the full settings object to the UI.
    """
    return web.json_response(SETTINGS.to_json())


# ------------------------------
# POST /api/comfyai/settings
# ------------------------------
async def save_settings(request: web.Request) -> web.Response:
    """
    Replaces the settings.json with provided values.
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    try:
        SETTINGS.update_from_json(body)
        SETTINGS.save()
        return web.json_response({"status": "ok"})
    except Exception as e:
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
