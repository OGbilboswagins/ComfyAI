import json
from typing import Dict, Any, List, Optional
import os
import glob
from pathlib import Path

from agents.agent import Agent
from agents.tool import function_tool

from custom_nodes.comfyui_copilot.backend.utils.comfy_gateway import get_object_info, get_object_info_by_class
from custom_nodes.comfyui_copilot.backend.service.database import get_workflow_data, save_workflow_data

@function_tool
def get_node_parameters(node_name: str, param_name: str = "") -> str:
    """获取节点的参数信息，如果param_name为空则返回所有参数"""
    try:
        node_info_dict = get_object_info_by_class(node_name)
        if not node_info_dict or node_name not in node_info_dict:
            return json.dumps({"error": f"Node '{node_name}' not found"})
        
        node_info = node_info_dict[node_name]
        if 'input' not in node_info:
            return json.dumps({"error": f"Node '{node_name}' has no input parameters"})
        
        input_params = node_info['input']
        
        if param_name:
            # 检查特定参数
            if input_params.get('required') and param_name in input_params['required']:
                return json.dumps({
                    "parameter": param_name,
                    "type": "required",
                    "config": input_params['required'][param_name]
                })
            
            if input_params.get('optional') and param_name in input_params['optional']:
                return json.dumps({
                    "parameter": param_name,
                    "type": "optional", 
                    "config": input_params['optional'][param_name]
                })
            
            return json.dumps({"error": f"Parameter '{param_name}' not found in node '{node_name}'"})
        else:
            # 返回所有参数
            return json.dumps({
                "node": node_name,
                "required": input_params.get('required', {}),
                "optional": input_params.get('optional', {})
            })
    
    except Exception as e:
        return json.dumps({"error": f"Failed to get node parameters: {str(e)}"})

@function_tool
def find_matching_parameter_value(node_name: str, param_name: str, current_value: str, error_info: str = "") -> str:
    """根据错误信息找到匹配的参数值"""
    try:
        # 获取参数配置
        param_info_str = get_node_parameters(node_name, param_name)
        param_info = json.loads(param_info_str)
        
        if "error" in param_info:
            return json.dumps(param_info)
        
        param_config = param_info.get("config", [])
        
        # 如果参数配置是列表，说明有固定的可选值
        if isinstance(param_config, list) and len(param_config) > 0:
            available_values = param_config
            
            # 改进的匹配算法
            current_lower = current_value.lower().replace("_", " ").replace("-", " ")
            
            # 1. 完全匹配
            for value in available_values:
                if current_value == value:
                    return json.dumps({
                        "found_match": True,
                        "recommended_value": value,
                        "match_type": "exact",
                        "all_available": available_values
                    })
            
            # 2. 忽略大小写和符号的匹配
            for value in available_values:
                value_lower = str(value).lower().replace("_", " ").replace("-", " ")
                if current_lower == value_lower:
                    return json.dumps({
                        "found_match": True,
                        "recommended_value": value,
                        "match_type": "case_insensitive",
                        "all_available": available_values
                    })
            
            # 3. 包含关系匹配
            best_match = None
            best_score = 0
            
            for value in available_values:
                value_lower = str(value).lower()
                value_parts = value_lower.replace("_", " ").replace("-", " ").split()
                current_parts = current_lower.split()
                
                # 计算匹配分数
                score = 0
                for part in current_parts:
                    if any(part in vp or vp in part for vp in value_parts):
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_match = value
            
            if best_match and best_score > 0:
                return json.dumps({
                    "found_match": True,
                    "recommended_value": best_match,
                    "match_type": "partial",
                    "match_score": best_score,
                    "all_available": available_values[:10],  # 只返回前10个选项
                    "original_value": current_value
                })
            
            # 4. 如果都没有匹配，返回所有可用选项
            return json.dumps({
                "found_match": False,
                "recommended_value": available_values[0] if available_values else None,
                "match_type": "no_match",
                "all_available": available_values[:10],  # 只返回前10个选项
                "total_options": len(available_values),
                "original_value": current_value,
                "suggestion": f"No match found for '{current_value}'. Please choose from available options."
            })
        
        # 如果不是列表类型的参数，返回参数信息
        return json.dumps({
            "found_match": False,
            "parameter_type": type(param_config).__name__,
            "config": param_config,
            "suggestion": f"Parameter '{param_name}' is not a list type, cannot provide specific recommendations"
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to find matching parameter value: {str(e)}"})

@function_tool
def get_model_files(model_type: str = "checkpoints") -> str:
    """获取可用的模型文件列表"""
    try:
        # 获取所有节点信息
        object_info = get_object_info()
        
        # 定义模型类型到节点的映射
        model_type_mapping = {
            "checkpoints": ["CheckpointLoaderSimple", "CheckpointLoader"],
            "loras": ["LoraLoader", "LoraLoaderModelOnly"],
            "vae": ["VAELoader"],
            "clip": ["CLIPLoader", "DualCLIPLoader"],
            "controlnet": ["ControlNetLoader", "ControlNetApply"],
            "unet": ["UNETLoader"],
            "ipadapter": ["IPAdapterModelLoader"]
        }
        
        # 查找对应的节点
        model_files = {}
        for node_name in model_type_mapping.get(model_type.lower(), []):
            if node_name in object_info:
                node_info = object_info[node_name]
                if 'input' in node_info:
                    # 查找包含文件列表的参数
                    for input_type in ['required', 'optional']:
                        if input_type in node_info['input']:
                            for param_name, param_config in node_info['input'][input_type].items():
                                if isinstance(param_config, tuple) and isinstance(param_config[0], list) and len(param_config[0]) > 0:
                                    model_files[f"{node_name}.{param_name}"] = param_config[0]
        
        if model_files:
            return json.dumps({
                "model_type": model_type,
                "available_models": model_files
            })
        else:
            return json.dumps({
                "model_type": model_type,
                "available_models": {},
                "message": f"No {model_type} models found. Please check your ComfyUI models folder."
            })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to get model files: {str(e)}"})

@function_tool
def suggest_model_download(model_type: str, missing_model: str) -> str:
    """建议下载缺失的模型，执行一次即可结束流程返回结果"""
    try:
        # 尝试从缺失的模型名称推断模型类型
        model_name_lower = missing_model.lower()
        detected_type = model_type.lower()
        
        # 自动检测模型类型
        if "checkpoint" in model_name_lower or "ckpt" in model_name_lower or ".safetensors" in model_name_lower:
            detected_type = "checkpoint"
        elif "lora" in model_name_lower:
            detected_type = "lora"
        elif "controlnet" in model_name_lower or "control" in model_name_lower:
            detected_type = "controlnet"
        elif "vae" in model_name_lower:
            detected_type = "vae"
        elif "clip" in model_name_lower:
            detected_type = "clip"
        elif "unet" in model_name_lower:
            detected_type = "unet"
        elif "ipadapter" in model_name_lower or "ip-adapter" in model_name_lower:
            detected_type = "ipadapter"
        else:
            detected_type = "checkpoint"
        
        suggestions = {
            "checkpoint": {
                "message": f"Missing checkpoint model: {missing_model}",
                "folder": "ComfyUI/models/checkpoints/",
                "suggestions": [
                    "1. Download from Hugging Face: https://huggingface.co/models",
                    "2. Download from Civitai: https://civitai.com/",
                    "3. Check model name spelling and file extension (.safetensors or .ckpt)",
                ],
                "common_models": [
                    "sd_xl_base_1.0.safetensors",
                    "v1-5-pruned-emaonly.safetensors",
                    "sd_xl_refiner_1.0.safetensors"
                ],
                "download_links": {
                    "SDXL Base": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0",
                    "SD 1.5": "https://huggingface.co/runwayml/stable-diffusion-v1-5"
                }
            },
            "lora": {
                "message": f"Missing LoRA model: {missing_model}",
                "folder": "ComfyUI/models/loras/",
                "suggestions": [
                    "1. Download from Civitai: https://civitai.com/models?types=LORA",
                    "2. Download from Hugging Face",
                    "3. Ensure the file is in .safetensors format"
                ],
                "common_models": [
                    "lcm-lora-sdxl.safetensors",
                    "detail-tweaker-xl.safetensors"
                ]
            },
            "controlnet": {
                "message": f"Missing ControlNet model: {missing_model}",
                "folder": "ComfyUI/models/controlnet/",
                "suggestions": [
                    "1. Download from Hugging Face ControlNet repository",
                    "2. Match the ControlNet version with your base model (SD1.5 or SDXL)"
                ],
                "common_models": [
                    "control_v11p_sd15_canny.pth",
                    "control_v11p_sd15_openpose.pth",
                    "diffusers_xl_canny_mid.safetensors"
                ],
                "download_links": {
                    "ControlNet 1.1": "https://huggingface.co/lllyasviel/ControlNet-v1-1",
                    "ControlNet SDXL": "https://huggingface.co/diffusers/controlnet-canny-sdxl-1.0"
                }
            },
            "vae": {
                "message": f"Missing VAE model: {missing_model}",
                "folder": "ComfyUI/models/vae/",
                "suggestions": [
                    "1. VAE often comes with checkpoint models",
                    "2. Download standalone VAE for better color reproduction"
                ],
                "common_models": [
                    "vae-ft-mse-840000-ema-pruned.safetensors",
                    "sdxl_vae.safetensors"
                ]
            },
            "clip": {
                "message": f"Missing CLIP model: {missing_model}",
                "folder": "ComfyUI/models/clip/",
                "suggestions": [
                    "1. CLIP models are usually included with checkpoints",
                    "2. For FLUX models, you need specific CLIP versions"
                ],
                "common_models": [
                    "clip_l.safetensors",
                    "t5xxl_fp16.safetensors"
                ]
            },
            "unet": {
                "message": f"Missing UNET model: {missing_model}",
                "folder": "ComfyUI/models/unet/",
                "suggestions": [
                    "1. UNET models for FLUX can be downloaded from Hugging Face",
                    "2. Check if you need fp8 or fp16 version based on your GPU"
                ],
                "common_models": [
                    "flux1-dev.safetensors",
                    "flux1-schnell.safetensors"
                ]
            },
            "ipadapter": {
                "message": f"Missing IPAdapter model: {missing_model}",
                "folder": "ComfyUI/models/ipadapter/",
                "suggestions": [
                    "1. Download from the official IPAdapter repository",
                    "2. Match the IPAdapter version with your base model"
                ],
                "download_links": {
                    "IPAdapter": "https://huggingface.co/h94/IP-Adapter"
                }
            }
        }
        
        if detected_type in suggestions:
            result = suggestions[detected_type]
            result["detected_type"] = detected_type
            result["missing_model"] = missing_model
            
            # 添加通用建议
            result["general_tips"] = [
                f"Place the downloaded file in: {result['folder']}",
                "Restart ComfyUI after adding new models",
                "Check file permissions if model is not detected"
            ]
            
            return json.dumps(result)
        else:
            return json.dumps({
                "detected_type": "unknown",
                "missing_model": missing_model,
                "message": f"Missing model: {missing_model}",
                "suggestions": [
                    "1. Identify the model type from the node that requires it",
                    "2. Download from appropriate sources",
                    "3. Place in the correct ComfyUI/models/ subfolder",
                    "4. Common folders: checkpoints/, loras/, vae/, controlnet/, clip/"
                ]
            })
    
    except Exception as e:
        return json.dumps({"error": f"Failed to suggest model download: {str(e)}"})

@function_tool
def update_workflow_parameter(session_id: str, node_id: str, param_name: str, new_value: str) -> str:
    """更新工作流中的特定参数"""
    try:
        # 获取当前工作流
        workflow_data = get_workflow_data(session_id)
        if not workflow_data:
            return json.dumps({"error": "No workflow data found for this session"})
        
        # 检查节点是否存在
        if node_id not in workflow_data:
            return json.dumps({"error": f"Node {node_id} not found in workflow"})
        
        # 更新参数
        if "inputs" not in workflow_data[node_id]:
            workflow_data[node_id]["inputs"] = {}
        
        old_value = workflow_data[node_id]["inputs"].get(param_name, "not set")
        workflow_data[node_id]["inputs"][param_name] = new_value
        
        # 保存更新后的工作流
        version_id = save_workflow_data(
            session_id, 
            workflow_data, 
            attributes={
                "description": f"Updated {param_name} in node {node_id}",
                "action": "parameter_update",
                "changes": {
                    "node_id": node_id,
                    "parameter": param_name,
                    "old_value": old_value,
                    "new_value": new_value
                }
            }
        )
        
        return json.dumps({
            "success": True,
            "version_id": version_id,
            "node_id": node_id,
            "parameter": param_name,
            "old_value": old_value,
            "new_value": new_value,
            "message": f"Successfully updated {param_name} from '{old_value}' to '{new_value}' in node {node_id}"
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to update workflow parameter: {str(e)}"})

parameter_agent = Agent(
    name="Parameter Agent",
    model="us.anthropic.claude-sonnet-4-20250514-v1:0",
    handoff_description="""
    I am the Parameter Agent. I specialize in handling parameter-related errors in ComfyUI workflows.
    
    I can help with:
    - Finding valid parameter values from available options
    - Identifying missing models (checkpoints, LoRAs, VAE, ControlNet, etc.)
    - Suggesting parameter fixes with smart matching
    - Updating workflow parameters automatically
    - Providing specific model download recommendations with links
    
    Call me when you have parameter validation errors, value_not_in_list errors, or missing model errors.
    """,
    instructions="""
    You are the Parameter Agent, an expert in ComfyUI parameter configuration and model management.
    
    **CRITICAL**: Your job is to analyze parameter errors and provide solutions. Once you've identified the issue and provided a solution, STOP immediately. Do NOT attempt multiple fixes or validation loops.
    
    **Your Process (Execute ONCE only):**
    
    1. **For value_not_in_list errors**:
       - Use get_node_parameters() to understand the parameter
       - Use find_matching_parameter_value() with smart matching
       - If exact/good match found: use update_workflow_parameter() and STOP
       - If no good match: show available options and STOP
    
    2. **For missing model errors (MOST COMMON)**:
       - Use get_model_files() to check what's available
       - If models folder is empty or missing models: use suggest_model_download() and STOP immediately
       - Do NOT attempt to fix missing models - just provide download instructions and END
    
    3. **For other parameter issues**:
       - Analyze the parameter requirements
       - If fixable: update and STOP
       - If not fixable: provide guidance and STOP
    
    **TERMINATION RULES:**
    - When models are missing: Provide download instructions and END immediately
    - When parameters are fixed: Confirm the fix and END immediately  
    - When no fix is possible: Explain why and END immediately
    - NEVER attempt to validate or re-check after providing a solution
    - NEVER loop back to check if the fix worked
    
    **Response Format:**
    1. "Issue identified: [brief description]"
    2. "Solution: [what you did or what user needs to do]"
    3. "Next steps: [if manual action required]"
    4. END - Do not continue after providing the solution
    
    **Remember**: Your role is to identify the issue and provide the solution. Let the user handle downloads and restarts. Do NOT attempt verification loops.
    """,
    tools=[get_node_parameters, find_matching_parameter_value, get_model_files, 
           suggest_model_download, update_workflow_parameter],
)