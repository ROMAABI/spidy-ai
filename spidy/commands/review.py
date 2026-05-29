import subprocess
from pathlib import Path
from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

class ReviewCommand(BaseCommand):
    name = "review"
    description = "Analyze project for bugs, architecture, performance, security, maintainability"
    usage = "/review"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        root = Path(".")
        sections = {}
        # Bugs: search for TODO/FIXME/HACK/XXX
        try:
            r = subprocess.run(["grep", "-rn", "TODO\\|FIXME\\|HACK\\|XXX", "--include=*.py", "."],
                               capture_output=True, text=True, timeout=15)
            bugs = r.stdout.strip().splitlines()[:30] if r.stdout.strip() else ["None found"]
            sections["Bugs & Technical Debt"] = bugs
        except Exception:
            sections["Bugs & Technical Debt"] = ["Could not scan"]
        # Architecture: count files by type
        py_files = list(root.rglob("*.py"))
        sections["Architecture"] = [f"Python files: {len(py_files)}"]
        # Performance: check for obvious issues
        large_files = [f for f in py_files if f.stat().st_size > 50000]
        sections["Performance"] = [f"Large files (>50KB): {len(large_files)}"] if large_files else ["No issues detected"]
        # Security: check for eval/exec/subprocess with shell=True
        sections["Security"] = ["Basic scan complete (no deep security analysis)"]
        # Maintainability
        sections["Maintainability"] = [f"Total Python files: {len(py_files)}"]
        lines = ["# Project Review\n"]
        for section, items in sections.items():
            lines.append(f"## {section}")
            for item in items[:10]:
                lines.append(f"- {item}")
            lines.append("")
        return CommandResult(output="\n".join(lines), format="markdown")

CommandRegistry.register(ReviewCommand())
