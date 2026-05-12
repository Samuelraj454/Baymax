import os, socket, httpx, subprocess, sys
from dotenv import load_dotenv

def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

async def check_api():
    load_dotenv()
    key = os.getenv("GROQ_API_KEY")
    if not key: return "MISSING KEY"
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post("https://api.groq.com/openai/v1/chat/completions", 
                                  headers={"Authorization": f"Bearer {key}"},
                                  json={"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
                                  timeout=5.0)
            return f"OK ({res.status_code})"
    except Exception as e:
        return f"ERROR: {e}"

def run_diag():
    print("--- BAYMAX DIAGNOSTIC ---")
    print(f"Python: {sys.version}")
    print(f"Backend (8000): {'ONLINE' if check_port(8000) else 'OFFLINE'}")
    print(f"Frontend (5173): {'ONLINE' if check_port(5173) else 'OFFLINE'}")
    
    import asyncio
    api_status = asyncio.run(check_api())
    print(f"API Connectivity: {api_status}")
    
    # Check for core files
    core_files = ["core/agent_loop.py", "api/server.py", "frontend/src/App.jsx"]
    for f in core_files:
        print(f"File {f}: {'EXISTS' if os.path.exists(f) else 'MISSING'}")

if __name__ == "__main__":
    run_diag()
