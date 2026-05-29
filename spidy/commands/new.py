from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

class NewCommand(BaseCommand):
    name = "new"
    description = "Start a new conversation session"
    usage = "/new"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        from spidy.sessions import SessionManager
        sm = SessionManager()
        session = sm.create({"type": "chat"})
        return CommandResult(output=f"New session created: {session.id}\nStart chatting!")

CommandRegistry.register(NewCommand())
