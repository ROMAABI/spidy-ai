import asyncio, json, subprocess
from pathlib import Path
from datetime import datetime, timedelta
from skills.base_skill import BaseSkill, SkillResult

_DATA = Path("/tmp/spidy_skills/alarms.json")

def _load():
    if _DATA.exists():
        return json.loads(_DATA.read_text())
    return []

def _save(data):
    _DATA.parent.mkdir(parents=True, exist_ok=True)
    _DATA.write_text(json.dumps(data, indent=2))

WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}

class RecurringAlarmSkill(BaseSkill):
    name = "recurring_alarm"
    description = "Set a recurring alarm (daily, weekday, or specific day)"
    triggers = ["alarm", "wake me", "every day", "recurring", "alarm set"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        time_str = ""
        for w in t.split():
            if ":" in w:
                time_str = w
        if not time_str:
            return {"success": False, "speak_en": "Specify time like 07:00.", "speak_ta": "நேரம் சொல்லுங்க அண்ணா."}
        day = "daily"
        for name, num in WEEKDAYS.items():
            if name in t:
                day = name
                break
        if "weekday" in t:
            day = "weekdays"
        alarms = _load()
        alarms.append({"time": time_str, "day": day, "enabled": True})
        _save(alarms)
        msg = f"Alarm set for {time_str} ({day})."
        return {"success": True, "speak_en": msg, "speak_ta": f"{time_str} க்கு alarm set பண்ணேன் அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "time": {"type": "string", "description": "Time in HH:MM format"},
            "day": {"type": "string", "enum": ["daily", "weekdays", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"], "description": "Recurrence day"},
        }, "required": ["time"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"alarm at {kwargs['time']} {kwargs.get('day', 'daily')}")["speak_en"])
