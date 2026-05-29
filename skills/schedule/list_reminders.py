import json
from pathlib import Path
from datetime import datetime
from skills.base_skill import BaseSkill, SkillResult

_DATA = Path("/tmp/spidy_skills/reminders.json")

class ListRemindersSkill(BaseSkill):
    name = "list_reminders"
    description = "List all pending reminders for today"
    triggers = ["list reminders", "show reminders", "my reminders", "reminders", "reminder list"]

    def run(self, text: str, lang: str = "en") -> dict:
        if not _DATA.exists():
            return {"success": True, "speak_en": "No reminders set.", "speak_ta": "Reminders இல்ல அண்ணா."}
        reminders = json.loads(_DATA.read_text())
        pending = [r for r in reminders if not r.get("done") and datetime.fromisoformat(r["time"]) > datetime.now()]
        if not pending:
            return {"success": True, "speak_en": "No pending reminders.", "speak_ta": "Pending reminders இல்ல அண்ணா."}
        lines = [f"{i+1}. {r['content']} at {datetime.fromisoformat(r['time']).strftime('%H:%M')}" for i, r in enumerate(pending)]
        msg = "\n".join(lines)
        return {"success": True, "speak_en": f"You have {len(pending)} reminders.", "speak_ta": f"{len(pending)} reminders உள்ளது அண்ணா.", "data": {"reminders": lines}}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs) -> SkillResult:
        result = self.run("list")
        return SkillResult(success=result["success"], output=result.get("data", {}).get("reminders", "No reminders.") if isinstance(result.get("data"), dict) else str(result["data"]) if result.get("data") else result["speak_en"])
