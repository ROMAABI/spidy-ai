import json
from pathlib import Path
from datetime import datetime, timedelta
from skills.base_skill import BaseSkill, SkillResult

_TODO_FILE = Path("/tmp/spidy_skills/todos.json")
_STUDY_FILE = Path("/tmp/spidy_skills/study_sessions.json")

class WeeklySummarySkill(BaseSkill):
    name = "weekly_summary"
    description = "Summarize todo completions and study time for the week"
    triggers = ["weekly summary", "week review", "weekly report", "this week", "week"]

    def run(self, text: str, lang: str = "en") -> dict:
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        parts = []

        # Todos completed this week
        if _TODO_FILE.exists():
            todos = json.loads(_TODO_FILE.read_text())
            completed = [t for t in todos if t.get("done") and t.get("created", "") >= week_ago]
            if completed:
                parts.append(f"Completed {len(completed)} tasks")

        # Study time this week
        if _STUDY_FILE.exists():
            sessions = json.loads(_STUDY_FILE.read_text())
            week_sessions = [s for s in sessions if s.get("start", "") >= week_ago]
            total_mins = sum(s.get("duration_min", 0) for s in week_sessions)
            if total_mins > 0:
                parts.append(f"Studied {total_mins:.0f} minutes")

        msg = ". ".join(parts) if parts else "No activity this week."
        return {"success": True, "speak_en": f"Weekly summary: {msg}", "speak_ta": f"Illa summary: {msg}", "data": {"summary": msg}}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run("")["speak_en"])
