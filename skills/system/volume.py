import asyncio, subprocess
from skills.base_skill import BaseSkill, SkillResult

_SINK = "@DEFAULT_SINK@"

class VolumeSkill(BaseSkill):
    name = "volume"
    description = "Control system volume: up, down, mute, unmute, or set level"
    triggers = ["volume", "sound", "satham", "mute", "loud", "soft", "unmute"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        if "mute" in t:
            subprocess.run(["pactl", "set-sink-mute", _SINK, "toggle"])
            return {"success": True, "speak_en": "Toggled mute.", "speak_ta": "Mute மாற்றினேன் அண்ணா."}
        if "unmute" in t:
            subprocess.run(["pactl", "set-sink-mute", _SINK, "0"])
            return {"success": True, "speak_en": "Unmuted.", "speak_ta": "Sound வந்துடுச்சு அண்ணா."}
        up = any(w in t for w in ["up", "jasti", "jastiyakku", "more", "high", "increase"])
        down = any(w in t for w in ["down", "kammi", "kammikko", "kuraikku", "kuraivo", "less", "low", "decrease"])
        if up:
            subprocess.run(["pactl", "set-sink-volume", _SINK, "+10%"])
            return {"success": True, "speak_en": "Volume up.", "speak_ta": "Sound ஜாஸ்தி பண்ணேன் அண்ணா."}
        if down:
            subprocess.run(["pactl", "set-sink-volume", _SINK, "-10%"])
            return {"success": True, "speak_en": "Volume down.", "speak_ta": "Sound கம்மி பண்ணேன் அண்ணா."}
        return {"success": False, "speak_en": "Say volume up/down/mute.", "speak_ta": "Volume up/down/mute சொல்லுங்க அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["up", "down", "mute", "unmute", "set"], "description": "Volume action"},
            "level": {"type": "number", "description": "Volume percentage 0-100 (for set action)"},
        }, "required": ["action"]}

    async def execute(self, **kwargs) -> SkillResult:
        action = kwargs.get("action", "")
        if action == "set":
            level = kwargs.get("level", 50)
            subprocess.run(["pactl", "set-sink-volume", _SINK, f"{level}%"])
            return SkillResult(success=True, output=f"Volume set to {level}%.")
        return SkillResult(success=True, output=self.run(action)["speak_en"])
