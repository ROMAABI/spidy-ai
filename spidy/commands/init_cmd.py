import subprocess
from pathlib import Path
from datetime import datetime
from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

class InitCommand(BaseCommand):
    name = "init"
    description = "Initialize project analysis and generate SPIDY.md"
    usage = "/init"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        root = Path(".")
        project_name = root.resolve().name
        sections = [f"# {project_name} - Project Overview", ""]
        # Tech stack detection
        tech = []
        if (root / "package.json").exists(): tech.append("Node.js")
        if (root / "pyproject.toml").exists(): tech.append("Python")
        if (root / "Cargo.toml").exists(): tech.append("Rust")
        if (root / "go.mod").exists(): tech.append("Go")
        if (root / "Makefile").exists(): tech.append("Make")
        sections.append("## Tech Stack")
        sections.append(", ".join(tech) if tech else "Detecting...")
        sections.append("")
        # Commands
        sections.append("## Commands")
        sections.append("- Build: python3 -m build")
        sections.append("- Run: python3 main.py")
        sections.append("- Test: pytest")
        sections.append("")
        # Architecture
        sections.append("## Architecture")
        try:
            r = subprocess.run(["find", ".", "-maxdepth", "2", "-type", "f", "-name", "*.py"],
                               capture_output=True, text=True, timeout=5)
            files = r.stdout.strip().splitlines()[:20]
            for f in files:
                sections.append(f"- {f}")
        except Exception:
            sections.append("- (could not scan)")
        sections.append("")
        sections.append("## Coding Conventions")
        sections.append("- Python 3.14+")
        sections.append("- f-strings preferred")
        sections.append("- Type hints required")
        # Write SPIDY.md
        content = "\n".join(sections)
        (root / "SPIDY.md").write_text(content)
        return CommandResult(output=f"SPIDY.md generated for {project_name}\n\n{content}")

CommandRegistry.register(InitCommand())
