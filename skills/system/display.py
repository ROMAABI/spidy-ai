import asyncio, subprocess, os, json
from skills.base_skill import BaseSkill, SkillResult

def _hyprctl(*args: str) -> str:
    try:
        r = subprocess.run(["hyprctl"] + list(args), capture_output=True, text=True, timeout=5)
        return r.stdout.strip()
    except Exception:
        return ""

def _is_hypr() -> bool:
    return bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"))

class DisplaySkill(BaseSkill):
    name = "display"
    description = "Switch display layout: single monitor, dual monitor, mirror"
    triggers = ["display", "monitor", "screen layout", "dual monitor", "single monitor", "display mode"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        if not _is_hypr():
            return {"success": False, "speak_en": "Display control only works in Hyprland.", "speak_ta": "Hyprland-ல மட்டுமே வேலை செய்யும் அண்ணா."}
        if "single" in t or "one" in t:
            _hyprctl("keyword", "monitor", "eDP-1,preferred,auto,1")
            return {"success": True, "speak_en": "Switched to single display.", "speak_ta": "Single display மாத்தினேன் அண்ணா."}
        if "dual" in t or "two" in t or "extend" in t:
            _hyprctl("keyword", "monitor", "eDP-1,preferred,0x0,1")
            _hyprctl("keyword", "monitor", "HDMI-A-1,preferred,auto-right,1")
            return {"success": True, "speak_en": "Switched to dual display.", "speak_ta": "Dual display மாத்தினேன் அண்ணா."}
        if "mirror" in t:
            _hyprctl("keyword", "monitor", "HDMI-A-1,preferred,0x0,1,mirror,eDP-1")
            return {"success": True, "speak_en": "Mirroring displays.", "speak_ta": "Mirror பண்ணேன் அண்ணா."}
        return {"success": False, "speak_en": "Say single/dual/mirror display.", "speak_ta": "Single/dual/mirror சொல்லுங்க அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "mode": {"type": "string", "enum": ["single", "dual", "mirror"], "description": "Display layout mode"},
        }, "required": ["mode"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(kwargs.get("mode", "single"))["speak_en"])
