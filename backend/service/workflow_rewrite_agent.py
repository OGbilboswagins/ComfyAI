"""
ComfyAI - Workflow Rewrite Agent Service
Provides the rewrite_workflow() function used by router.py.
"""

from __future__ import annotations
from typing import Dict, Any

from ..utils.logger import log
from ..utils.request_context import (
    get_rewrite_context,
    reset_request_context,
    WorkflowRewriteContext,
)
from .workflow_rewrite_tools import rewrite_graph_with_llm


# ============================================================
# PUBLIC ENTRYPOINT (used by router.py)
# ============================================================

async def rewrite_workflow(request_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Top-level function called by router.py.

    Expects:
        {
            "workflow": { ... },
            "prompt": "Rewrite this workflow..."
        }

    Returns:
        {
            "workflow": <rewritten graph>,
            "notes": <llm commentary>
        }
    """

    log.info("[ComfyAI] rewrite_workflow(): received request")

    # -------------------------------
    # Validate incoming request
    # -------------------------------
    if "workflow" not in request_json:
        return {"error": "Missing required field: workflow"}

    if "prompt" not in request_json:
        return {"error": "Missing required field: prompt"}

    original_graph = request_json["workflow"]
    user_prompt = request_json["prompt"]

    # -------------------------------
    # Acquire per-request context
    # -------------------------------
    rewrite_ctx: WorkflowRewriteContext = get_rewrite_context()

    log.info("[ComfyAI] Invoking LLM rewrite engine...")

    try:
        # -------------------------------------------------------
        # Core LLM rewrite logic
        # -------------------------------------------------------
        rewritten_graph, notes = await rewrite_graph_with_llm(
            graph=original_graph,
            user_prompt=user_prompt,
        )

        # Stash notes into the context object for downstream use
        try:
            rewrite_ctx.add_expert_info(notes)
        except Exception:
            # Don't let context logging kill the request
            log.warning(
                "[ComfyAI] Failed to add expert info to rewrite context",
                exc_info=True,
            )

        log.info("[ComfyAI] Workflow rewrite completed successfully")

        return {
            "workflow": rewritten_graph,
            "notes": notes,
        }

    finally:
        # Always clear context between requests
        reset_request_context()


__all__ = ["rewrite_workflow"]
