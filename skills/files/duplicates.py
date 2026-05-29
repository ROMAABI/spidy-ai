import subprocess, asyncio
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

class DuplicatesSkill(BaseSkill):
    name = "duplicates"
    description = "Find duplicate files in a directory"
    triggers = ["duplicate", "duplicate files", "find duplicates", "double files"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text
        for w in ["duplicate files", "find duplicates", "double files", "duplicate", "find"]:
            t = t.replace(w, "").strip()
        directory = t or str(Path.home())
        try:
            r = subprocess.run(["fdupes", "-r", directory], capture_output=True, text=True, timeout=60)
            if r.stdout.strip():
                sets = r.stdout.strip().split("\n\n")
                total = sum(1 for s in sets if s.strip())
                return {"success": True, "speak_en": f"Found {total} sets of duplicates.", "speak_ta": f"{total} duplicate sets கிடைத்தது அண்ணா.", "data": {"sets": sets[:10]}}
            return {"success": True, "speak_en": "No duplicates found.", "speak_ta": "Duplicates இல்ல அண்ணா."}
        except FileNotFoundError:
            return {"success": False, "speak_en": "Install fdupes: sudo pacman -S fdupes", "speak_ta": "fdupes install பண்ணுங்க அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "directory": {"type": "string", "description": "Directory to scan (default: home)"},
        }, "required": []}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(kwargs.get("directory", ""))["speak_en"])
