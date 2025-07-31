'''
Debug Agent for ComfyUI Workflow Error Analysis
'''
from ..agent_factory import create_agent
from .. import core
from agents.items import ItemHelpers
from agents.run import Runner
from agents.tool import function_tool
from ..utils.globals import get_language
from ..service.workflow_rewrite_tools import *
from openai.types.responses import ResponseTextDeltaEvent

from ..service.parameter_tools import *
from ..service.link_agent_tools import *
from ..service.database import get_workflow_data, save_workflow_data

# Import ComfyUI internal modules
import uuid
import execution

# Load environment variables from server.env


@function_tool
async def run_workflow(session_id: str) -> str:
    """验证当前session的工作流并返回结果"""
    try:
        workflow_data = get_workflow_data(session_id)
        if not workflow_data:
            return json.dumps({"error": "No workflow data found for this session"})
        
        print(f"Run workflow for session {session_id}")
        
        # 使用 ComfyGateway 调用 server.py 的 post_prompt 逻辑
        from ..utils.comfy_gateway import ComfyGateway
        
        # 简化方法：直接使用 requests 同步调用
        gateway = ComfyGateway()

        # 准备请求数据格式（与server.py post_prompt接口一致）
        request_data = {
            "prompt": workflow_data,
            "client_id": f"debug_agent_{session_id}"
        }
        
        result = await gateway.run_prompt(request_data)
        print(result)
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to run workflow: {str(e)}"})


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
                        error_detail_str = json.dumps(error_detail).lower()
                        error_type = error.get("type", "").lower()
                        # error_message = error.get("message", "").lower()
                        
                        # 优先判断连接相关错误（结构性错误）
                        if (any(keyword in error_detail_str for keyword in [
                            "connection", "input connection", "required input", "missing input",
                            "not connected", "no connection", "link", "output", "socket"
                        ]) or 
                        error_type in ["missing_input", "invalid_connection", "connection_error"]):
                            connection_errors += 1
                        
                        # 参数相关错误的判断（更精确）
                        elif (error_type in ["value_not_in_list", "invalid_input", "invalid_value"] or
                            any(keyword in error_detail_str for keyword in [
                                "value not in list", "invalid value", "not found in list",
                                "parameter value", "invalid parameter", "model not found", "invalid image file"
                            ])):
                            parameter_errors += 1
                        
                        # 其他结构性错误
                        else:
                            other_errors += 1
            
            # 根据错误类型决定使用哪个agent
            if connection_errors > 0 and parameter_errors == 0 and other_errors == 0:
                # 纯连接错误，使用专门的link_agent
                error_analysis["error_type"] = "connection_error"
                error_analysis["recommended_agent"] = "link_agent"
            elif connection_errors > 0:
                # 混合错误，优先处理连接问题
                error_analysis["error_type"] = "mixed_connection_error"
                error_analysis["recommended_agent"] = "link_agent"
            elif parameter_errors > 0:
                error_analysis["error_type"] = "parameter_error"
                error_analysis["recommended_agent"] = "parameter_agent"
            else:
                error_analysis["error_type"] = "structural_error"
                error_analysis["recommended_agent"] = "workflow_bugfix_default_agent"
        
        elif "error" in error_dict:
            # 处理其他格式的错误
            error_analysis = error_dict.get("error", {})
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
        
        agent = create_agent(
            name="ComfyUI-Debug-Coordinator",
            instructions=f"""You are a ComfyUI workflow debugging coordinator. Your role is to analyze workflow errors and coordinate with specialized agents to fix them.

**Session ID:** {session_id}

**Your Process:**
1. **Validate the workflow**: Use run_workflow("{session_id}") to validate the workflow and capture any errors
2. **Analyze errors**: If errors occur, use analyze_error_type() to determine the error type and hand off to the appropriate specialist. Note that analyze_error_type can help you determine the error type and which agent to hand off to, but it's only for reference. You still need to judge based on the current error information to determine which type of error it is:
   - Hand off to Link Agent for connection-related errors (missing connections, disconnected inputs, node linking issues)
   - Hand off to Parameter Agent for parameter-related errors (value_not_in_list, missing models, invalid values)
   - Hand off to Workflow Bugfix Default Agent for other structural issues (node compatibility, complex workflow restructuring)
3. **After specialist returns**: Continue validation from step 1 to check if the issue is resolved
4. **Repeat until complete**: Continue this cycle until there are no errors or maximum 10 iterations

**Critical Guidelines:**
- ALWAYS validate the workflow first to check for errors
- If no errors occur, report success immediately and STOP
- If errors occur, analyze them and hand off to the appropriate specialist
- When specialists return: IMMEDIATELY re-validate the workflow to check if the issue is resolved
- Continue the debugging cycle until all errors are fixed or max iterations reached
- Provide clear, streaming updates about what you're doing
- Be concise but informative in your responses
- If there is user history in history_messages, please determine the language based on the language in the history. Otherwise, use {get_language()} as the language.

**Handoff Strategy:**
- Hand off errors to specialists for fixing
- When they return: Re-validate immediately to check results  
- If new errors appear: Analyze and hand off again
- If same errors persist: Try different specialist (Link Agent → Parameter Agent → Workflow Bugfix Default Agent) or report limitation

**Note**: The workflow validation is done using ComfyUI's internal functions, not actual execution, so it's fast and safe.

Start by validating the workflow to see its current state.""",
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            tools=[run_workflow, analyze_error_type, save_current_workflow],
        )
        
        workflow_bugfix_default_agent = create_agent(
            name="Workflow Bugfix Default Agent",
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            handoff_description="""
            I am the Workflow Bugfix Default Agent. I specialize in fixing structural issues in ComfyUI workflows.
            
            I can help with:
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
            2. **Identify and fix issues**
            3. **Save changes** using update_workflow()
            4. **MANDATORY**: Transfer back to Debug Coordinator for verification
            
            **Transfer Rules:**
            - After making structural fixes: Save with update_workflow() then TRANSFER to ComfyUI-Debug-Coordinator
            - If no structural issues found: Report findings then TRANSFER to ComfyUI-Debug-Coordinator
            - If fixes cannot be applied: Explain why then TRANSFER to ComfyUI-Debug-Coordinator
            - ALWAYS transfer back - do not end without handoff
            
            **Tool Usage Guidelines:**
            - update_workflow(): Use to save your changes (ALWAYS call this after fixes)
            
            **Response Format:**
            1. "Structural analysis: [brief description of issues]"
            2. "Fixes applied: [what you changed]"
            3. "Workflow updated: [confirmation]"
            4. Transfer to ComfyUI-Debug-Coordinator for verification
            
            **Remember**: Focus on making necessary structural changes, then ALWAYS transfer back to let the coordinator verify the workflow.
            """,
            tools=[get_current_workflow, get_node_info, update_workflow],
            handoffs=[agent],
        )
        
        link_agent = create_agent(
            name="Link Agent",
            model="us.anthropic.claude-sonnet-4-20250514-v1:0",
            handoff_description="""
            I am the Link Agent. I specialize in analyzing and fixing workflow connection issues.
            
            I can help with:
            - Analyzing missing connections in workflows
            - Finding optimal connection solutions
            - Connecting existing nodes automatically
            - Adding missing nodes when required
            - Batch fixing multiple connection issues
            - Generating intelligent connection strategies
            
            Call me when you have connection errors, missing input connections, or workflow structure issues related to node linking.
            """,
            instructions="""
            You are the Link Agent, an expert in ComfyUI workflow connection analysis and automated fixing.
            
            **CRITICAL**: Your job is to analyze connection issues and apply intelligent fixes. After making fixes, you MUST transfer back to the Debug Coordinator to verify the results.
            
            **Your Enhanced Process:**
            
            1. **Analyze connection issues** using analyze_missing_connections():
            - This tool comprehensively analyzes all missing required inputs
            - It finds possible connections from existing nodes
            - It identifies when new nodes are needed
            - It provides confidence ratings and recommendations
            
            2. **Apply fixes strategically**:
            
            **Based on the analysis results**, decide the optimal strategy:
            
            **For connection-only fixes** (when existing nodes can be connected):
            - Use apply_connection_fixes() with connections from possible_connections
            - Prioritize high-confidence connections first
            - Handle medium-confidence connections as appropriate
            
            **For missing node scenarios** (when new nodes are required):
            - Use apply_connection_fixes() with both new_nodes and connections
            - Create new_nodes based on required_new_nodes suggestions
            - Add nodes with auto_connect specifications to streamline the process
            - Ensure new nodes have proper default parameters
            
            **Smart decision making**:
            - Review missing_connections and possible_connections from the analysis
            - Choose the most efficient combination of existing connections and new nodes
            - Consider connection_summary to understand the scope of work needed
            
            4. **Verification and handoff**:
            - After applying fixes: TRANSFER to ComfyUI-Debug-Coordinator for verification
            - Provide clear summary of what was fixed
            - If fixes cannot be applied: Explain why then TRANSFER to ComfyUI-Debug-Coordinator
            
            **Smart Decision Making:**
            - Prefer connecting existing nodes when type-compatible outputs are available
            - Add new nodes only when no existing connections are possible
            - Process fixes in optimal order (high-confidence first, then new nodes, then medium-confidence)
            - Handle batch operations efficiently to minimize workflow updates
            
            **Transfer Rules:**
            - After applying connection fixes: TRANSFER to ComfyUI-Debug-Coordinator
            - If no connection issues found: Report findings then TRANSFER to ComfyUI-Debug-Coordinator  
            - If fixes cannot be applied: Explain limitations then TRANSFER to ComfyUI-Debug-Coordinator
            - ALWAYS transfer back - do not end without handoff
            
            **Response Format:**
            1. "Connection analysis: [brief description of issues found from analyze_missing_connections]"
            2. "Chosen strategy: [approach taken - connect existing/add nodes/mixed, with reasoning]"
            3. "Fixes applied: [summary of changes made via apply_connection_fixes]"
            4. Transfer to ComfyUI-Debug-Coordinator for verification
            
            **Advanced Features:**
            - Comprehensive analysis: Full workflow connection scan with detailed diagnostics
            - Batch processing: Handle multiple connection issues in one operation
            - Smart node suggestions: Automatic recommendation of optimal node types for missing connections
            - Auto-connection: Automatically connect new nodes to their intended targets
            - Confidence-based prioritization: Make intelligent decisions based on connection confidence levels
            - Flexible strategy: Adapt approach based on specific workflow requirements
            
            **Remember**: You are the specialist for ALL connection-related issues. Make the necessary structural changes efficiently, then ALWAYS transfer back for workflow verification.
            """,
            tools=[analyze_missing_connections, apply_connection_fixes,
                   get_current_workflow, get_node_info],
            handoffs=[agent],
        )

        parameter_agent = create_agent(
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
            
            **CRITICAL**: Your job is to analyze parameter errors and provide solutions. After addressing the issue, you MUST transfer back to the Debug Coordinator to verify the results, EXCEPT when suggesting model downloads.
            
            **Your Enhanced Process:**
            
            1. **Analyze ALL parameter errors using find_matching_parameter_value()** first:
            - This function now intelligently categorizes errors and provides solution strategies
            - It handles: model missing, image file missing, enum value mismatches, and other parameter types
            - Check the response for "error_type", "solution_type", and "can_auto_fix" fields
            
            2. **Handle different error types based on analysis:**
            
            **Model Missing Errors** (error_type: "model_missing"):
            - Apply ComfyUI model system knowledge for intelligent matching
            - ComfyUI has four main model systems: SDXL, Flux, wan2.1, wan2.2
            - When model not found or name differs from local models, check workflow model name against these systems:
              * SDXL system (examples: SDXL_base, SDXL_refiner, etc.)
              * Flux system (examples: Flux-dev, Flux-dev-fp8, Flux-fill, etc.)
              * wan2.1 system (examples: wan2.1_base, wan2.1_t2v, etc.)
              * wan2.2 system (examples: wan2.2_t2v, wan2.2_iv2, wan2.2_kontext, wan2.2_redux, etc.)
            - Match by model system first (SDXL/Flux/wan2.1/wan2.2), then by model category (fill/dev/base/t2v/iv2/kontext/redux)
            - **System-specific component matching rules:**
              * **Flux series**: Requires fixed system components - vae: ae.safetensors, DualCLIPLoader: clip_l.safetensors + t5xxl_fp16.safetensors or t5xxl_fp8.safetensors, type: flux. In DualCLIP and UNetLoader/Load Checkpoint, search by system+category (e.g., Flux-dev-fp8 can be replaced with similar Flux-dev)
              * **SDXL series**: vae: sdxl_vae.safetensors or vae-fe-mse-840000-ema-pruned.safetensors (priority search by system: vae, category: sdxl/840000). Load checkpoint search by system: sdxl, category: similar name (e.g., SDXL-dreamshaper.safetensors where dreamshaper is the category)
            - If similar model from same system exists, replace with most similar match
            - When can_auto_fix = false and solution_type = "download_required" and no similar models found
            - Use suggest_model_download() to provide download instructions
            - Do NOT transfer back - the download suggestion is the final response
            
            **Image File Missing Errors** (error_type: "image_file_missing"):
            - When can_auto_fix = true and solution_type = "auto_replace"
            - Use the recommended_value directly with update_workflow_parameter() then TRANSFER back
            - When can_auto_fix = false: Provide guidance for adding images then TRANSFER back
            
            **Enum Value Errors** (error_type: "enum_value_mismatch"):
            - When can_auto_fix = true (solution_type: "auto_replace", "default_replace", "exact_match")
            - Use the recommended_value with update_workflow_parameter() then TRANSFER back
            - When can_auto_fix = false: Show available options then TRANSFER back
            
            **Other Parameter Types** (error_type: "non_enum_parameter"):
            - Provide configuration guidance based on parameter type then TRANSFER back
            
            3. **For multiple errors**: Process them systematically, one by one
            
            4. **Smart Fallback Strategy**:
            - If find_matching_parameter_value() fails, use get_model_files() to check if it's a model issue
            - Apply model system matching logic (SDXL/Flux/wan2.1/wan2.2 systems with categories)
            - If still unclear, use suggest_model_download() as last resort (no transfer back)
            
            **Auto-Fix Priority** (when can_auto_fix = true):
            1. Model replacements: Use intelligent system-based matching (SDXL/Flux/wan2.1/wan2.2)
            2. Image replacements: Use any available image to replace missing ones
            3. Enum matches: Use exact/partial/default matches automatically  
            4. Case corrections: Fix capitalization and formatting issues
            
            **Transfer Rules:**
            - Model missing (suggest_model_download): Provide download instructions and STOP - do not transfer back
            - Auto-fixed parameters: Confirm the fix then TRANSFER to ComfyUI-Debug-Coordinator
            - Manual fixes needed: Provide clear guidance then TRANSFER to ComfyUI-Debug-Coordinator
            - For all cases except model downloads: ALWAYS transfer back with clear status
            
            **Response Format:**
            1. "Issue identified: [error_type] - [brief description]"
            2. "Solution: [auto-fixed/download-required/manual-fix] - [what you did or what user needs to do]"
            3. "Status: [fixed/requires-download/requires-manual-action]"
            4. Transfer to ComfyUI-Debug-Coordinator for verification (EXCEPT for model download cases)
            
            **Key Enhancement**: You can now automatically fix many parameter issues (images, enums, intelligent model matching) without user intervention, but you still need downloads for missing models when no similar models exist. Be proactive in applying fixes when possible. When providing model download suggestions, that is your final action.
            """,
            tools=[find_matching_parameter_value, get_model_files, 
                suggest_model_download, update_workflow_parameter, get_current_workflow],
            handoffs=[agent],
        )

        agent.handoffs = [link_agent, workflow_bugfix_default_agent, parameter_agent]

        # Initial message to start the debugging process
        messages = [{"role": "user", "content": f"Validate and debug this ComfyUI workflow. Session ID: {session_id}"}]
            
        print(f"-- Starting workflow validation process for session {session_id}")

        result = Runner.run_streamed(
            agent,
            input=messages,
            max_turns=30,
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
                    tool_text = f"\n\n🔧 *{current_agent} is using {tool_name}...*\n\n"
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
                    tool_result_text = f"\n\n✅ *Tool execution completed*\n\n```\n{output_preview}\n```\n\n"
                    current_text += tool_result_text
                    item_updated = True
                    
                    # Try to parse tool output and extract ext data
                    try:
                        tool_output_json = json.loads(output)
                        if "ext" in tool_output_json and tool_output_json["ext"]:
                            for ext_item in tool_output_json["ext"]:
                                if ext_item.get("type") == "workflow_update" or ext_item.get("type") == "param_update":
                                    workflow_update_ext = ext_item
                                    print(f"-- Captured {ext_item.get('type')} ext from tool output, yielding immediately")
                                    
                                    # 立即yield workflow_update或param_update，让前端实时更新工作流
                                    ext_with_finished = {
                                        "data": [ext_item],
                                        "finished": False  # 标记为未完成，继续debug流程
                                    }
                                    yield (current_text, ext_with_finished)
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
                                current_text += f"\n\n{message_content}\n\n"
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
        error_message = current_text + f"\n\n❌ Error occurred during debugging: {str(e)}\n\n"

        # Include workflow_update ext if captured from tools before the error
        final_error_ext = None
        if 'workflow_update_ext' in locals() and workflow_update_ext:
            final_error_ext = [workflow_update_ext]
            print(f"-- Including latest workflow_update ext in error response")
        
        ext_with_finished = {
            "data": final_error_ext,
            "finished": True
        }
        yield (error_message, ext_with_finished)


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
