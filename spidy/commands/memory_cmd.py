import json, uuid
from pathlib import Path
from datetime import datetime, timezone
from spidy.commands.base import BaseCommand, CommandResult
from spidy.commands import CommandRegistry

MEMORY_DIR = Path.home() / ".spidy" / "memory"
MEMORY_FILE = MEMORY_DIR / "memory.json"

class MemoryCommand(BaseCommand):
    name = "memory"
    aliases = ["mem"]
    description = "Manage AI memory (add, search, delete)"
    usage = "/memory [add|search|delete] <text|id>"

    def _load(self) -> list:
        if MEMORY_FILE.exists():
            return json.loads(MEMORY_FILE.read_text())
        return []

    def _save(self, items: list) -> None:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        MEMORY_FILE.write_text(json.dumps(items, indent=2))

    async def run(self, args: list[str], context: dict | None = None) -> CommandResult:
        items = self._load()
        if not args:
            return CommandResult(output=f"Memory: {len(items)} item(s) stored\nUsage: /memory add <text> | /memory search <query> | /memory delete <id>")
        action = args[0].lower()
        if action == "add" and len(args) >= 2:
            entry = {"id": uuid.uuid4().hex[:8], "text": " ".join(args[1:]), "ts": datetime.now(timezone.utc).isoformat(), "tags": []}
            items.append(entry)
            self._save(items)
            return CommandResult(output=f"Memory saved (id: {entry['id']})")
        if action == "search" and len(args) >= 2:
            q = " ".join(args[1:]).lower()
            results = [i for i in items if q in i["text"].lower()]
            if results:
                lines = [f"Found {len(results)} result(s):"]
                for r in results[:10]:
                    lines.append(f"  [{r['id']}] {r['text'][:100]}")
                return CommandResult(output="\n".join(lines))
            return CommandResult(output="No matches found")
        if action == "delete" and len(args) >= 2:
            before = len(items)
            items = [i for i in items if i["id"] != args[1]]
            self._save(items)
            return CommandResult(output=f"Deleted {before - len(items)} item(s)")
        return CommandResult(output=f"Unknown action: {action}")

CommandRegistry.register(MemoryCommand())
