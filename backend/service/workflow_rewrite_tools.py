# Workflow Rewrite Agent for ComfyUI Workflow Structure Fixes

import json
import time
from typing import Dict, Any, Optional, List

from agents.agent import Agent
from agents.tool import function_tool

from ..service.database import get_workflow_data, save_workflow_data
from ..utils.comfy_gateway import get_object_info

@function_tool
def get_current_workflow(session_id: str) -> str:
    """获取当前session的工作流数据"""
    workflow_data = get_workflow_data(session_id)
    if not workflow_data:
        return json.dumps({"error": "No workflow data found for this session"})
    return json.dumps(workflow_data)

@function_tool
def get_node_info(node_class: str) -> str:
    """获取节点的详细信息，包括输入输出参数"""
    try:
        object_info = get_object_info()
        if node_class in object_info:
            return json.dumps(object_info[node_class])
        else:
            # 搜索类似的节点类
            similar_nodes = [k for k in object_info.keys() if node_class.lower() in k.lower()]
            if similar_nodes:
                return json.dumps({
                    "error": f"Node class '{node_class}' not found",
                    "suggestions": similar_nodes[:5]
                })
            return json.dumps({"error": f"Node class '{node_class}' not found"})
    except Exception as e:
        return json.dumps({"error": f"Failed to get node info: {str(e)}"})

def save_checkpoint_before_modification(session_id: str, action_description: str) -> Optional[int]:
    """在修改工作流前保存checkpoint，返回checkpoint_id"""
    try:
        current_workflow = get_workflow_data(session_id)
        if not current_workflow:
            return None
            
        checkpoint_id = save_workflow_data(
            session_id,
            current_workflow,
            workflow_data_ui=None,  # UI format not available in tools
            attributes={
                "checkpoint_type": "workflow_rewrite_start",
                "description": f"Checkpoint before {action_description}",
                "action": "workflow_rewrite_checkpoint",
                "timestamp": time.time()
            }
        )
        print(f"Saved workflow rewrite checkpoint with ID: {checkpoint_id}")
        return checkpoint_id
    except Exception as e:
        print(f"Failed to save checkpoint before modification: {str(e)}")
        return None

@function_tool
def update_workflow(session_id: str, workflow_data: str) -> str:
    """更新当前session的工作流数据"""
    try:
        # 在修改前保存checkpoint
        checkpoint_id = save_checkpoint_before_modification(session_id, "workflow update")
        
        # 解析JSON字符串
        workflow_dict = json.loads(workflow_data) if isinstance(workflow_data, str) else workflow_data
        
        version_id = save_workflow_data(
            session_id,
            workflow_dict,
            attributes={"action": "workflow_rewrite", "description": "Workflow structure fixed by rewrite agent"}
        )
        
        # 构建返回数据，包含checkpoint信息
        ext_data = [{
            "type": "workflow_update",
            "data": {
                "workflow_data": workflow_dict
            }
        }]
        
        # 如果成功保存了checkpoint，添加修改前的checkpoint信息（给用户消息）
        if checkpoint_id:
            ext_data.append({
                "type": "workflow_rewrite_checkpoint",
                "data": {
                    "checkpoint_id": checkpoint_id,
                    "checkpoint_type": "workflow_rewrite_start"
                }
            })
        
        # 添加修改后的版本信息（给AI响应）
        ext_data.append({
            "type": "workflow_rewrite_complete",
            "data": {
                "version_id": version_id,
                "checkpoint_type": "workflow_rewrite_complete"
            }
        })
        
        return json.dumps({
            "success": True,
            "version_id": version_id,
            "message": f"Workflow updated successfully with version ID: {version_id}",
            "ext": ext_data
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to update workflow: {str(e)}"})

@function_tool
def validate_workflow_connections(session_id: str) -> str:
    """验证工作流连接的有效性"""
    try:
        workflow_data = get_workflow_data(session_id)
        if not workflow_data:
            return json.dumps({"error": "No workflow data found"})
        
        object_info = get_object_info()
        validation_errors = []
        connection_map = {}
        
        # 构建连接映射
        for node_id, node_data in workflow_data.items():
            node_class = node_data.get("class_type")
            if node_class not in object_info:
                validation_errors.append({
                    "node_id": node_id,
                    "error": f"Unknown node class: {node_class}"
                })
                continue
            
            inputs = node_data.get("inputs", {})
            for input_name, input_value in inputs.items():
                if isinstance(input_value, list) and len(input_value) == 2:
                    # This is a connection [node_id, output_index]
                    source_node_id = str(input_value[0])
                    output_index = input_value[1]
                    
                    if source_node_id not in workflow_data:
                        validation_errors.append({
                            "node_id": node_id,
                            "input": input_name,
                            "error": f"Connected to non-existent node: {source_node_id}"
                        })
                    else:
                        # 验证输出索引是否有效
                        source_class = workflow_data[source_node_id].get("class_type")
                        if source_class in object_info:
                            outputs = object_info[source_class].get("output", [])
                            if output_index >= len(outputs):
                                validation_errors.append({
                                    "node_id": node_id,
                                    "input": input_name,
                                    "error": f"Invalid output index {output_index} from node {source_node_id}"
                                })
        
        return json.dumps({
            "valid": len(validation_errors) == 0,
            "errors": validation_errors
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to validate connections: {str(e)}"})

@function_tool
def fix_node_connections(session_id: str, node_id: str, input_name: str, source_node_id: str, output_index: int) -> str:
    """修复特定节点的连接，连接格式为[source_node_id, output_index]"""
    try:
        # 在修改前保存checkpoint
        checkpoint_id = save_checkpoint_before_modification(session_id, f"fix connection for {node_id}.{input_name}")
        
        workflow_data = get_workflow_data(session_id)
        if not workflow_data:
            return json.dumps({"error": "No workflow data found"})
        
        if node_id not in workflow_data:
            return json.dumps({"error": f"Node {node_id} not found"})
        
        # 构建新连接
        new_connection = [source_node_id, output_index]
        
        # 更新连接
        old_value = workflow_data[node_id]["inputs"].get(input_name, "not connected")
        workflow_data[node_id]["inputs"][input_name] = new_connection
        
        # 保存更新
        version_id = save_workflow_data(
            session_id,
            workflow_data,
            attributes={
                "action": "fix_connection",
                "description": f"Fixed connection for {node_id}.{input_name}",
                "changes": {
                    "node_id": node_id,
                    "input": input_name,
                    "old_value": old_value,
                    "new_value": new_connection
                }
            }
        )
        
        # 构建返回数据，包含checkpoint信息
        ext_data = [{
            "type": "workflow_update",
            "data": {
                "workflow_data": workflow_data,
                "changes": {
                    "node_id": node_id,
                    "input": input_name,
                    "old_value": old_value,
                    "new_value": new_connection
                }
            }
        }]
        
        # 如果成功保存了checkpoint，添加修改前的checkpoint信息（给用户消息）
        if checkpoint_id:
            ext_data.append({
                "type": "workflow_rewrite_checkpoint",
                "data": {
                    "checkpoint_id": checkpoint_id,
                    "checkpoint_type": "workflow_rewrite_start"
                }
            })
        
        # 添加修改后的版本信息（给AI响应）
        ext_data.append({
            "type": "workflow_rewrite_complete",
            "data": {
                "version_id": version_id,
                "checkpoint_type": "workflow_rewrite_complete"
            }
        })
        
        return json.dumps({
            "success": True,
            "version_id": version_id,
            "message": f"Fixed connection for {node_id}.{input_name}",
            "ext": ext_data
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to fix connection: {str(e)}"})

@function_tool
def add_missing_node(session_id: str, node_class: str, node_id: str = "", inputs_json: str = "{}") -> str:
    """添加缺失的节点到工作流，inputs_json应为JSON格式的字符串，node_id为空时自动生成"""
    try:
        # 在修改前保存checkpoint
        checkpoint_id = save_checkpoint_before_modification(session_id, f"add {node_class} node")
        
        workflow_data = get_workflow_data(session_id)
        if not workflow_data:
            return json.dumps({"error": "No workflow data found"})
        
        # 解析inputs JSON
        try:
            inputs = json.loads(inputs_json) if inputs_json else {}
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid inputs_json format"})
        
        # 生成节点ID
        if not node_id:
            # 找到未使用的ID
            existing_ids = set(workflow_data.keys())
            node_id = "1"
            while node_id in existing_ids:
                node_id = str(int(node_id) + 1)
        
        # 创建新节点
        new_node = {
            "class_type": node_class,
            "inputs": inputs,
            "_meta": {"title": node_class}
        }
        
        workflow_data[node_id] = new_node
        
        # 保存更新
        version_id = save_workflow_data(
            session_id,
            workflow_data,
            attributes={
                "action": "add_node",
                "description": f"Added {node_class} node with ID {node_id}",
                "changes": {
                    "node_id": node_id,
                    "node_class": node_class
                }
            }
        )
        
        # 构建返回数据，包含checkpoint信息
        ext_data = [{
            "type": "workflow_update",
            "data": {
                "workflow_data": workflow_data,
                "changes": {
                    "action": "add_node",
                    "node_id": node_id,
                    "node_class": node_class
                }
            }
        }]
        
        # 如果成功保存了checkpoint，添加修改前的checkpoint信息（给用户消息）
        if checkpoint_id:
            ext_data.append({
                "type": "workflow_rewrite_checkpoint",
                "data": {
                    "checkpoint_id": checkpoint_id,
                    "checkpoint_type": "workflow_rewrite_start"
                }
            })
        
        # 添加修改后的版本信息（给AI响应）
        ext_data.append({
            "type": "workflow_rewrite_complete",
            "data": {
                "version_id": version_id,
                "checkpoint_type": "workflow_rewrite_complete"
            }
        })
        
        return json.dumps({
            "success": True,
            "version_id": version_id,
            "node_id": node_id,
            "message": f"Added {node_class} node with ID {node_id}",
            "ext": ext_data
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to add node: {str(e)}"})

@function_tool
def remove_node(session_id: str, node_id: str) -> str:
    """从工作流中移除节点"""
    try:
        # 在修改前保存checkpoint
        checkpoint_id = save_checkpoint_before_modification(session_id, f"remove node {node_id}")
        
        workflow_data = get_workflow_data(session_id)
        if not workflow_data:
            return json.dumps({"error": "No workflow data found"})
        
        if node_id not in workflow_data:
            return json.dumps({"error": f"Node {node_id} not found"})
        
        # 移除节点
        removed_node = workflow_data.pop(node_id)
        
        # 移除所有指向该节点的连接
        for other_node_id, node_data in workflow_data.items():
            inputs = node_data.get("inputs", {})
            for input_name, input_value in list(inputs.items()):
                if isinstance(input_value, list) and len(input_value) == 2:
                    if str(input_value[0]) == node_id:
                        # 移除这个连接
                        del inputs[input_name]
        
        # 保存更新
        version_id = save_workflow_data(
            session_id,
            workflow_data,
            attributes={
                "action": "remove_node",
                "description": f"Removed node {node_id}",
                "changes": {
                    "node_id": node_id,
                    "removed_node": removed_node
                }
            }
        )
        
        # 构建返回数据，包含checkpoint信息
        ext_data = [{
            "type": "workflow_update",
            "data": {
                "workflow_data": workflow_data,
                "changes": {
                    "action": "remove_node",
                    "node_id": node_id,
                    "removed_node": removed_node
                }
            }
        }]
        
        # 如果成功保存了checkpoint，添加修改前的checkpoint信息（给用户消息）
        if checkpoint_id:
            ext_data.append({
                "type": "workflow_rewrite_checkpoint",
                "data": {
                    "checkpoint_id": checkpoint_id,
                    "checkpoint_type": "workflow_rewrite_start"
                }
            })
        
        # 添加修改后的版本信息（给AI响应）
        ext_data.append({
            "type": "workflow_rewrite_complete",
            "data": {
                "version_id": version_id,
                "checkpoint_type": "workflow_rewrite_complete"
            }
        })
        
        return json.dumps({
            "success": True,
            "version_id": version_id,
            "message": f"Removed node {node_id} and cleaned up connections",
            "ext": ext_data
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to remove node: {str(e)}"})


