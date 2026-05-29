import asyncio, subprocess
from skills.base_skill import BaseSkill, SkillResult

class BrightnessSkill(BaseSkill):
    name = "brightness"
    description = "Control screen brightness: up, down, or set level"
    triggers = ["brightness", "light", "screen bright", "dim", "screen light", "prakasam"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        up = any(w in t for w in ["high", "jasti", "jastiyakku", "more", "increase", "up"])
        down = any(w in t for w in ["low", "kammi", "kammikko", "less", "decrease", "down", "dim", "kuraivo"])
        if up:
            subprocess.run(["brightnessctl", "set", "+10%"])
            return {"success": True, "speak_en": "Brightness increased.", "speak_ta": "Brightness ஜாஸ்தி பண்ணேன் அண்ணா."}
        if down:
            subprocess.run(["brightnessctl", "set", "10%-"])
            return {"success": True, "speak_en": "Brightness decreased.", "speak_ta": "Brightness கம்மி பண்ணேன் அண்ணா."}
        return {"success": False, "speak_en": "Say brightness up/down.", "speak_ta": "Brightness up/down சொல்லுங்க அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["up", "down", "set"], "description": "Brightness action"},
            "level": {"type": "number", "description": "Brightness percentage 0-100 (for set action)"},
        }, "required": ["action"]}

    async def execute(self, **kwargs) -> SkillResult:
        action = kwargs.get("action", "")
        if action == "set":
            level = kwargs.get("level", 50)
            subprocess.run(["brightnessctl", "set", f"{level}%"])
            return SkillResult(success=True, output=f"Brightness set to {level}%.")
        return SkillResult(success=True, output=self.run(action)["speak_en"])
