import json
import tempfile
import os
from rich.console import Console
from .core import generate_content
from .utils import run_shell

console = Console()

def create_issue(idea, mode="fast"):
    """
    Translates an idea into a technical GitHub issue.
    """
    console.print(f"[cyan]Drafting technical issue for: {idea} ({mode} mode)...[/cyan]")
    
    prompt = f"""
You are a Senior Tech Lead.
User Input: '{idea}'
TASK: Translate this into a technical implementation plan.
STRUCTURE:
- **Context**: 1 sentence explaining WHY.
- **Directives**: Bullet points of EXACTLY what to change.
OUTPUT FORMAT: Return ONLY a JSON object with keys: "title", "body", "label", "easy" (boolean).
No markdown blocks.
"""

    result = generate_content(prompt, mode=mode)
    if not result: return

    try:
        clean_json = result.replace("```json", "").replace("```", "").strip()
        issue = json.loads(clean_json)
        
        title = f"[DRAFT] {issue['title']}"
        body = f"{issue['body']}\n\n> Automated by Git-Alchemist"
        label = issue.get('label', 'enhancement')
        
        console.print(f"[yellow]Uploading Draft: {title}[/yellow]")
        
        # Create labels if they don't exist
        run_shell('gh label create "automated" --color "505050" 2>/dev/null', check=False)
        run_shell('gh label create "status: draft" --color "333333" 2>/dev/null', check=False)
        run_shell(f'gh label create "{label}" 2>/dev/null', check=False)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tf:
            tf.write(body)
            temp_name = tf.name

        cmd = [
            'gh',
            'issue',
            'create',
            '--title',
            f'"{title}"',
            '--body-file',
            f'"{temp_name}"',
            '--label',
            '"status: draft"',
            '--label',
            '"automated"',
            '--label',
            f'"{label}"'
        ]
        
        if issue.get('easy'):
            run_shell('gh label create "good first issue" --color "7057ff" 2>/dev/null', check=False)
            cmd.extend(['--label', '"good first issue"'])

        run_shell(" ".join(cmd))
        os.unlink(temp_name)
        
        console.print("[green]Success! Issue created as draft.[/green]")
        
    except Exception as e:
        console.print(f"[red]Failed to create issue:[/red] {e}")
        console.print(f"[gray]Raw Output:[/gray] {result}")
