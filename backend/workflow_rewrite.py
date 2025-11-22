"""
Workflow Rewrite API handler for ComfyAI.
Provides an endpoint for rewriting a workflow graph using the selected provider.
"""

from aiohttp import web
import json

from .service.workflow_rewrite_agent import rewrite_workflow
from .utils.request_context import (
    reset_request_context,
    get_rewrite_context,
    set_session_id,
    set_active_provider,
)


async def rewrite_handler(request: web.Request):
    """
    POST /api/workflow/rewrite
    Body:
      {
        "workflow": {...},
        "provider": "openai",
        "session_id": "optional"
      }
    """
    data = await request.json()

    workflow = data.get("workflow")
    provider = data.get("provider", "openai")
    session_id = data.get("session_id")

    # Reset + initialize request context
    reset_request_context()
    set_session_id(session_id)
    set_active_provider(provider)

    # Initialize rewrite context
    rewrite_ctx = get_rewrite_context()

    # -----------------------------------------
    # Build request JSON for rewrite_workflow()
    # -----------------------------------------
    request_json = {
        "workflow": workflow,
        "prompt": rewrite_ctx.rewrite_expert if hasattr(rewrite_ctx, "rewrite_expert") else ""
    }

    # Run rewrite
    response = await rewrite_workflow(request_json)

    rewritten = response.get("workflow", workflow)
    notes = response.get("notes", "")

    return web.json_response({
        "ok": True,
        "session_id": session_id,
        "provider": provider,
        "rewrite_notes": notes,
        "workflow": rewritten,
    })


def setup(app: web.Application):
    """
    Called by router to register workflow rewrite routes.
    """
    app.router.add_post("/api/workflow/rewrite", rewrite_handler)
