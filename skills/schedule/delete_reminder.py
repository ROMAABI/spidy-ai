import json
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

_DATA = Path("/tmp/spidy_skills/reminders.json")

class DeleteReminderSkill(BaseSkill):
    name = "delete_reminder"
    description = "Delete or snooze a reminder by index"
    triggers = ["delete reminder", "remove reminder", "snooze", "cancel reminder", "remove alarm"]

    def run(self, text: str, lang: str = "en") -> dict:
        if not _DATA.exists():
            return {"success": False, "speak_en": "No reminders to delete.", "speak_ta": "Delete பண்ண reminders இல்ல அண்ணா."}
        reminders = json.loads(_DATA.read_text())
        t = text.lower()
        snooze = "snooze" in t
        for word in t.split():
            if word.isdigit():
                idx = int(word) - 1
                if 0 <= idx < len(reminders):
                    removed = reminders.pop(idx)
                    _DATA.write_text(json.dumps(reminders, indent=2))
                    if snooze:
                        from datetime import datetime, timedelta
                        removed["time"] = (datetime.now() + timedelta(minutes=5)).isoformat()
                        reminders.append(removed)
                        _DATA.write_text(json.dumps(reminders, indent=2))
                        return {"success": True, "speak_en": f"Snoozed for 5 minutes.", "speak_ta": "5 நிமிடம் கழித்து remind பண்ணுறேன் அண்ணா."}
                    return {"success": True, "speak_en": f"Removed reminder: {removed['content']}", "speak_ta": "Reminder delete பண்ணேன் அண்ணா."}
        return {"success": False, "speak_en": "Specify reminder number.", "speak_ta": "Reminder number சொல்லுங்க அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "index": {"type": "number", "description": "Reminder index to delete (1-based)"},
            "snooze": {"type": "boolean", "description": "Snooze instead of delete"},
        }, "required": ["index"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"delete {kwargs.get('index', 1)}")["speak_en"])
