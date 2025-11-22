from aiohttp import web

# Provider manager + utils
from .config.loader import get_provider_manager
from .backend.utils.logger import log

# Endpoints
from .backend.workflow_rewrite import handle_workflow_rewrite


# ------------------------------
# API ROUTES
# ------------------------------

async def workflow_rewrite(request: web.Request):
    """
    POST /api/workflow/rewrite
    Accepts:
        {
            "messages": [ { role: "user", content: "..." }, ... ]
        }
    """
    try:
        body = await request.json()
        messages = body.get("messages", [])

        log.info("[ROUTER] /workflow/rewrite called")

        result = await handle_workflow_rewrite(messages)
        return web.json_response(result)

    except Exception as e:
        log.exception("Error in /workflow/rewrite endpoint")
        return web.json_response(
            {"success": False, "error": str(e)}, status=500
        )


# ------------------------------
# APP SETUP
# ------------------------------

def setup_routes(app: web.Application):
    """
    Called automatically by ComfyUI’s extension system.
    Registers all HTTP endpoints for ComfyAI.
    """
    app.router.add_post("/api/workflow/rewrite", workflow_rewrite)
    log.info("[ROUTER] Registered /api/workflow/rewrite")


def setup(app: web.Application):
    """
    Main entrypoint loaded by ComfyUI when the custom node loads.
    Initializes provider manager and routes.
    """
    log.info("[ComfyAI] Initializing…")

    # Load providers BEFORE routes so the backend has config
    provider_manager = get_provider_manager()
    app["provider_manager"] = provider_manager

    log.info("[ComfyAI] Loaded provider manager")

    setup_routes(app)

    log.info("[ComfyAI] Router setup complete")