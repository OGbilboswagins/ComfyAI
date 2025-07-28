"""
ComfyUI Gateway Utilities

This module provides Python implementations of ComfyUI API functions,
directly calling ComfyUI internal functions instead of HTTP requests.
"""

import json
import os
import uuid
import logging
from typing import Dict, Any, Optional, List

# Import ComfyUI internal modules
import nodes
import execution
import folder_paths
import server


class ComfyGateway:
    """ComfyUI API Gateway for Python backend - uses internal functions instead of HTTP requests"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize ComfyUI Gateway
        
        Args:
            base_url: Deprecated - no longer used since we call internal functions directly
        """
        if base_url:
            logging.warning("ComfyGateway: base_url parameter is deprecated when using internal calls")
        
        # Get server instance for operations that need it
        self.server_instance = server.PromptServer.instance

    def run_prompt(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a prompt - direct internal call equivalent of server.py post_prompt
        
        This method replicates the exact logic from server.py's post_prompt route handler
        to ensure consistent behavior without requiring HTTP requests.
        
        Args:
            json_data: The prompt/workflow data in the same format as HTTP API
            
        Returns:
            Dict containing the validation result, similar to HTTP API response
        """
        try:
            # Trigger on_prompt handlers (same as server.py)
            json_data = self.server_instance.trigger_on_prompt(json_data)
            print(json_data)
            # Handle number logic (same as server.py)
            if "number" in json_data:
                number = float(json_data['number'])
            else:
                number = self.server_instance.number
                if "front" in json_data:
                    if json_data['front']:
                        number = -number
                self.server_instance.number += 1
            
            # Main prompt validation and processing logic (same as server.py)
            if "prompt" in json_data:
                prompt = json_data["prompt"]
                valid = execution.validate_prompt(prompt)
                extra_data = {}
                if "extra_data" in json_data:
                    extra_data = json_data["extra_data"]

                if "client_id" in json_data:
                    extra_data["client_id"] = json_data["client_id"]
                    
                if valid[0]:
                    # Validation successful
                    prompt_id = str(uuid.uuid4())
                    outputs_to_execute = valid[2]
                    
                    # Add to prompt queue (same as server.py)
                    if hasattr(self.server_instance, 'prompt_queue') and self.server_instance.prompt_queue:
                        self.server_instance.prompt_queue.put((number, prompt_id, prompt, extra_data, outputs_to_execute))
                    
                    response = {
                        "success": True,
                        "prompt_id": prompt_id, 
                        "number": number, 
                        "node_errors": valid[3]
                    }
                    return response
                else:
                    # Validation failed
                    logging.warning("invalid prompt: {}".format(valid[1]))
                    return {
                        "success": False,
                        "error": valid[1], 
                        "node_errors": valid[3]
                    }
            else:
                # No prompt provided
                error = {
                    "type": "no_prompt",
                    "message": "No prompt provided",
                    "details": "No prompt provided",
                    "extra_info": {}
                }
                return {
                    "success": False,
                    "error": error, 
                    "node_errors": {}
                }
                
        except Exception as e:
            logging.error(f"Error in run_prompt: {e}")
            return {
                "success": False,
                "error": {
                    "type": "internal_error",
                    "message": f"Internal error: {str(e)}",
                    "details": str(e)
                },
                "node_errors": {}
            }

    def get_object_info(self, node_class: Optional[str] = None) -> Dict[str, Any]:
        """
        Get ComfyUI node definitions - direct internal call equivalent
        
        Returns:
            Dict containing all available node definitions and their parameters
        """
        try:
            def node_info(node_class_name):
                """Internal function to get node info - based on server.py logic"""
                obj_class = nodes.NODE_CLASS_MAPPINGS[node_class_name]
                info = {}
                info['input'] = obj_class.INPUT_TYPES()
                info['input_order'] = {key: list(value.keys()) for (key, value) in obj_class.INPUT_TYPES().items()}
                info['output'] = obj_class.RETURN_TYPES
                info['output_is_list'] = obj_class.OUTPUT_IS_LIST if hasattr(obj_class, 'OUTPUT_IS_LIST') else [False] * len(obj_class.RETURN_TYPES)
                info['output_name'] = obj_class.RETURN_NAMES if hasattr(obj_class, 'RETURN_NAMES') else info['output']
                info['name'] = node_class_name
                info['display_name'] = nodes.NODE_DISPLAY_NAME_MAPPINGS.get(node_class_name, node_class_name)
                info['description'] = obj_class.DESCRIPTION if hasattr(obj_class,'DESCRIPTION') else ''
                info['python_module'] = getattr(obj_class, "RELATIVE_PYTHON_MODULE", "nodes")
                info['category'] = 'sd'
                if hasattr(obj_class, 'OUTPUT_NODE') and obj_class.OUTPUT_NODE == True:
                    info['output_node'] = True
                else:
                    info['output_node'] = False

                if hasattr(obj_class, 'CATEGORY'):
                    info['category'] = obj_class.CATEGORY

                if hasattr(obj_class, 'OUTPUT_TOOLTIPS'):
                    info['output_tooltips'] = obj_class.OUTPUT_TOOLTIPS

                if getattr(obj_class, "DEPRECATED", False):
                    info['deprecated'] = True
                if getattr(obj_class, "EXPERIMENTAL", False):
                    info['experimental'] = True
                return info
            
            if node_class:
                # Get specific node info
                if node_class in nodes.NODE_CLASS_MAPPINGS:
                    return {node_class: node_info(node_class)}
                else:
                    return {}
            else:
                # Get all node info
                with folder_paths.cache_helper:
                    out = {}
                    for x in nodes.NODE_CLASS_MAPPINGS:
                        try:
                            out[x] = node_info(x)
                        except Exception as e:
                            logging.error(f"[ERROR] An error occurred while retrieving information for the '{x}' node: {e}")
                    return out
                    
        except Exception as e:
            logging.error(f"Error getting object info: {e}")
            raise

    def get_installed_nodes(self) -> List[str]:
        """
        Get list of installed node types - direct internal call equivalent
        
        Returns:
            List of installed node type names
        """
        try:
            return list(nodes.NODE_CLASS_MAPPINGS.keys())
        except Exception as e:
            logging.error(f"Error getting installed nodes: {e}")
            return []

    def manage_queue(self, clear: bool = False, delete: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Clear the prompt queue or delete specific queue items - direct internal call equivalent
        
        Args:
            clear: If True, clears the entire queue
            delete: List of prompt IDs to delete from the queue
            
        Returns:
            Dict with the response from the queue management operation
        """
        try:
            if not self.server_instance or not hasattr(self.server_instance, 'prompt_queue'):
                return {"error": "Server instance or prompt queue not available"}
            
            if clear:
                self.server_instance.prompt_queue.wipe_queue()
                
            if delete:
                for id_to_delete in delete:
                    delete_func = lambda a: a[1] == id_to_delete
                    self.server_instance.prompt_queue.delete_queue_item(delete_func)
            
            return {"success": True}
            
        except Exception as e:
            logging.error(f"Error managing queue: {e}")
            return {"error": f"Failed to manage queue: {str(e)}"}

    def interrupt_processing(self) -> Dict[str, Any]:
        """
        Interrupt the current processing/generation - direct internal call equivalent
        
        Returns:
            Dict with the response from the interrupt operation
        """
        try:
            nodes.interrupt_processing()
            return {"success": True}
        except Exception as e:
            logging.error(f"Error interrupting processing: {e}")
            return {"error": f"Failed to interrupt processing: {str(e)}"}

    def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """
        Get execution history for a specific prompt - direct internal call equivalent
        
        Args:
            prompt_id: The ID of the prompt to get history for
            
        Returns:
            Dict containing the execution history and results
        """
        try:
            if not self.server_instance or not hasattr(self.server_instance, 'prompt_queue'):
                return {"error": "Server instance or prompt queue not available"}
            
            return self.server_instance.prompt_queue.get_history(prompt_id=prompt_id)
            
        except Exception as e:
            logging.error(f"Error fetching history for prompt {prompt_id}: {e}")
            return {"error": f"Failed to get history: {str(e)}"}


# Convenience functions for backward compatibility and easy importing
def run_prompt(json_data: Dict[str, Any], base_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Standalone function to run a prompt - direct equivalent of TypeScript runPrompt()
    
    Args:
        json_data: The prompt/workflow data to execute
        base_url: Deprecated - no longer used
        
    Returns:
        Dict containing the API response
    """
    gateway = ComfyGateway(base_url)
    return gateway.run_prompt(json_data)


def get_object_info(base_url: Optional[str] = None) -> Dict[str, Any]:
    """Standalone function to get object info - direct internal call equivalent"""
    if base_url:
        logging.warning("get_object_info: base_url parameter is deprecated when using internal calls")
    gateway = ComfyGateway(base_url)
    return gateway.get_object_info()

def get_object_info_by_class(node_class: str, base_url: Optional[str] = None) -> Dict[str, Any]:
    """Standalone function to get object info for specific node class - direct internal call equivalent"""
    if base_url:
        logging.warning("get_object_info_by_class: base_url parameter is deprecated when using internal calls")
    gateway = ComfyGateway(base_url)
    return gateway.get_object_info(node_class)


def get_installed_nodes(base_url: Optional[str] = None) -> List[str]:
    """Standalone function to get installed nodes - direct internal call equivalent"""
    if base_url:
        logging.warning("get_installed_nodes: base_url parameter is deprecated when using internal calls")
    gateway = ComfyGateway(base_url)
    return gateway.get_installed_nodes()


# Example usage
if __name__ == "__main__":
    # Example of how to use the ComfyGateway with internal calls
    gateway = ComfyGateway()
    
    # Example prompt structure (you would replace this with actual workflow data)
    example_prompt = {
        "prompt": {
            "1": {
                "inputs": {
                    "text": "a beautiful landscape"
                },
                "class_type": "CLIPTextEncode"
            }
        },
        "client_id": "python-example"
    }
    
    try:
        # Get available nodes
        nodes_list = gateway.get_installed_nodes()
        print(f"Found {len(nodes_list)} installed nodes")
        
        # Get object info by class
        node_info = gateway.get_object_info_by_class("CLIPTextEncode")
        print(f"Node info: {node_info}")
        
        # Validate a prompt (uncomment to actually execute)
        # result = gateway.run_prompt(example_prompt)
        # print(f"Prompt result: {result}")
        
    except Exception as e:
        print(f"Example failed: {e}")
