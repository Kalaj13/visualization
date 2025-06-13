import os
import requests
import argparse
from pathlib import Path

try:
    from rich.console import Console
    from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn
    rich_available = True
except ImportError:
    rich_available = False
    print("For a better experience, install the 'rich' library: pip install rich")

# ============================== SETTINGS ==============================

OLLAMA_MODEL = "gemma3:1b"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"

ALLOWED_EXTENSIONS = {
    ".py", ".cpp", ".h", ".hpp", ".c", ".java", ".js", ".ts", ".cs", ".go"
}
EXCLUDED_DIRS = {".git", ".idea", ".vscode", "__pycache__", ".venv", "build"}

DEBUG = True

# ============================== CHAT STATE ==============================

chat_history = []

def call_ollama_chat(user_prompt: str) -> str:
    """Sends a prompt to Ollama using the chat API and maintains context."""
    chat_history.append({"role": "user", "content": user_prompt})

    try:
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "messages": chat_history,
            "stream": False
        })
        response.raise_for_status()
        assistant_message = response.json().get("message", {}).get("content", "").strip()
        chat_history.append({"role": "assistant", "content": assistant_message})
        return assistant_message
    except requests.exceptions.RequestException as e:
        return f"[Error communicating with Ollama: {e}]"

# ============================== PROJECT HELPERS ==============================

def generate_project_tree(path: Path, indent: str = "") -> str:
    lines = []
    for item in sorted(path.iterdir()):
        if item.name in EXCLUDED_DIRS:
            continue
        lines.append(f"{indent}├── {item.name}")
        if item.is_dir():
            lines.append(generate_project_tree(item, indent + "│   "))
    return "\n".join(lines)

def collect_source_files(path: Path) -> list:
    files = []
    if DEBUG:
        print(f"\nSearching for source files in: {path}")
        print(f"Allowed extensions: {ALLOWED_EXTENSIONS}")
        print(f"Excluded directories: {EXCLUDED_DIRS}\n")

    for root, dirs, filenames in os.walk(path):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        if DEBUG and filenames:
            print(f"Directory: {root}")
            print(f"  Files: {filenames}\n")
        for filename in filenames:
            filepath = Path(root) / filename
            if filepath.suffix.lower() in ALLOWED_EXTENSIONS:
                files.append(filepath)
                if DEBUG:
                    print(f"  Added: {filepath}")
    print(f"\nFound {len(files)} source files to review")
    return files

# ============================== MAIN ANALYSIS ==============================

def analyze_project(project_dir: str, project_description: str, file_limit: int = None):
    print(f"\nAnalyzing project: {project_dir}")
    project_path = Path(project_dir)
    if not os.path.isdir(project_dir) or not project_path.exists():
        print(f"[Error] Path does not exist or is not a directory: {project_dir}")
        return

    if os.path.exists(os.path.join(project_dir, "README.md")):
        with open(os.path.join(project_dir, "README.md"), "r") as f:
            project_readme = f.read().strip()
    else:
        project_readme = "README.md not found."

    print(f"Project description: {project_description}")
    print(f"Project README: {project_readme}")

    console = Console() if rich_available else None

    # Step 1: Project description
    if console:
        console.print("\n[bold blue]Step 1:[/bold blue] Sending project description...")
    else:
        print("\n🔷 Step 1: Sending project description...")

    description_prompt = (
        f"This is a description of the project:\n\n{project_description}\n\n"
        f"This is the provided README.md file:\n\n{project_readme}\n\n"
        f"Use this to understand its purpose."
    )
    response = call_ollama_chat(description_prompt)
    console.print(response) if console else print(response)

    # Step 2: Project structure
    if console:
        console.print("\n[bold blue]Step 2:[/bold blue] Analyzing project folder structure...")
    else:
        print("\n🔷 Step 2: Sending project folder structure...")

    tree_str = generate_project_tree(project_path)
    if DEBUG:
        print(tree_str)
    tree_prompt = f"Here is the project's folder structure:\n\n{tree_str}\n\nComment on any organization or architecture issues."
    response = call_ollama_chat(tree_prompt)
    console.print(response) if console else print(response)

    # Step 3: File review
    files = collect_source_files(project_path)
    if file_limit and len(files) > file_limit:
        important_patterns = ["main", "app", "core", "index"]
        important_files = [f for f in files if any(pattern in f.stem.lower() for pattern in important_patterns)]
        other_files = [f for f in files if f not in important_files]
        files = (important_files + other_files)[:file_limit]
        if console:
            console.print(f"[yellow]Limiting to {file_limit} files[/yellow]")
        else:
            print(f"Limiting to {file_limit} files")

    if console:
        console.print(f"\n[bold blue]Step 3:[/bold blue] Reviewing {len(files)} source files...")
        with Progress(
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("Reviewing files", total=len(files))
            for file in files:
                try:
                    file_relative = file.relative_to(project_path)
                    progress.update(task, description=f"{file_relative}")
                    try:
                        code = file.read_text(encoding="utf-8", errors="ignore")[:3000]
                    except Exception as read_error:
                        print(f"Error reading {file}: {read_error}")
                        code = "# Error reading file content"
                    ext = file.suffix.lstrip('.')
                    prompt = f"""You are a senior code reviewer. Please review the following file for:
                    - Bugs
                    - Security issues
                    - Logic errors
                    - Style issues
                    - Maintainability
                    File: {file} Code:```{ext}\n{code}```"""
                    response = call_ollama_chat(prompt)
                    console.print(f"\n[bold green]🔍 Review for {file_relative}:[/bold green]")
                    console.print(response)
                    progress.update(task, advance=1)
                except Exception as e:
                    console.print(f"[bold red]ERROR:[/bold red] {file}: {e}")
                    progress.update(task, advance=1)
    else:
        print(f"\n🔷 Reviewing {len(files)} source files...")
        for i, file in enumerate(files, 1):
            print(f"\n🔍 Reviewing file {i}/{len(files)}: {file}")
            try:
                try:
                    code = file.read_text(encoding="utf-8", errors="ignore")[:3000]
                except Exception as read_error:
                    print(f"Error reading {file}: {read_error}")
                    code = "# Error reading file content"
                ext = file.suffix.lstrip('.')
                prompt = f"""You are a senior code reviewer. Please review the following file for:
                - Bugs
                - Security issues
                - Logic errors
                - Style issues
                - Maintainability
                File: {file} Code:```{ext}\n{code}```"""
                print(call_ollama_chat(prompt))
            except Exception as e:
                print(f"[ERROR] Skipping {file}: {e}")

    # Step 4: Summary
    if console:
        console.print("\n[bold blue]Step 4:[/bold blue] Generating project-wide summary...")
    else:
        print("\n🔷 Step 4: Requesting final project-wide summary...")

    summary_prompt = (
        """Based on your previous reviews of each file/files that were provided in previous prompts provided, provide a detailed project-wide summary. Please include:
           1. Any critical bugs
           2. Potential security issues
           3. Overall architectural problems
           4. Logic or flow issues
           5. Best practice violations
           Avoid repeating raw code. Be concise and actionable.
"""
    )
    response = call_ollama_chat(summary_prompt)
    console.print("\n[bold yellow]📋 PROJECT SUMMARY:[/bold yellow]") if console else print("\n📋 PROJECT SUMMARY:")
    console.print(response) if console else print(response)

    chat_history.clear()

# ============================== RUN SCRIPT ==============================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-powered code review tool using Ollama")
    parser.add_argument("--dir", "-d", help="Project directory to analyze")
    parser.add_argument("--description", "-desc", help="Short description of the project")
    parser.add_argument("--limit", "-l", type=int, help="Limit the number of files to review")
    args = parser.parse_args()

    project_dir = args.dir or r"C:\Users\aleks\Desktop\Python Projects\Visualization"
    project_description = args.description or "This is an app"

    desc_path = os.path.join(project_dir, "description.txt")
    if os.path.exists(desc_path):
        with open(desc_path, "r") as f:
            project_description = f.read().strip()

    analyze_project(project_dir, project_description, args.limit)
