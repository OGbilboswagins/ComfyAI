"""
ComfyAI - ComfyUI Assistant
Clean plugin entrypoint for ComfyAI.
"""

import os
from aiohttp import web
import server

print("[ComfyAI] __init__ LOADED")
def load(app: web.Application):
    """
    Loaded automatically by ComfyUI when this directory
    is inside custom_nodes/.

    This wires together:
        • API routes (via router.py)
        • Static web UI (dist/)
    """
    # Correct router import
    from .router import setup as setup_router

    print("[ComfyAI] load() CALLED")
    
    # Setup backend API routes
    setup_router(app)

    # Serve UI if it exists
    workspace = os.path.dirname(__file__)
    dist_dir = os.path.join(workspace, "dist", "copilot_web")

    if os.path.exists(dist_dir):
        server.PromptServer.instance.app.add_routes([
            web.static("/comfyai/", dist_dir)
        ])
        print("[ComfyAI] UI mounted at /comfyai/")
    else:
        print("[ComfyAI] ⚠ UI folder not found, backend-only mode")

    return app


# Required by ComfyUI (marks this folder as a plugin)
WEB_DIRECTORY = "dist/copilot_web"
NODE_CLASS_MAPPINGS = {}
__all__ = ["NODE_CLASS_MAPPINGS", "load"]