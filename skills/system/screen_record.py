import asyncio, subprocess, os
from skills.base_skill import BaseSkill, SkillResult

_OUTPUT = "/tmp/spidy_screen_record.mp4"

class ScreenRecordSkill(BaseSkill):
    name = "screen_record"
    description = "Start or stop screen recording"
    triggers = ["screen record", "record screen", "video capture", "screen rekord"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        if any(w in t for w in ["start", "edu", "edukko", "begin"]):
            subprocess.Popen(["wf-recorder", "-f", _OUTPUT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "speak_en": "Recording started.", "speak_ta": "Recording ஆரம்பிச்சேன் அண்ணா."}
        if any(w in t for w in ["stop", "niruthu", "nill", "end"]):
            subprocess.run(["pkill", "-f", "wf-recorder"])
            return {"success": True, "speak_en": f"Recording saved to {_OUTPUT}.", "speak_ta": "Recording நிறுத்தினேன் அண்ணா."}
        return {"success": False, "speak_en": "Say screen record start/stop.", "speak_ta": "Screen record start/stop சொல்லுங்க அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["start", "stop"], "description": "Recording action"},
        }, "required": ["action"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(kwargs.get("action", ""))["speak_en"])
