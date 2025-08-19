import json

from agents.tool import function_tool
from ..utils.request_context import get_session_id

from ..utils.comfy_gateway import get_object_info_by_class
from custom_nodes.comfyui_copilot.backend.dao.workflow_table import get_workflow_data, save_workflow_data
from ..utils.logger import log

async def get_node_parameters(node_name: str, param_name: str = "") -> str:
    """获取节点的参数信息，如果param_name为空则返回所有参数"""
    try:
        node_info_dict = await get_object_info_by_class(node_name)
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
async def find_matching_parameter_value(node_name: str, param_name: str, current_value: str, error_info: str = "") -> str:
    """根据错误信息找到匹配的参数值，支持多种参数类型的智能处理"""
    try:
        # 获取参数配置
        param_info_str = await get_node_parameters(node_name, param_name)
        param_info = json.loads(param_info_str)
        
        if "error" in param_info:
            return json.dumps(param_info)
        
        param_config = param_info.get("config", [])
        error_lower = error_info.lower()
        
        # 检查错误类型并提供相应处理策略
        error_analysis = {
            "error_type": "unknown",
            "is_model_related": False,
            "is_file_related": False,
        }
        
        # 优先识别image文件相关错误（在model检测之前，因为image文件可能包含model关键词）
        if (any(img_ext in current_value.lower() for img_ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]) or
              param_name.lower() in ["image", "img", "picture", "photo"] or
              any(img_keyword in error_lower for img_keyword in ["invalid image", "image file", "image not found"])):
            error_analysis["error_type"] = "image_file_missing"
            error_analysis["is_file_related"] = True
            error_analysis["can_auto_fix"] = True
            
            # 如果参数配置是列表，查找其他可用的图片
            if isinstance(param_config, list) and len(param_config) > 0 and param_config[0]:
                available_images = [img for img in param_config[0] if any(ext in str(img).lower() for ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"])]
                
                if available_images:
                    # 随机选择一张可用图片
                    import random
                    recommended_image = random.choice(available_images)
                    return json.dumps({
                        "found_match": True,
                        "error_type": "image_file_missing",
                        "solution_type": "auto_replace",
                        "recommended_value": recommended_image,
                        "match_type": "image_replacement",
                        "message": f"Replaced missing image '{current_value}' with available image '{recommended_image}'",
                        "can_auto_fix": True,
                        "next_action": "update_parameter"
                    })
            
            return json.dumps({
                "found_match": False,
                "error_type": "image_file_missing",
                "solution_type": "manual_fix",
                "message": f"Missing image file: {current_value}",
                "suggestion": "Please add a valid image file to your ComfyUI input folder or choose an existing one",
                "can_auto_fix": False
            })
        
        # 识别model相关错误（在image检测之后）
        elif (any(model_keyword in current_value.lower() for model_keyword in [
            ".ckpt", ".safetensors", ".pt", ".pth", ".bin", "checkpoint", "lora", "vae", "controlnet", "clip", "unet"
        ]) or any(model_keyword in param_name.lower() for model_keyword in [
            "model", "checkpoint", "lora", "vae", "clip", "controlnet", "unet"
        ]) or any(model_keyword in error_lower for model_keyword in [
            "model not found", "checkpoint", "missing model", "file not found"
        ])):
            error_analysis["error_type"] = "model_missing"
            error_analysis["is_model_related"] = True
            
            return json.dumps({
                "found_match": False,
                "error_type": "model_missing",
                "message": f"Missing model file: {current_value}",
                "recommendation": "Check for available model replacements, otherwise download required.",
                "next_action": "check_available_models_or_suggest_download",
                "details": {
                    "node_name": node_name,
                    "param_name": param_name,
                    "missing_file": current_value,
                    "is_model_related": True,
                    "param_config": param_config
                }
            })
        
        # 处理枚举类型的参数（原有逻辑，但增强）
        elif isinstance(param_config, list) and len(param_config) > 0:
            available_values = param_config
            error_analysis["error_type"] = "enum_value_mismatch"
            error_analysis["can_auto_fix"] = True
            
            # 改进的匹配算法
            current_lower = current_value.lower().replace("_", " ").replace("-", " ")
            
            # 1. 完全匹配
            for value in available_values:
                if current_value == value:
                    return json.dumps({
                        "found_match": True,
                        "recommended_value": value,
                        "match_type": "exact",
                        "error_type": "enum_value_mismatch",
                        "solution_type": "exact_match",
                        "can_auto_fix": True,
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
                        "error_type": "enum_value_mismatch",
                        "solution_type": "auto_replace",
                        "message": f"Found case-insensitive match: '{current_value}' -> '{value}'",
                        "can_auto_fix": True,
                        "next_action": "update_parameter",
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
                    "error_type": "enum_value_mismatch",
                    "solution_type": "auto_replace",
                    "match_score": best_score,
                    "message": f"Found partial match: '{current_value}' -> '{best_match}' (score: {best_score})",
                    "can_auto_fix": True,
                    "next_action": "update_parameter",
                    "all_available": available_values[:10],
                    "original_value": current_value
                })
            
            # 4. 没有匹配，但可以用第一个可用值替代
            return json.dumps({
                "found_match": False,
                "recommended_value": available_values[0] if available_values else None,
                "match_type": "no_match",
                "error_type": "enum_value_mismatch", 
                "solution_type": "default_replace",
                "message": f"No match found for '{current_value}'. Using default value '{available_values[0]}'",
                "can_auto_fix": True,
                "next_action": "update_parameter",
                "all_available": available_values[:10],
                "total_options": len(available_values),
                "original_value": current_value,
                "suggestion": f"No match found for '{current_value}'. Replacing with default option."
            })
        
        # 处理其他类型的参数
        else:
            error_analysis["error_type"] = "non_enum_parameter"
            error_analysis["can_auto_fix"] = False
            
            return json.dumps({
                "found_match": False,
                "error_type": "non_enum_parameter",
                "solution_type": "manual_fix",
                "parameter_type": type(param_config).__name__,
                "config": param_config,
                "can_auto_fix": False,
                "message": f"Parameter '{param_name}' is not an enumerable type",
                "suggestion": f"Parameter '{param_name}' requires manual configuration. Check the parameter requirements."
            })
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to find matching parameter value: {str(e)}",
            "can_auto_fix": False,
            "solution_type": "error"
        })

@function_tool
async def get_model_files(model_type: str = "checkpoints") -> str:
    """获取可用的模型文件列表"""
    try:
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
            try:
                # 使用 get_object_info_by_class 获取单个节点信息，减少数据量
                node_data = await get_object_info_by_class(node_name)
                
                # 处理不同的返回格式
                node_info = None
                if node_name in node_data:
                    # 格式：{"NodeName": {...}}
                    node_info = node_data[node_name]
                elif 'input' in node_data:
                    # 格式：直接返回节点信息 {...}
                    node_info = node_data
                
                if node_info and 'input' in node_info:
                    # 查找包含文件列表的参数
                    for input_type in ['required', 'optional']:
                        if input_type in node_info['input']:
                            for param_name, param_config in node_info['input'][input_type].items():
                                # 检查参数配置格式：[file_list, {...}] 或 [file_list]
                                if isinstance(param_config, list) and len(param_config) > 0:
                                    if isinstance(param_config[0], list) and len(param_config[0]) > 0:
                                        # 检查是否为文件列表（包含文件扩展名或路径）
                                        file_list = param_config[0]
                                        if any(isinstance(item, str) and ('.' in item or '/' in item) for item in file_list):
                                            model_files[f"{node_name}.{param_name}"] = file_list
                            
            except Exception as e:
                # 单个节点查询失败，继续处理其他节点
                log.error(f"Failed to get info for node {node_name}: {e}")
                continue
        
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
def update_workflow_parameter(node_id: str, param_name: str, new_value: str) -> str:
    """更新工作流中的特定参数"""
    try:
        session_id = get_session_id()
        if not session_id:
            log.error("update_workflow_parameter: No session_id found in context")
            return json.dumps({"error": "No session_id found in context"})
        
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
        
        # 保存更新的工作流到数据库
        save_workflow_data(
            session_id,
            workflow_data,
            workflow_data_ui=None,  # UI format not available here
            attributes={
                "action": "parameter_update", 
                "description": f"Updated {param_name} in node {node_id}",
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
            "answer": f"Successfully updated {param_name} from '{old_value}' to '{new_value}' in node {node_id}",
            "node_id": node_id,
            "parameter": param_name,
            "old_value": old_value,
            "new_value": new_value,
            "message": f"Successfully updated {param_name} from '{old_value}' to '{new_value}' in node {node_id}",
            # 添加ext数据用于前端实时更新画布
            "ext": [{
                "type": "param_update",
                "data": {
                    "workflow_data": workflow_data,
                    "changes": [{  # 包装成数组格式，与前端MessageList期望的格式匹配
                        "node_id": node_id,
                        "parameter": param_name,
                        "old_value": old_value,
                        "new_value": new_value
                    }]
                }
            }]
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to update workflow parameter: {str(e)}"})

