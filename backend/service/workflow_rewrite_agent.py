'''
Author: ai-business-hql qingli.hql@alibaba-inc.com
Date: 2025-07-24 17:10:23
LastEditors: ai-business-hql qingli.hql@alibaba-inc.com
LastEditTime: 2025-08-04 17:13:43
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


def create_workflow_rewrite_agent(session_id: str):
    """创建带有session_id的workflow_rewrite_agent实例"""
    
    language = get_language()
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
        - **性能考虑**：避免不必要的重复节点，优化工作流执行效率
        - **用户友好**：保持工作流结构清晰，便于用户理解和后续修改
        - **错误处理**：在修改过程中检查潜在的配置错误，提供修正建议
      
        **Tool Usage Guidelines:**
            - remove_node(): Use for incompatible or problematic nodes
            - update_workflow(): Use to save your changes (ALWAYS call this after fixes)

      
        ## 响应格式
        返回api格式的workflow

        始终以用户的实际需求为导向，提供专业、准确、高效的工作流改写服务。
        """,
        tools=[get_rewrite_expert_by_name, get_current_workflow, get_node_info, update_workflow, remove_node],
    )

# 保持向后兼容性的默认实例
workflow_rewrite_agent = create_workflow_rewrite_agent("default_session")

