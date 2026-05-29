import asyncio, subprocess, os
from skills.base_skill import BaseSkill, SkillResult

def _hyprctl(*args: str) -> None:
    subprocess.run(["hyprctl", "dispatch"] + list(args), capture_output=True, timeout=3)

def _is_hypr() -> bool:
    return bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"))

class WorkspaceSkill(BaseSkill):
    name = "workspace"
    description = "Switch to a workspace or desktop (Hyprland)"
    triggers = ["workspace", "desktop", "switch workspace", "go to workspace", "workspace pannu"]

    def run(self, text: str, lang: str = "en") -> dict:
        if not _is_hypr():
            return {"success": False, "speak_en": "Workspace control only in Hyprland.", "speak_ta": "Hyprland-ல மட்டுமே வேலை செய்யும் அண்ணா."}
        t = text.lower()
        for word in t.split():
            if word.isdigit():
                _hyprctl("workspace", word)
                return {"success": True, "speak_en": f"Switched to workspace {word}.", "speak_ta": f"Workspace {word} க்கு போனேன் அண்ணா."}
        if "next" in t or "+" in t:
            _hyprctl("workspace", "+1")
            return {"success": True, "speak_en": "Next workspace.", "speak_ta": "Adutha workspace போனேன் அண்ணா."}
        if "prev" in t or "-" in t or "previous" in t:
            _hyprctl("workspace", "-1")
            return {"success": True, "speak_en": "Previous workspace.", "speak_ta": "Mundhu workspace போனேன் அண்ணா."}
        return {"success": False, "speak_en": "Say workspace number or next/prev.", "speak_ta": "Workspace number சொல்லுங்க அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "number": {"type": "number", "description": "Workspace number to switch to (1-10)"},
        }, "required": ["number"]}

    async def execute(self, **kwargs) -> SkillResult:
        n = kwargs.get("number", 1)
        _hyprctl("workspace", str(n))
        return SkillResult(success=True, output=f"Switched to workspace {n}.")
