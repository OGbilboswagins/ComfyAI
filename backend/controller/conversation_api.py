# Copyright (C) 2025 AIDC-AI
# Licensed under the MIT License.

import json
import os
import asyncio
import time
from typing import Optional, Dict, Any, TypedDict, List, Union

from ..utils.globals import set_language
from ..utils.auth_utils import extract_and_store_api_key
import server
from aiohttp import web
import aiohttp
import base64
import requests

# Import the MCP client function
import sys
import os

from ..service.debug_agent import debug_workflow_errors
from ..service.database import save_workflow_data, get_workflow_data_by_id, update_workflow_ui_by_id
from ..service.mcp_client import comfyui_agent_invoke, ImageData


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
    
    # Extract and store API key from Authorization header
    extract_and_store_api_key(request)
    
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
    workflow_checkpoint_id = req_json.get('workflow_checkpoint_id')
    
    # 获取当前语言
    language = request.headers.get('Accept-Language', 'en')
    set_language(language)

    # 图片处理已移至前端，图片信息现在包含在历史消息的OpenAI格式中
    # 保留空的处理逻辑以向后兼容，但实际不再使用
    processed_images = []
    if images and len(images) > 0:
        print(f"Note: Received {len(images)} images in legacy format, but using OpenAI message format instead")

    # 历史消息已经从前端传递过来，格式为OpenAI格式，直接使用
    print(f"-- Received {len(historical_messages)} historical messages")
    
    # Log workflow checkpoint ID if provided (workflow is now pre-saved before invoke)
    if workflow_checkpoint_id:
        print(f"Using workflow checkpoint ID: {workflow_checkpoint_id} for session {session_id}")
    else:
        print(f"No workflow checkpoint ID provided for session {session_id}")

    # 历史消息已经从前端传递过来，包含了正确格式的OpenAI消息（包括图片）
    # 直接使用前端传递的历史消息，无需重新构建当前消息
    openai_messages = historical_messages
    
    # 不再需要创建用户消息存储到后端，前端负责消息存储

    try:
        # Call the MCP client to get streaming response with historical messages and image support
        # Pass OpenAI-formatted messages and processed images to comfyui_agent_invoke
        accumulated_text = ""
        ext_data = None
        finished = True  # Default to True
        has_sent_response = False
        previous_text_length = 0
        
        config = {
            "session_id": session_id,  # 添加session_id到配置中
            "workflow_checkpoint_id": workflow_checkpoint_id,  # 添加工作流检查点ID
            "openai_api_key": request.headers.get('Openai-Api-Key'),
            "openai_base_url": request.headers.get('Openai-Base-Url'),
            "model_select": next((x['data'][0] for x in ext if x['type'] == 'model_select' and x.get('data')), None)
        }
        print(f"config: {config}")
        
        # Pass messages in OpenAI format (images are now included in messages)
        async for result in comfyui_agent_invoke(openai_messages, None, config):
            # The MCP client now returns tuples (text, ext_with_finished) where ext_with_finished includes finished status
            if isinstance(result, tuple) and len(result) == 2:
                text, ext_with_finished = result
                if text:
                    accumulated_text = text  # text from MCP is already accumulated
                    print(f"-- Received text update, length: {len(accumulated_text)}")
                if ext_with_finished:
                    # Extract ext data and finished status from the structured response
                    ext_data = ext_with_finished.get("data")
                    finished = ext_with_finished.get("finished", True)
                    print(f"-- Received ext data: {ext_data}, finished: {finished}")
            else:
                # Handle single text chunk (backward compatibility)
                text_chunk = result
                if text_chunk:
                    accumulated_text += text_chunk
                    print(f"-- Received text chunk: '{text_chunk}', total length: {len(accumulated_text)}")
            
            # Send streaming response if we have new text content
            # Only send intermediate responses during streaming (not the final one)
            if accumulated_text and len(accumulated_text) > previous_text_length:
                print(f"-- Sending stream response: {len(accumulated_text)} chars (previous: {previous_text_length})")
                chat_response = ChatResponse(
                    session_id=session_id,
                    text=accumulated_text,
                    finished=False,  # Always false during streaming
                    type="message",
                    format="markdown",
                    ext=None  # ext is only sent in final response
                )
                
                await response.write(json.dumps(chat_response).encode() + b"\n")
                previous_text_length = len(accumulated_text)
                await asyncio.sleep(0.01)  # Small delay for streaming effect

        # Send final response with proper finished logic from MCP client
        print(f"-- Sending final response: {len(accumulated_text)} chars, ext: {bool(ext_data)}, finished: {finished}")
        
        final_response = ChatResponse(
            session_id=session_id,
            text=accumulated_text,
            finished=finished,  # Use finished status from MCP client
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
            finished=True,  # Always finish on error
            type="message",
            format="text",
            ext=None
        )
        await response.write(json.dumps(error_response).encode() + b"\n")

    await response.write_eof()
    return response


@server.PromptServer.instance.routes.post("/api/save-workflow-checkpoint")
async def save_workflow_checkpoint(request):
    """
    Save workflow checkpoint for restore functionality
    """
    print("Received save-workflow-checkpoint request")
    req_json = await request.json()
    
    try:
        session_id = req_json.get('session_id')
        workflow_api = req_json.get('workflow_api')  # API format workflow
        workflow_ui = req_json.get('workflow_ui')    # UI format workflow  
        checkpoint_type = req_json.get('checkpoint_type', 'debug_start')  # debug_start, debug_complete, user_message_checkpoint
        message_id = req_json.get('message_id')      # User message ID for linking (optional)
        
        if not session_id or not workflow_api:
            return web.json_response({
                "success": False,
                "message": "Missing required parameters: session_id and workflow_api"
            })
        
        # Save workflow with checkpoint type in attributes
        attributes = {
            "checkpoint_type": checkpoint_type,
            "timestamp": time.time()
        }
        
        # Set description and additional attributes based on checkpoint type
        if checkpoint_type == "user_message_checkpoint" and message_id:
            attributes.update({
                "description": f"Workflow checkpoint before user message {message_id}",
                "message_id": message_id,
                "source": "user_message_pre_invoke"
            })
        else:
            attributes["description"] = f"Workflow checkpoint: {checkpoint_type}"
        
        version_id = save_workflow_data(
            session_id=session_id,
            workflow_data=workflow_api,
            workflow_data_ui=workflow_ui,
            attributes=attributes
        )
        
        print(f"Workflow checkpoint saved with version ID: {version_id}")
        
        # Return response format based on checkpoint type
        response_data = {
            "version_id": version_id,
            "checkpoint_type": checkpoint_type
        }
        
        if checkpoint_type == "user_message_checkpoint" and message_id:
            response_data.update({
                "checkpoint_id": version_id,  # Add checkpoint_id alias for user message checkpoints
                "message_id": message_id
            })
        
        return web.json_response({
            "success": True,
            "data": response_data,
            "message": f"Workflow checkpoint saved successfully"
        })
        
    except Exception as e:
        print(f"Error saving workflow checkpoint: {str(e)}")
        return web.json_response({
            "success": False,
            "message": f"Failed to save workflow checkpoint: {str(e)}"
        })



@server.PromptServer.instance.routes.get("/api/restore-workflow-checkpoint")
async def restore_workflow_checkpoint(request):
    """
    Restore workflow checkpoint by version ID
    """
    print("Received restore-workflow-checkpoint request")
    
    try:
        version_id = request.query.get('version_id')
        
        if not version_id:
            return web.json_response({
                "success": False,
                "message": "Missing required parameter: version_id"
            })
        
        try:
            version_id = int(version_id)
        except ValueError:
            return web.json_response({
                "success": False,
                "message": "Invalid version_id format"
            })
        
        # Get workflow data by version ID
        workflow_version = get_workflow_data_by_id(version_id)
        
        if not workflow_version:
            return web.json_response({
                "success": False,
                "message": f"Workflow version {version_id} not found"
            })
        
        print(f"Restored workflow checkpoint version ID: {version_id}")
        
        return web.json_response({
            "success": True,
            "data": {
                "version_id": version_id,
                "workflow_data": workflow_version.get('workflow_data'),
                "workflow_data_ui": workflow_version.get('workflow_data_ui'),
                "attributes": workflow_version.get('attributes'),
                "created_at": workflow_version.get('created_at')
            },
            "message": f"Workflow checkpoint restored successfully"
        })
        
    except Exception as e:
        print(f"Error restoring workflow checkpoint: {str(e)}")
        return web.json_response({
            "success": False,
            "message": f"Failed to restore workflow checkpoint: {str(e)}"
        })


@server.PromptServer.instance.routes.post("/api/debug-agent")
async def invoke_debug(request):
    """
    Debug agent endpoint for analyzing ComfyUI workflow errors
    """
    print("Received debug-agent request")
    
    # Extract and store API key from Authorization header
    extract_and_store_api_key(request)
    
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

    # 获取当前语言
    language = request.headers.get('Accept-Language', 'en')
    set_language(language)
    
    print(f"Debug agent config: {config}")
    print(f"Session ID: {session_id}")
    print(f"Workflow nodes: {list(workflow_data.keys()) if workflow_data else 'None'}")

    try:
        # Call the debug agent with streaming response
        accumulated_text = ""
        final_ext_data = None
        finished = False
        
        async for result in debug_workflow_errors(workflow_data, config):
            # Stream the response
            if isinstance(result, tuple) and len(result) == 2:
                text, ext = result
                if text:
                    accumulated_text = text  # text is already accumulated from debug agent
                
                # Handle new ext format from debug_agent matching mcp-client
                if ext:
                    if isinstance(ext, dict) and "data" in ext and "finished" in ext:
                        # New format: {"data": ext, "finished": finished}
                        final_ext_data = ext["data"]
                        finished = ext["finished"]
                        
                        # 检查是否包含需要实时发送的workflow_update或param_update
                        has_realtime_ext = False
                        if final_ext_data:
                            for ext_item in final_ext_data:
                                if ext_item.get("type") in ["workflow_update", "param_update"]:
                                    has_realtime_ext = True
                                    break
                        
                        # 如果包含实时ext数据或者已完成，则发送响应
                        if has_realtime_ext or finished:
                            chat_response = ChatResponse(
                                session_id=session_id,
                                text=accumulated_text,
                                finished=finished,
                                type="message",
                                format="markdown",
                                ext=final_ext_data  # 发送ext数据
                            )
                            await response.write(json.dumps(chat_response).encode() + b"\n")
                        elif not finished:
                            # 只有文本更新，不发送ext数据
                            chat_response = ChatResponse(
                                session_id=session_id,
                                text=accumulated_text,
                                finished=False,
                                type="message",
                                format="markdown",
                                ext=None
                            )
                            await response.write(json.dumps(chat_response).encode() + b"\n")
                    else:
                        # Legacy format: direct ext data (for backward compatibility)
                        final_ext_data = ext
                        finished = False
                        
                        # Create streaming response
                        chat_response = ChatResponse(
                            session_id=session_id,
                            text=accumulated_text,
                            finished=False,
                            type="message",
                            format="markdown",
                            ext=ext
                        )
                        await response.write(json.dumps(chat_response).encode() + b"\n")
                else:
                    # No ext data, just text streaming
                    chat_response = ChatResponse(
                        session_id=session_id,
                        text=accumulated_text,
                        finished=False,
                        type="message",
                        format="markdown",
                        ext=None
                    )
                    await response.write(json.dumps(chat_response).encode() + b"\n")
                
                await asyncio.sleep(0.01)  # Small delay for streaming effect

        # Send final response
        final_response = ChatResponse(
            session_id=session_id,
            text=accumulated_text,
            finished=True,
            type="message",
            format="markdown",
            ext=final_ext_data if final_ext_data else [{"type": "debug_complete", "data": {"status": "completed"}}]
        )
        
        # Save workflow checkpoint after debug completion if we have workflow_data
        if workflow_data and accumulated_text:
            try:
                checkpoint_id = save_workflow_data(
                    session_id=session_id,
                    workflow_data=workflow_data,
                    workflow_data_ui=None,  # UI format not available in debug agent
                    attributes={
                        "checkpoint_type": "debug_complete",
                        "description": "Workflow state after debug completion",
                        "timestamp": time.time()
                    }
                )
                
                # Add checkpoint info to ext data
                if final_response["ext"]:
                    final_response["ext"].append({
                        "type": "debug_checkpoint",
                        "data": {
                            "checkpoint_id": checkpoint_id,
                            "checkpoint_type": "debug_complete"
                        }
                    })
                else:
                    final_response["ext"] = [{
                        "type": "debug_checkpoint",
                        "data": {
                            "checkpoint_id": checkpoint_id,
                            "checkpoint_type": "debug_complete"
                        }
                    }]
                
                print(f"Debug completion checkpoint saved with ID: {checkpoint_id}")
            except Exception as checkpoint_error:
                print(f"Failed to save debug completion checkpoint: {checkpoint_error}")
        
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
            type="message",
            format="text",
            ext=[{"type": "error", "data": {"error": str(e)}}]
        )
        await response.write(json.dumps(error_response).encode() + b"\n")

    await response.write_eof()
    return response


@server.PromptServer.instance.routes.post("/api/update-workflow-ui")
async def update_workflow_ui(request):
    """
    Update workflow_data_ui field for a specific checkpoint without affecting other fields
    """
    print("Received update-workflow-ui request")
    req_json = await request.json()
    
    try:
        checkpoint_id = req_json.get('checkpoint_id')
        workflow_data_ui = req_json.get('workflow_data_ui')
        
        if not checkpoint_id or not workflow_data_ui:
            return web.json_response({
                "success": False,
                "message": "Missing required parameters: checkpoint_id and workflow_data_ui"
            })
        
        try:
            checkpoint_id = int(checkpoint_id)
        except ValueError:
            return web.json_response({
                "success": False,
                "message": "Invalid checkpoint_id format"
            })
        
        # Update only the workflow_data_ui field
        success = update_workflow_ui_by_id(checkpoint_id, workflow_data_ui)
        
        if success:
            print(f"Successfully updated workflow_data_ui for checkpoint ID: {checkpoint_id}")
            return web.json_response({
                "success": True,
                "message": f"Workflow UI data updated successfully for checkpoint {checkpoint_id}"
            })
        else:
            return web.json_response({
                "success": False,
                "message": f"Checkpoint {checkpoint_id} not found"
            })
        
    except Exception as e:
        print(f"Error updating workflow UI data: {str(e)}")
        return web.json_response({
            "success": False,
            "message": f"Failed to update workflow UI data: {str(e)}"
        })
