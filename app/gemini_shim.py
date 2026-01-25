import os
import sys
import argparse
import time
from google import genai
from google.genai import types

def main():
    # 1. Parse Arguments to match the old CLI usage:
    #    usage: gemini [PROMPT] --model [MODEL_ID]
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="+", help="The prompt text")
    parser.add_argument("--model", required=True, help="Model ID (e.g., gemma-3-27b-it)")
    args = parser.parse_args()

    # Reconstruct the prompt if it was split by shell arguments
    full_prompt = " ".join(args.prompt)
    model_id = args.model

    # 2. Initialize the New 2026 Client
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set in environment.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # 3. Smart Rate Limit Protection (The "Manager" Logic)
    # If we detect Gemini 3, we force a safety sleep to prevent instant crashes.
    if "gemini-3" in model_id:
        time.sleep(15) 

    try:
        # 4. Generate Content
        response = client.models.generate_content(
            model=model_id,
            contents=full_prompt
        )
        
        # 5. Output CLEAN text (stdout) so PowerShell can capture it
        if response.text:
            print(response.text)
        else:
            print("Error: Empty response from AI.", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        # Output error to stderr so your PowerShell 'catch' block triggers
        print(f"Error executing {model_id}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()