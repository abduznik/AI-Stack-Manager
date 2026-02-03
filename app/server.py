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

# Internal state
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
    request: Request,
    gh_token: str = Form(None), 
    gemini_key: str = Form(None)
):
    msg = []
    if gh_token:
        token_clean = gh_token.strip().replace('"', '').replace("'", "")
        APP_STATE["GH_TOKEN"] = token_clean
        os.environ["GH_TOKEN"] = token_clean
        try:
            # Re-auth GH CLI
            process = subprocess.Popen(["gh", "auth", "login", "--with-token"], stdin=subprocess.PIPE, text=True)
            process.communicate(input=token_clean)
            msg.append("GitHub Token Saved.")
        except Exception as e:
            msg.append("GH Auth Error: " + str(e))
            
    if gemini_key:
        cleaned_key = gemini_key.strip().replace('"', '').replace("'", "")
        APP_STATE["GEMINI_API_KEY"] = cleaned_key
        os.environ["GEMINI_API_KEY"] = cleaned_key
        msg.append("Gemini API Key Saved.")

    return templates.TemplateResponse("partials/settings_alert.html", {"request": request, "messages": msg})

@app.get("/api/repos")
async def get_repos():
    if not APP_STATE["GH_TOKEN"]:
        return JSONResponse([])
    try:
        env = os.environ.copy()
        env["GH_TOKEN"] = APP_STATE["GH_TOKEN"]
        cmd = ["gh", "repo", "list", "--limit", "100", "--json", "nameWithOwner,updatedAt"]
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            return JSONResponse([])
        repos = json.loads(result.stdout)
        repos.sort(key=lambda x: x.get('updatedAt', ''), reverse=True)
        return JSONResponse([r["nameWithOwner"] for r in repos])
    except Exception:
        return JSONResponse([])

@app.websocket("/ws/run/{tool_name}")
async def websocket_endpoint(websocket: WebSocket, tool_name: str):
    await websocket.accept()
    
    # Mapping tool names to Git-Alchemist CLI arguments
    tool_map = {
        "gen-desc": ["describe"],
        "gen-topics": ["topics"],
        "gen-issue": ["issue"],
        "gen-profile": ["profile"],
        "arch-init": ["scaffold"],
        "arch-fix": ["fix"],
        "arch-explain": ["explain"]
    }
    
    args_base = tool_map.get(tool_name)
    if not args_base:
        await websocket.close()
        return

    process = None
    try:
        data = await websocket.receive_json()
        user_input = data.get("input", "").strip()
        user_file = data.get("file", "")
        target_repo = data.get("repo", "").strip()
        is_smart = data.get("smart", False)
        
        env = os.environ.copy()
        env["GEMINI_API_KEY"] = APP_STATE["GEMINI_API_KEY"]
        env["GH_TOKEN"] = APP_STATE["GH_TOKEN"]
        env["PYTHONPATH"] = os.getcwd() # Ensure imports work

        # Build full command
        cmd = ["python3", "-m", "app.git_alchemist.src.cli"]
        if is_smart:
            cmd.append("--smart")
        
        cmd.extend(args_base)
        
        # Add tool-specific positional/optional args
        if tool_name == "gen-issue":
            cmd.append(user_input)
        elif tool_name == "arch-init":
            cmd.append(user_input)
        elif tool_name == "arch-fix":
            cmd.append(user_file)
            cmd.append(user_input)
        elif tool_name == "arch-explain":
            cmd.append(user_input)
        
        working_dir = None
        if target_repo:
            await websocket.send_text(f"[SYSTEM] Context: {target_repo}\n")
            repo_slug = target_repo.replace("https://github.com/", "").replace(".git", "")
            safe_name = repo_slug.split("/")[-1]
            workspace_path = f"/app/workspace/{safe_name}"
            
            if not os.path.exists(workspace_path):
                os.makedirs(workspace_path, exist_ok=True)
                await websocket.send_text("[SYSTEM] Cloning repository...\n")
                subprocess.run(["gh", "repo", "clone", repo_slug, "."], cwd=workspace_path, check=False, env=env)
            
            working_dir = workspace_path

        await websocket.send_text(f"[SYSTEM] Running Git-Alchemist {tool_name}...\n")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
            cwd=working_dir
        )

        for line in process.stdout:
            await websocket.send_text(line)
            
        process.wait()
        await websocket.send_text(f"\n[SYSTEM] Finished (Exit Code: {process.returncode})")
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(f"\n[ERROR] {str(e)}")
    finally:
        if process and process.poll() is None:
            process.terminate()
        try:
            await websocket.close()
        except:
            pass
