import os
import sys
import argparse
import time
from google import genai

def main():
    # 1. Parse Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="+", help="The prompt text")
    parser.add_argument("--model", required=True, help="Model ID")
    args = parser.parse_args()

    full_prompt = " ".join(args.prompt)
    model_id = args.model

    # 2. AUTO-DETECT CONTEXT (The Magic Fix)
    # Get the repo name from the folder path
    current_folder = os.path.basename(os.getcwd())
    
    # Detect tech stack hints
    tech_hint = ""
    if os.path.exists("main.ts"): tech_hint = "(Obsidian Plugin / TypeScript)"
    elif os.path.exists("package.json"): tech_hint = "(Node.js / JavaScript)"
    elif os.path.exists("requirements.txt"): tech_hint = "(Python Project)"
    elif os.path.exists("Cargo.toml"): tech_hint = "(Rust Project)"

    # Inject context invisibly at the end of the prompt
    system_context = f"\n\n[SYSTEM CONTEXT: The user is working in the repository '{current_folder}' {tech_hint}. If they ask to 'check code', assume standard file structures for this tech stack.]"
    final_prompt = full_prompt + system_context

    # 3. Setup Client
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY missing.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # 4. Safety Sleep for Gemini 3 Preview (Prevents 429/500 errors)
    if "gemini-3" in model_id:
        time.sleep(15)

    # 5. Execute
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=final_prompt
        )
        if response.text:
            print(response.text)
        else:
            print("Error: Empty response.", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        # Print to stderr so PowerShell catches it as an error
        print(f"Error executing {model_id}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()