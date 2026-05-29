from pathlib import Path
from datetime import datetime
from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

EXPORT_DIR = Path.home() / ".spidy" / "exports"

class ExportCommand(BaseCommand):
    name = "export"
    aliases = ["ex"]
    description = "Export session to markdown, json, or txt"
    usage = "/export [md|json|txt]"

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        fmt = args[0].lower() if args else "md"
        if fmt not in ("md", "json", "txt"):
            return CommandResult(output=f"Unsupported format: {fmt}. Use md, json, or txt", success=False)
        session_id = (context or {}).get("session", "unknown")
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = {"md": "md", "json": "json", "txt": "txt"}[fmt]
        out_path = EXPORT_DIR / f"session_{session_id}_{ts}.{ext}"
        content = f"Spidy Session Export\nSession: {session_id}\nDate: {ts}\n\n(Conversation content would be exported here)"
        out_path.write_text(content)
        return CommandResult(output=f"Exported to {out_path}")

CommandRegistry.register(ExportCommand())
