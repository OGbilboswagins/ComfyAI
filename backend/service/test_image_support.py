#!/usr/bin/env python3
"""
Test script for image support in mcp-client
"""
import asyncio
import base64
import os
from mcp_client import comfyui_agent_invoke, ImageData

async def test_image_support():
    """Test image support functionality"""
    
    # Create a simple test image (1x1 pixel red image as base64)
    test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA4RDOaQAAAABJRU5ErkJggg=="
    
    # Create ImageData object
    test_image = ImageData(
        filename="test_image.png",
        data=f"data:image/png;base64,{test_image_base64}",
        url=None  # No URL, will use base64 data
    )
    
    # Test with image
    print("Testing image support...")
    prompt = "Please describe what you see in this image and suggest a ComfyUI workflow that could create something similar."
    
    try:
        async for text, ext in comfyui_agent_invoke(prompt, [test_image]):
            print(f"Response: {text[:100]}...")
            if ext:
                print(f"Extension data: {ext}")
        
        print("Image support test completed successfully!")
        
    except Exception as e:
        print(f"Error testing image support: {str(e)}")
    
    # Test without image for comparison
    print("\nTesting without image...")
    try:
        async for text, ext in comfyui_agent_invoke("Tell me about ComfyUI workflows for image generation.", None):
            print(f"Response: {text[:100]}...")
            if ext:
                print(f"Extension data: {ext}")
        
        print("Text-only test completed successfully!")
        
    except Exception as e:
        print(f"Error testing text-only: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_image_support()) 