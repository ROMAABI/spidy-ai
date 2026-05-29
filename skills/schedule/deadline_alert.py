import json, asyncio, subprocess
from pathlib import Path
from datetime import datetime, timedelta
from skills.base_skill import BaseSkill, SkillResult

_DATA = Path("/tmp/spidy_skills/deadlines.json")

def _load():
    if _DATA.exists():
        return json.loads(_DATA.read_text())
    return []

def _save(data):
    _DATA.parent.mkdir(parents=True, exist_ok=True)
    _DATA.write_text(json.dumps(data, indent=2))

class DeadlineAlertSkill(BaseSkill):
    name = "deadline_alert"
    description = "Set a deadline with alert X hours before due"
    triggers = ["deadline", "set deadline", "due date", "remind before", "due"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        for w in ["deadline", "set deadline", "due"]:
            t = t.replace(w, "").strip()
        parts = t.split(" in ")
        if len(parts) == 2:
            content = parts[0].strip()
            rest = parts[1]
            hours = 1
            for word in rest.split():
                if word.isdigit():
                    hours = int(word)
                    break
            due = datetime.now() + timedelta(hours=hours)
            deadlines = _load()
            deadlines.append({"content": content, "due": due.isoformat(), "alert_before_hours": 1})
            _save(deadlines)
            asyncio.create_task(self._alert_before(content, due, 1))
            return {"success": True, "speak_en": f"Deadline set: {content} in {hours} hours.", "speak_ta": f"{hours} மணி நேரத்தில் deadline அண்ணா."}
        return {"success": False, "speak_en": "Usage: deadline <task> in <hours> hours.", "speak_ta": "Deadline format: deadline <task> in <hours> hours."}

    async def _alert_before(self, content: str, due: datetime, hours_before: int):
        alert_time = due - timedelta(hours=hours_before)
        now = datetime.now()
        if alert_time > now:
            await asyncio.sleep((alert_time - now).total_seconds())
        subprocess.run(["notify-send", "Deadline Approaching", f"{content} is due in {hours_before} hour(s)!"])

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "content": {"type": "string", "description": "Deadline description"},
            "hours": {"type": "number", "description": "Hours from now"},
        }, "required": ["content", "hours"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"deadline {kwargs['content']} in {kwargs.get('hours', 1)} hours")["speak_en"])
