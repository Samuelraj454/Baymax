import os
import httpx
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

async def test_groq():
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 10
    }
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, headers=headers, json=payload)
            print(f"Status: {res.status_code}")
            print(f"Response: {res.text[:100]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_groq())
