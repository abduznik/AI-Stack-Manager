import argparse
import sys
from rich.console import Console
from .profile_gen import generate_profile
from .architect import scaffold_project, fix_code, explain_code
from .repo_tools import optimize_topics, generate_descriptions
from .issue_gen import create_issue

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Git-Alchemist: AI-powered Git Operations")
    parser.add_argument("--smart", action="store_true", help="Use high-end Gemini Pro models (slower/lower quota)")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # ... existing parser code ...
    # (I'll keep the subparser definitions as is, just the execution logic changes)

    # Re-pasting the subparser block to ensure replace works correctly with context
    # Profile Generator Command
    profile_parser = subparsers.add_parser("profile", help="Generate or update GitHub Profile README")
    profile_parser.add_argument("--force", action="store_true", help="Force full regeneration")
    profile_parser.add_argument("--user", help="GitHub username (optional, detects automatically)")

    # Repo Tools
    topics_parser = subparsers.add_parser("topics", help="Optimize repository topics/tags")
    topics_parser.add_argument("--user", help="GitHub username")

    describe_parser = subparsers.add_parser("describe", help="Generate missing repository descriptions")
    describe_parser.add_argument("--user", help="GitHub username")

    # Issue Generator
    issue_parser = subparsers.add_parser("issue", help="Draft a technical issue from an idea")
    issue_parser.add_argument("idea", help="The feature or bug idea")

    # Architect Commands
    scaffold_parser = subparsers.add_parser("scaffold", help="Generate a new project structure (safe mode)")
    scaffold_parser.add_argument("instruction", help="What to build (e.g., 'A Flask app with Docker')")

    fix_parser = subparsers.add_parser("fix", help="Modify a file using AI")
    fix_parser.add_argument("file", help="Path to the file to fix")
    fix_parser.add_argument("instruction", help="What to change")

    explain_parser = subparsers.add_parser("explain", help="Explain code or concepts")
    explain_parser.add_argument("context", help="The code or concept to explain")

    args = parser.parse_args()
    mode = "smart" if args.smart else "fast"
    
    if args.command == "profile":
        generate_profile(args.user, args.force, mode=mode)
    elif args.command == "topics":
        optimize_topics(args.user, mode=mode)
    elif args.command == "describe":
        generate_descriptions(args.user, mode=mode)
    elif args.command == "issue":
        create_issue(args.idea, mode=mode)
    elif args.command == "scaffold":
        scaffold_project(args.instruction, mode=mode)
    elif args.command == "fix":
        fix_code(args.file, args.instruction, mode=mode)
    elif args.command == "explain":
        explain_code(args.context, mode=mode)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
