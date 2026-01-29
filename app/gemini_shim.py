import os
import sys
import argparse
import time
import subprocess
from google import genai
from google.genai.errors import ServerError, ClientError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# ==========================================
#  GEMINI SHIM v2.0 (Orchestrator Edition)
# ==========================================

def get_file_tree():
    """
    Returns a clean string of the project's file structure.
    Crucial for preventing AI hallucinations.
    """
    # Method 1: Git (Fastest & Most Accurate)
    try:
        # We assume the CWD is the target repository root
        result = subprocess.run(
            ["git", "ls-files"], 
            capture_output=True, 
            text=True, 
            timeout=2
        )
        if result.returncode == 0 and result.stdout.strip():
            files = result.stdout.strip().split('\n')
            # Limit to top 300 files to save context window
            return "\n".join(files[:300])
    except Exception:
        pass

    # Method 2: Manual Scan (Fallback for non-git folders)
    allowed_exts = {'.py', '.js', '.ts', '.tsx', '.html', '.css', '.md', '.json', '.yml', '.rs', '.c', '.cpp', '.h', '.ps1'}
    file_list = []
    
    for root, dirs, files in os.walk("."):
        # Skip hidden folders, node_modules, and the script tools themselves
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'dist', 'venv', '__pycache__']]
        
        for file in files:
            if os.path.splitext(file)[1] in allowed_exts:
                rel_path = os.path.relpath(os.path.join(root, file), ".")
                file_list.append(rel_path)
                if len(file_list) >= 100: # Hard limit for fallback
                    break
        if len(file_list) >= 100:
            break
            
    return "\n".join(file_list)

def main():
    # 1. Parse Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="*", help="The prompt text") # Changed to * (optional)
    parser.add_argument("--model", required=True, help="Model ID")
    args = parser.parse_args()

    # HYBRID INPUT: Prefer Env Var (Robust), Fallback to Args (Legacy)
    full_prompt = os.environ.get("GEMINI_PROMPT", "")
    if not full_prompt:
        if args.prompt:
            full_prompt = " ".join(args.prompt)
        else:
            print("Error: No prompt provided (via args or GEMINI_PROMPT).", file=sys.stderr)
            sys.exit(1)

    model_id = args.model

    # 2. AUTO-DETECT CONTEXT
    # server.py sets the CWD to the /app/workspace/<repo> folder.
    current_folder = os.path.basename(os.getcwd())
    file_tree = get_file_tree()

    # 3. INJECT CONTEXT
    # This invisible footer forces the AI to look at the REAL files.
    system_context = f"""

    [SYSTEM CONTEXT INJECTION]
    Current Project Name: {current_folder}
    
    ACTUAL FILE STRUCTURE (Do not hallucinate files outside this list):
    ---
    {file_tree}
    ---
    """
    
    final_prompt = full_prompt + system_context

    # 4. Setup Client
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Print to stderr so PowerShell script catches it as an error
        print("Error: GEMINI_API_KEY missing in Docker environment.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # 5. Safety Sleep (Rate Limit Protection)
    if "gemini-3" in model_id:
        time.sleep(5) 

    # 6. Execute
    try:
        @retry(
            retry=retry_if_exception_type(ServerError),
            wait=wait_exponential(multiplier=2, min=4, max=20),
            stop=stop_after_attempt(5),
            reraise=True
        )
        def generate_with_retry():
            return client.models.generate_content(
                model=model_id,
                contents=final_prompt
            )

        response = generate_with_retry()
        
        if response.text:
            print(response.text)
        else:
            print("Error: Empty response from Gemini.", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        print(f"Error executing {model_id}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
