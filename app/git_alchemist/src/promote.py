import os
import requests
from rich.console import Console

console = Console()

STORY = """
I’ve been working on this tool for a couple of months now. It actually started as a 
collection of loose PowerShell scripts I wrote to handle my own GitHub maintenance 
(updating my profile, tagging repos, etc.). 

I finally decided to combine them all into a unified project. I ported everything to 
Python and built Git-Alchemist. It uses Gemini 3 and Gemma 3 to automate the boring 
parts of Git management—like writing descriptions or scaffolding project structures 
in safe, temporary workspaces. I'm really happy with how the consolidation turned out 
and wanted to share it with the community.
"""

def post_to_devto(api_key):
    """Automates posting to Dev.to"""
    url = "https://dev.to/api/articles"
    headers = {"api-key": api_key}
    
    article = {
        "article": {
            "title": "I consolidated my Git automation scripts into a unified AI stack: Git-Alchemist",
            "published": True,
            "body_markdown": f"# Git-Alchemist ⚗️\n\n{STORY}\n\nCheck it out here: [https://github.com/abduznik/Git-Alchemist](https://github.com/abduznik/Git-Alchemist)\n\nLanding Page: [https://abduznik.github.io/Git-Alchemist/](https://abduznik.github.io/Git-Alchemist/)",
            "tags": ["python", "github", "ai", "opensource"],
            "series": "Git Automation"
        }
    }
    
    try:
        response = requests.post(url, json=article, headers=headers)
        if response.status_code == 201:
            console.print("[green]Successfully posted to Dev.to![/green]")
        else:
            console.print(f"[red]Failed to post to Dev.to:[/red] {response.text}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

def generate_manual_submissions():
    """Generates text for manual form submissions"""
    submissions = {
        "Hackaday (https://hackaday.com/submit-a-tip/)": {
            "Subject": "AI-Powered GitHub Maintenance: Git-Alchemist",
            "Message": f"Hi Hackaday! I thought you might find this interesting. {STORY}\nRepo: https://github.com/abduznik/Git-Alchemist"
        },
        "TLDR Newsletter (https://tldr.tech/submit)": {
            "Link": "https://github.com/abduznik/Git-Alchemist",
            "Description": "A unified AI stack for GitHub repository management and project scaffolding."
        },
        "Console.dev (Newsletter for Dev Tools)": {
            "Email": "hello@console.dev",
            "Subject": "Tool Submission: Git-Alchemist",
            "Body": f"Hi Console team, {STORY}\nRepo: https://github.com/abduznik/Git-Alchemist"
        }
    }
    
    console.print("\n[bold cyan]--- Manual Submission Drafts ---[/bold cyan]")
    for platform, data in submissions.items():
        console.print(f"\n[bold yellow]{platform}[/bold yellow]")
        for k, v in data.items():
            console.print(f"[bold]{k}:[/bold] {v}")

if __name__ == "__main__":
    devto_key = os.getenv("DEVTO_API_KEY")
    if devto_key:
        post_to_devto(devto_key)
    else:
        console.print("[yellow]No DEVTO_API_KEY found. Skipping automated post.[/yellow]")
    
    generate_manual_submissions()
