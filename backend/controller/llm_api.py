'''
Author: ai-business-hql qingli.hql@alibaba-inc.com
Date: 2025-07-14 16:46:20
LastEditors: ai-business-hql qingli.hql@alibaba-inc.com
LastEditTime: 2025-07-14 20:04:08
FilePath: /comfyui_copilot/backend/controller/llm_api.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
# Copyright (C) 2025 AIDC-AI
# Licensed under the MIT License.

import json
from typing import List, Dict, Any
from aiohttp import web
import server

# LLM model configuration
llm_config: List[Dict[str, Any]] = [
    {
        "label": "gemini-2.5-flash",
        "name": "gemini-2.5-flash",
        "image_enable": True
    },
    {
        "label": "gpt-4.1",
        "name": "gpt-4.1-2025-04-14-GlobalStandard",
        "image_enable": True,
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
