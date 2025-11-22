#!/usr/bin/env python3
"""
Test script for ComfyAI workflow rewrite endpoint.
Run with ComfyUI running:

    python scripts/test_workflow_rewrite.py
"""

import aiohttp
import asyncio
import json


API_URL = "http://127.0.0.1:8188/api/workflow/rewrite"


async def main():
    print(f"Testing POST {API_URL}")

    # Minimal dummy workflow graph
    dummy_workflow = {
        "nodes": [
            {
                "id": 1,
                "type": "LoadImage",
                "inputs": {"filename": "input.png"},
                "outputs": {"IMAGE": 2}
            },
            {
                "id": 2,
                "type": "EmptyNode",
                "inputs": {},
                "outputs": {}
            }
        ]
    }

    test_payload = {
        "workflow": dummy_workflow,
        "prompt": "Rewrite this workflow: add a VAE encode node."
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json=test_payload) as resp:
            print("\n--- HTTP RESPONSE STATUS ---")
            print(resp.status)

            text = await resp.text()
            print("\n--- RAW RESPONSE BODY ---")
            print(text)

            # Try JSON decode
            try:
                data = json.loads(text)
                print("\n--- JSON PARSED ---")
                print(json.dumps(data, indent=2))
            except Exception:
                print("\n(Response was not JSON)")

    print("\nDone.\n")


if __name__ == "__main__":
    asyncio.run(main())
