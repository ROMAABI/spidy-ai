import subprocess, asyncio
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

class OldFilesSkill(BaseSkill):
    name = "old_files"
    description = "Find and optionally clean files not accessed in X days"
    triggers = ["old files", "clean files", "stale", "unused files", "purge"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text.lower()
        days = 30
        for word in t.split():
            if word.isdigit():
                days = int(word)
                break
        directory = Path.home()
        try:
            r = subprocess.run(
                ["find", str(directory), "-atime", f"+{days}", "-type", "f", "2>/dev/null"],
                capture_output=True, text=True, timeout=30, shell=False,
            )
            if r.stdout.strip():
                lines = r.stdout.strip().splitlines()
                sizes = sum(1 for _ in lines)
                return {"success": True, "speak_en": f"Found {sizes} files not accessed in {days} days.", "speak_ta": f"{days} நாட்களில் {sizes} files use பண்ணல.", "data": {"files": lines[:20]}}
            return {"success": True, "speak_en": f"No old files found ({days} days).", "speak_ta": f"Old files இல்ல ({days} days)."}
        except Exception as e:
            return {"success": False, "speak_en": f"Error: {e}", "speak_ta": "Error அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "days": {"type": "number", "description": "Age in days (files not accessed for this long)"},
            "directory": {"type": "string", "description": "Directory to scan"},
            "action": {"type": "string", "enum": ["list", "delete"], "description": "List or delete old files"},
        }, "required": ["days"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"{kwargs.get('days', 30)} {kwargs.get('action', 'list')}")["speak_en"])
