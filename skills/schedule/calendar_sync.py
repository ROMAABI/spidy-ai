import asyncio, subprocess
from skills.base_skill import BaseSkill, SkillResult

class CalendarSyncSkill(BaseSkill):
    name = "calendar_sync"
    description = "Read Google Calendar events (requires gcalcli setup)"
    triggers = ["calendar", "google calendar", "events", "schedule", "gcal", "cal"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        days = 1
        for word in t.split():
            if word.isdigit():
                days = int(word)
                break
        try:
            r = subprocess.run(
                ["gcalcli", "agenda", f"now", f"+{days}day"],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0 and r.stdout.strip():
                return {"success": True, "speak_en": f"Events for next {days} days listed.", "speak_ta": "Calendar events பாருங்க அண்ணா.", "data": {"events": r.stdout.strip()}}
            return {"success": False, "speak_en": "gcalcli not configured. Run 'gcalcli init' first.", "speak_ta": "gcalcli setup பண்ணனும் அண்ணா."}
        except FileNotFoundError:
            return {"success": False, "speak_en": "Install gcalcli: pip install gcalcli", "speak_ta": "gcalcli install பண்ணுங்க அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "days": {"type": "number", "description": "Number of days to look ahead"},
        }, "required": []}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"calendar {kwargs.get('days', 1)}")["speak_en"])
