from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

class SessionsCommand(BaseCommand):
    name = "sessions"
    aliases = ["session", "s"]
    description = "Manage conversation sessions"
    usage = "/sessions [list|show|delete] [id]"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        from spidy.sessions import SessionManager
        sm = SessionManager()
        if not args or args[0] == "list":
            sessions = sm.list_sessions(limit=20)
            if not sessions:
                return CommandResult(output="No sessions yet. Start one with /new")
            lines = ["Recent sessions:\n"]
            for s in sessions:
                lines.append(f"  {s['id']}  ({s['messages']} msgs)  {s['updated']}")
            return CommandResult(output="\n".join(lines))
        if args[0] == "show" and len(args) >= 2:
            session = sm.get(args[1])
            if not session:
                return CommandResult(output=f"Session {args[1]} not found", success=False)
            return CommandResult(output=f"Session {session.id}: {session.message_count} messages, created {session.created_at[:19]}")
        if args[0] == "delete" and len(args) >= 2:
            if sm.delete(args[1]):
                return CommandResult(output=f"Deleted session {args[1]}")
            return CommandResult(output=f"Session {args[1]} not found", success=False)
        return CommandResult(output=f"Usage: /sessions [list|show|delete] [id]")

CommandRegistry.register(SessionsCommand())
