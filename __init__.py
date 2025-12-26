"""
ComfyAI - ComfyUI Assistant
Plugin entrypoint for ComfyAI.
"""

import os

# -----------------------------------------------------------
# REGISTER BACKEND ROUTES
# -----------------------------------------------------------

try:
    from aiohttp import web
    import server

    from .backend.router import setup as setup_backend_router

    app = server.PromptServer.instance.app
    setup_backend_router(app)
    print("[ComfyAI] Backend API routes registered")
except Exception as e:
    print(f"[ComfyAI] ERROR registering routes: {e}")

# -----------------------------------------------------------
# SERVE FRONTEND STATIC ASSETS
# -----------------------------------------------------------

# ComfyUI will load JS from this directory under /extensions/ComfyAI/
# and automatically execute any .js files there.
WEB_DIRECTORY = "frontend"

try:
    from aiohttp import web
    import server

    workspace = os.path.dirname(__file__)
    frontend_dir = os.path.join(workspace, "frontend")

    server.PromptServer.instance.app.add_routes([
        web.static("/extensions/ComfyAI/frontend", frontend_dir)
    ])
    print(f"[ComfyAI] Frontend static assets mounted at /extensions/ComfyAI/frontend (dir: {frontend_dir})")
except Exception as e:
    print(f"[ComfyAI] ERROR explicitly mounting frontend static assets: {e}")

NODE_CLASS_MAPPINGS = {}
__all__ = ["NODE_CLASS_MAPPINGS"]
