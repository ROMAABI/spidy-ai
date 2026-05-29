import subprocess, asyncio
from pathlib import Path
from skills.base_skill import BaseSkill, SkillResult

class ArchiveSkill(BaseSkill):
    name = "archive"
    description = "Compress or extract zip/tar archives"
    triggers = ["compress", "extract", "zip", "unzip", "tar", "archive"]

    def run(self, text: str, lang: str = "en") -> dict:
        t = text
        for w in ["compress", "extract", "archive"]:
            t = t.replace(w, "").strip()
        if not t:
            return {"success": False, "speak_en": "What to compress/extract?", "speak_ta": "Enna compress/extract பண்ணட்டும் அண்ணா?"}

        words = t.split()
        target = Path(words[-1]).expanduser() if words else None

        if "extract" in t or "unzip" in t or "untar" in t:
            if target and target.exists():
                ext = target.suffix
                if ext == ".zip":
                    subprocess.run(["unzip", str(target), "-d", str(target.parent)], check=False)
                elif ext in (".tar.gz", ".tgz"):
                    subprocess.run(["tar", "-xzf", str(target), "-C", str(target.parent)], check=False)
                elif ext == ".tar":
                    subprocess.run(["tar", "-xf", str(target), "-C", str(target.parent)], check=False)
                else:
                    return {"success": False, "speak_en": f"Unsupported format: {ext}", "speak_ta": "Format support பண்ணல அண்ணா."}
                return {"success": True, "speak_en": f"Extracted {target.name}.", "speak_ta": f"Extract பண்ணேன் அண்ணா."}
            return {"success": False, "speak_en": "File not found.", "speak_ta": "File கிடைக்கல அண்ணா."}

        if "compress" in t or "zip" in t:
            if target and target.exists():
                if target.is_dir():
                    archive_name = str(target) + ".zip"
                    subprocess.run(["zip", "-r", archive_name, str(target)], check=False)
                else:
                    archive_name = str(target) + ".zip"
                    subprocess.run(["zip", archive_name, str(target)], check=False)
                return {"success": True, "speak_en": f"Compressed to {Path(archive_name).name}.", "speak_ta": "Compress பண்ணேன் அண்ணா."}
            return {"success": False, "speak_en": "File not found.", "speak_ta": "File கிடைக்கல அண்ணா."}

        return {"success": False, "speak_en": "Say compress or extract.", "speak_ta": "Compress/extract சொல்லுங்க அண்ணா."}

    @classmethod
    def _tool_params(cls) -> dict:
        return {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["compress", "extract"], "description": "Archive action"},
            "path": {"type": "string", "description": "Path to compress or extract"},
        }, "required": ["action", "path"]}

    async def execute(self, **kwargs) -> SkillResult:
        return SkillResult(success=True, output=self.run(f"{kwargs.get('action', '')} {kwargs.get('path', '')}")["speak_en"])
