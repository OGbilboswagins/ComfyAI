from __future__ import annotations

from aiohttp import web

from ..provider_manager import ProviderManager
from ..utils.logger import log


async def chat_handler(request: web.Request) -> web.Response:
    """
    POST /api/comfyai/chat
    Non-streaming chat, returns full reply as JSON.
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    provider_id = body.get("provider")
    model_name = body.get("model")
    messages = body.get("messages")

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
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    provider_id = body.get("provider")
    model_name = body.get("model")
    messages = body.get("messages")

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
