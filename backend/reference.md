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
from agent.llms import llm_4_chatbot, llm_4o, llm_deepseek, llm_4o_mini, llm_dashscope, get_openai_client, llm_dashscope_deepseek_v3, llm_qwen3, llm_4_1, llm_gemini2_5_flash
from agent.tools.workflow_recall_tool import recall_workflow
from agent.tools.gen_workflow_tool import gen_workflow
from agent.tools.model_search_tool import search_model
from initializer.db_initializer import Session, db_url
from utils.os_util import get_root_path
from dao.message_dao import Message, MessageSource
from dao.node_dao import Node
from dao.workflow_dao import Workflow

tools = [
    recall_workflow,  # 工作流召回
    gen_workflow,  # 工作流生成
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

# with ConnectionPool(
#     conninfo=db_url,
#     max_size=20,
#     kwargs=connection_kwargs,
# ) as pool:
pool = ConnectionPool(db_url, max_size=50, kwargs=connection_kwargs)
checkpointer = PostgresSaver(pool)
checkpointer.setup()

# checkpointer = MemorySaver()

# 修改 LLM 映射字典，使用正确的配置方式
llm_config: Dict = {
    "gemini-2.5-flash": {
        "client":llm_gemini2_5_flash,
        "image_enable":True,
    },
    "gpt-4o": {
        "client":llm_4_1,
        "image_enable":True,
    },
    "gpt-4.1": {
        "client":llm_4_1,
        "image_enable":True,
    },
    "qwen-plus": {
        "client":llm_dashscope,
        "image_enable":False,
    },
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
    
    model = config.get("model") if config else None

    with Session() as session:
        Message.create(session, **common_info, source=MessageSource.USER.value, content=query, attributes={"model": model})

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
            # "gpt-4o-mini": get_openai_client("gpt-4o-mini", custom_api_key, custom_base_url),
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
        tool_results = {}  # 存储不同工具的结果
        workflow_tools_called = set()  # 跟踪调用的工作流工具
        
        for chunk, _ in agent_response:
            content = chunk.content
            chunk_type = chunk.type
            if not content or not chunk_type:
                continue

            if chunk_type == 'tool':
                tool_name = chunk.name
                attributes = {
                    "tool_name": tool_name,
                    "model": model,
                }
                with Session() as session:
                    Message.create(session, **common_info, source=MessageSource.TOOL.value, content=content, attributes=attributes)
            
                if is_json_str(content):
                    content_dict = json.loads(content)
                    answer = content_dict.get("answer")
                    data = content_dict.get("data")
                    tool_ext = content_dict.get("ext")
                    
                    # 存储工具结果
                    tool_results[tool_name] = {
                        "answer": answer,
                        "data": data,
                        "ext": tool_ext,
                        "content_dict": content_dict
                    }
                    
                    # 跟踪工作流相关工具的调用
                    if tool_name in ["recall_workflow", "gen_workflow"]:
                        workflow_tools_called.add(tool_name)
                        
                else:
                    answer = content
                    data = None
                    tool_ext = None
                    tool_results[tool_name] = {
                        "answer": answer,
                        "data": data,
                        "ext": tool_ext,
                        "content_dict": None
                    }
                    
                    # 跟踪工作流相关工具的调用
                    if tool_name in ["recall_workflow", "gen_workflow"]:
                        workflow_tools_called.add(tool_name)

                if is_return_direct_tool(chunk.name):
                    logger.info(f"agent response answer: {answer}")
                    if tool_ext:
                        logger.info(f"agent response ext: {tool_ext}")
                    yield answer, tool_ext
                    return
            elif chunk_type == 'AIMessageChunk':
                current_text += content
                if not debug:
                    yield current_text, None

        # 处理工作流工具的结果合并
        workflow_tools_found = [tool for tool in ["recall_workflow", "gen_workflow"] if tool in tool_results]
        
        if workflow_tools_found:
            logger.info(f"Workflow tools called: {workflow_tools_found}")
            
            # 检查是否同时调用了两个工作流工具
            if "recall_workflow" in tool_results and "gen_workflow" in tool_results:
                logger.info("Both recall_workflow and gen_workflow were called, merging results")
                
                # 检查每个工具是否成功执行
                successful_workflows = []
                
                recall_result = tool_results["recall_workflow"]
                if recall_result["data"] and len(recall_result["data"]) > 0:
                    successful_workflows.extend(recall_result["data"])
                    logger.info(f"recall_workflow succeeded with {len(recall_result['data'])} workflows")
                else:
                    logger.info("recall_workflow failed or returned no data")
                
                gen_result = tool_results["gen_workflow"]
                if gen_result["data"] and len(gen_result["data"]) > 0:
                    successful_workflows.extend(gen_result["data"])
                    logger.info(f"gen_workflow succeeded with {len(gen_result['data'])} workflows")
                else:
                    logger.info("gen_workflow failed or returned no data")
                
                # 创建最终的ext
                if successful_workflows:
                    ext = [{
                        "type": "workflow",
                        "data": successful_workflows
                    }]
                    logger.info(f"Returning {len(successful_workflows)} workflows from successful tools")
                else:
                    ext = None
                    logger.info("No successful workflow data to return")
                    
            elif "recall_workflow" in tool_results and "gen_workflow" not in tool_results:
                # 只调用了recall_workflow，不返回ext，保持finished=false
                logger.info("Only recall_workflow was called, waiting for gen_workflow, not returning ext")
                ext = None
                
            elif "gen_workflow" in tool_results and "recall_workflow" not in tool_results:
                # 只调用了gen_workflow的情况，正常返回结果
                logger.info("Only gen_workflow was called, returning its result")
                gen_result = tool_results["gen_workflow"]
                if gen_result["data"] and len(gen_result["data"]) > 0:
                    ext = [{
                        "type": "workflow",
                        "data": gen_result["data"]
                    }]
                    logger.info(f"Returning {len(gen_result['data'])} workflows from gen_workflow")
                else:
                    ext = None
                    logger.info("gen_workflow failed or returned no data")
        else:
            # 没有调用工作流工具，检查是否有其他工具返回了ext
            for tool_name, result in tool_results.items():
                if result["ext"]:
                    ext = result["ext"]
                    logger.info(f"Using ext from {tool_name}")
                    break

        with Session() as session:
            filtered_images = []
            if config and config.get("images"):
                filtered_images = [{k: v for k, v in img.dict().items() if k != 'data'} for img in config["images"]] if config["images"] else []
            Message.create(session, **common_info, source=MessageSource.AI.value, content=current_text, attributes={"ext": ext, "images": filtered_images, "model": model})

        logger.info(f"agent response answer: {current_text}")
        if ext:
            logger.info(f"agent response ext: {ext}")
        yield current_text, ext
    except TimeoutError:
        logger.error("Agent execution timed out", exc_info=True)
        yield "I apologize, but the request timed out. Please try again or rephrase your question.", None
        return
    except Exception as e:
        logger.error(f"Agent execution failed: {str(e)}", exc_info=True)
        yield f"I apologize, but an error occurred: {str(e)}", None
        return
```

接口调用侧代码如下：
```python

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
```