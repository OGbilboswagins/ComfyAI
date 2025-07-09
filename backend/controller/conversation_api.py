# Copyright (C) 2025 AIDC-AI
# Licensed under the MIT License.

import json
import os
import asyncio
import time
from typing import Optional, Dict, Any, TypedDict, List, Union

import server
from aiohttp import web
import aiohttp
import base64
import requests

# Import the MCP client function
import sys
import os

from custom_nodes.comfyui_copilot.backend.service.debug_agent import debug_workflow_errors

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'service'))
try:
    # Try importing with underscore (Python module naming convention)
    from mcp_client import comfyui_agent_invoke, ImageData
except ImportError:
    try:
        # Try importing from actual filename mcp-client.py
        import importlib.util
        mcp_client_path = os.path.join(os.path.dirname(__file__), '..', 'service', 'mcp-client.py')
        spec = importlib.util.spec_from_file_location("mcp_client", mcp_client_path)
        mcp_client_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mcp_client_module)
        comfyui_agent_invoke = mcp_client_module.comfyui_agent_invoke
        ImageData = mcp_client_module.ImageData
    except Exception as e:
        print(f"Warning: Could not import comfyui_agent_invoke: {e}, using mock implementation")
        async def comfyui_agent_invoke(prompt, images=None, config=None):
            yield f"Mock response for: {prompt}"
        class ImageData:
            def __init__(self, filename: str, data: str, url: str = None):
                self.filename = filename
                self.data = data
                self.url = url


# 不再使用内存存储会话消息，改为从前端传递历史消息

# 在文件开头添加
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")

# Define types using TypedDict
class Node(TypedDict):
    name: str  # 节点名称
    description: str  # 节点描述
    image: str  # 节点图片url，可为空
    github_url: str  # 节点github地址
    from_index: int  # 节点在列表中的位置
    to_index: int  # 节点在列表中的位置

class NodeInfo(TypedDict):
    existing_nodes: List[Node]  # 已安装的节点
    missing_nodes: List[Node]  # 未安装的节点

class Workflow(TypedDict, total=False):
    id: Optional[int]  # 工作流id
    name: Optional[str]  # 工作流名称
    description: Optional[str]  # 工作流描述
    image: Optional[str]  # 工作流图片
    workflow: Optional[str]  # 工作流

class ExtItem(TypedDict):
    type: str  # 扩展类型
    data: Union[dict, list]  # 扩展数据

class ChatResponse(TypedDict):
    session_id: str  # 会话id
    text: Optional[str]  # 返回文本
    finished: bool  # 是否结束
    type: str  # 返回的类型
    format: str  # 返回的格式
    ext: Optional[List[ExtItem]]  # 扩展信息

def get_workflow_templates():
    templates = []
    workflows_dir = os.path.join(STATIC_DIR, "workflows")
    
    for filename in os.listdir(workflows_dir):
        if filename.endswith('.json'):
            with open(os.path.join(workflows_dir, filename), 'r') as f:
                template = json.load(f)
                templates.append(template)
    
    return templates


@server.PromptServer.instance.routes.post("/workspace/workflow_gen")
async def workflow_gen(request):
    print("Received workflow_gen request")
    req_json = await request.json()
    print("Request JSON:", req_json)

    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'application/json',
            'X-Content-Type-Options': 'nosniff'
        }
    )
    await response.prepare(request)

    session_id = req_json.get('session_id')
    user_message = req_json.get('message')

    # Create user message
    user_msg = {
        "id": str(len(session_messages.get(session_id, []))),
        "content": user_message,
        "role": "user"
    }

    if "workflow" in user_message.lower():
        workflow = {
            "name": "basic_image_gen",
            "description": "Create a basic image generation workflow",
            "image": "https://placehold.co/600x400",
            "workflow": """{ ... }"""  # Your workflow JSON here
        }

        chat_response = ChatResponse(
            session_id=session_id,
            text="",
            finished=False,
            type="workflow_option",
            format="text",
            ext=[{"type": "workflows", "data": [workflow]}]
        )

        await response.write(json.dumps(chat_response).encode() + b"\n")

        message = "Let me help you choose a workflow. Here are some options available:"
        accumulated = ""
        for char in message:
            accumulated += char
            chat_response["text"] = accumulated
            await response.write(json.dumps(chat_response).encode() + b"\n")
            await asyncio.sleep(0.01)

        chat_response["finished"] = True
        chat_response["text"] = message
        await response.write(json.dumps(chat_response).encode() + b"\n")

    elif "recommend" in user_message.lower():
        existing_nodes = [
            {
                "name": "LoraLoader",
                "description": "Load LoRA weights for conditioning.",
                "image": "",
                "github_url": "https://github.com/CompVis/taming-transformers",
                "from_index": 0,
                "to_index": 0
            },
            {
                "name": "KSampler",
                "description": "Generate images using K-diffusion sampling.",
                "image": "",
                "github_url": "https://github.com/CompVis/taming-transformers",
                "from_index": 0,
                "to_index": 0
            }
        ]

        missing_nodes = [
            {
                "name": "CLIPTextEncode",
                "description": "Encode text prompts for conditioning.",
                "image": "",
                "github_url": "https://github.com/CompVis/clip-interrogator",
                "from_index": 0,
                "to_index": 0
            }
        ]

        node_info = {
            "existing_nodes": existing_nodes,
            "missing_nodes": missing_nodes
        }

        chat_response = ChatResponse(
            session_id=session_id,
            text="",
            finished=False,
            type="downstream_node_recommend",
            format="text",
            ext=[{"type": "node_info", "data": node_info}]
        )

        await response.write(json.dumps(chat_response).encode() + b"\n")

        message = "Here are some recommended nodes:"
        accumulated = ""
        for char in message:
            accumulated += char
            chat_response["text"] = accumulated
            await response.write(json.dumps(chat_response).encode() + b"\n")
            await asyncio.sleep(0.01)

        chat_response["finished"] = True
        chat_response["text"] = message
        await response.write(json.dumps(chat_response).encode() + b"\n")

    else:
        chat_response = ChatResponse(
            session_id=session_id,
            text="",
            finished=False,
            type="message",
            format="text",
            ext=[{"type": "guides", "data": ["Create a workflow", "Search for nodes", "Get node recommendations"]}]
        )

        await response.write(json.dumps(chat_response).encode() + b"\n")

        message = "I can help you with workflows, nodes, and more. Try asking about:"
        accumulated = ""
        for char in message:
            accumulated += char
            chat_response["text"] = accumulated
            await response.write(json.dumps(chat_response).encode() + b"\n")
            await asyncio.sleep(0.01)

        chat_response["finished"] = True
        chat_response["text"] = message
        await response.write(json.dumps(chat_response).encode() + b"\n")

    # 不再使用内存存储，前端负责消息存储

    await response.write_eof()
    return response

# 删除fetch_messages相关方法，消息由前端IndexedDB管理

async def upload_to_oss(file_data: bytes, filename: str) -> str:
    # TODO: Implement your OSS upload logic here
    # For now, save locally and return a placeholder URL
    
    try:
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Generate unique filename to avoid conflicts
        import uuid
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(uploads_dir, unique_filename)
        
        # Save file locally
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # Return a local URL or base64 data URL for now
        # In production, replace this with actual OSS URL
        base64_data = base64.b64encode(file_data).decode('utf-8')
        # Determine MIME type based on file extension
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            mime_type = f"image/{filename.split('.')[-1].lower()}"
            if mime_type == "image/jpg":
                mime_type = "image/jpeg"
        else:
            mime_type = "image/jpeg"  # Default
            
        return f"data:{mime_type};base64,{base64_data}"
        
    except Exception as e:
        print(f"Error uploading file {filename}: {str(e)}")
        # Return original base64 data if upload fails
        base64_data = base64.b64encode(file_data).decode('utf-8')
        return f"data:image/jpeg;base64,{base64_data}"


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
            print(f"API key validation failed with status code: {response.status_code}")
            return web.json_response({
                "success": False, 
                "data": False,
                "message": f"Invalid API key: HTTP {response.status_code} - {response.text}"
            })
            
    except Exception as e:
        print(f"Error verifying OpenAI API key: {str(e)}")
        return web.json_response({
            "success": False, 
            "data": False, 
            "message": f"Invalid API key: {str(e)}"
        })

@server.PromptServer.instance.routes.post("/api/chat/invoke")
async def invoke_chat(request):
    print("Received invoke_chat request")
    req_json = await request.json()
    print("Request JSON:", req_json)

    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'application/json',
            'X-Content-Type-Options': 'nosniff'
        }
    )
    await response.prepare(request)

    session_id = req_json.get('session_id')
    prompt = req_json.get('prompt')
    images = req_json.get('images', [])
    intent = req_json.get('intent')
    ext = req_json.get('ext')
    historical_messages = req_json.get('messages', [])

    # Process images and upload to OSS (similar to reference implementation)
    processed_images = []
    if images and len(images) > 0:
        print(f"Processing {len(images)} images")
        for image in images:
            try:
                filename = image.get('filename', 'uploaded_image.jpg')
                image_data = image.get('data', '')
                
                # Extract base64 data after the comma if it's a data URL
                if image_data.startswith('data:'):
                    image_data = image_data.split(',')[1]
                
                # Decode base64 and upload to OSS
                image_bytes = base64.b64decode(image_data.encode('utf-8'))
                image_url = await upload_to_oss(image_bytes, filename)
                
                # Create ImageData object similar to reference implementation
                processed_image = ImageData(
                    filename=filename,
                    data=f"data:image/jpeg;base64,{image_data}",  # Keep original base64 for fallback
                    url=image_url
                )
                processed_images.append(processed_image)
                print(f"Processed image: {filename} -> {image_url}")
                
            except Exception as e:
                print(f"Error processing image {image.get('filename', 'unknown')}: {str(e)}")
                # Continue with other images even if one fails

    # 历史消息已经从前端传递过来，格式为OpenAI格式，直接使用
    print(f"-- Received {len(historical_messages)} historical messages")
    
    # Add current user message to OpenAI format
    current_user_message = {"role": "user", "content": prompt}
    
    # For current message with images, format according to OpenAI multimodal format
    if processed_images and len(processed_images) > 0:
        content = [{"type": "text", "text": prompt}]
        for image in processed_images:
            # Use image URL if available (uploaded to OSS), otherwise use base64 data
            image_url = image.url if image.url else image.data
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })
        current_user_message["content"] = content
    
    # Add current message to historical messages for MCP call
    openai_messages = historical_messages + [current_user_message]
    
    # 不再需要创建用户消息存储到后端，前端负责消息存储

    try:
        # Call the MCP client to get streaming response with historical messages and image support
        # Pass OpenAI-formatted messages and processed images to comfyui_agent_invoke
        accumulated_text = ""
        ext_data = None
        has_sent_response = False
        previous_text_length = 0
        
        config = {
            "openai_api_key": request.headers.get('Openai-Api-Key'),
            "openai_base_url": request.headers.get('Openai-Base-Url'),
            "model_select": next((x['data'][0] for x in ext if x['type'] == 'model_select' and x.get('data')), None)
        }
        print(f"config: {config}")
        
        # Pass messages in OpenAI format and processed images to comfyui_agent_invoke
        async for result in comfyui_agent_invoke(openai_messages, processed_images if processed_images else None, config):
            # The MCP client now returns tuples (text, ext) similar to facade.py
            if isinstance(result, tuple) and len(result) == 2:
                text, ext = result
                if text:
                    accumulated_text = text  # text from MCP is already accumulated
                    print(f"-- Received text update, length: {len(accumulated_text)}")
                if ext:
                    ext_data = ext
                    print(f"-- Received ext data: {ext_data}")
            else:
                # Handle single text chunk (backward compatibility)
                text_chunk = result
                if text_chunk:
                    accumulated_text += text_chunk
                    print(f"-- Received text chunk: '{text_chunk}', total length: {len(accumulated_text)}")
            
            # Send streaming response if we have new text content
            # Send every time we get new text, regardless of ext_data status
            if accumulated_text and len(accumulated_text) > previous_text_length:
                print(f"-- Sending stream response: {len(accumulated_text)} chars (previous: {previous_text_length})")
                chat_response = ChatResponse(
                    session_id=session_id,
                    text=accumulated_text,
                    finished=False,
                    type="message",
                    format="markdown",
                    ext=None  # ext is only sent in final response
                )
                
                await response.write(json.dumps(chat_response).encode() + b"\n")
                previous_text_length = len(accumulated_text)
                await asyncio.sleep(0.01)  # Small delay for streaming effect

        # Send final response with ext data (similar to facade.py final yield)
        print(f"-- Sending final response: {len(accumulated_text)} chars, ext: {bool(ext_data)}")
        final_response = ChatResponse(
            session_id=session_id,
            text=accumulated_text,
            finished=True,
            type="message",
            format="markdown",
            ext=ext_data
        )
        
        await response.write(json.dumps(final_response).encode() + b"\n")

        # AI响应不再存储到后端，前端负责消息存储

    except Exception as e:
        print(f"Error in invoke_chat: {str(e)}")
        error_response = ChatResponse(
            session_id=session_id,
            text=f"I apologize, but an error occurred: {str(e)}",
            finished=True,
            type="message",
            format="text",
            ext=None
        )
        await response.write(json.dumps(error_response).encode() + b"\n")

    await response.write_eof()
    return response


@server.PromptServer.instance.routes.post("/api/debug-agent")
async def debug_agent_endpoint(request):
    """
    Debug agent endpoint for analyzing ComfyUI workflow errors
    """
    print("Received debug-agent request")
    req_json = await request.json()
    
    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'application/json',
            'X-Content-Type-Options': 'nosniff'
        }
    )
    await response.prepare(request)

    session_id = req_json.get('session_id')
    workflow_data = req_json.get('workflow_data')
    
    # Get configuration from headers (OpenAI settings)
    config = {
        "session_id": session_id,
        "model": "gemini-2.5-flash",  # Default model for debug agents
        "openai_api_key": request.headers.get('Openai-Api-Key'),
        "openai_base_url": request.headers.get('Openai-Base-Url', 'https://api.openai.com/v1'),
    }
    
    print(f"Debug agent config: {config}")
    print(f"Session ID: {session_id}")
    print(f"Workflow nodes: {list(workflow_data.keys()) if workflow_data else 'None'}")

    try:
        # Call the debug agent with streaming response
        accumulated_text = ""
        final_ext_data = None
        
        async for result in debug_workflow_errors(workflow_data, config):
            # Stream the response
            if isinstance(result, tuple) and len(result) == 2:
                text, ext = result
                if text:
                    accumulated_text = text  # text is already accumulated from debug agent
                if ext:
                    final_ext_data = ext
                
                # Create streaming response
                chat_response = ChatResponse(
                    session_id=session_id,
                    text=accumulated_text,
                    finished=False,
                    type="debug",
                    format="markdown",
                    ext=ext
                )
                
                await response.write(json.dumps(chat_response).encode() + b"\n")
                await asyncio.sleep(0.01)  # Small delay for streaming effect

        # Send final response
        final_response = ChatResponse(
            session_id=session_id,
            text=accumulated_text,
            finished=True,
            type="debug",
            format="markdown",
            ext=final_ext_data if final_ext_data else [{"type": "debug_complete", "data": {"status": "completed"}}]
        )
        
        await response.write(json.dumps(final_response).encode() + b"\n")
        print("Debug agent processing complete")

    except Exception as e:
        print(f"Error in debug agent: {str(e)}")
        import traceback
        traceback.print_exc()
        
        error_response = ChatResponse(
            session_id=session_id,
            text=f"❌ Debug agent error: {str(e)}",
            finished=True,
            type="debug",
            format="text",
            ext=[{"type": "error", "data": {"error": str(e)}}]
        )
        await response.write(json.dumps(error_response).encode() + b"\n")

    await response.write_eof()
    return response
