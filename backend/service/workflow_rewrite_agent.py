# -*- coding: utf-8 -*-
"""
Workflow Rewrite Agent (Hybrid Local + Gemini Flash)
Automatically selects the heavy LLM for rewrite/debug tasks.
"""

from agents.agent import Agent
from agents.tool import function_tool
import json
from typing import Dict, Any

from ..utils.key_utils import workflow_config_adapt
from ..dao.expert_table import list_rewrite_experts_short, get_rewrite_expert_by_name_list
from ..agent_factory import create_agent
from ..utils.globals import get_language
from ..utils.request_context import get_config, get_session_id
from ..service.workflow_rewrite_tools import *
from ..utils.logger import log


@function_tool
def get_rewrite_expert_by_name(name_list: list[str]) -> str:
    result = get_rewrite_expert_by_name_list(name_list)
    temp = json.dumps(result, ensure_ascii=False)
    log.info(f"get_rewrite_expert_by_name, name_list: {name_list}, result: {temp}")
    get_rewrite_context().rewrite_expert += temp
    return temp


def get_rewrite_export_schema() -> dict:
    return list_rewrite_experts_short()


def select_rewrite_model(cfg: dict) -> str:
    """
    Auto-select the model:
        1. If gemini enabled → use gemini_flash
        2. Else → use local model
    """
    if cfg.get("enable_gemini") and cfg.get("heavy_workflow_model"):
        log.info(f"[Rewrite Agent] Using GEMINI heavy model: {cfg['heavy_workflow_model']}")
        return cfg["heavy_workflow_model"]

    log.info(f"[Rewrite Agent] Using LOCAL model: {cfg.get('local_model')}")
    return cfg.get("local_model")


def create_workflow_rewrite_agent():

    language = get_language()
    session_id = get_session_id() or "unknown_session"

    cfg = get_config()
    cfg = workflow_config_adapt(cfg)

    # --- Determine LLM to use ---
    selected_model = select_rewrite_model(cfg)

    # --- Configure OpenAI-compatible interface for Gemini ---
    if selected_model.startswith("gemini"):
        cfg.update({
            "model": selected_model,
            "openai_api_key": cfg.get("gemini_api_key"),
            "openai_base_url": cfg.get("gemini_base_url")
        })
    else:
        cfg.update({
            "model": selected_model,
            "openai_api_key": "ClosedAI",
            "openai_base_url": "http://localhost:11434/v1"
        })

    return create_agent(
        name="Workflow Rewrite Agent",
        model=selected_model,
        handoff_description="负责根据用户需求优化和修改 ComfyUI 工作流。",
        instructions="""
        你是专业的 ComfyUI 工作流改写代理，擅长根据用户的具体需求对现有工作流进行修改和优化。
        """,
        tools=[
            get_rewrite_expert_by_name,
            get_current_workflow,
            get_node_info,
            update_workflow,
            remove_node
        ],
        config={
            "max_tokens": 8192,
            **cfg
        }
    )

