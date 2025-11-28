from aiohttp import web
from ..config.loader import load_config
from ..config.providers_loader import load_providers
from .utils.logger import log
from .utils.settings import load_settings, save_settings

routes = web.RouteTableDef()

# -----------------------------------------------------------
# Utility: convert ProviderConfig → dict for UI
# -----------------------------------------------------------

def provider_to_dict(pcfg):
    return {
        "name": pcfg.name,
        "type": pcfg.type,
        "base_url": pcfg.base_url,
        "model": pcfg.model,
        "api_key": bool(pcfg.api_key),  # do not leak actual keys
        "default": pcfg.default,
    }


# -----------------------------------------------------------
# GET /comfyai/providers
# Primary route used by the UI for provider list
# -----------------------------------------------------------

@routes.get("/comfyai/providers")
async def get_comfyai_providers(request: web.Request) -> web.Response:
    """
    Return the normalized provider list from providers.json in a
    frontend-friendly shape.

    Response shape (compatible with current comfyai.js):

    {
      "providers": {
        "ollama": {
          "name": "ollama",
          "type": "local",
          "base_url": "http://localhost:11434",
          "default_model": "qwen2.5:7b-instruct-fp16",
          "models": ["qwen2.5:7b-instruct-fp16", "mistral-7b-instruct"],
          "options": { ... }
        },
        "openai": { ... }
      },
      "provider_list": ["ollama", "openai"],
      "default_provider": "ollama"
    }
    """
    try:
        providers_map = load_providers()  # Dict[str, ProviderConfig]

        providers_public = {
            name: cfg.to_public_dict() for name, cfg in providers_map.items()
        }

        provider_names = list(providers_public.keys())

        # For now, default to the first provider if present.
        # Later we’ll tie this into settings.json per-task (chat/plan/build).
        default_provider = provider_names[0] if provider_names else None

        payload = {
            "providers": providers_public,
            "provider_list": provider_names,
            "default_provider": default_provider,
        }

        return web.json_response(payload)

    except Exception as e:
        # Safe error message; we don't expose internals to the browser.
        return web.json_response(
            {"error": f"Failed to load providers.json: {e}"},
            status=500,
        )

# -----------------------------------------------------------
# POST /comfyai/providers (placeholder for future provider editing)
# -----------------------------------------------------------

@routes.post("/comfyai/providers")
async def update_providers(request: web.Request):
    log.info("[ComfyAI] POST /comfyai/providers (not implemented yet)")
    return web.json_response({
        "status": "noop",
        "message": "Provider editing via API not implemented yet."
    })


# -----------------------------------------------------------
# GET /comfyai/settings
# Returns Option-3 settings.json (merged with defaults)
# -----------------------------------------------------------

@routes.get("/comfyai/settings")
async def get_settings(request: web.Request):
    log.info("[ComfyAI] GET /comfyai/settings")
    try:
        cfg = load_settings()
        return web.json_response(cfg)
    except Exception as e:
        log.error(f"[ComfyAI] ERROR in GET /comfyai/settings: {e}")
        return web.json_response({"error": str(e)}, status=500)


# -----------------------------------------------------------
# POST /comfyai/settings
# Save updated settings.json (Option-3 schema)
# -----------------------------------------------------------

@routes.post("/comfyai/settings")
async def save_settings_route(request: web.Request):
    log.info("[ComfyAI] POST /comfyai/settings")
    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            return web.json_response({"error": "Payload must be an object"}, status=400)

        # Very light validation: ensure version and defaults exist
        if "defaults" not in payload:
            return web.json_response({"error": "Missing 'defaults' in settings"}, status=400)

        save_settings(payload)
        return web.json_response({"status": "ok"})

    except Exception as e:
        log.error(f"[ComfyAI] ERROR in POST /comfyai/settings: {e}")
        return web.json_response({"error": str(e)}, status=500)


# -----------------------------------------------------------
# Debug endpoints (optional, keep for now)
# -----------------------------------------------------------

@routes.get("/comfyai/debug-config")
async def debug_config(request: web.Request):
    cfg = load_config()
    return web.json_response({
        "attributes": dir(cfg),
        "type": str(type(cfg))
    })


@routes.get("/comfyai/debug-providers")
async def debug_providers(request: web.Request):
    cfg = load_config()
    out = {k: str(v) for k, v in cfg.providers.items()}
    return web.json_response({"providers": out})


# -----------------------------------------------------------
# API initializer
# -----------------------------------------------------------

def setup(app: web.Application):
    log.info("[ComfyAI] Registering ComfyAI API routes (providers + settings + debug)")
    app.add_routes(routes)
