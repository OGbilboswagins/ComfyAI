"""
ComfyUI Gateway Utilities

This module provides Python implementations of ComfyUI API functions,
mirroring the functionality from the TypeScript frontend.
"""

import json
import requests
import os
from typing import Dict, Any, Optional, List
import urllib.parse


class ComfyGateway:
    """ComfyUI API Gateway for Python backend"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize ComfyUI Gateway
        
        Args:
            base_url: Base URL for ComfyUI API. If not provided, will try to detect from environment
        """
        if base_url:
            self.base_url = base_url.rstrip('/')
        else:
            # Try to get from environment or use default ComfyUI address
            self.base_url = os.environ.get('COMFYUI_BASE_URL', 'http://127.0.0.1:8188')
        
        self.session = requests.Session()
        # Set reasonable timeout
        self.session.timeout = 30
    
    def _make_request(self, endpoint: str, method: str = 'GET', data: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make HTTP request to ComfyUI API
        
        Args:
            endpoint: API endpoint (e.g., '/prompt', '/object_info')
            method: HTTP method
            data: Request data for POST requests
            
        Returns:
            requests.Response object
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                headers = {'Content-Type': 'application/json'}
                response = self.session.post(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            print(f"Error making request to {url}: {e}")
            raise

    def run_prompt(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a prompt on ComfyUI - Python equivalent of the TypeScript runPrompt function
        
        This function sends a workflow/prompt to ComfyUI for execution.
        
        Args:
            json_data: The prompt/workflow data to execute. Should contain:
                - prompt: The workflow definition
                - client_id: Optional client identifier
                
        Returns:
            Dict containing the response from ComfyUI API, typically includes:
                - prompt_id: The ID of the queued prompt
                - number: Queue position
                - node_errors: Any validation errors
        
        Raises:
            requests.RequestException: If the API request fails
            ValueError: If the response format is invalid
            
        Example:
            gateway = ComfyGateway()
            prompt_data = {
                "prompt": {"1": {"inputs": {...}, "class_type": "KSampler", ...}},
                "client_id": "python-client"
            }
            result = gateway.run_prompt(prompt_data)
            print(f"Prompt queued with ID: {result['prompt_id']}")
        """
        try:
            response = self._make_request("/prompt", method="POST", data=json_data)
            return response.json()
        except requests.RequestException as e:
            print(f"Error running prompt: {e}")
            raise
        except json.JSONDecodeError as e:
            print(f"Error parsing response JSON: {e}")
            raise ValueError("Invalid JSON response from ComfyUI API")

    def get_object_info(self) -> Dict[str, Any]:
        """
        Get ComfyUI node definitions - Python equivalent of getObjectInfo()
        
        Returns:
            Dict containing all available node definitions and their parameters
        """
        try:
            response = self._make_request("/object_info")
            return response.json()
        except Exception as e:
            print(f"Error fetching object info: {e}")
            raise

    def get_installed_nodes(self) -> List[str]:
        """
        Get list of installed node types - Python equivalent of getInstalledNodes()
        
        Returns:
            List of installed node type names
        """
        object_info = self.get_object_info()
        return list(object_info.keys())

    def manage_queue(self, clear: bool = False, delete: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Clear the prompt queue or delete specific queue items - Python equivalent of manageQueue()
        
        Args:
            clear: If True, clears the entire queue
            delete: List of prompt IDs to delete from the queue
            
        Returns:
            Dict with the response from the queue management operation
        """
        options = {}
        if clear:
            options["clear"] = True
        if delete:
            options["delete"] = delete
            
        try:
            response = self._make_request("/queue", method="POST", data=options)
            return response.json() if response.content else {}
        except Exception as e:
            print(f"Error managing queue: {e}")
            raise

    def interrupt_processing(self) -> Dict[str, Any]:
        """
        Interrupt the current processing/generation - Python equivalent of interruptProcessing()
        
        Returns:
            Dict with the response from the interrupt operation
        """
        try:
            response = self._make_request("/interrupt", method="POST")
            return response.json() if response.content else {}
        except Exception as e:
            print(f"Error interrupting processing: {e}")
            raise

    def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """
        Get execution history for a specific prompt - Python equivalent of getHistory()
        
        Args:
            prompt_id: The ID of the prompt to get history for
            
        Returns:
            Dict containing the execution history and results
        """
        try:
            response = self._make_request(f"/history/{prompt_id}")
            return response.json()
        except Exception as e:
            print(f"Error fetching history for prompt {prompt_id}: {e}")
            raise


# Convenience functions for backward compatibility and easy importing
def run_prompt(json_data: Dict[str, Any], base_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Standalone function to run a prompt - direct equivalent of TypeScript runPrompt()
    
    Args:
        json_data: The prompt/workflow data to execute
        base_url: Optional ComfyUI base URL
        
    Returns:
        Dict containing the API response
    """
    gateway = ComfyGateway(base_url)
    return gateway.run_prompt(json_data)


def get_object_info(base_url: Optional[str] = None) -> Dict[str, Any]:
    """Standalone function to get object info"""
    gateway = ComfyGateway(base_url)
    return gateway.get_object_info()


def get_installed_nodes(base_url: Optional[str] = None) -> List[str]:
    """Standalone function to get installed nodes"""
    gateway = ComfyGateway(base_url)
    return gateway.get_installed_nodes()


# Example usage
if __name__ == "__main__":
    # Example of how to use the ComfyGateway
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
        nodes = gateway.get_installed_nodes()
        print(f"Found {len(nodes)} installed nodes")
        
        # Run a prompt (uncomment to actually execute)
        # result = gateway.run_prompt(example_prompt)
        # print(f"Prompt result: {result}")
        
    except Exception as e:
        print(f"Example failed: {e}")
