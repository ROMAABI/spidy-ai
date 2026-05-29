from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

class HelpCommand(BaseCommand):
    name = "help"
    aliases = ["h", "?"]
    description = "Show available commands or details for a specific one"
    usage = "/help [command]"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        if args:
            cmd = CommandRegistry.get(args[0])
            if cmd:
                return CommandResult(output=cmd.help())
            return CommandResult(output=f"Unknown command: /{args[0]}", success=False)
        lines = ["Available commands:\n"]
        for cmd in sorted(CommandRegistry.visible(), key=lambda c: c.name):
            lines.append(f"  /{cmd.name:<12} {cmd.description}")
        lines.append("\nTip: /help <cmd> for details")
        return CommandResult(output="\n".join(lines))

CommandRegistry.register(HelpCommand())
