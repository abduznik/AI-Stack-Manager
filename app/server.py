import os
import subprocess
import asyncio
import json
import shutil
from fastapi import FastAPI, Request, WebSocket, Form, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
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
        token_clean = gh_token.strip()
        APP_STATE["GH_TOKEN"] = token_clean
        # Set globally for the process
        os.environ["GH_TOKEN"] = token_clean
        
        try:
            # We use --with-token to avoid interactive prompts
            process = subprocess.Popen(["gh", "auth", "login", "--with-token"], stdin=subprocess.PIPE, text=True)
            process.communicate(input=token_clean)
            msg.append("GitHub Token Saved & Authenticated.")
        except Exception as e:
            msg.append(f"GitHub Auth Error: {str(e)}")
            
    if gemini_key:
        cleaned_key = gemini_key.strip()
        APP_STATE["GEMINI_API_KEY"] = cleaned_key
        os.environ["GEMINI_API_KEY"] = cleaned_key
        msg.append("Gemini API Key Saved.")

    html_msg = "<br>".join(msg)
    response_html = f"<div class='p-4 bg-green-900 text-green-100 rounded'>{html_msg}</div>"
    return HTMLResponse(content=response_html)

@app.get("/api/repos")
async def get_repos():
    """Fetches list of repositories for the authenticated user"""
    if not APP_STATE["GH_TOKEN"]:
        print("DEBUG: No GH_TOKEN found in state.")
        return JSONResponse([])
    
    try:
        env = os.environ.copy()
        env["GH_TOKEN"] = APP_STATE["GH_TOKEN"]
        
        # Explicitly disable interactivity
        env["GH_PROMPT_DISABLED"] = "1"
        env["NO_COLOR"] = "1"

        # Fixed command: removed --order and --sort which are not supported by 'gh repo list'
        cmd = ["gh", "repo", "list", "--limit", "100", "--json", "nameWithOwner,updatedAt"]
        
        # Capture stderr to diagnose failure
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode != 0:
            print(f"GH Error (Code {result.returncode}): {result.stderr}")
            return JSONResponse([])
            
        repos = json.loads(result.stdout)
        
        # Sort in Python (descending by updatedAt)
        repos.sort(key=lambda x: x.get('updatedAt', ''), reverse=True)
        
        return JSONResponse([r["nameWithOwner"] for r in repos])
    except Exception as e:
        print(f"Exception fetching repos: {e}")
        return JSONResponse([])

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

    process = None
    try:
        data = await websocket.receive_json()
        user_input = data.get("input", "")
        target_repo = data.get("repo", "").strip()
        
        env = os.environ.copy()
        # Ensure env vars are set
        if APP_STATE["GH_TOKEN"]:
            env["GH_TOKEN"] = APP_STATE["GH_TOKEN"]
        if APP_STATE["GEMINI_API_KEY"]:
            env["GEMINI_API_KEY"] = APP_STATE["GEMINI_API_KEY"]

        working_dir = None
        if target_repo:
            await websocket.send_text(f"[SYSTEM] Switching context to {target_repo}...
")
            repo_slug = target_repo.replace("https://github.com/", "").replace(".git", "")
            safe_name = repo_slug.split("/")[-1]
            workspace_path = f"/app/workspace/{safe_name}"
            
            if not os.path.exists(workspace_path):
                os.makedirs(workspace_path, exist_ok=True)
                await websocket.send_text(f"[SYSTEM] Cloning {repo_slug}...
")
                subprocess.run(["gh", "repo", "clone", repo_slug, "."], cwd=workspace_path, check=False, env=env)
            else:
                await websocket.send_text("[SYSTEM] Pulling latest changes...
")
                subprocess.run(["git", "pull"], cwd=workspace_path, check=False, env=env)
            
            working_dir = workspace_path
        
        ps_command = f". '{target['path']}'; {target['func']}"
        await websocket.send_text(f"[SYSTEM] Initializing {tool_name}...
")
        
        if "GEMINI_API_KEY" in env:
            masked = env["GEMINI_API_KEY"][:4] + "..." + env["GEMINI_API_KEY"][-4:]
            await websocket.send_text(f"[DEBUG] Using Gemini Key: {masked}
")

        process = subprocess.Popen(
            ["pwsh", "-NoProfile", "-Command", ps_command],
            stdin=subprocess.PIPE if user_input else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
            cwd=working_dir
        )

        if user_input and process.stdin:
            process.stdin.write(user_input + "\n")
            process.stdin.flush()
            process.stdin.close()

        for line in process.stdout:
            await websocket.send_text(line)
            
        process.wait()
        await websocket.send_text(f"\n[SYSTEM] Finished with Exit Code: {process.returncode}")
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(f"\n[ERROR] {str(e)}")
        except:
            pass
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
        try:
            await websocket.close()
        except:
            pass