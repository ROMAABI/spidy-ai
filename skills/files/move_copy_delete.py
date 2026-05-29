import shutil, asyncio
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

class MoveCopyDeleteSkill(BaseSkill):
    name = "move_copy_delete"
    description = "Move, copy, or delete a file"
    triggers = ["move", "copy", "delete file", "remove file", "copy pannu", "move pannu"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        dest = None
        if " to " in text:
            parts = text.split(" to ")
            src_part = parts[0]
            dest = parts[1].strip()
        else:
            src_part = text
        src = ""
        for w in ["move", "copy", "delete file", "remove file", "copy pannu", "move pannu", "delete"]:
            src_part = src_part.replace(w, "").strip()
        src = src_part
        if not src:
            return {"success": False, "speak_en": "Specify a file.", "speak_ta": "File path சொல்லுங்க அண்ணா."}

        src_path = Path(src).expanduser()
        if not src_path.exists():
            return {"success": False, "speak_en": f"File not found: {src}", "speak_ta": f"{src} file கிடைக்கல அண்ணா."}

        if "delete" in t or "remove" in t:
            return {"success": False, "needs_confirm": True, "command": f"rm -rf {src_path}",
                    "speak_en": f"Delete {src_path.name}?", "speak_ta": f"{src_path.name} delete பண்ணட்டுமா அண்ணா?"}

        if dest:
            dest_path = Path(dest).expanduser()
            if "copy" in t:
                shutil.copy2(src_path, dest_path)
                return {"success": True, "speak_en": f"Copied to {dest}.", "speak_ta": f"Copy பண்ணேன் அண்ணா."}
            if "move" in t:
                shutil.move(str(src_path), str(dest_path))
                return {"success": True, "speak_en": f"Moved to {dest}.", "speak_ta": f"Move பண்ணேன் அண்ணா."}

        return {"success": False, "speak_en": "Say: copy/move <source> to <dest> or delete <file>.", "speak_ta": "Copy/move/delete சொல்லுங்க அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["copy", "move", "delete"], "description": "File operation"},
            "source": {"type": "string", "description": "Source file path"},
            "destination": {"type": "string", "description": "Destination path (not needed for delete)"},
        }, "required": ["action", "source"]}

    async def execute(self, **kwargs) -> SkillResult:
        action = kwargs.get("action", "")
        src = kwargs.get("source", "")
        dst = kwargs.get("destination", "")
        text = f"{action} {src}"
        if dst:
            text += f" to {dst}"
        return SkillResult(success=True, output=self.run(text)["speak_en"])
