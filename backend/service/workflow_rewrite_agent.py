# Workflow Rewrite Agent for ComfyUI Workflow Structure Fixes

import json
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

@function_tool
def update_workflow(session_id: str, workflow_data: str) -> str:
    """更新当前session的工作流数据"""
    try:
        # 解析JSON字符串
        workflow_dict = json.loads(workflow_data) if isinstance(workflow_data, str) else workflow_data
        
        version_id = save_workflow_data(
            session_id,
            workflow_dict,
            attributes={"action": "workflow_rewrite", "description": "Workflow structure fixed by rewrite agent"}
        )
        
        return json.dumps({
            "success": True,
            "version_id": version_id,
            "message": f"Workflow updated successfully with version ID: {version_id}"
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
        
        return json.dumps({
            "success": True,
            "version_id": version_id,
            "message": f"Fixed connection for {node_id}.{input_name}"
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to fix connection: {str(e)}"})

@function_tool
def add_missing_node(session_id: str, node_class: str, node_id: str = "", inputs_json: str = "{}") -> str:
    """添加缺失的节点到工作流，inputs_json应为JSON格式的字符串，node_id为空时自动生成"""
    try:
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
        
        return json.dumps({
            "success": True,
            "version_id": version_id,
            "node_id": node_id,
            "message": f"Added {node_class} node with ID {node_id}"
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to add node: {str(e)}"})

@function_tool
def remove_node(session_id: str, node_id: str) -> str:
    """从工作流中移除节点"""
    try:
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
        
        return json.dumps({
            "success": True,
            "version_id": version_id,
            "message": f"Removed node {node_id} and cleaned up connections"
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to remove node: {str(e)}"})

workflow_rewrite_agent = Agent(
    name="Workflow Rewrite Agent",
    model="us.anthropic.claude-sonnet-4-20250514-v1:0",
    handoff_description="""
    I am the Workflow Rewrite Agent. I specialize in fixing structural issues in ComfyUI workflows.
    
    I can help with:
    - Fixing broken node connections
    - Adding missing nodes
    - Removing problematic nodes
    - Resolving node compatibility issues
    - Restructuring workflows to fix errors
    
    Call me when you have workflow structure errors that require modifying the workflow graph itself.
    """,
    instructions="""
    You are the Workflow Rewrite Agent, an expert in ComfyUI workflow structure analysis and modification.
    
    **CRITICAL**: Your job is to analyze structural errors and fix them. Once you've made the necessary fixes, STOP immediately. Do NOT attempt multiple validation loops or re-checking.
    
    **Your Process (Execute ONCE only):**
    
    1. **Get current workflow** using get_current_workflow()
    2. **Validate connections** using validate_workflow_connections() 
    3. **Identify and fix issues** using the appropriate tools:
       - **Missing connections**: Use fix_node_connections()
       - **Missing nodes**: Use add_missing_node()
       - **Problematic nodes**: Use remove_node()
    4. **Save changes** using update_workflow() and STOP
    
    **TERMINATION RULES:**
    - After making structural fixes: Save with update_workflow() and END immediately
    - If no structural issues found: Report "No structural issues detected" and END
    - If fixes cannot be applied: Explain why and END immediately
    - NEVER validate again after making fixes
    - NEVER loop back to check if fixes worked
    - Maximum ONE fix attempt per issue
    
    **Tool Usage Guidelines:**
    - fix_node_connections(): Use for broken connections between existing nodes
    - add_missing_node(): Use when workflow needs additional nodes
    - remove_node(): Use for incompatible or problematic nodes
    - update_workflow(): Use to save your changes (ALWAYS call this after fixes)
    
    **Response Format:**
    1. "Structural analysis: [brief description of issues]"
    2. "Fixes applied: [what you changed]"
    3. "Workflow updated: [confirmation]"
    4. END - Do not continue after saving changes
    
    **Remember**: Focus on making necessary structural changes quickly and efficiently. Let the user test the results. Do NOT attempt verification or multiple fix rounds.
    """,
    tools=[get_current_workflow, get_node_info, update_workflow, validate_workflow_connections, 
           fix_node_connections, add_missing_node, remove_node],
)
