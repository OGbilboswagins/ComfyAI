'''
Author: ai-business-hql qingli.hql@alibaba-inc.com
Date: 2025-07-14 16:46:20
LastEditors: ai-business-hql qingli.hql@alibaba-inc.com
LastEditTime: 2025-08-11 16:08:07
FilePath: /comfyui_copilot/backend/controller/llm_api.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
# Copyright (C) 2025 AIDC-AI
# Licensed under the MIT License.

import json
from typing import List, Dict, Any
from aiohttp import web
from ..utils.globals import LLM_DEFAULT_BASE_URL
import server
import requests

# LLM model configuration
# llm_config: List[Dict[str, Any]] = [
#     {
#         "label": "gemini-2.5-flash",
#         "name": "gemini-2.5-flash",
#         "image_enable": True
#     },
#     {
#         "label": "gpt-4.1-mini",
#         "name": "gpt-4.1-mini-2025-04-14-GlobalStandard",
#         "image_enable": True,
#     },
#     {
#         "label": "gpt-4.1",
#         "name": "gpt-4.1-2025-04-14-GlobalStandard",
#         "image_enable": True,
#     }
# ]


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
        openai_api_key = request.headers.get('Openai-Api-Key') or ""
        openai_base_url = request.headers.get('Openai-Base-Url') or LLM_DEFAULT_BASE_URL

        request_url = f"{openai_base_url}/models"
        
        headers = {
            "Authorization": f"Bearer {openai_api_key}"
        }
        
        response = requests.get(request_url, headers=headers)
        llm_config = []
        if response.status_code == 200:
            models = response.json()
            for model in models['data']:
                llm_config.append({
                    "label": model['id'],
                    "name": model['id'],
                    "image_enable": True
                })
        
        return web.json_response({
                "models": llm_config
            }
        )
        
    except Exception as e:
        print(f"Error in list_models: {str(e)}")
        return web.json_response({
            "error": f"Failed to list models: {str(e)}"
        }, status=500)
