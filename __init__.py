"""
ComfyAI - ComfyUI Assistant
Plugin entrypoint for ComfyAI.
"""

import os
from aiohttp import web
import server

# -----------------------------------------------------------
# REGISTER API ROUTES AT IMPORT TIME (Comfy-Copilot style)
# -----------------------------------------------------------

try:
    # Import router and register immediately
    from .backend.router import setup as setup_router
    setup_router(server.PromptServer.instance.app)
    print("[ComfyAI] Backend routes registered")
except Exception as e:
    print(f"[ComfyAI] ERROR registering backend routes: {e}")


# -----------------------------------------------------------
# SERVE STATIC UI AUTOMATICALLY
# -----------------------------------------------------------

workspace = os.path.dirname(__file__)
dist_dir = os.path.join(workspace, "dist", "copilot_web")

if os.path.exists(dist_dir):
    try:
        server.PromptServer.instance.app.add_routes([
            web.static("/comfyai/", dist_dir)
        ])
        print(f"[ComfyAI] UI mounted at /comfyai/  (dir: {dist_dir})")
    except Exception as e:
        print(f"[ComfyAI] ERROR mounting UI: {e}")
else:
    print("[ComfyAI] No UI found, running backend-only")


# Required exports
WEB_DIRECTORY = "dist/copilot_web"
NODE_CLASS_MAPPINGS = {}
__all__ = ["NODE_CLASS_MAPPINGS"]
