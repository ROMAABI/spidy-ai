import asyncio, subprocess
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

class RenameSkill(BaseSkill):
    name = "rename"
    description = "Rename a single file or batch rename with pattern"
    triggers = ["rename", "rename file", "name change", "batch rename", "rename pannu"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text
        for w in ["rename file", "batch rename", "rename pannu", "rename"]:
            t = t.replace(w, "").strip()
        if " to " in t:
            parts = t.split(" to ")
            old_name = parts[0].strip()
            new_name = parts[1].strip()
            old_path = Path(old_name).expanduser()
            new_path = old_path.parent / new_name
            if old_path.exists():
                old_path.rename(new_path)
                return {"success": True, "speak_en": f"Renamed to {new_name}.", "speak_ta": f"Rename பண்ணேன்: {new_name}."}
            return {"success": False, "speak_en": f"File not found: {old_name}", "speak_ta": f"{old_name} கிடைக்கல அண்ணா."}
        if "*" in t or "?" in t or t.startswith("batch"):
            try:
                subprocess.run(["rename", t], shell=True, check=False)
                return {"success": True, "speak_en": "Batch rename done.", "speak_ta": "Batch rename முடிந்தது அண்ணா."}
            except Exception as e:
                return {"success": False, "speak_en": f"Batch rename error: {e}", "speak_ta": "Batch rename error அண்ணா."}
        return {"success": False, "speak_en": "Usage: rename <old> to <new>", "speak_ta": "Rename format: rename <old> to <new>"}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "source": {"type": "string", "description": "Current file path"},
            "destination": {"type": "string", "description": "New file name (not full path)"},
        }, "required": ["source", "destination"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"rename {kwargs.get('source', '')} to {kwargs.get('destination', '')}")["speak_en"])
