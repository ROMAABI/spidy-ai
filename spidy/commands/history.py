from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

class HistoryCommand(BaseCommand):
    name = "history"
    aliases = ["hist"]
    description = "Show conversation history"
    usage = "/history [n]"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        n = 20
        if args:
            try:
                n = int(args[0])
            except ValueError:
                pass
        session = (context or {}).get("session")
        if not session:
            return CommandResult(output="No active session. Start one with /new")
        from spidy.sessions import SessionManager
        sm = SessionManager()
        s = sm.get(session)
        if not s:
            return CommandResult(output="Session not found", success=False)
        msgs = s.messages[-n:]
        if not msgs:
            return CommandResult(output="No messages in this session")
        lines = [f"Last {len(msgs)} message(s):\n"]
        for m in msgs:
            role = m.get("role", "?").upper()
            content = m.get("content", "")[:100]
            lines.append(f"  [{role}] {content}")
        return CommandResult(output="\n".join(lines))

CommandRegistry.register(HistoryCommand())
