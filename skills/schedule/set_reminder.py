import asyncio, json, subprocess
from pathlib import Path
from datetime import datetime, timedelta
from skills.base_skill import BaseSkill, SkillResult

_DATA = Path("/tmp/spidy_skills/reminders.json")

def _load():
    if _DATA.exists():
        return json.loads(_DATA.read_text())
    return []

def _save(data):
    _DATA.parent.mkdir(parents=True, exist_ok=True)
    _DATA.write_text(json.dumps(data, indent=2))

class SetReminderSkill(BaseSkill):
    name = "set_reminder"
    description = "Set a reminder that will notify at the specified time"
    triggers = ["remind", "reminder", "remember", "notify me", "nenjam", "nenjam pannu"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        for w in ["remind me to", "remind", "remember", "notify me to", "nenjam pannu"]:
            t = t.replace(w, "").strip()
        parts = t.split(" in ")
        if len(parts) == 2:
            content = parts[0].strip()
            time_str = parts[1].strip()
            minutes = 0
            for word in time_str.split():
                if word.isdigit():
                    minutes = int(word)
            if "hour" in time_str:
                minutes *= 60
            if "minute" in time_str:
                minutes = int(time_str.split()[0]) if time_str.split()[0].isdigit() else minutes
            if minutes > 0:
                remind_at = datetime.now() + timedelta(minutes=minutes)
                reminders = _load()
                reminders.append({"content": content, "time": remind_at.isoformat(), "done": False})
                _save(reminders)
                asyncio.create_task(self._notify_after(content, minutes))
                return {"success": True, "speak_en": f"Reminder set for {minutes} minutes from now.", "speak_ta": f"{minutes} நிமிடங்களில் remind பண்ணுறேன் அண்ணா."}
        return {"success": False, "speak_en": "Usage: remind me to <task> in <minutes> minutes.", "speak_ta": "Reminder format: remind me to <task> in <minutes> minutes."}

    async def _notify_after(self, content: str, minutes: int):
        await asyncio.sleep(minutes * 60)
        subprocess.run(["notify-send", "Spidy Reminder", content])

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "content": {"type": "string", "description": "What to remind about"},
            "minutes": {"type": "number", "description": "Minutes from now"},
        }, "required": ["content", "minutes"]}

    async def execute(self, **kwargs) -> SkillResult:
        content = kwargs.get("content", "")
        minutes = kwargs.get("minutes", 5)
        remind_at = datetime.now() + timedelta(minutes=minutes)
        reminders = _load()
        reminders.append({"content": content, "time": remind_at.isoformat(), "done": False})
        _save(reminders)
        asyncio.create_task(self._notify_after(content, minutes))
        return SkillResult(success=True, output=f"Reminder set for {minutes} minutes from now: {content}")
