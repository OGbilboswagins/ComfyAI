'''
Debug Agent for ComfyUI Workflow Error Analysis
'''
import asyncio
import os
import json
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

async def debug_workflow_errors(error_data: Dict[str, Any], workflow_data: Dict[str, Any], config: Dict[str, Any] = None):
    """
    Analyze workflow errors using MCP tools and provide debugging guidance.
    
    Args:
        error_data: Error response from ComfyUI queue endpoint
        workflow_data: Current workflow data from app.graphToPrompt()
        config: Configuration dict with model settings
        
    Yields:
        tuple: (text, ext) where text is accumulated text and ext is structured data
    """
    try:          
        agent = Agent(
            name="ComfyUI-Debug-Agent",
            instructions="""You are a ComfyUI workflow debugging expert. Your role is to analyze workflow errors and provide clear, actionable solutions.

When analyzing errors, follow these steps:

1. **Error Analysis**: Carefully examine the error data to identify:
   - Error types and their root causes
   - Affected nodes and their relationships
   - Missing or incorrect values

2. **Solution Guidance**: Provide specific, actionable solutions:
   - Exact parameter values that need to be changed
   - Alternative node configurations
   - Missing model/checkpoint recommendations
   - File path corrections

3. **Response Format**: Structure your response with:
   - Clear problem description
   - Step-by-step solutions
   - Alternative approaches if applicable
   - Prevention tips

4. **Language**: Always respond in English for consistency.

5. **Focus Areas**:
   - Model/checkpoint compatibility issues
   - Node parameter validation errors
   - Missing dependencies or files
   - Node connection problems
   - Resource availability issues

Do not use tools unless specifically needed for complex analysis. Focus on providing immediate, practical debugging guidance based on the error information provided.
                """,
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
        )

        # Format the debug prompt with error and workflow context
        debug_prompt = f"""I have a ComfyUI workflow that's encountering errors when queued. Please help me debug and fix these issues.

**Error Information:**
```json
{json.dumps(error_data, indent=2)}
```

**Workflow Context:**
```json
{json.dumps(workflow_data, indent=2)}
```

Please analyze these errors and provide specific solutions to fix them. Focus on:
1. What exactly is wrong
2. How to fix each error
3. Recommended parameter values or alternatives
4. Any other potential issues I should be aware of

Provide clear, step-by-step guidance that I can immediately implement."""

        messages = [{"role": "user", "content": debug_prompt}]
            
        print(f"-- Processing debug request with {len(messages)} messages")

        result = Runner.run_streamed(
            agent,
            input=messages,
        )
        print("=== Debug Agent Run starting ===")
        
        # Variables to track response state
        current_text = ''
        ext = None
        last_yield_length = 0
        
        async for event in result.stream_events():
            # Handle different event types
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                # Stream text deltas for real-time response
                delta_text = event.data.delta
                if delta_text:
                    current_text += delta_text
                    print(f"-- Delta received: '{delta_text}', current_text length: {len(current_text)}")
                    # Yield tuple (accumulated_text, None) for streaming
                    if len(current_text) > last_yield_length:
                        last_yield_length = len(current_text)
                        yield (current_text, None)
                continue
                
            elif event.type == "agent_updated_stream_event":
                print(f"Debug Agent updated: {event.new_agent.name}")
                continue
                
            elif event.type == "run_item_stream_event":
                if event.item.type == "tool_call_item":
                    print(f"-- Tool '{event.item.type}' was called")
                elif event.item.type == "tool_call_output_item":
                    print(f"-- Tool output: {event.item.output}")
                    # Store tool output for potential ext data processing (not used)
                elif event.item.type == "message_output_item":
                    # Handle message output
                    text = ItemHelpers.text_message_output(event.item)
                    if text:
                        print(f"-- Debug Message: {text}\n\n")
                else:
                    pass  # Ignore other event types

        print("\n=== Debug Agent Run complete ===")
        
        # Final yield with complete text and ext data
        yield current_text, None
            
    except Exception as e:
        print(f"Error in debug_workflow_errors: {str(e)}")
        error_message = f"I apologize, but an error occurred while analyzing your workflow: {str(e)}"
        # Yield error as tuple to maintain consistency
        yield error_message, None


async def test_debug():
    # Test error data format
    test_error_data = {
        "error": {
            "type": "prompt_outputs_failed_validation",
            "message": "Prompt outputs failed validation",
            "details": "",
            "extra_info": {}
        },
        "node_errors": {
            "12": {
                "errors": [
                    {
                        "type": "value_not_in_list",
                        "message": "Value not in list",
                        "details": "control_net_name: 'control_v11p_sd15_scribble_fp16.safetensors' not in (list of length 41)",
                        "extra_info": {
                            "input_name": "control_net_name",
                            "input_config": None,
                            "received_value": "control_v11p_sd15_scribble_fp16.safetensors"
                        }
                    }
                ],
                "dependent_outputs": ["9"],
                "class_type": "ControlNetLoader"
            }
        }
    }
    
    test_workflow_data = {
        "output": {
            "12": {
                "inputs": {
                    "control_net_name": "control_v11p_sd15_scribble_fp16.safetensors"
                },
                "class_type": "ControlNetLoader"
            }
        }
    }
    
    async for result in debug_workflow_errors(test_error_data, test_workflow_data):
        print(f"Test debug result: {result}")


if __name__ == "__main__":
    asyncio.run(test_debug())
