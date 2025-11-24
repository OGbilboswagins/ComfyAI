"""
ComfyAI - Workflow Rewrite Tools

Core rewrite_graph_with_llm() used by workflow_rewrite_agent.py.

Takes:
    • workflow graph (dict)
    • user prompt (string)
Returns:
    • rewritten graph (dict)
    • notes (str)
"""

from __future__ import annotations
from typing import Dict, Any, Tuple

import json

from ..provider_manager import ProviderManager
from ..utils.logger import log


# ============================================================
# CORE LOGIC
# ============================================================

async def rewrite_graph_with_llm(
    graph: Dict[str, Any],
    user_prompt: str,
) -> Tuple[Dict[str, Any], str]:
    """
    Main workflow rewrite function.

    Sends the workflow + prompt to the active LLM and expects a rewritten graph.
    The LLM returns JSON which we parse back into a graph.
    """

    log.info("[ComfyAI] rewrite_graph_with_llm(): starting rewrite")

    provider_mgr = ProviderManager.instance()

    # Prefer a provider suitable for "rewrite" task
    llm = provider_mgr.pick_provider(task="rewrite") or provider_mgr.get_default_llm()

    if llm is None:
        raise RuntimeError("No LLM provider configured")

    # --------------------------------------------------------
    # Construct LLM messages
    # --------------------------------------------------------
    system_msg = (
        "You are ComfyAI, an expert workflow architect for ComfyUI. "
        "You rewrite graph JSON safely. "
        "Always return valid JSON with the same structure as the input graph."
    )

    user_msg = (
        f"User instructions:\n{user_prompt}\n\n"
        f"Original workflow graph JSON:\n{json.dumps(graph, indent=2)}\n\n"
        "Return ONLY JSON. No explanation."
    )

    log.info("[ComfyAI] Sending rewrite request to LLM provider…")

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]

    # --------------------------------------------------------
    # Query the model
    # --------------------------------------------------------
    response = await llm.chat(messages)

    log.info("[ComfyAI] Received LLM rewrite response")

    # ChatClient returns raw string content
    raw_output = response


    # --------------------------------------------------------
    # Parse rewritten graph
    # --------------------------------------------------------
    try:
        new_graph = json.loads(raw_output)
    except Exception as e:
        log.error(f"[ComfyAI] ERROR parsing rewritten JSON: {e}")
        # Fall back to original graph
        new_graph = graph

    notes = "Rewrite completed by LLM"

    return new_graph, notes


__all__ = ["rewrite_graph_with_llm"]
