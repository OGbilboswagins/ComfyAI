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
from ..utils.logger import log


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
        log.info("Received list_models request")
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
        log.error(f"Error in list_models: {str(e)}")
        return web.json_response({
            "error": f"Failed to list models: {str(e)}"
        }, status=500)


@server.PromptServer.instance.routes.get("/verify_openai_key")
async def verify_openai_key(req):
    """
    Verify if an OpenAI API key is valid by calling the OpenAI models endpoint
    
    Returns:
        JSON response with success status and message
    """
    try:
        openai_api_key = req.headers.get('Openai-Api-Key')
        openai_base_url = req.headers.get('Openai-Base-Url', 'https://api.openai.com/v1')
        
        if not openai_api_key:
            return web.json_response({
                "success": False, 
                "message": "No API key provided"
            })
        
        # Use a direct HTTP request instead of the OpenAI client
        # This gives us more control over the request method and error handling
        headers = {
            "Authorization": f"Bearer {openai_api_key}"
        }
        
        # Make a simple GET request to the models endpoint
        response = requests.get(f"{openai_base_url}/models", headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            return web.json_response({
                "success": True, 
                "data": True, 
                "message": "API key is valid"
            })
        else:
            log.error(f"API key validation failed with status code: {response.status_code}")
            return web.json_response({
                "success": False, 
                "data": False,
                "message": f"Invalid API key: HTTP {response.status_code} - {response.text}"
            })
            
    except Exception as e:
        log.error(f"Error verifying OpenAI API key: {str(e)}")
        return web.json_response({
            "success": False, 
            "data": False, 
            "message": f"Invalid API key: {str(e)}"
        })