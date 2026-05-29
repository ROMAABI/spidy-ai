import subprocess
from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

class ModelsCommand(BaseCommand):
    name = "models"
    aliases = ["model"]
    description = "List available LLM models"
    usage = "/models [ollama|provider]"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        if args and args[0] == "ollama":
            try:
                r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
                if r.returncode == 0:
                    return CommandResult(output=f"Ollama models:\n{r.stdout.strip()}")
                return CommandResult(output=f"Ollama error: {r.stderr.strip()}", success=False)
            except FileNotFoundError:
                return CommandResult(output="Ollama not installed", success=False)
            except Exception as e:
                return CommandResult(output=str(e), success=False)
        try:
            r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
            ollama_out = r.stdout.strip() if r.returncode == 0 else "Ollama not available"
        except Exception:
            ollama_out = "Ollama not available"
        return CommandResult(output=f"Providers:\n  Ollama (local)\n\nOllama models:\n{ollama_out}")

CommandRegistry.register(ModelsCommand())
