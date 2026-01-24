#!/usr/bin/env python3
import sys
import os
import google.generativeai as genai

# This script mocks the behavior of the 'gemini' CLI tool used in the .ps1 scripts.
# It takes the prompt as the first argument and prints the response.

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: gemini <prompt>", file=sys.stderr)
        sys.exit(1)

    prompt = sys.argv[1]

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Determine if we need JSON output based on the prompt content (heuristic)
        # The .ps1 scripts often ask for JSON. Gemini Pro handles this well via prompt engineering,
        # but we can also set generation_config if needed. For now, standard generation is usually fine.
        
        response = model.generate_content(prompt)
        
        # Check for safety blocks or errors
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            print(f"Error: Blocked by safety filters: {response.prompt_feedback.block_reason}", file=sys.stderr)
            sys.exit(1)
            
        if not response.text:
             print("Error: Empty response from AI.", file=sys.stderr)
             sys.exit(1)

        # Output ONLY the text, as the .ps1 script expects
        print(response.text)

    except Exception as e:
        print(f"Critical Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
