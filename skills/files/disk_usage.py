import subprocess, asyncio
from skills.base_skill import BaseSkill, SkillResult

class DiskUsageSkill(BaseSkill):
    name = "disk_usage"
    description = "Show disk usage breakdown by folder"
    triggers = ["disk usage", "disk space", "storage", "du", "folder size"]

    def run(self, text: str, lang: str = "en") -> dict:
        try:
            r = subprocess.run(
                ["du", "-h", "--max-depth=2", "/home", "2>/dev/null", "|", "sort", "-rh", "|", "head", "-15"],
                shell=True, capture_output=True, text=True, timeout=30,
            )
            if r.stdout.strip():
                lines = r.stdout.strip().splitlines()
                return {"success": True, "speak_en": "Disk usage by folder.", "speak_ta": "Folder size பாருங்க அண்ணா.", "data": {"folders": lines}}
            return {"success": True, "speak_en": "No data.", "speak_ta": "Data இல்ல."}
        except Exception as e:
            return {"success": False, "speak_en": f"Error: {e}", "speak_ta": "Error அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "directory": {"type": "string", "description": "Directory to analyze (default: /home)"},
        }, "required": []}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run("")["speak_en"])
