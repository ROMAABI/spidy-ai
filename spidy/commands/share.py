from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

class ShareCommand(BaseCommand):
    name = "share"
    description = "Share current session context"
    usage = "/share"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        session_id = (context or {}).get("session", "unknown")
        export_dir = Path.home() / ".spidy" / "exports"
        return CommandResult(output=f"Session {session_id} export ready at {export_dir / f'session_{session_id}_*.md'}\n(copy that file to share)")

from pathlib import Path
CommandRegistry.register(ShareCommand())
