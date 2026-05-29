import json
from pathlib import Path
from datetime import datetime
from skills.base_skill import BaseSkill, SkillResult

_DATA = Path("/tmp/spidy_skills/study_sessions.json")

def _load():
    if _DATA.exists():
        return json.loads(_DATA.read_text())
    return []

def _save(data):
    _DATA.parent.mkdir(parents=True, exist_ok=True)
    _DATA.write_text(json.dumps(data, indent=2))

_CURRENT_SESSION = None

class StudyTrackerSkill(BaseSkill):
    name = "study_tracker"
    description = "Track study sessions: log start and end times"
    triggers = ["study start", "study end", "track study", "session log", "study", "padikira"]

    def run(self, text: str, lang: str = "en") -> dict:
        global _CURRENT_SESSION
        t = text.lower()
        if any(w in t for w in ["start", "begin", "edu", "beginning"]):
            _CURRENT_SESSION = {"start": datetime.now().isoformat()}
            return {"success": True, "speak_en": "Study session started.", "speak_ta": "Study session ஆரம்பிச்சேன் அண்ணா."}
        if any(w in t for w in ["end", "stop", "finish", "niruthu", "mudichu"]):
            if _CURRENT_SESSION:
                end = datetime.now()
                start = datetime.fromisoformat(_CURRENT_SESSION["start"])
                dur = (end - start).total_seconds() / 60
                sessions = _load()
                sessions.append({"start": _CURRENT_SESSION["start"], "end": end.isoformat(), "duration_min": round(dur, 1)})
                _save(sessions)
                _CURRENT_SESSION = None
                return {"success": True, "speak_en": f"Studied for {dur:.0f} minutes.", "speak_ta": f"{dur:.0f} நிமிடம் படிச்சீங்க அண்ணா."}
            return {"success": False, "speak_en": "No active session.", "speak_ta": "Session ஆரம்பிக்கல அண்ணா."}
        sessions = _load()
        today = datetime.now().strftime("%Y-%m-%d")
        today_sessions = [s for s in sessions if s["start"].startswith(today)]
        total = sum(s["duration_min"] for s in today_sessions)
        return {"success": True, "speak_en": f"Total study time today: {total:.0f} minutes.", "speak_ta": f"Illa study time: {total:.0f} minutes.", "data": {"sessions": today_sessions, "total_minutes": total}}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["start", "end", "status"], "description": "Session action"},
        }, "required": ["action"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"study {kwargs.get('action', 'status')}")["speak_en"])
