'''
Debug Agent for ComfyUI Workflow Error Analysis
'''
import os
import json
from typing import List, Dict, Any, Optional
from agents._config import set_default_openai_api
from agents.agent import Agent
from agents.items import ItemHelpers
from agents.run import Runner
from agents.tool import function_tool
from agents.tracing import set_tracing_disabled
from ..service.workflow_rewrite_tools import *
from openai.types.responses import ResponseTextDeltaEvent

from ..service.parameter_tools import *
from ..service.database import get_workflow_data, save_workflow_data

# Import ComfyUI internal modules
import execution
import uuid
import logging

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
def run_workflow(session_id: str) -> str:
    """验证当前session的工作流并返回结果"""
    try:
        workflow_data = get_workflow_data(session_id)
        if not workflow_data:
            return json.dumps({"error": "No workflow data found for this session"})
        
        print(f"Validating workflow for session {session_id}")
        
        # 直接调用 ComfyUI 的内部验证函数，避免 HTTP 请求
        try:
            # 调用工作流验证
            valid = execution.validate_prompt(workflow_data)
            
            if valid[0]:  # 验证成功
                # valid = (True, None, outputs_to_execute, node_errors)
                prompt_id = str(uuid.uuid4())
                result = {
                    "success": True,
                    "prompt_id": prompt_id,
                    "outputs_to_execute": valid[2],
                    "node_errors": valid[3],
                    "message": "Workflow validation successful"
                }
                print(f"Workflow validation successful for session {session_id}")
                return json.dumps(result)
            else:
                # valid = (False, error, outputs_to_execute, node_errors)
                error_info = valid[1]  # 错误信息
                node_errors = valid[3]  # 节点错误
                
                result = {
                    "success": False,
                    "error": error_info,
                    "node_errors": node_errors,
                    "message": "Workflow validation failed"
                }
                print(f"Workflow validation failed for session {session_id}: {error_info}")
                return json.dumps(result)
                
        except Exception as e:
            print(f"Exception during workflow validation: {str(e)}")
            import traceback
            traceback.print_exc()
            return json.dumps({
                "success": False,
                "error": {
                    "type": "validation_exception",
                    "message": f"Exception during validation: {str(e)}",
                    "details": str(e)
                },
                "node_errors": {}
            })
        
    except Exception as e:
        print(f"Error in run_workflow: {str(e)}")
        import traceback
        traceback.print_exc()
        return json.dumps({
            "success": False,
            "error": {
                "type": "function_error",
                "message": f"Failed to validate workflow: {str(e)}",
                "details": str(e)
            },
            "node_errors": {}
        })

@function_tool
def analyze_error_type(error_data: str) -> str:
    """分析错误类型，判断应该使用哪个agent，输入应为JSON字符串"""
    try:
        # 解析JSON字符串
        error_dict = json.loads(error_data) if isinstance(error_data, str) else error_data
        
        error_analysis = {
            "error_type": "unknown",
            "recommended_agent": "workflow_bugfix_default_agent",
            "error_details": [],
            "affected_nodes": []
        }
        
        # 检查新的返回格式
        if "success" in error_dict:
            if error_dict["success"]:
                # 工作流验证成功
                error_analysis["error_type"] = "no_error"
                error_analysis["recommended_agent"] = "none"
                error_analysis["error_details"] = [{"message": "Workflow validation successful"}]
                return json.dumps(error_analysis)
            else:
                # 工作流验证失败，继续分析错误类型
                pass
        
        # 检查是否有node_errors (ComfyUI验证错误格式)
        if "node_errors" in error_dict and error_dict["node_errors"]:
            node_errors = error_dict["node_errors"]
            parameter_errors = 0
            connection_errors = 0
            other_errors = 0
            
            for node_id, node_error in node_errors.items():
                error_analysis["affected_nodes"].append(node_id)
                
                if "errors" in node_error:
                    for error in node_error["errors"]:
                        error_detail = {
                            "node_id": node_id,
                            "error_type": error.get("type", "unknown"),
                            "message": error.get("message", ""),
                            "details": error.get("details", "")
                        }
                        error_analysis["error_details"].append(error_detail)
                        
                        # 改进的错误类型判断
                        error_type = error.get("type", "").lower()
                        error_message = error.get("message", "").lower()
                        
                        # 优先判断连接相关错误（结构性错误）
                        if (any(keyword in error_message for keyword in [
                            "connection", "input connection", "required input", "missing input",
                            "not connected", "no connection", "link", "output", "socket"
                        ]) or 
                        error_type in ["missing_input", "invalid_connection", "connection_error"]):
                            connection_errors += 1
                        
                        # 参数相关错误的判断（更精确）
                        elif (error_type in ["value_not_in_list", "invalid_input", "invalid_value"] or
                            any(keyword in error_message for keyword in [
                                "value not in list", "invalid value", "not found in list",
                                "parameter value", "invalid parameter", "model not found"
                            ])):
                            parameter_errors += 1
                        
                        # 其他结构性错误
                        else:
                            other_errors += 1
            
            # 根据错误类型决定使用哪个agent（连接错误优先级最高）
            if connection_errors > 0:
                error_analysis["error_type"] = "connection_error"
                error_analysis["recommended_agent"] = "workflow_bugfix_default_agent"
            elif parameter_errors > 0:
                error_analysis["error_type"] = "parameter_error"
                error_analysis["recommended_agent"] = "parameter_agent"
            else:
                error_analysis["error_type"] = "structural_error"
                error_analysis["recommended_agent"] = "workflow_bugfix_default_agent"
        
        elif "error" in error_dict:
            # 处理其他格式的错误
            error_info = error_dict.get("error", {})
            if isinstance(error_info, dict):
                error_message = error_info.get("message", "").lower()
                error_type = error_info.get("type", "").lower()
            else:
                error_message = str(error_info).lower()
                error_type = "unknown"
            
            # 改进的错误分类逻辑
            if any(keyword in error_message for keyword in [
                "connection", "input connection", "required input", "missing input",
                "not connected", "no connection", "link", "output", "socket"
            ]):
                error_analysis["error_type"] = "connection_error"
                error_analysis["recommended_agent"] = "workflow_bugfix_default_agent"
            elif any(keyword in error_message for keyword in [
                "value not in list", "invalid value", "parameter", "model not found",
                "invalid parameter", "not found in list"
            ]):
                error_analysis["error_type"] = "parameter_error"
                error_analysis["recommended_agent"] = "parameter_agent"
            else:
                error_analysis["error_type"] = "structural_error"
                error_analysis["recommended_agent"] = "workflow_bugfix_default_agent"
            
            error_analysis["error_details"].append({
                "error_type": error_type,
                "message": error_info.get("message", str(error_info)) if isinstance(error_info, dict) else str(error_info),
                "details": error_info.get("details", "") if isinstance(error_info, dict) else ""
            })
        
        return json.dumps(error_analysis)
        
    except Exception as e:
        return json.dumps({
            "error_type": "analysis_failed",
            "recommended_agent": "workflow_bugfix_default_agent",
            "error": f"Failed to analyze error: {str(e)}"
        })

@function_tool
def save_current_workflow(session_id: str, workflow_data: str) -> str:
    """保存当前工作流数据到数据库，workflow_data应为JSON字符串"""
    try:
        # 解析JSON字符串
        workflow_dict = json.loads(workflow_data) if isinstance(workflow_data, str) else workflow_data
        
        version_id = save_workflow_data(
            session_id, 
            workflow_dict, 
            attributes={"action": "debug_save", "description": "Workflow saved during debugging"}
        )
        return json.dumps({
            "success": True,
            "version_id": version_id,
            "message": f"Workflow saved with version ID: {version_id}"
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to save workflow: {str(e)}"})


async def debug_workflow_errors(workflow_data: Dict[str, Any], config: Dict[str, Any] = None):
    """
    Analyze and debug workflow errors using multi-agent architecture.
    
    This function validates ComfyUI workflows using internal functions instead of HTTP requests
    to avoid blocking issues. It coordinates with specialized agents to fix different types of errors.
    
    Args:
        workflow_data: Current workflow data from app.graphToPrompt()
        config: Configuration dict with model settings
        
    Yields:
        tuple: (text, ext) where text is accumulated text and ext is structured data
    """
    try:
        # 生成session_id (可以从config中获取，或者生成新的)
        session_id = config.get('session_id') if config else str(uuid.uuid4())
        
        # 1. 保存工作流数据到数据库
        print(f"Saving workflow data for session {session_id}")
        save_result = save_workflow_data(
            session_id, 
            workflow_data, 
            attributes={"action": "debug_start", "description": "Initial workflow save for debugging"}
        )
        print(f"Workflow saved with version ID: {save_result}")
        
        agent = Agent(
            name="ComfyUI-Debug-Coordinator",
            instructions=f"""You are a ComfyUI workflow debugging coordinator. Your role is to analyze workflow errors and coordinate with specialized agents to fix them.

**Session ID:** {session_id}

**Your Process:**
1. **Validate the workflow**: Use run_workflow("{session_id}") to validate the workflow and capture any errors
2. **Analyze errors**: If errors occur, use analyze_error_type() to determine the error type and hand off to the appropriate specialist:
   - Hand off to Parameter Agent for parameter-related errors (value_not_in_list, missing models, invalid values)
   - Hand off to Workflow Bugfix Default Agent for structural issues (Node connection issues, missing nodes, incompatible configurations)
3. **After specialist returns**: Continue validation from step 1 to check if the issue is resolved
4. **Repeat until complete**: Continue this cycle until there are no errors or maximum 6 iterations

**Critical Guidelines:**
- ALWAYS validate the workflow first to check for errors
- If no errors occur, report success immediately and STOP
- If errors occur, analyze them and hand off to the appropriate specialist
- When specialists return to you: IMMEDIATELY re-validate the workflow to check if the issue is resolved
- Continue the debugging cycle until all errors are fixed or max iterations reached
- Provide clear, streaming updates about what you're doing
- Be concise but informative in your responses

**Handoff Strategy:**
- Hand off errors to specialists for fixing
- When they return: Re-validate immediately to check results
- If new errors appear: Analyze and hand off again
- If same errors persist: Try the other specialist or report limitation

**Note**: The workflow validation is done using ComfyUI's internal functions, not actual execution, so it's fast and safe.

Start by validating the workflow to see its current state.""",
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            tools=[run_workflow, analyze_error_type, save_current_workflow],
        )
        
        workflow_bugfix_default_agent = Agent(
            name="Workflow Bugfix Default Agent",
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            handoff_description="""
            I am the Workflow Bugfix Default Agent. I specialize in fixing structural issues in ComfyUI workflows.
            
            I can help with:
            - Fixing broken node connections
            - Adding missing nodes
            - Removing problematic nodes
            - Resolving node compatibility issues
            - Restructuring workflows to fix errors
            
            Call me when you have workflow structure errors that require modifying the workflow graph itself.
            """,
            instructions="""
            You are the Workflow Bugfix Default Agent, an expert in ComfyUI workflow structure analysis and modification.
            
            **CRITICAL**: Your job is to analyze structural errors and fix them. After making fixes, you MUST transfer back to the Debug Coordinator to verify the results.
            
            **Your Process:**
            
            1. **Get current workflow** using get_current_workflow()
            2. **Validate connections** using validate_workflow_connections() 
            3. **Identify and fix issues** using the appropriate tools:
            - **Missing connections**: Use fix_node_connections()
            - **Missing nodes**: Use add_missing_node()
            - **Problematic nodes**: Use remove_node()
            4. **Save changes** using update_workflow()
            5. **MANDATORY**: Transfer back to Debug Coordinator for verification
            
            **Transfer Rules:**
            - After making structural fixes: Save with update_workflow() then TRANSFER to ComfyUI-Debug-Coordinator
            - If no structural issues found: Report findings then TRANSFER to ComfyUI-Debug-Coordinator
            - If fixes cannot be applied: Explain why then TRANSFER to ComfyUI-Debug-Coordinator
            - ALWAYS transfer back - do not end without handoff
            
            **Tool Usage Guidelines:**
            - fix_node_connections(): Use for broken connections between existing nodes
            - add_missing_node(): Use when workflow needs additional nodes
            - remove_node(): Use for incompatible or problematic nodes
            - update_workflow(): Use to save your changes (ALWAYS call this after fixes)
            
            **Response Format:**
            1. "Structural analysis: [brief description of issues]"
            2. "Fixes applied: [what you changed]"
            3. "Workflow updated: [confirmation]"
            4. Transfer to ComfyUI-Debug-Coordinator for verification
            
            **Remember**: Focus on making necessary structural changes, then ALWAYS transfer back to let the coordinator verify the workflow.
            """,
            tools=[get_current_workflow, get_node_info, update_workflow, validate_workflow_connections, 
                fix_node_connections, add_missing_node, remove_node],
            handoffs=[agent],
        )
        
        parameter_agent = Agent(
            name="Parameter Agent",
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            handoff_description="""
            I am the Parameter Agent. I specialize in handling parameter-related errors in ComfyUI workflows.
            
            I can help with:
            - Finding valid parameter values from available options
            - Identifying missing models (checkpoints, LoRAs, VAE, ControlNet, etc.)
            - Suggesting parameter fixes with smart matching
            - Updating workflow parameters automatically
            - Providing specific model download recommendations with links
            
            Call me when you have parameter validation errors, value_not_in_list errors, or missing model errors.
            """,
            instructions="""
            You are the Parameter Agent, an expert in ComfyUI parameter configuration and model management.
            
            **CRITICAL**: Your job is to analyze parameter errors and provide solutions. After addressing the issue, you MUST transfer back to the Debug Coordinator to verify the results.
            
            **Your Process:**
            
            1. **For value_not_in_list errors**:
            - Use get_node_parameters() to understand the parameter
            - Use find_matching_parameter_value() with smart matching
            - If exact/good match found: use update_workflow_parameter() then TRANSFER back
            - If no good match: show available options then TRANSFER back
            
            2. **For missing model errors (MOST COMMON)**:
            - Use get_model_files() to check what's available
            - If models folder is empty or missing models: use suggest_model_download() then TRANSFER back
            - Do NOT attempt to fix missing models - just provide download instructions and TRANSFER back
            
            3. **For other parameter issues**:
            - Analyze the parameter requirements
            - If fixable: update then TRANSFER back
            - If not fixable: provide guidance then TRANSFER back
            
            **Transfer Rules:**
            - When models are missing: Provide download instructions then TRANSFER to ComfyUI-Debug-Coordinator
            - When parameters are fixed: Confirm the fix then TRANSFER to ComfyUI-Debug-Coordinator  
            - When no fix is possible: Explain why then TRANSFER to ComfyUI-Debug-Coordinator
            - ALWAYS transfer back - do not end without handoff
            
            **Response Format:**
            1. "Issue identified: [brief description]"
            2. "Solution: [what you did or what user needs to do]"
            3. "Next steps: [if manual action required]"
            4. Transfer to ComfyUI-Debug-Coordinator for verification
            
            **Remember**: Your role is to identify the issue and provide the solution, then ALWAYS transfer back to let the coordinator verify the workflow.
            """,
            tools=[get_node_parameters, find_matching_parameter_value, get_model_files, 
                suggest_model_download, update_workflow_parameter],
            handoffs=[agent],
        )

        agent.handoffs = [workflow_bugfix_default_agent, parameter_agent]

        # Initial message to start the debugging process
        messages = [{"role": "user", "content": f"Validate and debug this ComfyUI workflow. Session ID: {session_id}"}]
            
        print(f"-- Starting workflow validation process for session {session_id}")

        result = Runner.run_streamed(
            agent,
            input=messages,
            max_turns=20,
        )
        print("=== Debug Coordinator starting ===")
        
        # Variables to track response state similar to mcp-client
        current_text = ''
        current_agent = "ComfyUI-Debug-Coordinator"
        last_yielded_length = 0
        
        # Collect debug events for final ext data
        debug_events = []
        
        # Collect workflow update ext data from tools
        workflow_update_ext = None
        
        async for event in result.stream_events():
            # Handle different event types according to OpenAI Agents documentation
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                # Stream text deltas for real-time response
                delta_text = event.data.delta
                if delta_text:
                    current_text += delta_text
                    # Only yield text updates during streaming, similar to mcp-client
                    if len(current_text) > last_yielded_length:
                        last_yielded_length = len(current_text)
                        yield (current_text, None)
                
            elif event.type == "agent_updated_stream_event":
                new_agent_name = event.new_agent.name
                print(f"Handoff to: {new_agent_name}")
                current_agent = new_agent_name
                # Add handoff information to the stream
                handoff_text = f"\n\n🔄 **Switching to {new_agent_name}**\n\n"
                current_text += handoff_text
                last_yielded_length = len(current_text)
                
                # Collect debug event data
                debug_events.append({
                    "type": "agent_handoff",
                    "current_agent": current_agent,
                    "to_agent": new_agent_name,
                    "timestamp": len(current_text)
                })
                
                # Yield text update only
                yield (current_text, None)
                
            elif event.type == "run_item_stream_event":
                item_updated = False
                
                if event.item.type == "tool_call_item":
                    # Tool call started
                    tool_name = getattr(event.item.raw_item, 'name', 'unknown_tool')
                    
                    print(f"-- Tool called: {tool_name}")
                    # Add tool call information
                    tool_text = f"\n🔧 *{current_agent} 正在使用 {tool_name}...*\n"
                    current_text += tool_text
                    item_updated = True
                    
                    # Collect debug event data
                    debug_events.append({
                        "type": "tool_call",
                        "tool": tool_name,
                        "agent": current_agent,
                        "timestamp": len(current_text)
                    })
                    
                elif event.item.type == "tool_call_output_item":
                    # Tool call result
                    output = str(event.item.output)
                    # Limit output length to avoid too long display
                    output_preview = output[:200] + "..." if len(output) > 200 else output
                    tool_result_text = f"✅ *工具执行完成*\n```\n{output_preview}\n```\n"
                    current_text += tool_result_text
                    item_updated = True
                    
                    # Try to parse tool output and extract ext data
                    try:
                        tool_output_json = json.loads(output)
                        if "ext" in tool_output_json and tool_output_json["ext"]:
                            for ext_item in tool_output_json["ext"]:
                                if ext_item.get("type") == "workflow_update" or ext_item.get("type") == "param_update":
                                    workflow_update_ext = ext_item
                                    print(f"-- Captured workflow_update ext from tool output")
                                    break
                    except (json.JSONDecodeError, TypeError):
                        # Tool output is not JSON, continue normally
                        pass
                    
                    # Collect debug event data
                    debug_events.append({
                        "type": "tool_result",
                        "output_preview": output_preview,
                        "agent": current_agent,
                        "timestamp": len(current_text)
                    })
                    
                elif event.item.type == "message_output_item":
                    # Message output completed
                    try:
                        message_content = ItemHelpers.text_message_output(event.item)
                        if message_content and message_content.strip():
                            # Avoid adding duplicate message content
                            if message_content not in current_text:
                                current_text += f"\n{message_content}\n"
                                item_updated = True
                                
                                # Collect debug event data
                                debug_events.append({
                                    "type": "message_complete",
                                    "content_length": len(message_content),
                                    "agent": current_agent,
                                    "timestamp": len(current_text)
                                })
                    except Exception as e:
                        print(f"Error processing message output: {str(e)}")
                
                # Update yielded length and yield text updates only
                if item_updated:
                    last_yielded_length = len(current_text)
                    yield (current_text, None)

        print("\n=== Debug process complete ===")
        
        # Save final workflow checkpoint after debugging completion
        debug_completion_checkpoint_id = None
        try:
            current_workflow = get_workflow_data(session_id)
            if current_workflow:
                debug_completion_checkpoint_id = save_workflow_data(
                    session_id, 
                    current_workflow,
                    workflow_data_ui=None,  # UI format not available here
                    attributes={
                        "checkpoint_type": "debug_complete",
                        "description": "Workflow state after debug completion",
                        "action": "debug_complete",
                        "final_agent": current_agent
                    }
                )
                print(f"Debug completion checkpoint saved with ID: {debug_completion_checkpoint_id}")
        except Exception as checkpoint_error:
            print(f"Failed to save debug completion checkpoint: {checkpoint_error}")
        
        # Final yield with complete text and debug ext data, matching mcp-client format
        debug_ext = [{
            "type": "debug_complete",
            "data": {
                "status": "completed",
                "final_agent": current_agent,
                "events": debug_events,
                "total_events": len(debug_events)
            }
        }]
        
        # Add debug checkpoint info if successful
        if debug_completion_checkpoint_id:
            debug_ext.append({
                "type": "debug_checkpoint",
                "data": {
                    "checkpoint_id": debug_completion_checkpoint_id,
                    "checkpoint_type": "debug_complete"
                }
            })
        
        # Include workflow_update ext if captured from tools
        final_ext = debug_ext
        if workflow_update_ext:
            final_ext = [workflow_update_ext] + debug_ext
            print(f"-- Including workflow_update ext in final response")
        
        # Return format matching mcp-client: {"data": ext, "finished": finished}
        ext_with_finished = {
            "data": final_ext,
            "finished": True
        }
        yield (current_text, ext_with_finished)
            
    except Exception as e:
        print(f"Error in debug_workflow_errors: {str(e)}")
        error_message = f"❌ Error occurred during debugging: {str(e)}"
        # Return error format matching mcp-client: {"data": ext, "finished": finished}
        error_ext = [{
            "type": "error",
            "data": {
                "error": True,
                "message": str(e),
                "error_type": "debug_agent_error"
            }
        }]
        error_ext_with_finished = {
            "data": error_ext,
            "finished": True
        }
        yield (error_message, error_ext_with_finished)


# Test function
async def test_debug():
    """Test the debug agent with a sample workflow"""
    test_workflow_data = {
        "1": {
            "inputs": {
                "vae_name": "ae.sft"  # This will likely cause an error
            },
            "class_type": "VAELoader",
            "_meta": {"title": "Load VAE"}
        },
        "2": {
            "inputs": {
                "ckpt_name": "sd_xl_base_1.0.safetensors"
            },
            "class_type": "CheckpointLoaderSimple",
            "_meta": {"title": "Load Checkpoint"}
        }
    }
    
    config = {
        "session_id": "test_session_123",
        "model": "us.anthropic.claude-sonnet-4-20250514-v1:0"
    }
    
    async for text, ext in debug_workflow_errors(test_workflow_data, config):
        print(f"Stream output: {text[-100:] if len(text) > 100 else text}")  # Print last 100 chars
        if ext:
            print(f"Ext data: {ext}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_debug())
