import subprocess, asyncio
from skills.base_skill import BaseSkill, SkillResult

class TrashSkill(BaseSkill):
    name = "trash"
    description = "List, empty, or restore files from trash"
    triggers = ["trash", "trash list", "empty trash", "restore trash", "waste"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        if "empty" in t or "clear" in t:
            try:
                subprocess.run(["trash-empty"], check=True, timeout=30)
                return {"success": True, "speak_en": "Trash emptied.", "speak_ta": "Trash empty பண்ணேன் அண்ணா."}
            except Exception as e:
                return {"success": False, "speak_en": f"Error: {e}", "speak_ta": "Error அண்ணா."}
        if "restore" in t:
            try:
                r = subprocess.run(["trash-restore"], capture_output=True, text=True, timeout=10)
                return {"success": True, "speak_en": "Restore interactive. Check terminal.", "speak_ta": "Restore பண்ண Terminal-ல பாருங்க அண்ணா."}
            except Exception as e:
                return {"success": False, "speak_en": f"Error: {e}", "speak_ta": "Error அண்ணா."}
        try:
            r = subprocess.run(["trash-list"], capture_output=True, text=True, timeout=10)
            if r.stdout.strip():
                lines = r.stdout.strip().splitlines()[:15]
                return {"success": True, "speak_en": f"{len(lines)} items in trash.", "speak_ta": f"Trash-ல {len(lines)} items உள்ளது அண்ணா.", "data": {"items": lines}}
            return {"success": True, "speak_en": "Trash is empty.", "speak_ta": "Trash காலி அண்ணா."}
        except FileNotFoundError:
            return {"success": False, "speak_en": "Install trash-cli: sudo pacman -S trash-cli", "speak_ta": "trash-cli install பண்ணுங்க அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["list", "empty", "restore"], "description": "Trash action"},
        }, "required": ["action"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"{kwargs.get('action', 'list')} trash")["speak_en"])
