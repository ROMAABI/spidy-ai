from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

class CompactCommand(BaseCommand):
    name = "compact"
    description = "Summarize and compress conversation history"
    usage = "/compact"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        session = (context or {}).get("session")
        if not session:
            return CommandResult(output="No active session to compact")
        from spidy.sessions import SessionManager
        sm = SessionManager()
        s = sm.get(session)
        if not s:
            return CommandResult(output="Session not found", success=False)
        n = len(s.messages)
        return CommandResult(output=f"Session {session}: {n} messages.\nCompacting would summarize {n} messages into a condensed prompt.\n(Full compaction not yet implemented)")

CommandRegistry.register(CompactCommand())
