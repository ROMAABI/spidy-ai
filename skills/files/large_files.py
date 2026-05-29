import subprocess, asyncio
from skills.base_skill import BaseSkill, SkillResult

class LargeFilesSkill(BaseSkill):
    name = "large_files"
    description = "Find the largest files on disk"
    triggers = ["large files", "big files", "disk usage", "top files", "size"]

    def run(self, text: str, lang: str = "en") -> dict:
        try:
            r = subprocess.run(
                ["du", "-ah", "/home", "2>/dev/null", "|", "sort", "-rh", "|", "head", "-10"],
                shell=True, capture_output=True, text=True, timeout=30,
            )
            if r.stdout.strip():
                lines = r.stdout.strip().splitlines()
                return {"success": True, "speak_en": f"Top {len(lines)} largest files.", "speak_ta": f"{len(lines)} பெரிய files.", "data": {"files": lines}}
            return {"success": True, "speak_en": "No files found.", "speak_ta": "Files கிடைக்கல அண்ணா."}
        except Exception as e:
            return {"success": False, "speak_en": f"Error: {e}", "speak_ta": "Error அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "directory": {"type": "string", "description": "Directory to scan"},
            "count": {"type": "number", "description": "Number of results (default: 10)"},
        }, "required": []}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run("")["speak_en"])
