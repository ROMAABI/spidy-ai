import subprocess
from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

class ConnectCommand(BaseCommand):
    name = "connect"
    description = "Connect to or check an LLM provider"
    usage = "/connect [ollama|openai|gemini|anthropic]"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        if not args:
            try:
                r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
                status = "connected" if r.returncode == 0 else "not responding"
            except FileNotFoundError:
                status = "not installed"
            return CommandResult(output=f"Current provider: Ollama ({status})")
        provider = args[0].lower()
        if provider == "ollama":
            try:
                r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
                if r.returncode == 0:
                    return CommandResult(output=f"Connected to Ollama.\n{r.stdout.strip()}")
                return CommandResult(output=f"Ollama error: {r.stderr.strip()}", success=False)
            except FileNotFoundError:
                return CommandResult(output="Ollama not found. Install it first.", success=False)
        elif provider in ("openai", "gemini", "anthropic"):
            return CommandResult(output=f"To use {provider}: set the API key in ~/.config/spidy/config.yaml")
        return CommandResult(output=f"Unknown provider: {provider}. Try: ollama, openai, gemini, anthropic", success=False)

CommandRegistry.register(ConnectCommand())
