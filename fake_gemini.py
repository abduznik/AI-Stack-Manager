#!/usr/bin/env python3
import sys
import os
from google import genai

# Wrapper for the new Google Gen AI SDK
# Replaces the old 'gemini' CLI tool

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: gemini <prompt>", file=sys.stderr)
        sys.exit(1)

    prompt = sys.argv[1]

    try:
        client = genai.Client(api_key=api_key)
        
        # Use a modern model. 'gemini-1.5-flash' is fast and reliable for these tasks.
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        
        if response.text:
            print(response.text)
        else:
            print("Error: No text returned.", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        # Print only the error message to stderr to avoid confusing the calling script
        print(f"GenAI Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()