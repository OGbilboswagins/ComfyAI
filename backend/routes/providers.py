# backend/routes/providers.py

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from aiohttp import web

from ..provider_manager import ProviderManager
from ..utils.logger import log
from ..utils.paths import PROVIDERS_PATH


# ---------------------------------------------------------------------------
# Low-level helpers to read/write providers.json
# ---------------------------------------------------------------------------

def _load_providers_file() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Load providers.json in its raw JSON form.

    Returns:
        (root_json, providers_mapping)

    Where:
      root_json         = the full JSON object from providers.json
      providers_mapping = root_json["providers"] (or root_json itself as fallback)
    """
    if PROVIDERS_PATH.exists():
        with PROVIDERS_PATH.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            raise RuntimeError("providers.json must contain a JSON object at the top level")
    else:
        # If missing, start with an empty providers object
        raw = {"providers": {}}

    providers_raw = raw.get("providers")
    if providers_raw is None:
        # Fallback to treating whole file as providers map
        providers_raw = raw.setdefault("providers", {})

    if not isinstance(providers_raw, dict):
        raise RuntimeError("'providers' must be a JSON object in providers.json")

    return raw, providers_raw


def _save_providers_file(root: Dict[str, Any]) -> None:
    """
    Persist the updated providers.json to disk.
    """
    PROVIDERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PROVIDERS_PATH.open("w", encoding="utf-8") as f:
        json.dump(root, f, indent=2)
    log.info(f"[ComfyAI] Saved providers.json at {PROVIDERS_PATH}")


def _reload_provider_manager(request: web.Request) -> None:
    """
    Reinitialize the existing ProviderManager instance in-place so that
    all ChatClient instances and config reflect the latest providers.json.
    """
    mgr = request.app.get("provider_manager") or ProviderManager.instance()
    # Re-run __init__ on the same instance to refresh config/providers.
    mgr.__init__()  # type: ignore[misc]
    log.info("[ComfyAI] ProviderManager reloaded after config change")


# ---------------------------------------------------------------------------
# GET /api/comfyai/providers
# ---------------------------------------------------------------------------

async def list_providers(request: web.Request) -> web.Response:
    """
    Return providers in a normalized, UI-friendly structure.

    Response:
    {
      "providers": {
        "ollama": { ...public fields... },
        "openai": { ... }
      }
    }
    """
    mgr = request.app.get("provider_manager") or ProviderManager.instance()
    providers_cfg = getattr(mgr.config, "providers", {})  # Dict[str, ProviderConfig]

    providers_out: Dict[str, Any] = {}
    for name, cfg in providers_cfg.items():
        # Use ProviderConfig.to_public_dict(), but include an 'id' field.
        data = cfg.to_public_dict()
        data["id"] = name
        providers_out[name] = data

    return web.json_response({"providers": providers_out})


# ---------------------------------------------------------------------------
# GET /api/comfyai/models?provider=<id>
# ---------------------------------------------------------------------------

async def list_models(request: web.Request) -> web.Response:
    """
    List models for a given provider in a normalized array.

    GET /api/comfyai/models?provider=openai

    Response:
    [
      {
        "name": "gpt-4.1-mini",
        "display_name": "gpt-4.1-mini",
        "provider": "openai",
        "type": "cloud"
      },
      ...
    ]
    """
    provider_id = request.rel_url.query.get("provider")
    if not provider_id:
        return web.json_response({"error": "Missing 'provider' query parameter"}, status=400)

    mgr = request.app.get("provider_manager") or ProviderManager.instance()
    cfg = getattr(mgr.config, "providers", {}).get(provider_id)
    if not cfg:
        return web.json_response({"error": f"Provider '{provider_id}' not found"}, status=404)

    models_out: List[Dict[str, Any]] = []
    for m in cfg.models:
        models_out.append(
            {
                "name": m.name,
                "display_name": m.name,  # you can later add a 'display_name' field to ModelConfig if desired
                "provider": provider_id,
                "type": cfg.type or "unknown",
            }
        )

    return web.json_response(models_out)


# ---------------------------------------------------------------------------
# POST /api/comfyai/providers/add
# ---------------------------------------------------------------------------

async def add_provider(request: web.Request) -> web.Response:
    """
    Add a provider entry to providers.json.

    Expected JSON body:
    {
      "id": "openrouter",
      "type": "cloud",
      "base_url": "https://openrouter.ai/api/v1",
      "api_key": "sk-...",
      "models": ["gpt-4.1", "gpt-4.1-mini"],
      "default_model": "gpt-4.1-mini",
      "options": { ... }
    }

    The shape is intentionally similar to what load_config() expects.
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    provider_id = body.get("id")
    if not provider_id:
        return web.json_response({"error": "Missing 'id' field"}, status=400)

    # We don't want to store 'id' inside the provider object itself
    provider_cfg_dict = dict(body)
    provider_cfg_dict.pop("id", None)

    try:
        root, providers_raw = _load_providers_file()
    except Exception as e:
        log.exception("[ComfyAI] Failed to load providers.json in add_provider")
        return web.json_response({"error": str(e)}, status=500)

    if provider_id in providers_raw:
        return web.json_response({"error": f"Provider '{provider_id}' already exists"}, status=400)

    providers_raw[provider_id] = provider_cfg_dict

    try:
        _save_providers_file(root)
    except Exception as e:
        log.exception("[ComfyAI] Failed to save providers.json in add_provider")
        return web.json_response({"error": str(e)}, status=500)

    _reload_provider_manager(request)

    return web.json_response({"status": "ok", "id": provider_id})


# ---------------------------------------------------------------------------
# POST /api/comfyai/providers/save
# ---------------------------------------------------------------------------

async def save_provider(request: web.Request) -> web.Response:
    """
    Update an existing provider's settings.

    Expected JSON:
    {
      "id": "openai",
      "updates": {
        "api_key": "sk-NEWKEY",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4.1-mini",
        "models": [ ... ]         # optional
      }
    }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    provider_id = body.get("id")
    updates: Dict[str, Any] = body.get("updates") or {}

    if not provider_id:
        return web.json_response({"error": "Missing 'id' field"}, status=400)

    try:
        root, providers_raw = _load_providers_file()
    except Exception as e:
        log.exception("[ComfyAI] Failed to load providers.json in save_provider")
        return web.json_response({"error": str(e)}, status=500)

    cfg = providers_raw.get(provider_id)
    if not isinstance(cfg, dict):
        return web.json_response({"error": f"Provider '{provider_id}' not found"}, status=404)

    # Shallow merge updates into existing provider dict
    for k, v in updates.items():
        cfg[k] = v

    try:
        _save_providers_file(root)
    except Exception as e:
        log.exception("[ComfyAI] Failed to save providers.json in save_provider")
        return web.json_response({"error": str(e)}, status=500)

    _reload_provider_manager(request)

    return web.json_response({"status": "ok"})


# ---------------------------------------------------------------------------
# DELETE /api/comfyai/providers/{id}
# ---------------------------------------------------------------------------

async def delete_provider(request: web.Request) -> web.Response:
    """
    Delete a provider from providers.json.

    DELETE /api/comfyai/providers/<id>
    """
    provider_id = request.match_info.get("provider_id")
    if not provider_id:
        return web.json_response({"error": "Missing provider id in URL"}, status=400)

    try:
        root, providers_raw = _load_providers_file()
    except Exception as e:
        log.exception("[ComfyAI] Failed to load providers.json in delete_provider")
        return web.json_response({"error": str(e)}, status=500)

    if provider_id not in providers_raw:
        return web.json_response({"error": f"Provider '{provider_id}' not found"}, status=404)

    del providers_raw[provider_id]

    try:
        _save_providers_file(root)
    except Exception as e:
        log.exception("[ComfyAI] Failed to save providers.json in delete_provider")
        return web.json_response({"error": str(e)}, status=500)

    _reload_provider_manager(request)

    return web.json_response({"status": "ok"})


# ---------------------------------------------------------------------------
# Public setup hook called from backend/router.py
# ---------------------------------------------------------------------------

def setup_provider_routes(app: web.Application) -> None:
    """
    Register all /api/comfyai/* routes on the given aiohttp app.
    """
    app.router.add_get("/api/comfyai/providers", list_providers)
    app.router.add_get("/api/comfyai/models", list_models)
    app.router.add_post("/api/comfyai/providers/add", add_provider)
    app.router.add_post("/api/comfyai/providers/save", save_provider)
    app.router.add_delete("/api/comfyai/providers/{provider_id}", delete_provider)

    log.info("[ROUTER] Registered /api/comfyai/* provider routes")
