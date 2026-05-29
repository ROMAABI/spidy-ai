import subprocess, asyncio
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

class GrepFileSkill(BaseSkill):
    name = "grep_file"
    description = "Find files containing specific text (content search)"
    triggers = ["find text", "search content", "grep", "text in files", "file la text"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text
        for w in ["find text", "search content", "grep", "text in files", "file la text", "find"]:
            t = t.replace(w, "").strip()
        if not t:
            return {"success": False, "speak_en": "What text to search?", "speak_ta": "Enna text search பண்ணட்டும் அண்ணா?"}
        try:
            r = subprocess.run(["grep", "-ril", t, str(Path.home())], capture_output=True, text=True, timeout=30)
            if r.stdout.strip():
                lines = r.stdout.strip().splitlines()[:15]
                return {"success": True, "speak_en": f"Found in {len(lines)} files.", "speak_ta": f"{len(lines)} files-ல கிடைத்தது அண்ணா.", "data": {"files": lines}}
            return {"success": True, "speak_en": f"No files contain '{t}'.", "speak_ta": f"'{t}' எங்கும் இல்ல அண்ணா."}
        except subprocess.TimeoutExpired:
            return {"success": False, "speak_en": "Search timed out. Try a more specific term.", "speak_ta": "Search timeout அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "pattern": {"type": "string", "description": "Text pattern to search for"},
            "directory": {"type": "string", "description": "Directory to search (default: home)"},
        }, "required": ["pattern"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"grep {kwargs.get('pattern', '')}")["speak_en"])
