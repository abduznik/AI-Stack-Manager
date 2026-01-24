import os
import subprocess
import asyncio
import json
from fastapi import FastAPI, Request, WebSocket, Form, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

if not os.path.exists("app/static"):
    os.makedirs("app/static")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Internal state (reset on container restart)
APP_STATE = {
    "GH_TOKEN": os.getenv("GH_TOKEN", ""),
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", "")
}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "gh_token_set": bool(APP_STATE["GH_TOKEN"]),
        "gemini_key_set": bool(APP_STATE["GEMINI_API_KEY"])
    })

@app.post("/settings")
async def save_settings(
    gh_token: str = Form(None), 
    gemini_key: str = Form(None)
):
    msg = []
    if gh_token:
        APP_STATE["GH_TOKEN"] = gh_token.strip()
        try:
            # We use --with-token to avoid interactive prompts
            process = subprocess.Popen(["gh", "auth", "login", "--with-token"], stdin=subprocess.PIPE, text=True)
            process.communicate(input=APP_STATE["GH_TOKEN"])
            msg.append("GitHub Token Saved & Authenticated.")
        except Exception as e:
            msg.append(f"GitHub Auth Error: {str(e)}")
            
    if gemini_key:
        cleaned_key = gemini_key.strip()
        APP_STATE["GEMINI_API_KEY"] = cleaned_key
        os.environ["GEMINI_API_KEY"] = cleaned_key
        msg.append("Gemini API Key Saved.")

    return HTMLResponse(content=f"<div class='p-4 bg-green-900 text-green-100 rounded'>{'<br>'.join(msg)}</div>")

@app.websocket("/ws/run/{tool_name}")
async def websocket_endpoint(websocket: WebSocket, tool_name: str):
    await websocket.accept()
    
    script_map = {
        "gen-desc": {"path": "/scripts/AI-Gen-Description/script.ps1", "func": "gen-desc"},
        "gen-issue": {"path": "/scripts/AI-Gen-Issue/script.ps1", "func": "gen-issue"},
        "gen-profile": {"path": "/scripts/AI-Gen-Profile/script.ps1", "func": "gen-profile"},
        "gen-topics": {"path": "/scripts/AI-Gen-Topics/script.ps1", "func": "gen-topics"}
    }
    
    target = script_map.get(tool_name)
    if not target:
        await websocket.send_text("Error: Tool not found.")
        await websocket.close()
        return

    try:
        data = await websocket.receive_json()
        user_input = data.get("input", "")
        
        # PowerShell execution string: dot-source script then call function
        ps_command = f". '{target['path']}'; {target['func']}"
        
        await websocket.send_text(f"[SYSTEM] Initializing {tool_name}...
")
        
        env = os.environ.copy()
        if APP_STATE["GH_TOKEN"]:
            env["GH_TOKEN"] = APP_STATE["GH_TOKEN"]
        
        # Verify key presence for debugging
        if APP_STATE["GEMINI_API_KEY"]:
            env["GEMINI_API_KEY"] = APP_STATE["GEMINI_API_KEY"]
            masked_key = APP_STATE["GEMINI_API_KEY"][:4] + "..." + APP_STATE["GEMINI_API_KEY"][-4:]
            await websocket.send_text(f"[DEBUG] Using Gemini Key: {masked_key}\n")
        else:
            await websocket.send_text(f"[WARN] No Gemini Key found in settings!\n")

        process = subprocess.Popen(
            ["pwsh", "-NoProfile", "-Command", ps_command],
            stdin=subprocess.PIPE if user_input else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env
        )

        if user_input and process.stdin:
            process.stdin.write(user_input + "\n")
            process.stdin.flush()
            process.stdin.close()

        # Stream output line by line
        # We need a non-blocking read to allow checking for websocket disconnects, 
        # but standard 'for line in stdout' blocks.
        # Instead, we run the blocking read in a thread executor or just risk it blocking briefly.
        # For simplicity in this stack, we stick to the loop but wrap in try/finally to kill process.
        
        for line in process.stdout:
            await websocket.send_text(line)
            
        process.wait()
        await websocket.send_text(f"\n[SYSTEM] Finished with Exit Code: {process.returncode}")
        
    except WebSocketDisconnect:
        # Expected when user clicks Stop or closes tab
        print("Websocket disconnected, killing process...")
    except Exception as e:
        # Try to send error if socket is still open
        try:
            await websocket.send_text(f"\n[ERROR] {str(e)}")
        except:
            pass
    finally:
        # ENSURE PROCESS IS KILLED
        if 'process' in locals() and process.poll() is None:
            print(f"Terminating process for {tool_name}...")
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
        
        try:
            await websocket.close()
        except:
            pass