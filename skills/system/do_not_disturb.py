import asyncio, subprocess
from skills.base_skill import BaseSkill, SkillResult

class DoNotDisturbSkill(BaseSkill):
    name = "do_not_disturb"
    description = "Toggle Do Not Disturb mode (mute all notifications)"
    triggers = ["dnd", "do not disturb", "silent", "notification", "disturb", "dnd mode"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        off = any(w in t for w in ["off", "disable", "stop", "end", "niruthu"])
        if off:
            subprocess.run(["makoctl", "mode", "-r", "dnd"], capture_output=True)
            return {"success": True, "speak_en": "Do Not Disturb turned off.", "speak_ta": "Notifications on பண்ணேன் அண்ணா."}
        on = any(w in t for w in ["on", "enable", "start", "begin", "edu"])
        if on:
            subprocess.run(["makoctl", "mode", "-a", "dnd"], capture_output=True)
            return {"success": True, "speak_en": "Do Not Disturb turned on.", "speak_ta": "DND mode on பண்ணேன் அண்ணா."}
        subprocess.run(["makoctl", "mode", "-a", "dnd"], capture_output=True)
        return {"success": True, "speak_en": "Do Not Disturb on.", "speak_ta": "DND mode on பண்ணேன் அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["on", "off", "toggle"], "description": "DND action"},
        }, "required": ["action"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(kwargs.get("action", "on"))["speak_en"])
