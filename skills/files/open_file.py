import subprocess, asyncio
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

class OpenFileSkill(BaseSkill):
    name = "open_file"
    description = "Open a file or folder in the default application"
    triggers = ["open file", "open", "thira", "thirakku", "open folder"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text
        for w in ["open file", "open folder", "thirakku", "thira", "open"]:
            t = t.replace(w, "").strip()
        if not t:
            target = str(Path.home())
        else:
            target = str(Path(t).expanduser())
        try:
            subprocess.Popen(["xdg-open", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "speak_en": f"Opening {Path(target).name}.", "speak_ta": f"{Path(target).name} திறக்கிறேன் அண்ணா."}
        except Exception as e:
            return {"success": False, "speak_en": f"Failed to open: {e}", "speak_ta": "திறக்க முடியல அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "path": {"type": "string", "description": "File or directory path to open"},
        }, "required": ["path"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"open {kwargs.get('path', '')}")["speak_en"])
