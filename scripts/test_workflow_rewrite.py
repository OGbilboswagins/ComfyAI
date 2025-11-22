import json
import aiohttp
import asyncio

async def main():
    async with aiohttp.ClientSession() as session:
        payload = {
            "messages": [
                {"role": "user", "content": "Make a simple workflow that loads a checkpoint and generates an image."}
            ]
        }

        async with session.post("http://127.0.0.1:8188/api/workflow/rewrite", json=payload) as resp:
            print("Status:", resp.status)
            data = await resp.json()
            print(json.dumps(data, indent=2))

asyncio.run(main())