# Copyright (C) 2025 AIDC-AI
# Licensed under the MIT License.

import json
from typing import List, Dict, Any
from aiohttp import web
import server

# LLM model configuration
llm_config: List[Dict[str, Any]] = [
    {
        "label": "gpt-4.1",
        "name": "gpt-4.1-2025-04-14-GlobalStandard",
        "image_enable": True,
    },
    {
        "label": "gpt-4o-mini",
        "name": "gpt-4o-mini",
        "image_enable": True,
    },
    {
        "label": "gemini-2.5-flash", 
        "name": "gemini-2.5-flash-preview-04-17", 
        "image_enable": True
    },
    {
        "label": "qwen-plus",
        "name": "qwen-plus",
        "image_enable": False,
    }
]


@server.PromptServer.instance.routes.get("/api/model_config")
async def list_models(request):
    """
    List available LLM models
    
    Returns:
        JSON response with models list in the format expected by frontend:
        {
            "models": [
                {"name": "model_name", "image_enable": boolean},
                ...
            ]
        }
    """
    try:
        print("Received list_models request")
        
        # Return the models in the expected format
        response_data = {
            "models": llm_config
        }
        
        return web.json_response(response_data)
        
    except Exception as e:
        print(f"Error in list_models: {str(e)}")
        return web.json_response({
            "error": f"Failed to list models: {str(e)}"
        }, status=500)
