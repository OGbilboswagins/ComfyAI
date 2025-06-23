'''
Author: ai-business-hql qingli.hql@alibaba-inc.com
Date: 2025-06-16 16:50:17
LastEditors: ai-business-hql qingli.hql@alibaba-inc.com
LastEditTime: 2025-06-18 19:30:44
FilePath: /comfyui_copilot/backend/service/mcp-client.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import asyncio
import os
from typing import List, Dict, Any, Optional
from agents import Agent, Runner, function_tool, set_default_openai_api, set_tracing_disabled, ItemHelpers
from agents.mcp import MCPServerSse
from openai.types.responses import ResponseTextDeltaEvent

# Load environment variables from server.env
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

@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny."

class ImageData:
    """Image data structure to match reference implementation"""
    def __init__(self, filename: str, data: str, url: str = None):
        self.filename = filename
        self.data = data  # base64 data
        self.url = url    # uploaded URL

async def comfyui_agent_invoke(messages: List[Dict[str, Any]], images: List[ImageData] = None, config: Dict[str, Any] = None):
    """
    Invoke the ComfyUI agent with MCP tools and image support.
    
    This function mimics the behavior of the reference facade.py chat function,
    yielding (text, ext) tuples similar to the reference implementation.
    
    Args:
        messages: List of messages in OpenAI format [{"role": "user", "content": "..."}, ...]
        images: List of image data objects (optional)
        
    Yields:
        tuple: (text, ext) where text is accumulated text and ext is structured data
    """
    try:
        async with MCPServerSse(
            params= {
                "url": os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp-server/mcp"),
                "timeout": 300.0,
            },
            cache_tools_list=True,
            client_session_timeout_seconds=300.0
        ) as server:
            tools = await server.list_tools()
            
            # Get model from environment or use default
            model_name = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
            if config and config.get("model_select") and config.get("model_select") != "":
                model_name = config.get("model_select")
            if config and config.get("openai_api_key") and config.get("openai_api_key") != "":
                os.environ["OPENAI_API_KEY"] = config.get("openai_api_key")
            if config and config.get("openai_base_url") and config.get("openai_base_url") != "":
                os.environ["OPENAI_BASE_URL"] = config.get("openai_base_url")
            print(f"Using model: {model_name}")
            print(f"OpenAI API Base: {os.environ.get('OPENAI_BASE_URL', 'default')}")
            print(f"OpenAI API Key: {os.environ.get('OPENAI_API_KEY', 'default')}")
            
            agent = Agent(
                name="ComfyUI-Copilot",
                instructions="""You are a powerful AI assistant for designing image processing workflows, capable of automating problem-solving using tools and commands.

You must adhere to the following constraints to complete the task:

- [Important!] Respond must in the language used by the user in their question. Regardless of the language returned by the tools being called, please return the results based on the language used in the user's query. For example, if user ask by English, you must return in English.
- Use only one tool for each decision you make.
- Ensure that the commands or tools you invoke are within the provided tool list.
- If the execution of a command or tool fails, try changing the parameters or their format before attempting again.
- Your generated responses must follow the factual information given above. Do not make up information.
- If the result obtained is incorrect, try rephrasing your approach.
- Do not query for already obtained information repeatedly. If you successfully invoked a tool and obtained relevant information, carefully confirm whether you need to invoke it again.
- Ensure that the actions you generate can be executed accurately. Actions may include specific methods and target outputs.
- When you encounter a concept, try to obtain its precise definition and analyze what inputs can yield specific values for it.
- When generating a natural language query, include all known information in the query.
- Before performing any analysis or calculation, ensure that all sub-concepts involved have been defined.
- Printing the entire content of a file is strictly prohibited, as such actions have high costs and can lead to unforeseen consequences.
- Ensure that when you call a tool, you have obtained all the input variables for that tool, and do not fabricate any input values for it.
- When the user's intent is to query, return the query result directly without attempting to assist the user in performing operations.
- When the user's intent is to get prompts for image generation (like Stable Diffusion). Use specific descriptive language with proper weight modifiers (e.g., (word:1.2)), prefer English terms, and separate elements with commas. Include quality terms (high quality, detailed), style specifications (realistic, anime), lighting (cinematic, golden hour), and composition (wide shot, close up) as needed. When appropriate, include negative prompts to exclude unwanted elements. Return words divided by commas directly without any additional text.
- When a user pastes text that appears to be an error message (containing terms like "Failed", "Error", or stack traces), prioritize providing troubleshooting help rather than invoking search tools. Follow these steps:
  1. Analyze the error to identify the root cause (error type, affected component, missing dependencies, etc.)
  2. Explain the issue in simple terms
  3. Provide concrete, executable solutions including:
     - Specific shell commands to fix the issue (e.g., `git pull`, `pip install`, file path corrections)
     - Code snippets if applicable
     - Configuration file changes with exact paths and values
  4. If the error relates to a specific ComfyUI extension or node, include instructions for:
     - Updating the extension (`cd path/to/extension && git pull`)
     - Reinstalling dependencies
     - Alternative approaches if the extension is problematic
  5. Suggest preventative measures to avoid similar errors
  6. Do NOT automatically invoke search_node or other tools when processing error messages unless specifically requested
- When user provides images, analyze them carefully and incorporate the visual information into your responses and recommendations.
- Ensure your responses do not contain illegal or offensive information.
                """,
                mcp_servers=[server],
                model=model_name,
            )

            # Use messages directly as agent input since they're already in OpenAI format
            # The caller has already handled image formatting within messages
            agent_input = messages
            print(f"-- Processing {len(messages)} messages")

            result = Runner.run_streamed(
                agent,
                input=agent_input,
            )
            print("=== MCP Agent Run starting ===")
            
            # Variables to track response state similar to reference facade.py
            current_text = ''
            ext = None
            tool_output_data = None
            last_yield_length = 0
            
            async for event in result.stream_events():
                # Handle different event types similar to reference implementation
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    # Stream text deltas for real-time response
                    delta_text = event.data.delta
                    if delta_text:
                        current_text += delta_text
                        print(f"-- Delta received: '{delta_text}', current_text length: {len(current_text)}")
                        # Yield tuple (accumulated_text, None) for streaming - similar to facade.py
                        # Only yield if we have new content to avoid duplicate yields
                        if len(current_text) > last_yield_length:
                            last_yield_length = len(current_text)
                            yield (current_text, None)
                    continue
                    
                elif event.type == "agent_updated_stream_event":
                    print(f"Agent updated: {event.new_agent.name}")
                    continue
                    
                elif event.type == "run_item_stream_event":
                    if event.item.type == "tool_call_item":
                        print(f"-- Tool '{event.item.type}' was called")
                    elif event.item.type == "tool_call_output_item":
                        print(f"-- Tool output: {event.item.output}")
                        # Store tool output for potential ext data processing
                        tool_output_data_str = event.item.output
                        try:
                            import json
                            tool_output_data = json.loads(tool_output_data_str)
                            if tool_output_data['text']:
                                parsed_output = json.loads(tool_output_data['text'])
                                if 'ext' in parsed_output:
                                    ext = parsed_output['ext']
                                if 'answer' in parsed_output:
                                    # If tool returns direct answer, add it to current text
                                    answer_text = parsed_output['answer']
                                    # yield (current_text, None)
                        except (json.JSONDecodeError, TypeError):
                            # If not JSON or parsing fails, treat as regular text
                            pass
                            
                    elif event.item.type == "message_output_item":
                        # Handle message output - this is the main response text
                        # This usually contains the final complete response, so we don't yield it here
                        # to avoid overwriting the streaming text. We'll use it in the final yield.
                        text = ItemHelpers.text_message_output(event.item)
                        if text:
                            print(f"-- Message: {text}\n\n")
                            # Store the complete message but don't yield it here to avoid interrupting stream
                            # The final yield will use current_text which contains the streamed content
                    else:
                        pass  # Ignore other event types

            print("\n=== MCP Agent Run complete ===")
            
            # Final yield with complete text and ext data - similar to facade.py pattern
            yield (current_text, ext)
            
    except Exception as e:
        print(f"Error in comfyui_agent_invoke: {str(e)}")
        error_message = f"I apologize, but an error occurred while processing your request: {str(e)}"
        # Yield error as tuple to maintain consistency
        yield (error_message, None)


async def test():
    test_messages = [
        {"role": "user", "content": "我需要一个推荐的工作流来创建SK波普风插画，请帮我找到合适的工作流。"}
    ]
    async for result in comfyui_agent_invoke(test_messages):
        print(f"Test result: {result}")


if __name__ == "__main__":
    asyncio.run(test())