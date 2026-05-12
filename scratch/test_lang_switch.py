import asyncio
from core.agent_loop import BAYMAXAgent

async def test():
    agent = BAYMAXAgent()
    
    queries = [
        "speak in hindi",
        "speak in telugu",
        "change back to english"
    ]
    
    for q in queries:
        print(f"\nUser: {q}")
        res = await agent.run(q)
        print(f"Response: {res.get('response')}")
        print(f"Language Change: {res.get('language_change')}")
        print(f"New Language: {res.get('new_language')}")

asyncio.run(test())
