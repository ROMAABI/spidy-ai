import asyncio, subprocess
from skills.base_skill import BaseSkill, SkillResult

_POMODORO_RUNNING = False

class PomodoroSkill(BaseSkill):
    name = "pomodoro"
    description = "Start or stop a Pomodoro timer (25 min work, 5 min break)"
    triggers = ["pomodoro", "focus timer", "study timer", "tomato", "focus"]

    def run(self, text: str, lang: str = "en") -> dict:
        global _POMODORO_RUNNING
        t = text.lower()
        if any(w in t for w in ["stop", "end", "cancel", "niruthu"]):
            _POMODORO_RUNNING = False
            subprocess.run(["notify-send", "Pomodoro", "Timer stopped."])
            return {"success": True, "speak_en": "Pomodoro stopped.", "speak_ta": "Pomodoro நிறுத்தினேன் அண்ணா."}
        if any(w in t for w in ["start", "begin", "edu", "run"]):
            if not _POMODORO_RUNNING:
                _POMODORO_RUNNING = True
                asyncio.create_task(self._run_pomodoro())
            return {"success": True, "speak_en": "Pomodoro started! 25 minutes focus.", "speak_ta": "Pomodoro ஆரம்பிச்சேன்! 25 நிமிடம் focus."}
        return {"success": True, "speak_en": "Say pomodoro start or stop.", "speak_ta": "Pomodoro start/stop சொல்லுங்க."}

    async def _run_pomodoro(self):
        await asyncio.sleep(25 * 60)
        if _POMODORO_RUNNING:
            subprocess.run(["notify-send", "Pomodoro", "Work session finished! Take a 5 min break."])

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["start", "stop"], "description": "Pomodoro action"},
            "minutes": {"type": "number", "description": "Custom focus duration in minutes"},
        }, "required": ["action"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(kwargs.get("action", "start"))["speak_en"])
