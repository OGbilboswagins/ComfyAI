"""
Agent factory for ComfyAI.

Centralizes:
- provider selection (local / cloud)
- model selection per task type
- OpenAI-compatible client configuration for the `openai-agents` library
"""

from typing import Optional, List, Any, Dict

from agents.agent import Agent
from agents._config import set_default_openai_api

from .provider_manager import provider_manager
from .utils.logger import log
from .utils.request_context import get_config as get_request_config


def _merge_config(base: Optional[Dict[str, Any]], override: Dict[str, Any]) -> Dict[str, Any]:
    """Shallow merge two config dicts, with override taking precedence."""
    result: Dict[str, Any] = dict(base or {})
    for k, v in (override or {}).items():
        if v is not None:
            result[k] = v
    return result


def _infer_task_type(agent_name: str, explicit: Optional[str]) -> str:
    """Infer a reasonable task type from the agent name if explicit is not given."""
    if explicit:
        return explicit

    name = agent_name.lower()
    if "debug" in name:
        return "workflow_debug"
    if "rewrite" in name:
        return "workflow_rewrite"
    # Default for the main chat assistant
    return "chat"


def create_agent(
    *,
    name: str,
    instructions: str,
    model: Optional[str] = None,
    tools: Optional[List[Any]] = None,
    mcp_servers: Optional[List[Any]] = None,
    handoffs: Optional[List[Any]] = None,
    handoff_description: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    task_type: Optional[str] = None,
) -> Agent:
    """
    Unified agent factory used by:
    - main ComfyAI / Comfy Copilot agent (chat)
    - workflow rewrite agent
    - debug agent
    - any future agents

    Call sites can keep using keyword args as before:

        create_agent(
            name="ComfyUI-Copilot",
            instructions="...",
            mcp_servers=server_list,
            handoffs=[...],
            config=config,
        )

        create_agent(
            name="Workflow Rewrite Agent",
            instructions="...",
            tools=[...],
            config=config,
        )
    """

    # 1. Start from request-scoped config (conversation_api passes it via context)
    request_cfg = get_request_config() or {}
    cfg = _merge_config(request_cfg, config or {})

    # 2. Determine task type for routing
    inferred_task = _infer_task_type(name, task_type)

    # 3. Ask ProviderManager which provider/model to use
    routing_choice: Optional[Dict[str, Any]] = None
    try:
        routing_choice = provider_manager.choose_model(inferred_task)
    except Exception as e:
        log.error(f"[AgentFactory] Provider routing failed for {name}: {e}")
        log.error("[AgentFactory] Falling back to raw config/model without routing.")

    if routing_choice:
        endpoint = routing_choice.get("endpoint")
        api_key = routing_choice.get("api_key") or cfg.get("openai_api_key")
        final_model = routing_choice.get("model") or model or cfg.get("model_select")

        if endpoint:
            cfg["openai_base_url"] = endpoint
        if api_key:
            cfg["openai_api_key"] = api_key

        log.info(
            "[AgentFactory] Agent '%s' → provider=%s type=%s model=%s",
            name,
            routing_choice.get("provider"),
            routing_choice.get("type"),
            final_model,
        )
    else:
        # No routing decision: use whatever was passed in
        final_model = model or cfg.get("model_select")
        log.info(
            "[AgentFactory] Agent '%s' using fallback model=%s (no routing)",
            name,
            final_model,
        )

    # 4. Configure OpenAI-compatible client (used by `openai-agents`)
    if cfg.get("openai_api_key") or cfg.get("openai_base_url"):
        set_default_openai_api(
            api_key=cfg.get("openai_api_key"),
            base_url=cfg.get("openai_base_url"),
        )
        log.info(
            "[AgentFactory] set_default_openai_api base_url=%s",
            cfg.get("openai_base_url"),
        )

    # 5. Create the Agent instance
    agent = Agent(
        name=name,
        model=final_model,
        instructions=instructions,
        tools=tools or [],
        mcp_servers=mcp_servers,
        handoffs=handoffs or [],
        handoff_description=handoff_description,
        config=cfg,
    )

    return agent