'''
Author: ai-business-hql qingli.hql@alibaba-inc.com
Date: 2025-07-24 17:10:23
LastEditors: ai-business-hql qingli.hql@alibaba-inc.com
LastEditTime: 2025-08-06 18:05:17
FilePath: /comfyui_copilot/backend/service/workflow_rewrite_agent.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from agents.agent import Agent
from agents.tool import function_tool
import json
import time
import uuid
from agents.tool import function_tool
import os
from typing import Dict, Any

from ..agent_factory import create_agent
from ..utils.globals import get_language

from ..service.workflow_rewrite_tools import *

@function_tool
def get_rewrite_expert_by_name(name_list: list[str]) -> str:
    """根据经验名称来获取工作流改写专家经验"""
    result = ""
    with open(os.path.join(os.path.dirname(__file__), "..", "data", "workflow_rewrite_expert.json"), "r") as f:
        data = json.load(f)
        for name in name_list:    
            for item in data:
                if item["name"] == name:
                    result += f'### {name}({item["description"]})：\n{item["content"]}\n'
    return result

def get_rewrite_export_schema() -> dict:
    """获取工作流改写专家经验schema"""
    expert_schema = []
    with open(os.path.join(os.path.dirname(__file__), "..", "data", "workflow_rewrite_expert.json"), "r") as f:
        data = json.load(f)
        for item in data:
            expert_schema.append({
                "name": item["name"],
                "description": item["description"]
            })
    return expert_schema


def create_workflow_rewrite_agent(session_id: str, config: Dict[str, Any] = None):
    """创建带有session_id和config的workflow_rewrite_agent实例"""
    
    language = get_language()
    # 导入workflow_rewrite_tools并设置配置
    from .workflow_rewrite_tools import get_workflow_data_from_config, update_workflow, remove_node, get_node_info
    from ..service.database import get_workflow_data
    
    # 创建带有配置的工具函数
    @function_tool
    def get_current_workflow_with_config(session_id: str) -> str:
        """获取当前session的工作流数据"""
        workflow_data = get_workflow_data_from_config(config) if config else get_workflow_data(session_id)
        if not workflow_data:
            return json.dumps({"error": "No workflow data found for this session"})
        return json.dumps(workflow_data)
    
    return create_agent(
        name="Workflow Rewrite Agent",
        model="us.anthropic.claude-sonnet-4-20250514-v1:0",
        handoff_description="""
        我是工作流改写代理，专门负责根据用户需求修改和优化当前画布上的ComfyUI工作流。
        """,
        instructions="""
        你是专业的ComfyUI工作流改写代理，擅长根据用户的具体需求对现有工作流进行智能修改和优化。
        如果在history_messages里有用户的历史对话，请根据历史对话中的语言来决定返回的语言。否则使用{}作为返回的语言。

        **当前Session ID:** {}""".format(language, session_id) + """

        ## 主要处理场景
        {}
        """.format(json.dumps(get_rewrite_export_schema())) + """
        你可以根据用户的需求，从上面的专家经验中选择一个或多个经验，并根据经验内容进行工作流改写。
        
        ## 操作原则
        - **保持兼容性**：确保修改后的工作流与现有节点兼容
        - **优化连接**：正确设置节点间的输入输出连接
        - **连线完整性**：修改工作流时必须确保所有节点的连线关系完整，不遗漏任何必要的输入输出连接
          * 检查每个节点的必需输入是否已连接
          * 对于未连接的必需输入，优先寻找类型匹配的现有节点输出进行连接
          * 如果找不到合适的现有输出，则创建适当的输入节点（如常量节点、加载节点等）
          * 确保连接的参数类型完全匹配，避免类型不兼容的连接
        - **连线检查**：在添加、删除或修改节点时，务必检查所有相关的输入和输出连接是否正确配置
        - **连接关系维护**：修改节点时必须保持原有的连接逻辑，确保数据流向正确
        - **节点连线规则**：特别注意，任何对工作流的修改都必须检查并保持节点间的正确连线，连线的时候注意参数类型，不要把不相匹配的参数连线
        - **性能考虑**：避免不必要的重复节点，优化工作流执行效率
        - **用户友好**：保持工作流结构清晰，便于用户理解和后续修改
        - **错误处理**：在修改过程中检查潜在的配置错误，提供修正建议
      
        **Tool Usage Guidelines:**
            - get_current_workflow(): Get current workflow from checkpoint or session
            - remove_node(): Use for incompatible or problematic nodes
            - update_workflow(): Use to save your changes (ALWAYS call this after fixes)
            - get_node_info(): Get detailed node information

      
        ## 响应格式
        返回api格式的workflow

        始终以用户的实际需求为导向，提供专业、准确、高效的工作流改写服务。
        """,
        tools=[get_rewrite_expert_by_name, get_current_workflow_with_config, get_node_info, update_workflow, remove_node],
    )

# 保持向后兼容性的默认实例
workflow_rewrite_agent = create_workflow_rewrite_agent("default_session")

