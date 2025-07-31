from agents import Agent, OpenAIChatCompletionsModel
from dotenv import dotenv_values
from openai import AsyncOpenAI

import os

from agents._config import set_default_openai_api
from agents.tracing import set_tracing_disabled


def load_env_config():
    """Load environment variables from .env.llm file"""
    from dotenv import load_dotenv

    env_file_path = os.path.join(os.path.dirname(__file__), '.env.llm')
    if os.path.exists(env_file_path):
        # load_dotenv(env_file_path)
        print(f"Loaded environment variables from {env_file_path}")
        return dotenv_values(env_file_path)
    else:
        print(f"Warning: .env.llm not found at {env_file_path}")


# Load environment configuration
load_env_config()

set_default_openai_api("chat_completions")
set_tracing_disabled(True)
def create_agent(**kwargs) -> Agent:
    # 通过用户配置拿/环境变量
    client = AsyncOpenAI(
        api_key="aib_ComfyUI_Copilot_8d28a3",
        base_url="https://comfyui-copilot-server-pre.onrender.com/v1",
    )

    default_model_name = os.environ.get("OPENAI_MODEL", "gemini-2.5-flash")
    model_name = kwargs.pop("model") or default_model_name
    model = OpenAIChatCompletionsModel(model_name, openai_client=client)

    return Agent(model=model, **kwargs)