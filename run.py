import subprocess, sys, os, time, threading, webbrowser

def check_env():
    from dotenv import load_dotenv
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("\n[BAYMAX] ERROR: OPENAI_API_KEY missing from .env")
        print("[BAYMAX] Get your key at platform.openai.com/api-keys")
        print("[BAYMAX] Add it to .env as: OPENAI_API_KEY=your_key\n")
        sys.exit(1)
    print("[BAYMAX] Environment OK.")

def start_backend():
    print("[BAYMAX] Starting backend on port 8000...")
    log_file = open("backend.log", "w")
    subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "api.server:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ], stdout=log_file, stderr=log_file)

def start_frontend():
    print("[BAYMAX] Starting frontend on port 5173...")
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    log_file = open("frontend.log", "w")
    subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", "5173", "--host", "0.0.0.0"],
        cwd=frontend_dir,
        shell=(sys.platform == "win32"),
        stdout=log_file,
        stderr=log_file
    )

def open_browser():
    time.sleep(4)
    webbrowser.open("http://localhost:5173")
    print("[BAYMAX] Browser opened.")
    print("[BAYMAX] Say 'Hey BAYMAX' to begin.")

if __name__ == "__main__":
    print("[BAYMAX] v11.0 — Starting up...")
    print("[BAYMAX] Say 'Hey BAYMAX' when ready")
    check_env()
    start_backend()
    time.sleep(2)
    start_frontend()
    threading.Thread(target=open_browser, daemon=True).start()
    print("[BAYMAX] All systems online.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[BAYMAX] Shutting down. Goodbye.")
