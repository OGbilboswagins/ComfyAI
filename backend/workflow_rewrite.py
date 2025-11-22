import json
from typing import List, Dict, Any

from .provider_manager import provider_manager
from ..utils.logger import log


SYSTEM_PROMPT = """
You are the ComfyAI Workflow Rewrite Agent.

Your job:
- Take the user's instruction and (optionally) a current ComfyUI workflow JSON.
- Propose a NEW or UPDATED workflow suitable for ComfyUI.
- Be explicit and structured.

You MUST ALWAYS respond with PURE JSON. No markdown, no commentary, no prose.

Expected response schema (JSON only):

{
  "workflow": {
    // A valid ComfyUI workflow JSON object
  },
  "summary": "Short natural language summary of what changed or what this workflow does.",
  "notes": "Optional extra commentary, tips, or caveats for the user."
}

Rules:
- If the user gives you an existing workflow JSON, try to MODIFY/EXTEND it rather than starting from scratch, unless they explicitly say otherwise.
- Keep node names, types, and connections consistent with typical ComfyUI conventions.
- Make sure inputs/outputs match (latent/image/model/etc).
- Never print explanations outside the JSON structure.
- If you cannot build a valid workflow, return:

{
  "workflow": null,
  "summary": "Why you could not generate a workflow.",
  "notes": "Suggestions for what the user should provide or fix."
}
""".strip()


async def handle_workflow_rewrite(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    High-level adapter for 'workflow rewrite' tasks.

    - Uses the provider configured for the 'workflow_rewrite' task
      (falls back to 'chat' if not configured).
    - Wraps the incoming messages with a strong system prompt.
    - Tries to parse the model output as JSON according to the schema above.

    Returns a dict that the router can send directly as JSON response.
    """
    # Decide which provider/task to use
    task_used = "workflow_rewrite"
    try:
        client = provider_manager.create_client(task_used)
        provider_cfg = provider_manager.get_provider(task_used)
    except Exception as e:
        # Fallback to general chat provider if no workflow_rewrite provider
        log.error(f"[WORKFLOW REWRITE] No dedicated workflow_rewrite provider, falling back to 'chat': {e}")
        task_used = "chat"
        client = provider_manager.create_client(task_used)
        provider_cfg = provider_manager.get_provider(task_used)

    model_name = provider_cfg.get("model", "unknown-model")
    log.info(f"[WORKFLOW REWRITE] Using provider task='{task_used}', model='{model_name}'")

    # Build final message list: system + user history
    final_messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *messages,
    ]

    try:
        # Call the model via OpenAI-compatible client
        completion = client.chat.completions.create(
            model=model_name,
            messages=final_messages,
            max_tokens=4096,
            temperature=0.15,
            stream=False,
        )

        # OpenAI-style response: choices[0].message["content"]
        raw_text = completion.choices[0].message["content"]
        log.info(f"[WORKFLOW REWRITE] Raw model reply length: {len(raw_text)}")

        parsed: Any = None
        workflow = None
        summary = ""
        notes = ""

        try:
            parsed = json.loads(raw_text)
            if isinstance(parsed, dict):
                workflow = parsed.get("workflow")
                summary = parsed.get("summary") or ""
                notes = parsed.get("notes") or ""
            else:
                # If it's not a dict, treat as failure but keep raw
                log.error("[WORKFLOW REWRITE] Parsed JSON is not an object; treating as failure.")
        except json.JSONDecodeError as je:
            log.error(f"[WORKFLOW REWRITE] Failed to parse JSON from model: {je}")
            parsed = None

        # If we couldn't get a valid structured object, return a graceful fallback
        if not isinstance(parsed, dict):
            return {
                "workflow": None,
                "summary": "The model did not return valid JSON in the expected format.",
                "notes": (
                    "Raw reply from model is included in 'raw_reply'. "
                    "You may need to adjust the prompt or use a more capable model."
                ),
                "raw_reply": raw_text,
                "model": model_name,
                "provider_task": task_used,
                "success": False,
            }

        return {
            "workflow": workflow,
            "summary": summary,
            "notes": notes,
            "raw_reply": raw_text,
            "model": model_name,
            "provider_task": task_used,
            "success": workflow is not None,
        }

    except Exception as e:
        log.error(f"[WORKFLOW REWRITE] Fatal error: {e}", exc_info=True)
        return {
            "workflow": None,
            "summary": "An internal error occurred while generating or rewriting the workflow.",
            "notes": str(e),
            "raw_reply": "",
            "model": model_name,
            "provider_task": task_used,
            "success": False,
        }