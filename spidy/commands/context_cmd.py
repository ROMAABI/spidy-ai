from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

class ContextCommand(BaseCommand):
    name = "context"
    aliases = ["ctx"]
    description = "Show current context: mode, model, session"
    usage = "/context"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        ctx = context or {}
        assistant = ctx.get("assistant")
        mode = "general"
        model = "gemma4:e2b"
        session = ctx.get("session", "none")
        if assistant:
            mode = getattr(assistant, "active_mode", None)
            mode = mode.name if mode else "general"
            brain = getattr(assistant, "brain", None)
            if brain:
                model = getattr(brain, "model", model)
        lines = [
            f"  Mode    : @{mode}",
            f"  Model   : {model}",
            f"  Session : {session}",
        ]
        return CommandResult(output="Current context:\n" + "\n".join(lines))

CommandRegistry.register(ContextCommand())
