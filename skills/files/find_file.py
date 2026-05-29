import subprocess, asyncio
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

class FindFileSkill(BaseSkill):
    name = "find_file"
    description = "Find a file by name across the filesystem"
    triggers = ["find file", "search file", "locate", "where is", "file kandupidi"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text
        for w in ["find file", "search file", "locate", "where is", "file kandupidi", "file", "find"]:
            t = t.replace(w, "").strip()
        if not t:
            return {"success": False, "speak_en": "What file to find?", "speak_ta": "Enna file find பண்ணட்டும் அண்ணா?"}
        try:
            r = subprocess.run(["locate", "-i", t], capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                lines = r.stdout.strip().splitlines()[:15]
                return {"success": True, "speak_en": f"Found {len(lines)} matches.", "speak_ta": f"{len(lines)} files கிடைத்தது அண்ணா.", "data": {"files": lines}}
        except FileNotFoundError:
            r = subprocess.run(["find", Path.home(), "-iname", f"*{t}*", "-maxdepth", "5"], capture_output=True, text=True, timeout=15)
            if r.stdout.strip():
                lines = r.stdout.strip().splitlines()[:15]
                return {"success": True, "speak_en": f"Found {len(lines)} matches.", "speak_ta": f"{len(lines)} files கிடைத்தது அண்ணா.", "data": {"files": lines}}
        return {"success": True, "speak_en": f"No files found matching '{t}'.", "speak_ta": f"'{t}' file கிடைக்கல அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "name": {"type": "string", "description": "Filename or pattern to search"},
            "directory": {"type": "string", "description": "Directory to search in (default: home)"},
        }, "required": ["name"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"find file {kwargs.get('name', '')}")["speak_en"])
