import asyncio, subprocess
from skills.base_skill import BaseSkill, SkillResult

class NightModeSkill(BaseSkill):
    name = "night_mode"
    description = "Toggle night mode / blue light filter"
    triggers = ["night", "blue light", "night mode", "eye strain", "warm light", "shift"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        if "off" in t or "disable" in t:
            subprocess.run(["pkill", "wlsunset"], capture_output=True)
            return {"success": True, "speak_en": "Night mode turned off.", "speak_ta": "Night mode off பண்ணேன் அண்ணா."}
        if "on" in t or "enable" in t or any(w in t for w in ["start", "run", "apply"]):
            subprocess.Popen(["wlsunset", "-t", "3500", "-T", "6500"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "speak_en": "Night mode turned on.", "speak_ta": "Night mode on பண்ணேன் அண்ணா."}
        if subprocess.run(["pgrep", "wlsunset"], capture_output=True).returncode == 0:
            subprocess.run(["pkill", "wlsunset"], capture_output=True)
            return {"success": True, "speak_en": "Night mode toggled off.", "speak_ta": "Night mode நிறுத்தினேன் அண்ணா."}
        else:
            subprocess.Popen(["wlsunset", "-t", "3500", "-T", "6500"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "speak_en": "Night mode toggled on.", "speak_ta": "Night mode ஆரம்பிச்சேன் அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["on", "off", "toggle"], "description": "Night mode action"},
        }, "required": ["action"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(kwargs.get("action", "toggle"))["speak_en"])
