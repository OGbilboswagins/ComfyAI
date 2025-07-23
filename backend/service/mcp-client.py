'''
Author: ai-business-hql qingli.hql@alibaba-inc.com
Date: 2025-06-16 16:50:17
LastEditors: ai-business-hql qingli.hql@alibaba-inc.com
LastEditTime: 2025-07-23 17:26:49
FilePath: /comfyui_copilot/backend/service/mcp-client.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import asyncio
import os
from typing import List, Dict, Any, Optional

from agents._config import set_default_openai_api
from agents.agent import Agent
from agents.items import ItemHelpers
from agents.mcp import MCPServerSse
from agents.run import Runner
from agents.tracing import set_tracing_disabled
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

# @function_tool
# def get_weather(city: str) -> str:
#     return f"The weather in {city} is sunny."

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
                "url": os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp-server/mcp"),
                "timeout": 300.0,
            },
            cache_tools_list=True,
            client_session_timeout_seconds=300.0
        ) as server:
            # tools = await server.list_tools()
            
            # Get model from environment or use default
            model_name = os.environ.get("OPENAI_MODEL", "gemini-2.5-flash")
            if config and config.get("model_select") and config.get("model_select") != "":
                model_name = config.get("model_select")
            if config and config.get("openai_api_key") and config.get("openai_api_key") != "":
                os.environ["OPENAI_API_KEY"] = config.get("openai_api_key")
            if config and config.get("openai_base_url") and config.get("openai_base_url") != "":
                os.environ["OPENAI_BASE_URL"] = config.get("openai_base_url")
            print(f"Using model: {model_name}")
            
            agent = Agent(
                name="ComfyUI-Copilot",
                instructions="""You are a powerful AI assistant for designing image processing workflows, capable of automating problem-solving using tools and commands.

You must adhere to the following constraints to complete the task:

- [Important!] Respond must in the language used by the user in their question. Regardless of the language returned by the tools being called, please return the results based on the language used in the user's query. For example, if user ask by English, you must return
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
- Respond with markdown, using a minimum of 3 heading levels (H3, H4, H5...), and when including images use the format ![alt text](url),
- [Critical!] When the user's intent is to get workflows or generate images with specific requirements, you MUST ALWAYS call BOTH recall_workflow tool AND gen_workflow tool to provide comprehensive workflow options. Never call just one of these tools - both are required for complete workflow assistance. First call recall_workflow to find existing similar workflows, then call gen_workflow to generate new workflow options.
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
            tool_results = {}  # Store results from different tools
            workflow_tools_called = set()  # Track called workflow tools
            last_yield_length = 0
            tool_call_queue = []  # Queue to track tool calls in order
            current_tool_call = None  # Track current tool being called
            
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
                        # Get tool name correctly using raw_item.name
                        tool_name = getattr(event.item.raw_item, 'name', 'unknown_tool')
                        # Add to queue instead of overwriting current_tool_call
                        tool_call_queue.append(tool_name)
                        print(f"-- Tool '{tool_name}' was called")
                        
                        # Track workflow tools being called
                        if tool_name in ["recall_workflow", "gen_workflow"]:
                            workflow_tools_called.add(tool_name)
                            print(f"-- Workflow tool '{tool_name}' added to tracking")
                    elif event.item.type == "tool_call_output_item":
                        print(f"-- Tool output: {event.item.output}")
                        # Store tool output for potential ext data processing
                        tool_output_data_str = event.item.output
                        
                        # Get the next tool from the queue (FIFO)
                        if tool_call_queue:
                            tool_name = tool_call_queue.pop(0)
                            print(f"-- Associating output with tool '{tool_name}'")
                        else:
                            tool_name = 'unknown_tool'
                            print(f"-- Warning: No tool call in queue for output")
                        
                        try:
                            import json
                            tool_output_data = json.loads(tool_output_data_str)
                            if tool_output_data.get('text'):
                                parsed_output = json.loads(tool_output_data['text'])
                                answer = parsed_output.get("answer")
                                data = parsed_output.get("data")
                                tool_ext = parsed_output.get("ext")
                                
                                # Store tool results similar to reference facade.py
                                tool_results[tool_name] = {
                                    "answer": answer,
                                    "data": data,
                                    "ext": tool_ext,
                                    "content_dict": parsed_output
                                }
                                print(f"-- Stored result for tool '{tool_name}': data={len(data) if data else 0}, ext={tool_ext}")
                                
                                # Track workflow tools that produced results
                                if tool_name in ["recall_workflow", "gen_workflow"]:
                                    print(f"-- Workflow tool '{tool_name}' produced result with data: {len(data) if data else 0}")
                                    
                        except (json.JSONDecodeError, TypeError) as e:
                            # If not JSON or parsing fails, treat as regular text
                            print(f"-- Failed to parse tool output as JSON: {e}")
                            tool_results[tool_name] = {
                                "answer": tool_output_data_str,
                                "data": None,
                                "ext": None,
                                "content_dict": None
                            }
                        
                    elif event.item.type == "message_output_item":
                        # Handle message output - this is the main response text
                        text = ItemHelpers.text_message_output(event.item)
                        if text:
                            print(f"-- Message: {text}\n\n")
                    else:
                        pass  # Ignore other event types

            print("\n=== MCP Agent Run complete ===")

            # Add detailed debugging info about tool results
            print(f"=== Tool Results Summary ===")
            print(f"Total tool results: {len(tool_results)}")
            for tool_name, result in tool_results.items():
                print(f"Tool: {tool_name}")
                print(f"  - Has data: {result['data'] is not None}")
                print(f"  - Data length: {len(result['data']) if result['data'] else 0}")
                print(f"  - Has ext: {result['ext'] is not None}")
                print(f"  - Answer preview: {result['answer'][:100] if result['answer'] else 'None'}...")
            print(f"=== End Tool Results Summary ===\n")

            # Process workflow tools results integration similar to reference facade.py
            workflow_tools_found = [tool for tool in ["recall_workflow", "gen_workflow"] if tool in tool_results]
            finished = True  # Default finished state

            if workflow_tools_found:
                print(f"Workflow tools called: {workflow_tools_found}")
                
                # Check if both workflow tools were called
                if "recall_workflow" in tool_results and "gen_workflow" in tool_results:
                    print("Both recall_workflow and gen_workflow were called, merging results")
                    
                    # Check each tool's success and merge results
                    successful_workflows = []

                    recall_result = tool_results["recall_workflow"]
                    if recall_result["data"] and len(recall_result["data"]) > 0:
                        print(f"recall_workflow succeeded with {len(recall_result['data'])} workflows")
                        print(f"  - Workflow IDs: {[w.get('id') for w in recall_result['data']]}")
                        successful_workflows.extend(recall_result["data"])
                    else:
                        print("recall_workflow failed or returned no data")

                    gen_result = tool_results["gen_workflow"]
                    if gen_result["data"] and len(gen_result["data"]) > 0:
                        print(f"gen_workflow succeeded with {len(gen_result['data'])} workflows")
                        print(f"  - Workflow IDs: {[w.get('id') for w in gen_result['data']]}")
                        successful_workflows.extend(gen_result["data"])
                    else:
                        print("gen_workflow failed or returned no data")

                    # Remove duplicates based on workflow ID
                    seen_ids = set()
                    unique_workflows = []
                    for workflow in successful_workflows:
                        workflow_id = workflow.get('id')
                        if workflow_id and workflow_id not in seen_ids:
                            seen_ids.add(workflow_id)
                            unique_workflows.append(workflow)
                            print(f"  - Added unique workflow: {workflow_id} - {workflow.get('name', 'Unknown')}")
                        elif workflow_id:
                            print(f"  - Skipped duplicate workflow: {workflow_id} - {workflow.get('name', 'Unknown')}")
                        else:
                            # If no ID, add anyway (shouldn't happen but just in case)
                            unique_workflows.append(workflow)
                            print(f"  - Added workflow without ID: {workflow.get('name', 'Unknown')}")

                    print(f"Total workflows before deduplication: {len(successful_workflows)}")
                    print(f"Total workflows after deduplication: {len(unique_workflows)}")

                    # Create final ext structure
                    if unique_workflows:
                        ext = [{
                            "type": "workflow",
                            "data": unique_workflows
                        }]
                        print(f"Returning {len(unique_workflows)} workflows from successful tools")
                    else:
                        ext = None
                        print("No successful workflow data to return")
                    
                    # Both tools called, finished = True
                    finished = True
                        
                elif "recall_workflow" in tool_results and "gen_workflow" not in tool_results:
                    # Only recall_workflow was called, don't return ext, keep finished=false
                    print("Only recall_workflow was called, waiting for gen_workflow, not returning ext")
                    ext = None
                    finished = False  # This is the key: keep finished=false to wait for gen_workflow
                    
                elif "gen_workflow" in tool_results and "recall_workflow" not in tool_results:
                    # Only gen_workflow was called, return its result normally
                    print("Only gen_workflow was called, returning its result")
                    gen_result = tool_results["gen_workflow"]
                    if gen_result["data"] and len(gen_result["data"]) > 0:
                        ext = [{
                            "type": "workflow",
                            "data": gen_result["data"]
                        }]
                        print(f"Returning {len(gen_result['data'])} workflows from gen_workflow")
                    else:
                        ext = None
                        print("gen_workflow failed or returned no data")
                    
                    # Only gen_workflow called, finished = True
                    finished = True
            else:
                # No workflow tools called, check if other tools returned ext
                for tool_name, result in tool_results.items():
                    if result["ext"]:
                        ext = result["ext"]
                        print(f"Using ext from {tool_name}")
                        break
                
                # No workflow tools, finished = True
                finished = True
            
            # Final yield with complete text, ext data, and finished status
            # Return as tuple (text, ext_with_finished) where ext_with_finished includes finished info
            if ext:
                # Add finished status to ext structure
                ext_with_finished = {
                    "data": ext,
                    "finished": finished
                }
            else:
                ext_with_finished = {
                    "data": None,
                    "finished": finished
                }
            
            yield (current_text, ext_with_finished)
            
    except Exception as e:
        print(f"Error in comfyui_agent_invoke: {str(e)}")
        error_message = f"I apologize, but an error occurred while processing your request: {str(e)}"
        # Yield error as tuple with finished=True
        error_ext = {
            "data": None,
            "finished": True
        }
        yield (error_message, error_ext)

