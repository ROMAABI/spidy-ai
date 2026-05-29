import asyncio, subprocess, os, time
from skills.base_skill import BaseSkill, SkillResult

_PATH = "/tmp/spidy_screenshot.png"

class ScreenshotSkill(BaseSkill):
    name = "screenshot"
    description = "Take a screenshot (full screen or selected area)"
    triggers = ["screenshot", "screen shot", "capture screen", "screen capture", "screen edukko"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        area = any(w in t for w in ["area", "part", "selection", "portion", "edukko"])
        args = ["grim", "-g"] if area else ["grim"]
        if area:
            return {"success": False, "speak_en": "Please select the area.", "speak_ta": "Area தேர்ந்தெடுக்கவும் அண்ணா."}
        try:
            subprocess.run(["grim", _PATH], check=True, timeout=5)
            return {"success": True, "speak_en": f"Screenshot saved to {_PATH}.", "speak_ta": "Screenshot எடுத்தேன் அண்ணா."}
        except Exception as e:
            return {"success": False, "speak_en": f"Screenshot failed: {e}", "speak_ta": "Screenshot எடுக்க முடியல அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "mode": {"type": "string", "enum": ["full", "area", "window"], "description": "Screenshot mode"},
        }, "required": ["mode"]}

    async def execute(self, **kwargs) -> SkillResult:
        mode = kwargs.get("mode", "full")
        cmd = ["grim"]
        if mode == "window":
            cmd = ["grim", "-g", "$(hyprctl activewindow -j | jq -r '.at[0:2],.size[0:2]' | paste -sd ',' | sed 's/ /,/g')"]
        try:
            subprocess.run(cmd, check=True, timeout=5)
            return SkillResult(success=True, output=f"{mode} screenshot saved.")
        except Exception as e:
            return SkillResult(success=False, output=f"Screenshot failed: {e}")
