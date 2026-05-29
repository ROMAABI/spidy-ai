from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

class UpdateCommand(BaseCommand):
    name = "update"
    description = "Check for Spidy updates"
    usage = "/update"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        try:
            from spidy import __version__
            version = __version__
        except Exception:
            version = "0.2.0"
        return CommandResult(output=f"Current version: {version}\nCheck https://github.com/spix/spidy-ai for updates")

CommandRegistry.register(UpdateCommand())
