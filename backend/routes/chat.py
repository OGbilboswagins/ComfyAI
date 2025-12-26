from __future__ import annotations

from aiohttp import web

from ..provider_manager import ProviderManager
from ..utils.logger import log
from ..utils.settings import load_settings
from ..utils.paths import SETTINGS_PATH
log.warning(f"[ComfyAI][DEBUG] Using settings file: {SETTINGS_PATH}")
log.error("[ComfyAI][LOAD] backend/routes/chat.py LOADED")
async def chat_handler(request: web.Request) -> web.Response:
    """
    POST /api/comfyai/chat
    Non-streaming chat, returns full reply as JSON.
    """
    log.error("[ComfyAI][HIT] chat_handler ENTERED")
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    provider_id = body.get("provider")
    model_name = body.get("model")
    messages = body.get("messages")

    # -------------------------------------------------
    # Mode-aware system prompt injection
    # -------------------------------------------------
    settings = load_settings()
    mode = settings.get("mode", "chat")

    log.warning(f"[ComfyAI][DEBUG] Loaded mode = {mode}")

    # Get the mode-specific system prompt from defaults
    defaults = settings.get("defaults", {})
    mode_system_prompt = defaults.get(f"system_prompt_{mode}", "").strip()

    # Get the global user-defined system prompt
    user_system_prompt = settings.get("system_prompt", "").strip()

    # Combine prompts: user_system_prompt (if present) prepends mode_system_prompt
    final_system_prompt = ""
    if user_system_prompt and mode_system_prompt:
        final_system_prompt = f"{user_system_prompt}\n\n{mode_system_prompt}"
    elif user_system_prompt:
        final_system_prompt = user_system_prompt
    elif mode_system_prompt:
        final_system_prompt = mode_system_prompt

    log.warning(
        f"[ComfyAI][DEBUG] Final system_prompt (mode={mode}) = {final_system_prompt!r}"
    )

    final_messages = []

    if final_system_prompt:
        final_messages.append({
            "role": "system",
            "content": final_system_prompt,
        })

    final_messages.extend(messages)

    messages = final_messages
    
    if not provider_id or not model_name or not messages:
        return web.json_response(
            {"error": "Missing provider, model, or messages"}, status=400
        )

    mgr = ProviderManager.instance()
    client = mgr.get_provider(provider_id)

    if not client:
        return web.json_response({"error": f"Unknown provider '{provider_id}'"}, status=404)

    client.model = model_name

    log.info(f"[ComfyAI] Chat request → provider={provider_id}, model={model_name}")

    try:
        reply = await client.chat(messages)
    except Exception as e:
        log.exception("[ComfyAI] Chat failed")
        return web.json_response({"error": str(e)}, status=500)

    return web.json_response({"reply": reply})


async def chat_stream_handler(request: web.Request) -> web.StreamResponse:
    """
    POST /api/comfyai/chat/stream
    Streaming chat: returns plain text chunks.
    """
    log.error("[ComfyAI][HIT] chat_stream_handler ENTERED")
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    provider_id = body.get("provider")
    model_name = body.get("model")
    messages = body.get("messages")

    # -------------------------------------------------
    # Mode-aware system prompt injection
    # -------------------------------------------------
    settings = load_settings()
    mode = settings.get("mode", "chat")

    log.warning(f"[ComfyAI][DEBUG] Loaded mode = {mode}")

    # Get the mode-specific system prompt from defaults
    defaults = settings.get("defaults", {})
    mode_system_prompt = defaults.get(f"system_prompt_{mode}", "").strip()

    # Get the global user-defined system prompt
    user_system_prompt = settings.get("system_prompt", "").strip()

    # Combine prompts: user_system_prompt (if present) prepends mode_system_prompt
    final_system_prompt = ""
    if user_system_prompt and mode_system_prompt:
        final_system_prompt = f"{user_system_prompt}\n\n{mode_system_prompt}"
    elif user_system_prompt:
        final_system_prompt = user_system_prompt
    elif mode_system_prompt:
        final_system_prompt = mode_system_prompt

    log.warning(
        f"[ComfyAI][DEBUG] Final system_prompt (mode={mode}) = {final_system_prompt!r}"
    )

    final_messages = []

    if final_system_prompt:
        final_messages.append({
            "role": "system",
            "content": final_system_prompt,
        })

    final_messages.extend(messages)

    messages = final_messages

    if not provider_id or not model_name or not messages:
        return web.json_response(
            {"error": "Missing provider, model, or messages"}, status=400
        )

    mgr = ProviderManager.instance()
    client = mgr.get_provider(provider_id)

    if not client:
        return web.json_response({"error": f"Unknown provider '{provider_id}'"}, status=404)

    client.model = model_name

    log.info(f"[ComfyAI] STREAM chat request → provider={provider_id}, model={model_name}")

    resp = web.StreamResponse(
        status=200,
        headers={
            "Content-Type": "text/plain; charset=utf-8",
        },
    )

    await resp.prepare(request)

    try:
        async for chunk in client.stream_chat(messages):
            if not chunk:
                continue
            await resp.write(chunk.encode("utf-8"))
            await resp.drain()
    except Exception:
        log.exception("[ComfyAI] Streaming chat failed")
    finally:
        await resp.write_eof()

    return resp

def setup(app: web.Application) -> None:
    """
    Register chat + streaming chat endpoints
    """
    app.router.add_post("/api/comfyai/chat", chat_handler)
    app.router.add_post("/api/comfyai/chat/stream", chat_stream_handler)

    log.info("[ROUTER] Registered /api/comfyai/chat* routes")
