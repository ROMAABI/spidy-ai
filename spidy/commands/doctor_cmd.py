import subprocess, sys
from pathlib import Path
from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

class DoctorCommand(BaseCommand):
    name = "doctor"
    description = "Run system diagnostics check"
    usage = "/doctor"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        checks = []
        # Ollama
        try:
            r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            checks.append(("Ollama", "PASS" if r.returncode == 0 else "FAIL", r.stdout.strip()[:100] if r.returncode == 0 else r.stderr.strip()))
        except FileNotFoundError:
            checks.append(("Ollama", "FAIL", "not installed"))
        except Exception as e:
            checks.append(("Ollama", "FAIL", str(e)))
        # Python
        checks.append(("Python", "PASS", sys.version.split()[0]))
        # Config
        config_ok = "PASS" if Path("config.yaml").exists() else "FAIL"
        checks.append(("Config", config_ok, "config.yaml" if config_ok == "PASS" else "missing"))
        # Disk
        try:
            r = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
            disk_line = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "?"
            checks.append(("Disk", "PASS", disk_line))
        except Exception as e:
            checks.append(("Disk", "FAIL", str(e)))
        lines = ["# Spidy Diagnostics Report\n"]
        for name, status, detail in checks:
            icon = "✅" if status == "PASS" else "❌"
            lines.append(f"{icon} **{name}**: {detail}")
        return CommandResult(output="\n".join(lines), format="markdown")

CommandRegistry.register(DoctorCommand())
