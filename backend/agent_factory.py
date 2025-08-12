'''
Author: ai-business-hql qingli.hql@alibaba-inc.com
Date: 2025-07-31 19:38:08
LastEditors: ai-business-hql qingli.hql@alibaba-inc.com
LastEditTime: 2025-08-11 16:57:23
FilePath: /comfyui_copilot/backend/agent_factory.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from agents import Agent, OpenAIChatCompletionsModel
from dotenv import dotenv_values
from .utils.globals import LLM_DEFAULT_BASE_URL, get_comfyui_copilot_api_key
from openai import AsyncOpenAI

import os

from agents._config import set_default_openai_api
from agents.tracing import set_tracing_disabled


def load_env_config():
    """Load environment variables from .env.llm file"""
    from dotenv import load_dotenv

    env_file_path = os.path.join(os.path.dirname(__file__), '.env.llm')
    if os.path.exists(env_file_path):
        load_dotenv(env_file_path)
        print(f"Loaded environment variables from {env_file_path}")
    else:
        print(f"Warning: .env.llm not found at {env_file_path}")


# Load environment configuration
load_env_config()

set_default_openai_api("chat_completions")
set_tracing_disabled(True)
def create_agent(**kwargs) -> Agent:
    # 通过用户配置拿/环境变量
    config = kwargs.pop("config") if "config" in kwargs else {}
    # 避免将 None 写入 headers
    session_id = (config or {}).get("session_id")
    default_headers = {}
    if session_id:
        default_headers["X-Session-ID"] = session_id

    client = AsyncOpenAI(
        api_key=get_comfyui_copilot_api_key() or "",
        base_url=LLM_DEFAULT_BASE_URL,
        default_headers=default_headers,
    )

    if config:
        if config.get("openai_api_key") and config.get("openai_api_key") != "":
            client.api_key = config.get("openai_api_key")
        if config.get("openai_base_url") and config.get("openai_base_url") != "":
            client.base_url = config.get("openai_base_url")
        # if config.get("session_id") and config.get("session_id") != "":
        #     client.default_headers["X-Session-ID"] = config.get("session_id")

    default_model_name = os.environ.get("OPENAI_MODEL", "gemini-2.5-flash")
    model_name = kwargs.pop("model") or default_model_name
    model = OpenAIChatCompletionsModel(model_name, openai_client=client)
    
    return Agent(model=model, **kwargs)