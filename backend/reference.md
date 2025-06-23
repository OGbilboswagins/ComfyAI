我需要参考另外一个工程的代码，来实现我当前的后端能力，当前的工程是个ComfyUI的插件，我在这里实现了一个mcp_client,来替代掉原来的workflowChatApi.ts里的`${BASE_URL}/api/chat/invoke`接口。

核心代码facade.py实现了agent-tools的能力：
```python
from typing import Optional, Generator, Dict
import json
import uuid
from agent.tools.node_explain_agent_tool import explain_node
from agent.tools.node_search_tool import search_node
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres import PostgresSaver
from context import get_user_id
from logger import logger
from psycopg_pool import ConnectionPool
from agent.llms import llm_4_chatbot, llm_4o, llm_deepseek, llm_4o_mini, llm_dashscope, llm_volcengine, get_openai_client, llm_dashscope_deepseek_v3, llm_qwen3, llm_4_1
from agent.tools.workflow_recall_tool import recall_workflow, generate_workflow_step2
from agent.tools.model_search_tool import search_model
from initializer.db_initializer import Session, db_url
from utils.os_util import get_root_path
from dao.message_dao import Message, MessageSource
from dao.node_dao import Node
from dao.workflow_dao import Workflow

tools = [
    recall_workflow,  # 工作流召回
    search_node,  # 节点搜索
    search_model,  # 模型召回
    explain_node,  # 节点解释
    # analyze_workflow,  # 工作流分析
]
system_prompt_path = get_root_path('prompts/system_prompt.txt')
with open(system_prompt_path, 'r', encoding='utf-8') as f:
    system_prompt_content = f.read()
new_system_prompt = SystemMessage(content=system_prompt_content)

connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

pool = ConnectionPool(db_url, max_size=50, kwargs=connection_kwargs)
checkpointer = PostgresSaver(pool)
checkpointer.setup()


# 修改 LLM 映射字典，使用正确的配置方式
llm_config: Dict = {
    "gpt-4o": {
        "client":llm_4_1,
        "image_enable":True,
    },
    "gpt-4.1": {
        "client":llm_4_1,
        "image_enable":True,
    },
    "gpt-4o-mini": {
        "client":llm_4o_mini,
        "image_enable":True,
    },
    "DeepSeek-V3": {
        "client":llm_deepseek,
        "image_enable":False,
    },
    "qwen-plus": {
        "client":llm_dashscope,
        "image_enable":False,
    }
}

llm_mapping = {k: llm_config[k]["client"] for k in llm_config}


# 获取所有llm列表
def get_model_list():
    model_list = []
    remove_models = ["gpt-4o"]
    for model, config in llm_config.items():
        if model not in remove_models:
            model_list.append({
                "name": model,
                "image_enable": config["image_enable"],
            })
    return model_list

# 创建一个函数用于限制对话历史
def limit_conversation_history(state, max_turns=5):
    """
    限制对话历史只保留最近的几轮对话
    
    Args:
        state: 当前的状态对象
        max_turns: 保留的最大对话轮数
    
    Returns:
        修改后的状态
    """
    messages = state.get("messages", [])
    system_messages = []
    conversation_messages = []
    
    # 分离系统消息和对话消息
    for msg in messages:
        if isinstance(msg, SystemMessage):
            system_messages.append(msg)
        else:
            conversation_messages.append(msg)
    
    # 保留对话消息的最后max_turns*2条(每轮包含用户消息和AI回复)
    limited_conversation = conversation_messages[-max_turns*2:] if len(conversation_messages) > max_turns*2 else conversation_messages
    
    # 重新组合消息
    state["messages"] = system_messages + limited_conversation
    return state

# 将系统提示和历史限制组合在一起
def combined_state_modifier(state):
    """
    组合状态修改器，添加系统提示并限制对话历史
    
    Args:
        state: 当前的状态对象
    
    Returns:
        修改后的消息列表
    """
    messages = state.get("messages", [])
    
    # 分离系统消息和对话消息
    system_messages = []
    conversation_messages = []
    
    for msg in messages:
        if isinstance(msg, SystemMessage):
            system_messages.append(msg)
        else:
            conversation_messages.append(msg)
    
    # 如果没有系统消息，添加系统提示
    if not system_messages and isinstance(new_system_prompt, SystemMessage):
        system_messages = [new_system_prompt]
    
    # 保留对话消息的最后5轮(每轮包含用户消息和AI回复)
    max_turns = 10
    limited_conversation = conversation_messages[-max_turns*2:] if len(conversation_messages) > max_turns*2 else conversation_messages
    
    # 返回系统消息和限制后的对话消息的组合
    return system_messages + limited_conversation

# 创建基础 agent 时使用 combined_state_modifier
agent_executor = create_react_agent(
    llm_4o,
    tools,
    checkpointer=checkpointer,
    state_modifier=combined_state_modifier,
)


def is_return_direct_tool(tool_name: str) -> bool:
    return any([tool_name == t.name and t.return_direct for t in tools])


def is_json_str(value: str) -> bool:
    try:
        json.loads(value)
        return True
    except ValueError:
        return False


def chat(
        query: str,
        config: Optional[RunnableConfig] = None,
        session_id: str=None,
        debug: bool = False,
) -> (Generator[tuple[str, any], None, None]):
    logger.info(f"agent query: {query}")

    assert session_id is not None, "session_id is required"
    common_info = {
        "user_id": get_user_id() or -1,
        "session_id": session_id,
        "sub_session_id": str(uuid.uuid4()).replace('-', ''),
    }

    with Session() as session:
        Message.create(session, **common_info, source=MessageSource.USER.value, content=query)

    if config and config.get("images"):
        images = config["images"]
        content = [{"type": "text", "text": query}]
        for image in images:
            content.append({
                "type": "image_url",
                "image_url": {"url": image.data}
            })
        agent_input = {"messages": [HumanMessage(content=content)]}
    else:
        agent_input = {"messages": [HumanMessage(content=query)]}

    # 检查自定义 OpenAI 凭据
    custom_api_key = config.get("openai_api_key") if config else None
    custom_base_url = config.get("openai_base_url") if config else None

    # 创建 LLM 映射
    if custom_api_key:
        # 使用客户端管理器获取客户端
        custom_llm_mapping = {
            "gpt-4o": get_openai_client("gpt-4o", custom_api_key, custom_base_url),
            "gpt-4o-mini": get_openai_client("gpt-4o-mini", custom_api_key, custom_base_url),
        }
        # 对于其他模型，使用默认实例
        custom_llm_mapping.update({
            "DeepSeek-V3": llm_deepseek,
            "qwen-plus": llm_dashscope
        })
    else:
        custom_llm_mapping = llm_mapping

    # 根据 config 中的 model 参数选择 LLM
    if config and config.get("model") and config["model"] in custom_llm_mapping:
        selected_llm = custom_llm_mapping[config["model"]]
        agent = create_react_agent(selected_llm, tools, checkpointer=checkpointer, state_modifier=combined_state_modifier)
    else:
        agent = agent_executor
    agent.step_timeout = 60  # 将单步超时时间增加到60秒

    try:
        agent_response = agent.stream(agent_input, config, stream_mode="messages")

        current_text = ''
        # data = None
        ext = None
        recall_workflow_data = None
        
        for chunk, _ in agent_response:
            content = chunk.content
            chunk_type = chunk.type
            if not content or not chunk_type:
                continue

            if chunk_type == 'tool':
                tool_name = chunk.name
                attributes = {
                    "tool_name": tool_name,
                }
                with Session() as session:
                    Message.create(session, **common_info, source=MessageSource.TOOL.value, content=content, attributes=attributes)
            
                if is_json_str(content):
                    content_dict = json.loads(content)
                    answer = content_dict.get("answer")
                    data = content_dict.get("data")
                    ext = content_dict.get("ext")
                    
                    # 检查是否是 recall_workflow 的第一步响应
                    step = content_dict.get("step")
                    if tool_name == "recall_workflow" and step == 1:
                        # 保存第一步数据以便后续处理
                        recall_workflow_data = {
                            "instruction": content_dict.get("instruction"),
                            "keywords": content_dict.get("keywords"),
                            "workflows": data
                        }
                        
                else:
                    answer = content
                    data = None
                    ext = None

                if is_return_direct_tool(chunk.name):
                    logger.info(f"agent response answer: {answer}")
                    if ext:
                        logger.info(f"agent response ext: {ext}")
                    yield answer, ext
                    return
            elif chunk_type == 'AIMessageChunk':
                current_text += content
                if not debug:
                    yield current_text, None

        # 处理完第一步后，如果有 recall_workflow 的数据，执行第二步
        if recall_workflow_data:
            logger.info("Executing step 2 of recall_workflow")
            workflow_values = []
            with Session() as session:
                # 获取原始工作流数据
                if recall_workflow_data["workflows"]:
                    workflow_ids = [w.get("id") for w in recall_workflow_data["workflows"]]
                    workflow_dos = Workflow.query_workflow_by_ids(session, workflow_ids)
                    workflow_values = [workflow_do.to_dict().get('workflow') for workflow_do in workflow_dos]
            
            # 执行步骤二：生成工作流
            if workflow_values:
                try:
                    step2_result = generate_workflow_step2(
                        recall_workflow_data["instruction"],
                        recall_workflow_data["keywords"],
                        workflow_values
                    )
                    
                    # 将步骤二的结果添加到原有数据中
                    if recall_workflow_data["workflows"]:
                        recall_workflow_data["workflows"].append(step2_result)
                    else:
                        recall_workflow_data["workflows"] = [step2_result]
                except Exception as e:
                    logger.error(f"Error in step 2 of recall_workflow: {str(e)}", exc_info=True)
                    # 如果步骤2执行过程中报错，就直接使用原始workflows
                
                # 创建新的ext数据
                if ext and isinstance(ext, list):
                    for item in ext:
                        if item.get("type") == "workflow":
                            item["data"] = recall_workflow_data["workflows"]
                
                # 返回完整结果
                yield current_text, ext

        with Session() as session:
            filtered_images = []
            if config and config.get("images"):
                filtered_images = [{k: v for k, v in img.dict().items() if k != 'data'} for img in config["images"]] if config["images"] else []
            Message.create(session, **common_info, source=MessageSource.AI.value, content=current_text, attributes={"ext": ext, "images": filtered_images})

        logger.info(f"agent response answer: {current_text}")
        if ext:
            logger.info(f"agent response ext: {ext}")
        yield current_text, ext
    except TimeoutError:
        logger.error("Agent execution timed out", exc_info=True)
        if config and config.get("model") and config["model"] == "DeepSeek-V3":
            yield "I apologize, but our DeepSeek service provider is currently unstable. Please try using GPT-4 instead.", None
        else:
            yield "I apologize, but the request timed out. Please try again or rephrase your question.", None
        return
    except Exception as e:
        logger.error(f"Agent execution failed: {str(e)}", exc_info=True)
        yield f"I apologize, but an error occurred: {str(e)}", None
        return

```

为了能跟理解原始的架构，展示一recall_workflow的代码：
```python
from hashlib import md5
import json
from typing import List, Dict, Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from agent.tools.tool_funcs.recall_workflow import query_workflows_from_db, generate_workflow_step2, summary
from logger import logger

class RecallWorkflowParamSchema(BaseModel):
    name: str = Field(
        description='''
        Extract the core intent, key technical terms from user input.
        ''')
    description: str = Field(
        description='''
        Concisely describe the user's core requirements, no extra words, including:
        1. Performance requirements (e.g. low VRAM, fast generation)
        2. Source preferences (e.g. official workflows)
        3. Technical specifications and constraints
        4. Model requirements
        ''')

    keywords: List[str] = Field(
        description='''
        Extract all core keywords from user input, make keywords shorter.
        Do not include too generic keywords, like "workflow"|"model"|"apply"|"工作流"|"模型".
        ''')

    instruction: str = Field(
        description='''
    Convert the user's question into a non-technical problem statement from a user-centric perspective, reply use English.
    It articulates the desired functionality or outcome the user wishes to achieve, often in layman terms, 
    without specifying technical or implementation details. The instruction should:
    1. State a concrete creative or computational goal.
    2. Specify input requirements (e.g., "a photo of my cat").
    3. Define desired output characteristics (e.g., "watercolor painting style").
    4. Avoid implementation terms such as nodes, models, or parameters.
    5. Be phrased as a natural language request rather than a technical specification.
    Example: Build a workflow that turns my portrait photos into vintage comic book art. It should preserve facial features accurately while applying bold ink outlines and halftone shading effects.
        ''')

@tool(args_schema=RecallWorkflowParamSchema, return_direct=False)
def recall_workflow(name: str, description: str, keywords: List[str], instruction: str) -> str:
    """
    Recall_workflow Tool is designed to select the most suitable workflow from a pool of candidate workflows based on user requirements.
    Call this tool when the user's intent is to want a workflow or to generate an image with specific requirements.
    Respond in the language used by the user in their question.
    For each workflow, only one representative image will be returned to avoid excessive image data.
    Must add a respond to the last: "You can choose from the recommended workflows above, or let AI generate a personalized solution based on your input (approximately 20 seconds, please wait). If generation fails, the new solution will be automatically hidden."
    """
    # keywords = ['LTX', 'Videos', '高质量']
    logger.info(f"recall_workflow args: {name}| {description} | {keywords}")
    
    # 步骤一：召回工作流
    workflows = query_workflows_from_db(f'{name} | {description}', keywords)
    answer = summary(workflows)

    # Format the response
    if workflows:
        workflow_list = [{
            "type": "workflow",
            "data": workflows
        }]
        ext_items = workflow_list
    else:
        ext_items = None

    return json.dumps({
        "answer": answer,
        "data": workflows,
        "ext": ext_items,
        "instruction": instruction,
        "keywords": keywords,
        "step": 1
    }, ensure_ascii=False)

# 原来的函数内容已经移到 tool_funcs/recall_workflow.py
# 这里只保留对tool的定义和调用

# 导出函数以保持与facade.py的兼容性
__all__ = ['recall_workflow', 'generate_workflow_step2']
```

接口实现层如下：
```python
import base64
from typing import List, Generator
from agent import facade
from agent.intent_call import intent_call
from agent.tools.workflow_param_optimize2 import get_optimized_params
from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import StreamingResponse
import time

from base.core import app
from logger import logger

from base.result import Result

from model.chat import *
from agent.facade import chat
from utils import oss_util, crypto_util
import requests
import openai
from dao.track_dao import Track
from initializer.db_initializer import Session

router = APIRouter()
# conversations: dict[str, any] = {}


@router.post('/invoke')
def invoke_post(request: ChatRequest, req: Request):
    return _handle_invoke(request, req)


@router.get('/invoke')
def invoke_get(req: Request):
    request = ChatRequest(**req.query_params)
    return _handle_invoke(request, req)


def _handle_invoke(request: ChatRequest, req: Request):
    # Extract headers
    accept_language = req.headers.get('Accept-Language')
    openai_base_url = req.headers.get('Openai-Base-Url')
    encrypted_api_key = req.headers.get('Encrypted-Openai-Api-Key')
    model = req.headers.get('Model')
    user_type = getattr(req.state, 'user_type', None)
    
    if user_type == "new":
        def new_user_response_generator():
            if accept_language == "zh-CN":
                text = """
您好！我是ComfyUI-Copilot，您的AI工作流助手。我可以帮您快速上手ComfyUI、提高工作流调优效率，包括：

- 创建ComfyUI工作流、提供工作流模板和示例；
- 提供节点使用建议和最佳实践
- 解答ComfyUI相关问题
- 帮助调试和优化现有工作流
- 查询相关模型信息等

请告诉我你需要什么帮助，我会尽我所能协助你完成ComfyUI相关任务。
第一次访问我们的服务请访问[链接](https://form.typeform.com/to/tkg91K8D)完成Key申请(免费)，并点击⚙️配置Key。
                """
            else:
                text = """Hello! I'm ComfyUI-Copilot, your AI workflow assistant. I can help you quickly get started with ComfyUI and improve your workflow optimization efficiency, including:

- Creating ComfyUI workflows and providing workflow templates and examples
- Offering node usage recommendations and best practices
- Answering ComfyUI-related questions
- Helping debug and optimize existing workflows
- Querying relevant model information

Please let me know what assistance you need, and I'll do my best to help you with your ComfyUI-related tasks.

For first-time visitors, please visit [link](https://form.typeform.com/to/tkg91K8D) to complete your Key application (free), and click ⚙️ to configure your Key.
                """
            
            response = ChatResponse(
                session_id=request.session_id,
                text=text,
                format="markdown",
                finished=True
            )
            yield response.model_dump_json()
            yield '\n'
        
        return StreamingResponse(new_user_response_generator())
    
    if user_type == "unregister":
        def unregister_response_generator():
            if accept_language == "zh-CN":
                text = "ComfyUI-Copilot服务升级，请访问[链接](https://form.typeform.com/to/tkg91K8D)输入邮箱完成Key申请(免费)，并点击⚙️配置Key。若原先已有Key，需要修改成邮箱新收到的Key。"
            else:
                text = "ComfyUI-Copilot service upgrade, please visit [link](https://form.typeform.com/to/tkg91K8D) to input your email and complete your Key application (free), and click 🔨 to configure your Key. If you already have a Key, you need to modify it to the new Key."
            
            response = ChatResponse(
                session_id=request.session_id,
                text=text,
                format="markdown",
                finished=True
            )
            yield response.model_dump_json()
            yield '\n'
        
        return StreamingResponse(unregister_response_generator())
    
    # Build config
    config = {}
    if accept_language:
        config["language"] = accept_language
    if openai_base_url:
        config["openai_base_url"] = openai_base_url
    
    # Handle encrypted API key if provided
    if encrypted_api_key:
        try:
            openai_api_key = crypto_util.decrypt_with_private_key(encrypted_api_key)
            logger.info("Successfully decrypted OpenAI API key")
            config["openai_api_key"] = openai_api_key
        except Exception as e:
            logger.error(f"Failed to decrypt OpenAI API key: {str(e)}")
            # Continue with potentially None openai_api_key
    
    if model:
        config["model"] = model
        
    return do_invoke(request, config)


def do_invoke(request: ChatRequest, params: dict = None) -> StreamingResponse:
    logger.info(f"chat request: {request.model_dump_json()}")

    session_id = request.session_id
    prompt = request.prompt

    if request.mock:
        return StreamingResponse(mock_response(session_id))
    
    if not request.prompt or request.prompt.strip() == "":
        return StreamingResponse(iter([]))

    func_chat = chat
    config = {
        "configurable": {
            "thread_id": session_id,
        }
    }
    
    # Add language from Accept-Language header if available
    if params:
        config.update(params)
    
    if request.images and len(request.images) > 0:
        for image in request.images:
            image_data = image.data
            # Extract base64 data after the comma if it's a data URL
            if image_data.startswith('data:'):
                image_data = image_data.split(',')[1]
            image_data = image_data.encode('utf-8')
            image_data = base64.b64decode(image_data)
            image_url = oss_util.upload_data(image_data, image.filename)
            image.url = image_url
        config["images"] = request.images
    
    if request.ext and isinstance(request.ext, list):
        for ext_item in request.ext:
            if ext_item.type == "model_select" and len(ext_item.data) > 0:
                config["model"] = ext_item.data[0]
    
    if request.intent and request.intent != "":
        config = {"intent": request.intent, "ext": request.ext, "language": config.get("language", "zh-CN")}
        func_chat = intent_call

    def response_generator():
        last_text = None
        ext = None
        for text, ext in func_chat(prompt, config, session_id=session_id):
            response = ChatResponse(
                session_id=session_id,
                text=text,
                finished=ext is not None
            )
            
            # If we have ext information, convert it to list[ExtItem] if needed
            if ext:
                if isinstance(ext, dict):
                    ext = [ExtItem(**ext)]
                elif isinstance(ext, list):
                    ext = [item if isinstance(item, ExtItem) else ExtItem(**item) for item in ext]
                response.ext = ext

            last_text = text
            yield response.model_dump_json()
            yield '\n'

        # Send final response with finished=True if we haven't already
        if not ext:
            final_response = ChatResponse(
                session_id=session_id,
                text=last_text,
                finished=True
            )
            yield final_response.model_dump_json()
            yield '\n'

    return StreamingResponse(response_generator())

```