"""
ComfyUI Gateway Python Usage Examples

This file demonstrates how to use the Python implementation of runPrompt
and other ComfyUI API functions.
"""

from comfy_gateway import ComfyGateway, run_prompt
import json

def example_basic_usage():
    """Basic usage example of ComfyGateway"""
    
    # Initialize the gateway (uses default ComfyUI URL: http://127.0.0.1:8188)
    gateway = ComfyGateway()
    
    # Or specify a custom URL
    # gateway = ComfyGateway("http://192.168.1.100:8188")
    
    try:
        # Get list of available nodes
        nodes = gateway.get_installed_nodes()
        print(f"Available nodes: {len(nodes)}")
        print(f"First 5 nodes: {nodes[:5]}")
        
        # Get detailed object info
        object_info = gateway.get_object_info()
        print(f"Got object info for {len(object_info)} node types")
        
    except Exception as e:
        print(f"Error: {e}")

def example_run_prompt():
    """Example of running a prompt/workflow"""
    
    gateway = ComfyGateway()
    
    # Example workflow data - this would typically come from a saved ComfyUI workflow
    prompt_data = {
        "prompt": {
            "1": {
                "inputs": {
                    "text": "a beautiful landscape, photorealistic, high quality",
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "2": {
                "inputs": {
                    "text": "blurry, low quality, ugly",
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "3": {
                "inputs": {
                    "seed": 123456,
                    "steps": 20,
                    "cfg": 8.0,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "positive": ["1", 0],
                    "negative": ["2", 0],
                    "model": ["4", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler"
            },
            "4": {
                "inputs": {
                    "ckpt_name": "v1-5-pruned-emaonly.safetensors"
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "5": {
                "inputs": {
                    "width": 512,
                    "height": 512,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            "6": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEDecode"
            },
            "7": {
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": ["6", 0]
                },
                "class_type": "SaveImage"
            }
        },
        "client_id": "python-client-example"
    }
    
    try:
        # Run the prompt
        result = gateway.run_prompt(prompt_data)
        print(f"Prompt submitted successfully!")
        print(f"Prompt ID: {result.get('prompt_id')}")
        print(f"Queue number: {result.get('number')}")
        
        if 'node_errors' in result and result['node_errors']:
            print(f"Node errors: {result['node_errors']}")
        
        # You can then check the history to see results
        if 'prompt_id' in result:
            # Wait a bit for processing, then check history
            import time
            time.sleep(2)
            
            history = gateway.get_history(result['prompt_id'])
            print(f"Execution history: {json.dumps(history, indent=2)}")
        
    except Exception as e:
        print(f"Error running prompt: {e}")

def example_standalone_function():
    """Example using the standalone run_prompt function"""
    
    # Simple prompt data
    prompt_data = {
        "prompt": {
            "1": {
                "inputs": {"text": "test prompt"},
                "class_type": "CLIPTextEncode"
            }
        }
    }
    
    try:
        # Use the standalone function (equivalent to TypeScript runPrompt)
        result = run_prompt(prompt_data)
        print(f"Standalone function result: {result}")
        
    except Exception as e:
        print(f"Error with standalone function: {e}")

def example_queue_management():
    """Example of queue management functions"""
    
    gateway = ComfyGateway()
    
    try:
        # Clear the entire queue
        result = gateway.manage_queue(clear=True)
        print(f"Queue cleared: {result}")
        
        # Delete specific prompts (if you have prompt IDs)
        # result = gateway.manage_queue(delete=["prompt-id-1", "prompt-id-2"])
        
        # Interrupt current processing
        result = gateway.interrupt_processing()
        print(f"Processing interrupted: {result}")
        
    except Exception as e:
        print(f"Error managing queue: {e}")

if __name__ == "__main__":
    print("=== ComfyUI Gateway Python Examples ===\n")
    
    print("1. Basic Usage:")
    example_basic_usage()
    
    print("\n2. Queue Management:")
    example_queue_management()
    
    print("\n3. Standalone Function:")
    example_standalone_function()
    
    # Uncomment to test actual prompt execution
    # print("\n4. Run Prompt Example:")
    # example_run_prompt() 