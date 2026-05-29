import asyncio, json, subprocess
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

_TODO_FILE = Path("/tmp/spidy_skills/todos.json")
_BAT = Path("/sys/class/power_supply/")

class DailyBriefingSkill(BaseSkill):
    name = "daily_briefing"
    description = "Morning summary: todos, weather, battery, and reminders"
    triggers = ["daily briefing", "good morning", "morning summary", "start day", "briefing"]

    def run(self, text: str, lang: str = "en") -> dict:
        parts = []

        # Battery
        for d in _BAT.glob("BAT*"):
            cap = d / "capacity"
            if cap.exists():
                parts.append(f"Battery: {cap.read_text().strip()}%")
                break

        # Todos
        if _TODO_FILE.exists():
            todos = json.loads(_TODO_FILE.read_text())
            pending = [t for t in todos if not t.get("done")]
            if pending:
                parts.append(f"{len(pending)} tasks pending")

        # Weather via wttr.in
        try:
            r = subprocess.run(["curl", "-s", "wttr.in?format=%c+%t+%w"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                parts.append(f"Weather: {r.stdout.strip()}")
        except Exception:
            pass

        msg = " | ".join(parts) if parts else "Good morning!"
        return {"success": True, "speak_en": f"Good morning! {msg}", "speak_ta": f"Vanakkam! {msg}", "data": {"briefing": msg}}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run("")["speak_en"])
