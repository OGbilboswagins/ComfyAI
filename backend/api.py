import os
import json
from aiohttp import web

routes = web.RouteTableDef()

@routes.get("/comfyai/providers")
async def get_comfyai_providers(request):
    try:
        # Determine the root directory of ComfyUI-ComfyAI (this plugin)
        # This assumes the plugin is located at COMFYUI_ROOT/custom_nodes/ComfyUI-ComfyAI
        plugin_root = os.path.dirname(os.path.abspath(__file__))
        # Navigate up to the ComfyUI root
        # custom_nodes/ComfyUI-ComfyAI -> custom_nodes -> COMFYUI_ROOT
        comfyui_root = os.path.abspath(os.path.join(plugin_root, "../../"))

        # Construct the path to providers.json
        # COMFYUI_ROOT/user/default/ComfyUI-ComfyAI/providers.json
        providers_json_path = os.path.join(comfyui_root, "user", "default", "ComfyUI-ComfyAI", "providers.json")

        if not os.path.exists(providers_json_path):
            raise FileNotFoundError(f"providers.json not found at {providers_json_path}")

        with open(providers_json_path, "r") as f:
            providers_data = json.load(f)

        return web.json_response(providers_data)
    except FileNotFoundError as e:
        return web.json_response({"error": str(e)}, status=404)
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON in providers.json"}, status=500)
    except Exception as e:
        return web.json_response({"error": f"An unexpected error occurred: {e}"}, status=500)

def setup(app):
    app.add_routes(routes)
    print("[ComfyAI] Frontend API routes registered")
