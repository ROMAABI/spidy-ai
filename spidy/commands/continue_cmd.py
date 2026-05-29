from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

class ContinueCommand(BaseCommand):
    name = "continue"
    aliases = ["cont", "resume"]
    description = "Continue a previous session"
    usage = "/continue [session_id]"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        from spidy.sessions import SessionManager
        sm = SessionManager()
        if not args:
            sessions = sm.list_sessions(limit=10)
            if not sessions:
                return CommandResult(output="No previous sessions found")
            lines = ["Select a session:\n"]
            for s in sessions:
                lines.append(f"  {s['id']}  ({s['messages']} msgs)")
            lines.append("\nUsage: /continue <session_id>")
            return CommandResult(output="\n".join(lines))
        sid = args[0]
        session = sm.get(sid)
        if not session:
            return CommandResult(output=f"Session {sid} not found", success=False)
        return CommandResult(output=f"Resumed session {sid} ({session.message_count} messages)")

CommandRegistry.register(ContinueCommand())
