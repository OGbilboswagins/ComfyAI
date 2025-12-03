from aiohttp import web

from .provider_manager import ProviderManager
from .utils.logger import log
from .utils.request_context import (
    reset_request_context,
    set_session_id,
    get_rewrite_context,
)

from .workflow_rewrite import rewrite_workflow
from .routes.chat import chat_handler, chat_stream_handler
from .routes.providers import setup

from .routes import chat
from .routes import providers
from .routes import settings

# ============================================================
# ROUTE HANDLER
# ============================================================

async def workflow_rewrite_route(request: web.Request):
    """
    POST /api/workflow/rewrite

    Expected JSON:
        {
            "workflow": { ... },     # workflow graph dict
            "prompt": "Rewrite this workflow..."
        }
    """
    try:
        reset_request_context()
        set_session_id()

        body = await request.json()

        workflow = body.get("workflow")
        prompt = body.get("prompt")

        if workflow is None:
            return web.json_response(
                {"error": "Missing `workflow`"}, status=400
            )

        if prompt is None:
            return web.json_response(
                {"error": "Missing `prompt`"}, status=400
            )

        rewrite_ctx = get_rewrite_context()

        log.info("[ROUTER] /workflow/rewrite received request")

        result = await rewrite_workflow(
            {"workflow": workflow, "prompt": prompt}
        )

        return web.json_response(result)

    except Exception as e:
        log.exception("[ROUTER] Error in /workflow/rewrite")
        return web.json_response({"error": str(e)}, status=500)


# ============================================================
# SETUP ROUTES
# ============================================================

def setup_routes(app: web.Application):
    app.router.add_post("/api/workflow/rewrite", workflow_rewrite_route)
    log.info("[ROUTER] Registered /api/workflow/rewrite")

    setup(app)

    app.router.add_post("/api/comfyai/chat", chat_handler)
    app.router.add_post("/api/comfyai/chat/stream", chat_stream_handler)
    log.info("[ROUTER] Registered /api/comfyai/chat")
    log.info("[ROUTER] Registered /api/comfyai/chat/stream")

# ============================================================
# MAIN ENTRYPOINT CALLED BY __init__.py
# ============================================================

def setup(app: web.Application):
    log.info("[ComfyAI] Router initializing…")

    # Ensure ProviderManager is initialized once
    provider_manager = ProviderManager.instance()
    app["provider_manager"] = provider_manager

    log.info("[ComfyAI] ProviderManager loaded")

    # Register all sub-route modules
    chat.setup(app)
    providers.setup(app)
    settings.setup(app)

    log.info("[ComfyAI] Router setup complete")
